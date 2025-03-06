import os
from typing import Dict, List, Any, Optional
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

load_dotenv()


class AIModels:

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL",
                                         "http://localhost:11434")
        self.providers = self._initialize_providers()
        self.models = self._initialize_models()

    def _initialize_providers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize model providers with their available production models"""
        return {
            "groq": {
                "display_name":
                "Groq",
                "models": [
                    "llama-3.3-70b-versatile",  # Meta's Llama-3.3 70B versatile model
                    "llama-3.1-8b-instant",  # Meta's Llama-3.1 8B instant model
                    "mixtral-8x7b-32768",  # Mistral's Mixtral 8x7B with 32K context window
                    "llama-guard-3-8b",  # Meta's Llama-Guard 3 8B model
                    "llama3-70b-8192",  # Meta's Llama3 70B with 8K context window
                    "llama3-8b-8192",  # Meta's Llama3 8B with 8K context window
                    "gemma2-9b-it",  # Google's Gemma2 9B IT model
                    "distil-whisper-large-v3-en",  # HuggingFace's Distil Whisper Large V3 English model
                    "whisper-large-v3",  # OpenAI's Whisper Large V3 model
                    "whisper-large-v3-turbo"  # OpenAI's Whisper Large V3 Turbo model
                ],
                "api_key":
                self.groq_api_key
            },
            "ollama": {
                "display_name":
                "Ollama (Local)",
                "models": [
                    "llama2", "mistral", "codellama", "neural-chat",
                    "starling-lm"
                ],
                "base_url":
                self.ollama_base_url
            },
            "openai": {
                "display_name": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "api_key": self.openai_api_key
            },
            "google": {
                "display_name": "Google AI",
                "models": ["gemini-pro", "gemini-ultra", "palm-2"],
                "api_key": self.google_api_key
            },
            "anthropic": {
                "display_name": "Anthropic",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-2.1"],
                "api_key": self.anthropic_api_key
            }
        }

    def _initialize_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all available models from different providers"""
        models = {}

        # Groq models
        if self.groq_api_key:
            for model_name in self.providers["groq"]["models"]:
                models[f"groq/{model_name}"] = {
                    "name":
                    model_name,
                    "provider":
                    "groq",
                    "tokens":
                    32768 if "32768" in model_name else 16384,
                    "model":
                    lambda name=model_name: ChatGroq(
                        groq_api_key=self.groq_api_key, model_name=name)
                }

        # OpenAI models
        if self.openai_api_key:
            for model_name in self.providers["openai"]["models"]:
                tokens = 16384 if "gpt-4" in model_name else 4096
                models[f"openai/{model_name}"] = {
                    "name":
                    model_name,
                    "provider":
                    "openai",
                    "tokens":
                    tokens,
                    "model":
                    lambda name=model_name: ChatOpenAI(
                        api_key=self.openai_api_key, model_name=name)
                }

        # Google models
        if self.google_api_key:
            for model_name in self.providers["google"]["models"]:
                models[f"google/{model_name}"] = {
                    "name":
                    model_name,
                    "provider":
                    "google",
                    "tokens":
                    16384 if "ultra" in model_name else 8192,
                    "model":
                    lambda name=model_name: ChatGoogleGenerativeAI(
                        google_api_key=self.google_api_key, model=name)
                }

        # Anthropic models
        if self.anthropic_api_key:
            for model_name in self.providers["anthropic"]["models"]:
                tokens = 32768 if "opus" in model_name else 16384
                models[f"anthropic/{model_name}"] = {
                    "name":
                    model_name,
                    "provider":
                    "anthropic",
                    "tokens":
                    tokens,
                    "model":
                    lambda name=model_name: ChatAnthropic(
                        api_key=self.anthropic_api_key, model_name=name)
                }

        # Ollama models
        for model_name in self.providers["ollama"]["models"]:
            models[f"ollama/{model_name}"] = {
                "name":
                model_name,
                "provider":
                "ollama",
                "tokens":
                8192,  # Default context window for most Ollama models
                "model":
                lambda name=model_name: ChatOllama(
                    model=name, base_url=self.ollama_base_url)
            }

        return models

    def get_model(self, model_key: str):
        """Get a model instance by its key (provider/model_name)"""
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not found")
        return self.models[model_key]["model"]()

    def get_model_names(self) -> List[str]:
        """Get all available model keys"""
        return list(self.models.keys())

    def get_provider_names(self) -> List[str]:
        """Get all provider names"""
        return list(self.providers.keys())

    def get_provider_models(self, provider: str) -> List[str]:
        """Get all models for a specific provider"""
        if provider not in self.providers:
            return []
        return [
            f"{provider}/{model}"
            for model in self.providers[provider]["models"]
        ]

    def get_model_info(self, model_key: str) -> Dict:
        """Get information about a specific model"""
        return self.models.get(model_key, {})

    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured (has API key)"""
        if provider == "ollama":
            return True  # Ollama is always available (local)

        if provider not in self.providers:
            return False

        api_key = self.providers[provider].get("api_key", "")
        return api_key != ""
