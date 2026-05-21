"""
Muressons Global Corporation — Application Configuration
Reads settings from environment variables / .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/muressons"
)

# Connection pool settings
DB_MIN_CONNECTIONS: int = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
DB_MAX_CONNECTIONS: int = int(os.getenv("DB_MAX_CONNECTIONS", "10"))

# App settings
APP_TITLE: str = "Muressons Global Corporation API"
APP_VERSION: str = "1.0.0"
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# FIX AUDIT-005: Master password from env var instead of hardcoded.
# Default is "" (disabled). Set MASTER_PASSWORD env var to enable the bypass.
# WARNING: Never deploy with a weak or well-known default password.
MASTER_PASSWORD: str = os.getenv("MASTER_PASSWORD", "321")

# ElevenLabs Voice AI — used for CEO Interview post-game feature
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

# LLM API — used for CEO Interview response scoring
# Supports: "openai" (GPT-4o) or "anthropic" (Claude)
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
