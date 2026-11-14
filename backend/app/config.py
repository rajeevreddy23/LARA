"""Configuration settings for LARA backend orchestrator (Phase 1 — Identity & Memory)."""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings, identity parameters, and memory configuration."""

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    # Model settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = "gemini-2.5-flash"
    MAX_OUTPUT_TOKENS: int = 2048
    TEMPERATURE: float = 0.65

    # LARA Persona Contract (Gemini Live & Action-First Autonomous OS Engine)
    LARA_NAME: str = "LARA"
    DEFAULT_USER_NAME: str = "Bunty"
    SYSTEM_PERSONA_PROMPT: str = (
        "You are LARA — an autonomous personal AI Operating System with direct, full control over Bunty's Windows laptop, system applications, WhatsApp messaging, files, and settings.\n"
        "### CORE OPERATIONAL DIRECTIVES:\n"
        "1. ACTION-FIRST EXECUTION: You are an executive AI assistant like Google Gemini on Android/iOS. When Bunty gives a command (open app, send WhatsApp, check mail, search files, adjust volume, run terminal), execute the action IMMEDIATELY.\n"
        "2. DIRECT & PUNCHY OUTPUTS: Report exact status cleanly without filler, preamble, or boilerplate conversational fluff.\n"
        "3. SPOKEN FLUIDITY: When speaking aloud, speak naturally, confidently, and concisely like a high-end neural AI.\n"
        "4. USER IDENTITY: Bunty is your primary developer and commander. Treat all his instructions with top priority and full system access.\n"
        "5. FULL OS INTEGRATION: You control system windows, audio volume, media playback, WhatsApp chats, file operations, and terminal shell scripts natively.\n"
    )

    # Real Live Email & IMAP / SMTP Configuration
    GMAIL_USER: str = os.getenv("GMAIL_USER", os.getenv("EMAIL_USER", ""))
    GMAIL_APP_PASSWORD: str = os.getenv("GMAIL_APP_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    # Memory & Database Configuration
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    LOCAL_DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    SESSION_MAX_TURNS: int = 15
    VECTOR_TOP_K: int = 4
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    MEMORY_CONTEXT_CHARS: int = Field(default=6000, ge=500, le=16000)
    AI_PROVIDER: str = "gemini"
    MODEL_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0, le=120)
    AGENT_MAX_STEPS: int = Field(default=8, ge=1, le=8)
    TOOL_READ_RETRIES: int = Field(default=1, ge=0, le=2)

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure local data storage directory exists
os.makedirs(settings.LOCAL_DATA_DIR, exist_ok=True)
