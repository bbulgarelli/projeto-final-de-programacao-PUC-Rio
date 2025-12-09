import { PaginationQuery, UUID } from "./common";

export type ToolsetType = "NP_TOOLSET" | "MCP_SERVER" | "CUSTOM";
export type ToolType = "AGENT" | "WEBHOOK" | "MCP";

export interface Tool {
    id: UUID;
    name: string;
    description?: string | null;
    tool_type: ToolType;
    webhook_url?: string | null;
    webhook_auth_header?: Record<string, string> | null;
    webhook_query_params_schema?: Record<string, unknown> | null;
    webhook_path_params_schema?: Record<string, unknown> | null;
    webhook_body_params_schema?: Record<string, unknown> | null;
    webhook_http_method?: string | null;
    mcp_title?: string | null;
    input_schema?: Record<string, unknown> | null;
    output_schema?: Record<string, unknown> | null;
    target_agent_id?: UUID | null;
    toolset_id?: UUID | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    toolset?: Pick<Toolset, "id" | "name"> | null;
}

export interface Toolset {
    id: UUID;
    name: string;
    description?: string | null;
    toolset_type: ToolsetType;
    mcp_server_url?: string | null;
    mcp_server_auth_header?: Record<string, string> | null;
    enum_np_toolset?: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    tools: Tool[];
}

export interface ToolsetListResponse {
    total_toolsets: number;
    toolsets: Toolset[];
}

export interface CreateToolPayload {
    tool_type: ToolType;
    name: string;
    description?: string | null;
    webhook_url?: string | null;
    webhook_auth_header?: Record<string, string> | null;
    webhook_query_params_schema?: Record<string, unknown> | null;
    webhook_path_params_schema?: Record<string, unknown> | null;
    webhook_body_params_schema?: Record<string, unknown> | null;
    webhook_http_method?: string | null;
    target_agent_id?: UUID | null;
    mcp_title?: string | null;
    input_schema?: Record<string, unknown> | null;
    output_schema?: Record<string, unknown> | null;
}

export interface UpdateToolPayload extends Partial<CreateToolPayload> {
    tool_type?: ToolType;
}

export interface CreateToolsetPayload {
    toolset_type?: ToolsetType;
    name: string;
    description?: string | null;
    mcp_server_url?: string | null;
    mcp_server_auth_header?: Record<string, string> | null;
    tools?: CreateToolPayload[];
}

export interface UpdateToolsetPayload extends Partial<CreateToolsetPayload> {
    toolset_type?: ToolsetType;
    tools?: never;
}

export type ToolsetListQuery = PaginationQuery;

export type WebhookAuthHeader = Record<string, string> | null;

