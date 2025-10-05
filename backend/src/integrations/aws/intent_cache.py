"""
Q-LLM Intent Cache - Cost Optimization Layer

Caches Q-LLM intent extraction results in DynamoDB to avoid redundant LLM calls.
Expected cost reduction: 30-40% by caching common user queries.

Benefits:
- Reduced Bedrock API calls (lower cost)
- Faster response times (cache hits skip LLM)
- Consistent intent classification for identical inputs
- Automatic TTL cleanup (7 days)

Usage:
    cache = IntentCache()

    # Try cache first
    cached = await cache.get(user_message, conversation_context)
    if cached:
        return cached

    # Cache miss - call Q-LLM
    result = await q_llm_extract_intent(user_message)
    await cache.set(user_message, conversation_context, result)
"""

import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("intent_cache")


class IntentCache:
    """
    DynamoDB-backed cache for Q-LLM intent extraction results.

    Cache key: Hash of (user_message + conversation_context)
    TTL: 7 days (balance between cost savings and freshness)
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        ttl_days: int = 7,
        region_name: Optional[str] = None
    ):
        """
        Initialize intent cache.

        Args:
            table_name: DynamoDB table name (defaults to settings.DYNAMO_TABLE_INTENT_CACHE)
            ttl_days: Days until cache entry expires (default: 7)
            region_name: AWS region (defaults to settings.AWS_REGION)
        """
        self.table_name = table_name or settings.DYNAMO_TABLE_INTENT_CACHE
        self.ttl_days = ttl_days
        self.region_name = region_name or settings.AWS_REGION

        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region_name)
        self.table = self.dynamodb.Table(self.table_name)

        # Cache stats
        self.hits = 0
        self.misses = 0

        logger.info(
            f"Intent Cache initialized",
            extra={
                "table": self.table_name,
                "region": self.region_name,
                "ttl_days": ttl_days,
            }
        )

    def _generate_cache_key(
        self,
        user_message: str,
        conversation_context: str = ""
    ) -> str:
        """
        Generate deterministic cache key from input.

        Args:
            user_message: Raw user input
            conversation_context: Previous conversation (optional)

        Returns:
            SHA256 hash of inputs
        """
        # Normalize inputs (lowercase, strip whitespace)
        normalized_message = user_message.lower().strip()
        normalized_context = conversation_context.lower().strip()

        # Combine and hash
        cache_input = f"{normalized_message}||{normalized_context}"
        cache_key = hashlib.sha256(cache_input.encode()).hexdigest()

        return cache_key

    def _calculate_ttl(self) -> int:
        """Calculate TTL timestamp (Unix epoch)."""
        expiration = datetime.utcnow() + timedelta(days=self.ttl_days)
        return int(expiration.timestamp())

    async def get(
        self,
        user_message: str,
        conversation_context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached intent extraction result.

        Args:
            user_message: Raw user input
            conversation_context: Previous conversation (optional)

        Returns:
            Cached intent data if found, None otherwise
        """
        cache_key = self._generate_cache_key(user_message, conversation_context)

        try:
            response = self.table.get_item(
                Key={'input_hash': cache_key}
            )

            if 'Item' not in response:
                self.misses += 1
                logger.debug(
                    "❌ Cache MISS",
                    extra={
                        "cache_key": cache_key[:16],
                        "message_preview": user_message[:50],
                        "hit_rate": self._get_hit_rate(),
                    }
                )
                return None

            item = response['Item']

            # Check if TTL expired (belt-and-suspenders, DynamoDB should auto-delete)
            ttl = item.get('ttl', 0)
            if datetime.utcnow().timestamp() > ttl:
                logger.debug("Cache entry expired")
                return None

            # Deserialize cached intent
            cached_intent = json.loads(item.get('intent_data', '{}'))

            self.hits += 1
            logger.info(
                "✅ Cache HIT",
                extra={
                    "cache_key": cache_key[:16],
                    "message_preview": user_message[:50],
                    "intent": cached_intent.get('intent'),
                    "safety": cached_intent.get('safety_assessment'),
                    "hit_rate": self._get_hit_rate(),
                    "cost_saved": "~$0.0001",  # Approximate per Haiku call
                }
            )

            # Update access metadata
            self._update_access_count(cache_key)

            return cached_intent

        except ClientError as e:
            logger.error(
                f"DynamoDB error retrieving cache: {e}",
                extra={"cache_key": cache_key[:16]}
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving cache: {e}",
                extra={"cache_key": cache_key[:16]}
            )
            return None

    async def set(
        self,
        user_message: str,
        conversation_context: str,
        intent_data: Dict[str, Any]
    ) -> bool:
        """
        Cache intent extraction result.

        Args:
            user_message: Raw user input
            conversation_context: Previous conversation
            intent_data: Intent extraction result from Q-LLM

        Returns:
            True if cached successfully, False otherwise
        """
        cache_key = self._generate_cache_key(user_message, conversation_context)

        try:
            # Prepare cache item
            item = {
                'input_hash': cache_key,
                'user_message': user_message[:200],  # Store preview for debugging
                'intent_data': json.dumps(intent_data),
                'created_at': datetime.utcnow().isoformat(),
                'access_count': 0,
                'ttl': self._calculate_ttl(),
            }

            # Write to DynamoDB
            self.table.put_item(Item=item)

            logger.debug(
                "💾 Cached intent",
                extra={
                    "cache_key": cache_key[:16],
                    "message_preview": user_message[:50],
                    "intent": intent_data.get('intent'),
                    "safety": intent_data.get('safety_assessment'),
                }
            )

            return True

        except ClientError as e:
            logger.error(
                f"DynamoDB error caching intent: {e}",
                extra={"cache_key": cache_key[:16]}
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error caching intent: {e}",
                extra={"cache_key": cache_key[:16]}
            )
            return False

    def _update_access_count(self, cache_key: str) -> None:
        """Update access count for cache analytics."""
        try:
            self.table.update_item(
                Key={'input_hash': cache_key},
                UpdateExpression='SET access_count = access_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        except Exception as e:
            # Non-critical, don't fail on analytics update
            logger.debug(f"Failed to update access count: {e}")

    def _get_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate
        """
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self._get_hit_rate(),
            "total_requests": self.hits + self.misses,
        }


# Global cache instance
_intent_cache: Optional[IntentCache] = None


def get_intent_cache() -> IntentCache:
    """
    Get or create global intent cache instance.

    Returns:
        IntentCache instance
    """
    global _intent_cache
    if _intent_cache is None:
        _intent_cache = IntentCache(
            table_name=settings.DYNAMO_TABLE_INTENT_CACHE,
            ttl_days=7,
            region_name=settings.AWS_REGION
        )
    return _intent_cache
