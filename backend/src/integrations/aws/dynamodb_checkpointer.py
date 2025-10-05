"""
DynamoDB Checkpointer for LangGraph - Production State Persistence

This replaces MemorySaver with DynamoDB-backed state persistence for
production deployment. Enables conversation continuity across Lambda invocations.

Features:
- Atomic state updates with DynamoDB
- TTL-based automatic cleanup
- Point-in-time recovery enabled
- Session-based state isolation
"""

import json
import hashlib
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
import boto3
from boto3.dynamodb.conditions import Key

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("dynamodb_checkpointer")


class DynamoDBCheckpointer(BaseCheckpointSaver):
    """
    DynamoDB-backed checkpointer for LangGraph state persistence.

    Stores conversation state in DynamoDB with:
    - session_id as partition key
    - checkpoint_id as sort key
    - Automatic TTL cleanup (30 days)
    - Point-in-time recovery

    Usage:
        checkpointer = DynamoDBCheckpointer()
        graph.compile(checkpointer=checkpointer)
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        ttl_days: int = 30,
        region_name: Optional[str] = None
    ):
        """
        Initialize DynamoDB checkpointer.

        Args:
            table_name: DynamoDB table name (defaults to settings.DYNAMO_TABLE_CONVERSATIONS)
            ttl_days: Days until checkpoint expires (default: 30)
            region_name: AWS region (defaults to settings.AWS_REGION)
        """
        self.table_name = table_name or settings.DYNAMO_TABLE_CONVERSATIONS
        self.ttl_days = ttl_days
        self.region_name = region_name or settings.AWS_REGION

        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        self.table = self.dynamodb.Table(self.table_name)

        logger.info(
            f"DynamoDB Checkpointer initialized",
            extra={
                "table": self.table_name,
                "region": self.region_name,
                "ttl_days": ttl_days,
            }
        )

    def _generate_checkpoint_id(self, config: RunnableConfig) -> str:
        """
        Generate deterministic checkpoint ID from config.

        Uses thread_id (session_id) + checkpoint_ns to create unique checkpoint.
        """
        thread_id = config.get("configurable", {}).get("thread_id", "default")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        # Create checkpoint ID: thread_id + timestamp + namespace
        timestamp = datetime.utcnow().isoformat()
        checkpoint_data = f"{thread_id}:{checkpoint_ns}:{timestamp}"

        # Hash for consistent length
        checkpoint_id = hashlib.sha256(checkpoint_data.encode()).hexdigest()[:16]

        return checkpoint_id

    def _get_session_id(self, config: RunnableConfig) -> str:
        """Extract session ID from config."""
        return config.get("configurable", {}).get("thread_id", "default")

    def _calculate_ttl(self) -> int:
        """Calculate TTL timestamp (Unix epoch)."""
        expiration = datetime.utcnow() + timedelta(days=self.ttl_days)
        return int(expiration.timestamp())

    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """
        Retrieve checkpoint from DynamoDB.

        Args:
            config: Runnable config with thread_id (session_id)

        Returns:
            Checkpoint if found, None otherwise
        """
        session_id = self._get_session_id(config)

        try:
            # Query for latest checkpoint for this session
            response = self.table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,  # Descending order (latest first)
                Limit=1
            )

            items = response.get('Items', [])
            if not items:
                logger.debug(f"No checkpoint found for session: {session_id}")
                return None

            item = items[0]

            # Deserialize checkpoint
            checkpoint = Checkpoint(
                v=item.get('version', 1),
                ts=item.get('created_at', datetime.utcnow().isoformat()),
                channel_values=json.loads(item.get('state', '{}')),
                channel_versions={},  # Not used in our implementation
                versions_seen={}  # Not used in our implementation
            )

            logger.debug(
                f"Retrieved checkpoint",
                extra={
                    "session_id": session_id,
                    "checkpoint_id": item.get('checkpoint_id'),
                }
            )

            return checkpoint

        except Exception as e:
            logger.error(
                f"Error retrieving checkpoint: {e}",
                extra={"session_id": session_id}
            )
            return None

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RunnableConfig:
        """
        Save checkpoint to DynamoDB.

        Args:
            config: Runnable config with thread_id (session_id)
            checkpoint: Checkpoint to save
            metadata: Optional metadata

        Returns:
            Updated config with checkpoint ID
        """
        session_id = self._get_session_id(config)
        checkpoint_id = self._generate_checkpoint_id(config)

        try:
            # Serialize state
            state_json = json.dumps(checkpoint.get('channel_values', {}))

            # Prepare item
            item = {
                'session_id': session_id,
                'checkpoint_id': checkpoint_id,
                'version': checkpoint.get('v', 1),
                'created_at': checkpoint.get('ts', datetime.utcnow().isoformat()),
                'state': state_json,
                'metadata': json.dumps(metadata or {}),
                'ttl': self._calculate_ttl(),
            }

            # Write to DynamoDB
            self.table.put_item(Item=item)

            logger.info(
                f"Saved checkpoint",
                extra={
                    "session_id": session_id,
                    "checkpoint_id": checkpoint_id,
                    "state_size": len(state_json),
                }
            )

            # Return updated config with checkpoint ID
            updated_config = config.copy()
            if "configurable" not in updated_config:
                updated_config["configurable"] = {}
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id

            return updated_config

        except Exception as e:
            logger.error(
                f"Error saving checkpoint: {e}",
                extra={
                    "session_id": session_id,
                    "checkpoint_id": checkpoint_id,
                }
            )
            # Return original config on error
            return config

    def list(
        self,
        config: RunnableConfig,
        limit: Optional[int] = 10
    ) -> List[Tuple[RunnableConfig, Checkpoint]]:
        """
        List recent checkpoints for a session.

        Args:
            config: Runnable config with thread_id (session_id)
            limit: Maximum number of checkpoints to return

        Returns:
            List of (config, checkpoint) tuples
        """
        session_id = self._get_session_id(config)

        try:
            response = self.table.query(
                KeyConditionExpression=Key('session_id').eq(session_id),
                ScanIndexForward=False,  # Descending order (latest first)
                Limit=limit or 10
            )

            items = response.get('Items', [])
            results = []

            for item in items:
                checkpoint = Checkpoint(
                    v=item.get('version', 1),
                    ts=item.get('created_at', datetime.utcnow().isoformat()),
                    channel_values=json.loads(item.get('state', '{}')),
                    channel_versions={},
                    versions_seen={}
                )

                # Create config for this checkpoint
                checkpoint_config = config.copy()
                checkpoint_config["configurable"] = {
                    "thread_id": session_id,
                    "checkpoint_id": item.get('checkpoint_id'),
                }

                results.append((checkpoint_config, checkpoint))

            logger.debug(
                f"Listed {len(results)} checkpoints",
                extra={"session_id": session_id}
            )

            return results

        except Exception as e:
            logger.error(
                f"Error listing checkpoints: {e}",
                extra={"session_id": session_id}
            )
            return []


def get_dynamodb_checkpointer() -> DynamoDBCheckpointer:
    """
    Factory function to create DynamoDB checkpointer.

    Returns:
        DynamoDBCheckpointer configured with settings
    """
    return DynamoDBCheckpointer(
        table_name=settings.DYNAMO_TABLE_CONVERSATIONS,
        ttl_days=30,
        region_name=settings.AWS_REGION
    )
