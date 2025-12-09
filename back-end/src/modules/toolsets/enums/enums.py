from enum import Enum


class ToolsetEnumField:

    def __init__(self, name: str, is_visible: bool = True):
        self.name = name
        self.is_visible = is_visible

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.name}"

    def __json__(self):
        return self.__dict__

class ToolsetTypeEnum(Enum):
    NP_TOOLSET = ToolsetEnumField("NP_TOOLSET", is_visible=False)
    MCP_SERVER = ToolsetEnumField("MCP_SERVER")
    CUSTOM = ToolsetEnumField("CUSTOM")

    @classmethod
    def get_field_names(cls):
        return [field.name for field in cls if field.value.is_visible]

    @classmethod
    def get_visible_types(cls):
        return [field for field in cls if field.value.is_visible]

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return str(self.name)


class ToolTypeEnum(Enum):
    AGENT = ToolsetEnumField("AGENT")
    WEBHOOK = ToolsetEnumField("WEBHOOK")
    MCP = ToolsetEnumField("MCP_TOOL", is_visible=False)

    @classmethod
    def get_field_names(cls):
        return [field.name for field in cls if field.value.is_visible]

    @classmethod
    def get_visible_types(cls):
        return [field for field in cls if field.value.is_visible]

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return str(self.name)
