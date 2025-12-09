import { api } from "../api";
import { Agent, AgentListQuery, AgentListResponse, CreateAgentPayload, UpdateAgentPayload } from "../types/agents";
import { buildQueryString } from "./utils";

export async function createAgent(payload: CreateAgentPayload): Promise<Agent> {
    return api.post<Agent>("/agents", { data: payload });
}

export async function listAgents(query?: AgentListQuery): Promise<AgentListResponse> {
    const qs = buildQueryString({
        page_number: query?.pageNumber,
        page_size: query?.pageSize,
    });
    return api.get<AgentListResponse>(`/agents${qs}`);
}

export async function getAgent(agentId: string): Promise<Agent> {
    return api.get<Agent>(`/agents/${agentId}`);
}

export async function updateAgent(agentId: string, payload: UpdateAgentPayload): Promise<Agent> {
    return api.patch<Agent>(`/agents/${agentId}`, { data: payload });
}

export async function deleteAgent(agentId: string): Promise<void> {
    await api.delete(`/agents/${agentId}`);
}

