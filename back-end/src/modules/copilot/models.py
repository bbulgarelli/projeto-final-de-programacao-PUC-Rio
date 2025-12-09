import enum

from typing import Dict, List, Optional
from pydantic_ai.models import Model
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.models.openai import OpenAIModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.grok import GrokProvider
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from src.config import settings


class ModelProvider(enum.Enum):
    open_ai = "OpenAI"
    anthropic = "Anthropic"
    google = "Google"
    x_ai = "X AI"

def get_pydantic_ai_provider(provider: ModelProvider, api_key: Optional[str] = None):
    if provider == ModelProvider.open_ai:
        return OpenAIProvider(api_key=api_key or settings.OPENAI_API_KEY)
    elif provider == ModelProvider.google:
        return GoogleProvider(api_key=api_key or settings.GOOGLE_API_KEY)
    elif provider == ModelProvider.x_ai:
        return GrokProvider(api_key=api_key or settings.X_AI_API_KEY)
    elif provider == ModelProvider.anthropic:
        return AnthropicProvider(api_key=api_key or settings.ANTHROPIC_API_KEY)


class LLM:
    def __init__(
        self, name: str, model_id: str, provider: ModelProvider, temperature: float,
        context_length: int, output_tokens: int,
        available: bool = True, legacy_model: bool = False, internet_access: bool = False,
        input_price_per_million_tokens: float = 0, reasoning_price_per_million_tokens: float = 0, output_price_per_million_tokens: float = 0
    ):
        self.name = name
        self.description = ""
        self.model_id = model_id
        self.provider = provider
        self.temperature = temperature
        self.available = available
        self.legacy_model = legacy_model
        self.context_length = context_length
        self.output_tokens = output_tokens
        self.internet_access = internet_access

        self.input_price_per_million_tokens = input_price_per_million_tokens
        self.reasoning_price_per_million_tokens = reasoning_price_per_million_tokens
        self.output_price_per_million_tokens = output_price_per_million_tokens

    def to_dict(self):
        """Convert LLM object to a dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "context_length": self.context_length,
            "output_tokens": self.output_tokens,
            "temperature": self.temperature,
            "provider": self.provider.value,
            "legacy_model": self.legacy_model
        }


class LLMModel(enum.Enum):
    anthropic_claude_4_1_opus = "anthropic_claude_4_1_opus"
    anthropic_claude_4_sonnet = "anthropic_claude_4_sonnet"
    grok_4_fast = "grok_4_fast"
    gemini_2_5_pro = "gemini_2_5_pro"
    gemini_2_0_flash_lite = "gemini_2_0_flash_lite"
    gemini_2_0_flash_grounded_search = "gemini_2_0_flash_grounded_search"
    gemini_2_0_flash = "gemini_2_0_flash"
    chatgpt_5 = "chatgpt_5"
    chatgpt_5_mini = "chatgpt_5_mini"
    chatgpt_4_1 = "chatgpt_4_1"
    chatgpt_4_1_mini = "chatgpt_4_1_mini"
    chatgpt_4o = "chatgpt_4o"
    chatgpt_4o_mini = "chatgpt_4o_mini"
    chatgpt_3_5_turbo = "chatgpt_3_5_turbo"


    _MODEL_DETAILS = {
        anthropic_claude_4_1_opus: LLM("Claude 4.1 Opus", "claude-opus-4-1-20250805", ModelProvider.anthropic, 1,
                                     context_length=200000, output_tokens=16000, available=True,
                                     input_price_per_million_tokens=15.0, reasoning_price_per_million_tokens=75.0, output_price_per_million_tokens=75.0),
        anthropic_claude_4_sonnet: LLM("Claude 4 Sonnet", "claude-sonnet-4-20250514", ModelProvider.anthropic, 1,
                                       context_length=200000, output_tokens=16000, available=True,
                                       input_price_per_million_tokens=3.0, reasoning_price_per_million_tokens=15.0, output_price_per_million_tokens=15.0),
        grok_4_fast: LLM("Grok 4 Fast", "grok-4-fast-reasoning", ModelProvider.x_ai, 0.7,
                          context_length=2000000, output_tokens=100000, available=True,
                          input_price_per_million_tokens=3.0, reasoning_price_per_million_tokens=15.0, output_price_per_million_tokens=15.0),
        gemini_2_5_pro: LLM("Gemini 2.5 Pro", "gemini-2.5-pro", ModelProvider.google, 0.7,
                            context_length=1048576, output_tokens=8192, available=True,
                            input_price_per_million_tokens=1.25, reasoning_price_per_million_tokens=10.0, output_price_per_million_tokens=5.0),
        gemini_2_0_flash_lite: LLM("Gemini 2.0 Flash-Lite", "gemini-2.0-flash-lite-preview-02-05",
                                   ModelProvider.google, 0.7, context_length=1048576, output_tokens=4096, available=True,
                                   input_price_per_million_tokens=0.075, reasoning_price_per_million_tokens=0.30, output_price_per_million_tokens=0.30),
        gemini_2_0_flash_grounded_search: LLM("Gemini 2.0 Flash with Grounded Search", "gemini-2.0-flash",
                                              ModelProvider.google, 0.7, context_length=1048576,
                                              output_tokens=8192, available=False, internet_access=True,
                                              input_price_per_million_tokens=0.15, reasoning_price_per_million_tokens=0.60, output_price_per_million_tokens=0.60),
        gemini_2_0_flash: LLM("Gemini 2.0 Flash", "gemini-2.0-flash", ModelProvider.google, 0.7,
                              context_length=1048576, output_tokens=8192, available=True,
                              input_price_per_million_tokens=0.15, reasoning_price_per_million_tokens=0.60, output_price_per_million_tokens=0.60),
        chatgpt_5: LLM("GPT-5", "gpt-5", ModelProvider.open_ai, 1,
                       context_length=400000, output_tokens=128000, available=False),
        chatgpt_5_mini: LLM("GPT-5 mini", "gpt-5-mini", ModelProvider.open_ai, 1,
                       context_length=400000, output_tokens=128000, available=False),
        chatgpt_4_1: LLM("GPT-4.1", "gpt-4.1", ModelProvider.open_ai, 1,
                         context_length=1048576, output_tokens=4096, available=True,
                         input_price_per_million_tokens=2.0, reasoning_price_per_million_tokens=8.0, output_price_per_million_tokens=8.0),
        chatgpt_4o: LLM("GPT-4o", "gpt-4o", ModelProvider.open_ai, 1,
                        context_length=128000, output_tokens=4096, available=True,
                        input_price_per_million_tokens=2.5, reasoning_price_per_million_tokens=10.0, output_price_per_million_tokens=10.0),
        chatgpt_4_1_mini: LLM("GPT-4.1 mini", "gpt-4.1-mini", ModelProvider.open_ai, 1,
                              context_length=1048576, output_tokens=4096, available=True,
                              input_price_per_million_tokens=0.4, reasoning_price_per_million_tokens=1.6, output_price_per_million_tokens=1.6),
        chatgpt_4o_mini: LLM("GPT-4o mini", "gpt-4o-mini", ModelProvider.open_ai, 1,
                             context_length=128000, output_tokens=16384, available=True,
                             input_price_per_million_tokens=0.15, reasoning_price_per_million_tokens=0.60, output_price_per_million_tokens=0.60),
        chatgpt_3_5_turbo: LLM("GPT-3.5 Turbo", "gpt-3.5-turbo", ModelProvider.open_ai, 1,
                               context_length=16000, output_tokens=4096, available=False, legacy_model=True,
                               input_price_per_million_tokens=0.50, reasoning_price_per_million_tokens=1.50, output_price_per_million_tokens=1.50),
    }

    def get_details(self) -> LLM:
        """Retrieve details for the given model instance."""
        return LLMModel._MODEL_DETAILS.value[self.value]

    def get_pydantic_ai_model(self, api_key: Optional[str] = None, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None, region_name: Optional[str] = 'us-east-1') -> Model:
        if self.get_details().provider == ModelProvider.open_ai:
            return OpenAIModel(
                model_name=self.get_details().model_id,
                provider=get_pydantic_ai_provider(
                    ModelProvider.open_ai, api_key)
            )

        elif self.get_details().provider == ModelProvider.google:
            return GoogleModel(
                model_name=self.get_details().model_id,
                provider=get_pydantic_ai_provider(
                    ModelProvider.google, api_key),
                settings=GoogleModelSettings(google_thinking_config={'include_thoughts': True})
            )

        elif self.get_details().provider == ModelProvider.x_ai:
            return OpenAIModel(
                model_name=self.get_details().model_id,
                provider=get_pydantic_ai_provider(
                    ModelProvider.x_ai, api_key),
                settings=OpenAIResponsesModelSettings(
                    openai_reasoning_summary='detailed'
                )
            )

        elif self.get_details().provider == ModelProvider.anthropic:
            return AnthropicModel(
                model_name=self.get_details().model_id,
                provider=get_pydantic_ai_provider(
                    ModelProvider.anthropic, api_key)
            )

    @classmethod
    def get_available_models(cls) -> List[Dict]:
        """Return a list of available models."""
        return [
            {"model_key": model_enum, **model.to_dict()}
            for model_enum, model in cls._MODEL_DETAILS.value.items()
            if model.available
        ]

    @classmethod
    def get_keys_of_available_models(cls) -> List[str]:
        return [model["model_key"] for model in LLMModel.get_available_models()]

