"""Keep Gemini offline and tests separate from the user's saved data."""
import os
import tempfile
from unittest.mock import AsyncMock
import pytest

_test_data = tempfile.TemporaryDirectory(prefix="lara-tests-")
os.environ["LOCAL_DATA_DIR"] = _test_data.name
os.environ["GEMINI_API_KEY"] = ""
os.environ["FIREBASE_PROJECT_ID"] = ""


@pytest.fixture(autouse=True)
def disable_network_speech(monkeypatch):
    from app.services.voice_service import voice_service
    monkeypatch.setattr(voice_service, "generate_speech_bytes", AsyncMock(return_value=b""))
