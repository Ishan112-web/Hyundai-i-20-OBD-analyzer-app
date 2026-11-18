"""
i20 AI Garage - AI Service Tests
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_service import AIService, AIServiceError, ChatMessage, ModelInfo


@pytest.fixture
def ai_service():
    """Create AI service instance for testing."""
    return AIService()


@patch('services.ai_service.requests.Session.get')
def test_check_connection_success(mock_get, ai_service):
    """Test successful connection check."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = ai_service.check_connection()
    assert result is True
    mock_get.assert_called_once()


@patch('services.ai_service.requests.Session.get')
def test_check_connection_failure(mock_get, ai_service):
    """Test failed connection check."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError()

    result = ai_service.check_connection()
    assert result is False


@patch('services.ai_service.requests.Session.get')
def test_get_available_models(mock_get, ai_service):
    """Test fetching available models."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "model1", "object": "model", "owned_by": "org"},
            {"id": "model2", "object": "model", "owned_by": "org"},
        ]
    }
    mock_get.return_value = mock_response

    models = ai_service.get_available_models(force_refresh=True)

    assert len(models) == 2
    assert models[0].id == "model1"
    assert models[1].id == "model2"


@patch('services.ai_service.requests.Session.post')
def test_chat_completion_success(mock_post, ai_service):
    """Test successful chat completion."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "chatcmpl-123",
        "model": "qwen2.5-3b-instruct",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "Test response"},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "created": 1234567890
    }
    mock_post.return_value = mock_response

    messages = [ChatMessage(role="user", content="Hello")]
    response = ai_service.chat_completion(messages)

    assert response.content == "Test response"
    assert response.model == "qwen2.5-3b-instruct"
    assert response.usage["total_tokens"] == 30


@patch('services.ai_service.requests.Session.post')
def test_chat_completion_timeout(mock_post, ai_service):
    """Test chat completion timeout handling."""
    import requests
    mock_post.side_effect = requests.exceptions.Timeout()

    messages = [ChatMessage(role="user", content="Hello")]

    with pytest.raises(AIServiceError) as exc_info:
        ai_service.chat_completion(messages)

    assert "timed out" in str(exc_info.value).lower()


@patch('services.ai_service.requests.Session.post')
def test_chat_completion_connection_error(mock_post, ai_service):
    """Test chat completion connection error handling."""
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError()

    messages = [ChatMessage(role="user", content="Hello")]

    with pytest.raises(AIServiceError) as exc_info:
        ai_service.chat_completion(messages)

    assert "cannot connect" in str(exc_info.value).lower()


def test_create_conversation_context(ai_service):
    """Test conversation context creation."""
    history = [
        ChatMessage(role="user", content="Hello"),
        ChatMessage(role="assistant", content="Hi there!"),
    ]
    vehicle_context = {"rpm": 2000, "speed_kmh": 60}

    messages = ai_service.create_conversation_context(
        user_message="What's my RPM?",
        history=history,
        vehicle_context=vehicle_context
    )

    assert len(messages) >= 4  # system + context + history(2) + user
    assert messages[0].role == "system"
    assert "i20 AI Garage" in messages[0].content
    assert messages[-1].role == "user"
    assert messages[-1].content == "What's my RPM?"


def test_format_vehicle_context(ai_service):
    """Test vehicle context formatting."""
    context = {
        "rpm": 2500.5,
        "speed_kmh": 80.0,
        "coolant_temp_c": 92.3,
        "throttle_pos_pct": 35.0,
    }

    formatted = ai_service._format_vehicle_context(context)

    # RPM is formatted as integer (.0f)
    assert "2500" in formatted
    assert "80.0" in formatted
    assert "92.3" in formatted
    assert "35.0" in formatted
    assert "SIMULATED" in formatted


def test_get_system_status(ai_service):
    """Test system status retrieval."""
    with patch.object(ai_service, 'check_connection', return_value=True), \
         patch.object(ai_service, 'get_available_models', return_value=[
             ModelInfo("model1", "model", "org"),
             ModelInfo("model2", "model", "org"),
         ]), \
         patch.object(ai_service, 'is_model_available', return_value=True):

        status = ai_service.get_system_status()

        assert status["connected"] is True
        assert status["configured_model"] == "qwen2.5-3b-instruct"
        assert status["model_available"] is True
        assert len(status["available_models"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])