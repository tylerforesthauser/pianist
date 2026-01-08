"""
Configuration management for pianist.

Supports multiple configuration sources (in order of precedence):
1. Command-line arguments (highest priority)
2. Environment variables
3. User config file (~/.pianist/config.toml)
4. Project config file (.pianist/config.toml)
5. Defaults (lowest priority)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Try to import tomllib (Python 3.11+) or tomli (for older versions)
HAS_TOML = False
tomllib = None
tomli = None

try:
    import tomllib  # Python 3.11+
    HAS_TOML = True
except ImportError:
    try:
        import tomli  # type: ignore
        HAS_TOML = True
    except ImportError:
        HAS_TOML = False


class Config:
    """Global configuration for pianist."""
    
    def __init__(self):
        self._user_config: dict[str, Any] = {}
        self._project_config: dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from files."""
        if not HAS_TOML:
            return
        
        # Load user config (~/.pianist/config.toml)
        user_config_path = Path.home() / ".pianist" / "config.toml"
        if user_config_path.exists():
            try:
                with open(user_config_path, "rb") as f:
                    if tomllib is not None:
                        self._user_config = tomllib.load(f)
                    elif tomli is not None:
                        self._user_config = tomli.load(f)  # type: ignore
            except Exception:
                # Silently ignore config file errors
                pass
        
        # Load project config (.pianist/config.toml)
        # Look in current directory and parent directories (up to 3 levels)
        for level in range(4):
            if level == 0:
                project_config_path = Path.cwd() / ".pianist" / "config.toml"
            else:
                project_config_path = Path.cwd()
                for _ in range(level):
                    project_config_path = project_config_path.parent
                project_config_path = project_config_path / ".pianist" / "config.toml"
            project_config_path = project_config_path.resolve()
            if project_config_path.exists():
                try:
                    with open(project_config_path, "rb") as f:
                        if tomllib is not None:
                            self._project_config = tomllib.load(f)
                        elif tomli is not None:
                            self._project_config = tomli.load(f)  # type: ignore
                    break
                except Exception:
                    # Silently ignore config file errors
                    pass
    
    def get_ai_provider(self, default: str = "openrouter") -> str:
        """Get AI provider from config or environment, with fallback to default."""
        # Check environment variable first
        env_provider = os.getenv("AI_PROVIDER")
        if env_provider:
            return env_provider
        
        # Check user config
        if "ai" in self._user_config and "provider" in self._user_config["ai"]:
            return self._user_config["ai"]["provider"]
        
        # Check project config
        if "ai" in self._project_config and "provider" in self._project_config["ai"]:
            return self._project_config["ai"]["provider"]
        
        return default
    
    def get_ai_model(self, provider: str | None = None, default: str | None = None) -> str | None:
        """Get AI model from config or environment, with fallback to default."""
        # Check environment variable first
        env_model = os.getenv("AI_MODEL")
        if env_model:
            return env_model
        
        # Check user config
        if "ai" in self._user_config:
            ai_config = self._user_config["ai"]
            # Check provider-specific model
            if provider and "models" in ai_config and provider in ai_config["models"]:
                return ai_config["models"][provider]
            # Check global model
            if "model" in ai_config:
                return ai_config["model"]
        
        # Check project config
        if "ai" in self._project_config:
            ai_config = self._project_config["ai"]
            # Check provider-specific model
            if provider and "models" in ai_config and provider in ai_config["models"]:
                return ai_config["models"][provider]
            # Check global model
            if "model" in ai_config:
                return ai_config["model"]
        
        return default
    
    def get_ai_delay(self, default: float = 0.0) -> float:
        """Get AI delay from config or environment, with fallback to default."""
        # Check environment variable first
        env_delay = os.getenv("AI_DELAY_SECONDS")
        if env_delay:
            try:
                return float(env_delay)
            except ValueError:
                pass
        
        # Check user config
        if "ai" in self._user_config and "delay" in self._user_config["ai"]:
            return float(self._user_config["ai"]["delay"])
        
        # Check project config
        if "ai" in self._project_config and "delay" in self._project_config["ai"]:
            return float(self._project_config["ai"]["delay"])
        
        return default


# Global config instance
_config = Config()


def get_ai_provider(default: str = "openrouter") -> str:
    """Get AI provider from config, with fallback to default."""
    return _config.get_ai_provider(default)


def get_ai_model(provider: str | None = None, default: str | None = None) -> str | None:
    """Get AI model from config, with fallback to default."""
    return _config.get_ai_model(provider, default)


def get_ai_delay(default: float = 0.0) -> float:
    """Get AI delay from config, with fallback to default."""
    return _config.get_ai_delay(default)

