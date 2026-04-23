"""Base agent class for common OpenAI operations."""
import logging
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
from openai import OpenAI
from shared.models import AgentResponse
from shared.config import ModelConfig

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for agents using OpenAI API."""

    # Load model from config
    MODEL_NAME = ModelConfig.MODEL_NAME
    MAX_TOKENS = ModelConfig.MAX_TOKENS

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI()

    def call_openai(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call OpenAI API with given prompt.

        Args:
            prompt: The prompt to send to OpenAI
            system_prompt: Optional system message to guide the AI behavior

        Returns:
            Response text from OpenAI
            
        Raises:
            RuntimeError: If OpenAI API fails
        """
        try:
            # Default system prompt if not provided
            if system_prompt is None:
                system_prompt = "You are a helpful assistant."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            message = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                max_tokens=self.MAX_TOKENS,
                messages=messages,
            )
            return message.choices[0].message.content.strip()
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def process_batch(
        self,
        items: List[Any],
        processor_func: Callable[[Any], Any],
        error_key: str = "email_id"
    ) -> AgentResponse:
        """
        Generic batch processor to avoid code duplication.
        
        Args:
            items: List of items to process
            processor_func: Function that takes one item and returns processed result
            error_key: Key name for error field (default: email_id)
        
        Returns:
            AgentResponse with processed items or error details
        """
        try:
            results = []
            errors = []
            
            agent_name = self.__class__.__name__.replace("Agent", "").upper()
            print(f"   ⚙️  {agent_name}: Processing {len(items)} emails...")

            for idx, item in enumerate(items):
                try:
                    subject = getattr(item, "subject", f"Email {idx+1}")
                    print(f"      ⏳ [{idx+1}/{len(items)}] Processing: {str(subject)[:50]}")
                    logger.info(f"⏳ {agent_name}: Processing email {idx+1}/{len(items)}")
                    
                    result = processor_func(item)
                    results.append(result)
                    print(f"         ✓ Completed")
                    
                except Exception as e:
                    error_entry = {
                        error_key: getattr(item, error_key, f"item_{idx}"),
                        "error": str(e),
                    }
                    # Add sender if available
                    if hasattr(item, "sender"):
                        error_entry["sender"] = item.sender
                    errors.append(error_entry)
                    print(f"         ✗ Error: {str(e)[:50]}")
                    logger.error(f"✗ {agent_name}: Error processing email {idx+1}: {str(e)}")

            # Safe serialization: handle both Pydantic models and dicts
            data = [
                e.model_dump() if hasattr(e, "model_dump") else e
                for e in results
            ]

            return self.create_success_response(
                data=data,
                total_processed=len(results),
                total_errors=len(errors),
                errors=errors if errors else None
            )

        except Exception as e:
            return self.create_error_response(str(e))

    def create_success_response(
        self,
        data: List[Dict[str, Any]],
        total_processed: int,
        total_errors: int,
        errors: List[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Create success/partial response.

        Args:
            data: Processed data
            total_processed: Number of successfully processed items
            total_errors: Number of processing errors
            errors: List of error details

        Returns:
            AgentResponse with success status
        """
        metadata = {
            "total_processed": total_processed,
            "total_errors": total_errors,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if errors:
            metadata["errors"] = errors
        
        return AgentResponse(
            status="success" if not errors else "partial",
            data=data,
            metadata=metadata,
            error=None,
        )

    def create_error_response(self, error_msg: str) -> AgentResponse:
        """
        Create error response.

        Args:
            error_msg: Error message

        Returns:
            AgentResponse with error status
        """
        return AgentResponse(
            status="error",
            data=None,
            metadata={"timestamp": datetime.utcnow().isoformat()},
            error=error_msg,
        )
