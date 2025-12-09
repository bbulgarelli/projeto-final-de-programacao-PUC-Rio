from pydantic import BaseModel, Field


class AvailableModelsSchema(BaseModel):
    model_key: str = Field(
        ...,
        description="Internal identifier used to select the model.",
    )
    name: str = Field(
        ...,
        description="Human friendly name of the model.",
    )
    description: str = Field(
        ...,
        description="Short explanation of the model capabilities.",
    )
    context_length: int = Field(
        ...,
        description="Maximum number of tokens accepted in the prompt.",
    )
    provider: str = Field(
        ...,
        description="Name of the provider offering the model.",
    )
    legacy_model: bool = Field(
        ...,
        description="Indicates whether this model is considered legacy.",
    )
    output_tokens: int = Field(
        ...,
        description="Maximum number of tokens the model can generate.",
    )
    temperature: float = Field(
        ...,
        description="Default sampling temperature used by the model.",
    )