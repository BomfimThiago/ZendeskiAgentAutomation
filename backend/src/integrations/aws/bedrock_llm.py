"""
AWS Bedrock LLM wrapper compatible with LangChain.

Replaces ChatOpenAI with Bedrock Claude models for production deployment.
"""

import json
import boto3
from typing import Any, Dict, List, Optional, Iterator
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field
from src.core.logging_config import get_logger

logger = get_logger("bedrock_llm")


class BedrockChatModel(BaseChatModel):
    """
    AWS Bedrock chat model wrapper for Claude.

    Compatible with LangChain's ChatModel interface, allowing drop-in
    replacement of ChatOpenAI with Bedrock.

    Usage:
        llm = BedrockChatModel(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            region_name="us-east-1"
        )
        response = llm.invoke([HumanMessage(content="Hello")])
    """

    model_id: str = Field(default="anthropic.claude-3-haiku-20240307-v1:0")
    region_name: str = Field(default="us-east-1")
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=1024)
    top_p: float = Field(default=1.0)

    client: Any = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )

    @property
    def _llm_type(self) -> str:
        return "bedrock-claude"

    def _convert_messages_to_bedrock_format(
        self, messages: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Convert LangChain messages to Bedrock Claude format."""

        # Separate system message from conversation
        system_message = ""
        conversation_messages = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_message = msg.content
            elif isinstance(msg, HumanMessage):
                conversation_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                conversation_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })

        # Build request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "messages": conversation_messages
        }

        if system_message:
            body["system"] = system_message

        return body

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response from Bedrock."""

        # Convert messages to Bedrock format
        body = self._convert_messages_to_bedrock_format(messages)

        # Add stop sequences if provided
        if stop:
            body["stop_sequences"] = stop

        # Call Bedrock
        try:
            logger.debug(f"Invoking Bedrock model: {self.model_id}")

            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())

            # Extract text from response
            content = response_body['content'][0]['text']

            logger.debug(f"Bedrock response received: {len(content)} chars")

            # Return in LangChain format
            message = AIMessage(content=content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])

        except Exception as e:
            logger.error(f"Bedrock error: {e}")
            raise

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Async generate (uses sync for now, Bedrock SDK doesn't have native async).

        TODO: Implement with aioboto3 for true async support.
        """
        return self._generate(messages, stop, run_manager, **kwargs)


# Convenience functions for different Claude models

def get_haiku_llm(temperature: float = 0.0, max_tokens: int = 1024) -> BedrockChatModel:
    """
    Get Claude 3 Haiku (fast, cheap - for Q-LLM).

    Pricing: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
    """
    return BedrockChatModel(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        temperature=temperature,
        max_tokens=max_tokens
    )


def get_sonnet_llm(temperature: float = 0.2, max_tokens: int = 2048) -> BedrockChatModel:
    """
    Get Claude 3.5 Sonnet (powerful - for P-LLM).

    Pricing: ~$3 per 1M input tokens, ~$15 per 1M output tokens
    """
    return BedrockChatModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        temperature=temperature,
        max_tokens=max_tokens
    )


def get_opus_llm(temperature: float = 0.2, max_tokens: int = 4096) -> BedrockChatModel:
    """
    Get Claude 3 Opus (most powerful - optional fallback).

    Pricing: ~$15 per 1M input tokens, ~$75 per 1M output tokens
    """
    return BedrockChatModel(
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        temperature=temperature,
        max_tokens=max_tokens
    )
