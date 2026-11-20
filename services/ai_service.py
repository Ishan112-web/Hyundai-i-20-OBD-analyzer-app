"""
i20 AI Garage - AI Service

LM Studio integration for local AI automotive assistant.
Supports both regular chat and structured JSON output for diagnostics.
"""

import requests
import json
import logging
from typing import Optional, List, Dict, Any, Generator, Type, TypeVar
from dataclasses import dataclass
from datetime import datetime
import time
from pydantic import BaseModel

from config import (
    LM_STUDIO_BASE_URL, LM_STUDIO_MODEL, LM_STUDIO_TEMPERATURE,
    LM_STUDIO_TIMEOUT, AI_SYSTEM_PROMPT, IS_STAGING
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    object: str
    owned_by: str


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str
    content: str


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""
    id: str
    model: str
    content: str
    finish_reason: str
    usage: Dict[str, int]
    created: int


class AIService:
    """Service for interacting with LM Studio local API."""

    def __init__(self):
        # Handle missing/empty LM_STUDIO_BASE_URL (staging mode)
        base_url = LM_STUDIO_BASE_URL or ""
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.model = LM_STUDIO_MODEL
        self.temperature = LM_STUDIO_TEMPERATURE
        self.timeout = LM_STUDIO_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
        self._available_models: List[ModelInfo] = []
        self._last_model_check = 0
        self._model_cache_ttl = 60  # seconds
        self._staging_mode = IS_STAGING
        self._connection_checked = False
        self._connection_result = False

    def check_connection(self) -> bool:
        """Check if LM Studio server is available."""
        # Cache result to avoid repeated failed connections
        if self._connection_checked:
            return self._connection_result

        # In staging mode or if no base URL configured, skip connection attempt
        if self._staging_mode or not self.base_url:
            logger.info("AI Service: LM Studio not configured (staging mode or empty URL)")
            self._connection_checked = True
            self._connection_result = False
            return False

        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=5
            )
            self._connection_result = response.status_code == 200
            self._connection_checked = True
            return self._connection_result
        except requests.exceptions.RequestException as e:
            logger.warning(f"LM Studio connection check failed: {e}")
            self._connection_checked = True
            self._connection_result = False
            return False

    def get_available_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """Get list of available models from LM Studio."""
        # In staging mode or if no base URL, return empty list
        if self._staging_mode or not self.base_url:
            return []

        current_time = time.time()
        if not force_refresh and self._available_models and \
           (current_time - self._last_model_check) < self._model_cache_ttl:
            return self._available_models

        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            self._available_models = [
                ModelInfo(
                    id=model.get("id", ""),
                    object=model.get("object", ""),
                    owned_by=model.get("owned_by", "")
                )
                for model in data.get("data", [])
            ]
            self._last_model_check = current_time
            return self._available_models
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch models: {e}")
            return self._available_models  # Return cached models if available

    def is_model_available(self, model_name: str = None) -> bool:
        """Check if the configured model is available."""
        model = model_name or self.model
        models = self.get_available_models()
        return any(m.id == model for m in models)

    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> ChatCompletionResponse:
        """
        Send a chat completion request to LM Studio.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            ChatCompletionResponse with the assistant's response

        Raises:
            AIServiceError: If LM Studio is not available (staging mode or connection failure)
        """
        # In staging mode or if no base URL, return informative error
        if self._staging_mode or not self.base_url:
            raise AIServiceError(
                "AI Assistant unavailable: LM Studio not configured in staging environment. "
                "Please run LM Studio locally for AI features."
            )

        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            response.raise_for_status()

            if stream:
                return self._handle_stream_response(response)
            else:
                return self._handle_response(response)

        except requests.exceptions.Timeout:
            raise AIServiceError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise AIServiceError("Cannot connect to LM Studio. Is it running on localhost:1234?")
        except requests.exceptions.HTTPError as e:
            raise AIServiceError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except json.JSONDecodeError:
            raise AIServiceError("Invalid JSON response from LM Studio")
        except Exception as e:
            raise AIServiceError(f"Unexpected error: {str(e)}")

    def _handle_response(self, response: requests.Response) -> ChatCompletionResponse:
        """Handle non-streaming response."""
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        return ChatCompletionResponse(
            id=data.get("id", ""),
            model=data.get("model", ""),
            content=message.get("content", ""),
            finish_reason=choice.get("finish_reason", ""),
            usage=data.get("usage", {}),
            created=data.get("created", 0)
        )

    def _handle_stream_response(self, response: requests.Response) -> Generator[str, None, None]:
        """Handle streaming response - yields content chunks."""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                line = line.strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choice = data.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Generator[str, None, None]:
        """
        Send a streaming chat completion request.

        Yields:
            Content chunks as they arrive

        Raises:
            AIServiceError: If LM Studio is not available (staging mode or connection failure)
        """
        # In staging mode or if no base URL, raise informative error
        if self._staging_mode or not self.base_url:
            raise AIServiceError(
                "AI Assistant unavailable: LM Studio not configured in staging environment. "
                "Please run LM Studio locally for AI features."
            )

        model = model or self.model
        temperature = temperature if temperature is not None else self.temperature

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            yield from self._handle_stream_response(response)

        except requests.exceptions.Timeout:
            raise AIServiceError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise AIServiceError("Cannot connect to LM Studio. Is it running on localhost:1234?")
        except requests.exceptions.HTTPError as e:
            raise AIServiceError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise AIServiceError(f"Unexpected error: {str(e)}")

    def create_conversation_context(
        self,
        user_message: str,
        history: List[ChatMessage] = None,
        vehicle_context: Dict[str, Any] = None
    ) -> List[ChatMessage]:
        """
        Create a conversation context with system prompt and history.

        Args:
            user_message: The current user message
            history: Previous conversation history
            vehicle_context: Current vehicle telemetry/context

        Returns:
            List of messages ready for API call
        """
        messages = [ChatMessage(role="system", content=AI_SYSTEM_PROMPT)]

        # Add vehicle context if provided
        if vehicle_context:
            context_msg = self._format_vehicle_context(vehicle_context)
            messages.append(ChatMessage(role="system", content=context_msg))

        # Add conversation history (limit to last 10 exchanges to manage context)
        if history:
            # Keep last 20 messages (10 user + 10 assistant)
            recent_history = history[-20:]
            for msg in recent_history:
                messages.append(ChatMessage(role=msg.role, content=msg.content))

        # Add current user message
        messages.append(ChatMessage(role="user", content=user_message))

        return messages

    def _format_vehicle_context(self, context: Dict[str, Any]) -> str:
        """Format vehicle telemetry data for AI context."""
        lines = ["Current Vehicle Telemetry (SIMULATED DATA):"]

        if "rpm" in context:
            lines.append(f"- Engine RPM: {context['rpm']:.0f} RPM")
        if "speed_kmh" in context:
            lines.append(f"- Vehicle Speed: {context['speed_kmh']:.1f} km/h")
        if "coolant_temp_c" in context:
            lines.append(f"- Coolant Temperature: {context['coolant_temp_c']:.1f}°C")
        if "throttle_pos_pct" in context:
            lines.append(f"- Throttle Position: {context['throttle_pos_pct']:.1f}%")
        if "engine_load_pct" in context:
            lines.append(f"- Engine Load: {context['engine_load_pct']:.1f}%")
        if "intake_pressure_kpa" in context:
            lines.append(f"- Intake Manifold Pressure: {context['intake_pressure_kpa']:.1f} kPa")
        if "stft_b1_pct" in context:
            lines.append(f"- Short Term Fuel Trim (Bank 1): {context['stft_b1_pct']:.1f}%")
        if "ltft_b1_pct" in context:
            lines.append(f"- Long Term Fuel Trim (Bank 1): {context['ltft_b1_pct']:.1f}%")
        if "voltage_v" in context:
            lines.append(f"- Battery Voltage: {context['voltage_v']:.2f} V")

        lines.append("\nNOTE: These are SIMULATED values for demonstration. Not real vehicle data.")

        return "\n".join(lines)

    def get_system_status(self) -> Dict[str, Any]:
        """Get AI service status information."""
        connected = self.check_connection()
        models = self.get_available_models() if connected else []
        model_available = self.is_model_available() if connected else False

        return {
            "connected": connected,
            "base_url": self.base_url if self.base_url else "Not configured (staging)",
            "configured_model": self.model,
            "model_available": model_available,
            "available_models": [m.id for m in models],
            "temperature": self.temperature,
            "timeout": self.timeout,
            "staging_mode": self._staging_mode,
            "ai_available": connected and model_available,
        }

    # =========================================================================
    # STRUCTURED OUTPUT SUPPORT
    # =========================================================================

    def structured_completion(
        self,
        messages: List[ChatMessage],
        response_model: Type[T],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        max_retries: int = 2
    ) -> T:
        """
        Get a structured JSON response validated against a Pydantic model.

        Args:
            messages: List of chat messages
            response_model: Pydantic model class to validate against
            model: Model to use
            temperature: Sampling temperature (low for structured output)
            max_tokens: Maximum tokens to generate
            max_retries: Maximum retry attempts on validation failure

        Returns:
            Instance of response_model with validated data

        Raises:
            AIServiceError: If all retries fail
        """
        # Generate JSON schema from Pydantic model
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        # Add schema instruction to system message
        schema_instruction = (
            f"\n\nYou MUST respond with valid JSON that conforms to this schema:\n"
            f"{schema_str}\n\n"
            f"Output ONLY the JSON object. No additional text, no markdown formatting."
        )

        # Create messages with schema instruction
        enhanced_messages = list(messages)
        # Find system message and append schema instruction
        for msg in enhanced_messages:
            if msg.role == "system":
                msg.content += schema_instruction
                break
        else:
            # No system message, add one
            enhanced_messages.insert(0, ChatMessage(
                role="system",
                content=schema_instruction
            ))

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = self.chat_completion(
                    messages=enhanced_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                if not response.content:
                    raise AIServiceError("Empty response from AI")

                # Extract JSON from response
                json_str = self._extract_json(response.content)
                if not json_str:
                    raise AIServiceError("No valid JSON found in response")

                # Parse and validate
                data = json.loads(json_str)
                return response_model(**data)

            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                logger.warning(f"Structured completion attempt {attempt + 1} failed: {last_error}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Structured completion attempt {attempt + 1} failed: {last_error}")

            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))  # Exponential backoff

        raise AIServiceError(f"Structured completion failed after {max_retries + 1} attempts: {last_error}")

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from AI response text."""
        text = text.strip()

        # Look for code block with json
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Look for code block without language
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]

        return None

    def structured_completion_stream(
        self,
        messages: List[ChatMessage],
        response_model: Type[T],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get a streaming structured completion.

        Yields partial JSON objects as they are generated.
        Note: Validation only happens on complete response.
        """
        # For streaming, we don't inject schema (too complex for streaming)
        # Instead, we rely on the model to output valid JSON
        enhanced_messages = list(messages)
        for msg in enhanced_messages:
            if msg.role == "system":
                msg.content += (
                    "\n\nYou MUST respond with valid JSON only. "
                    "No additional text, no markdown formatting."
                )
                break

        for chunk in self.chat_completion_stream(
            messages=enhanced_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield {"chunk": chunk, "is_complete": False}

        # Signal completion - full validation would need accumulated response
        yield {"chunk": "", "is_complete": True}


class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass


# Singleton instance
_ai_instance: Optional[AIService] = None

def get_ai_service() -> AIService:
    """Get the AI service singleton."""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = AIService()
    return _ai_instance