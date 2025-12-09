import { api } from "../api";
import {
    CreateToolPayload,
    CreateToolsetPayload,
    Tool,
    Toolset,
    ToolsetListQuery,
    ToolsetListResponse,
    UpdateToolPayload,
    UpdateToolsetPayload,
    WebhookAuthHeader,
} from "../types/toolsets";
import { buildQueryString } from "./utils";

export async function createToolset(payload: CreateToolsetPayload): Promise<Toolset> {
    return api.post<Toolset>("/toolsets", { data: payload });
}

export async function listToolsets(query?: ToolsetListQuery): Promise<ToolsetListResponse> {
    const qs = buildQueryString({
        page_number: query?.pageNumber,
        page_size: query?.pageSize,
    });
    return api.get<ToolsetListResponse>(`/toolsets${qs}`);
}

export async function getToolset(toolsetId: string): Promise<Toolset> {
    return api.get<Toolset>(`/toolsets/${toolsetId}`);
}

export async function updateToolset(
    toolsetId: string,
    payload: UpdateToolsetPayload
): Promise<Toolset> {
    return api.patch<Toolset>(`/toolsets/${toolsetId}`, { data: payload });
}

export async function deleteToolset(toolsetId: string): Promise<void> {
    await api.delete(`/toolsets/${toolsetId}`);
}

export async function getMcpServerAuthHeader(toolsetId: string): Promise<WebhookAuthHeader> {
    return api.get<WebhookAuthHeader>(`/toolsets/${toolsetId}/mcp-server-auth-header`);
}

export async function createTool(toolsetId: string, payload: CreateToolPayload): Promise<Tool> {
    return api.post<Tool>(`/toolsets/${toolsetId}/tools`, { data: payload });
}

export async function getTool(toolId: string): Promise<Tool> {
    return api.get<Tool>(`/tools/${toolId}`);
}

export async function updateTool(toolId: string, payload: UpdateToolPayload): Promise<Tool> {
    return api.patch<Tool>(`/tools/${toolId}`, { data: payload });
}

export async function deleteTool(toolId: string): Promise<void> {
    await api.delete(`/tools/${toolId}`);
}

export async function getWebhookAuthHeader(toolId: string): Promise<WebhookAuthHeader> {
    return api.get<WebhookAuthHeader>(`/tools/${toolId}/webhook-auth-header`);
}

