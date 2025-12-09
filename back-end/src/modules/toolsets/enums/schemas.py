from typing import Optional

from pydantic import BaseModel, Field, model_validator, field_validator

from src.modules.toolsets.enums.enums import ToolsetTypeEnum, ToolTypeEnum


class ToolsetTypeSchema(BaseModel):
    toolset_type: Optional[str] = Field(
        description=(
            "The type of the toolset. "
            f"Allowed values: {ToolsetTypeEnum.get_field_names()}."
        )
    )
    _toolset_type: Optional[ToolsetTypeEnum] = None

    @field_validator("toolset_type")
    @classmethod
    def validate_toolset_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = [field.name for field in ToolsetTypeEnum.get_visible_types()]
        if value not in allowed:
            allowed_str = ", ".join(allowed)
            raise ValueError(f"toolset_type must be one of: {allowed_str}")
        return value

    @model_validator(mode="after")
    def set_toolset_type(self):
        if self.toolset_type is not None:
            self._toolset_type = ToolsetTypeEnum[self.toolset_type]
        return self

    @property
    def enum(self) -> Optional[ToolsetTypeEnum]:
        return self._toolset_type


class ToolTypeSchema(BaseModel):
    tool_type: Optional[str] = Field(
        description=(
            "The type of the tool. "
            f"Allowed values: {ToolTypeEnum.get_field_names()}."
        )
    )
    _tool_type: Optional[ToolTypeEnum] = None

    @field_validator("tool_type")
    @classmethod
    def validate_tool_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = [field.name for field in ToolTypeEnum.get_visible_types()]
        if value not in allowed:
            allowed_str = ", ".join(allowed)
            raise ValueError(f"tool_type must be one of: {allowed_str}")
        return value

    @model_validator(mode="after")
    def set_tool_type(self):
        if self.tool_type is not None:
            self._tool_type = ToolTypeEnum[self.tool_type]
        return self

    @property
    def enum(self) -> Optional[ToolTypeEnum]:
        return self._tool_type