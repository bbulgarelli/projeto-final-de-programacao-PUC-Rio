import { PaginationQuery, UUID } from "./common";
import { KnowledgeBase } from "./knowledgeBases";
import { Toolset } from "./toolsets";

export interface Agent {
    id: UUID;
    name: string;
    description?: string | null;
    color?: string | null;
    prompt: string;
    contextualize_system_prompt: string;
    enum_model: string;
    max_response_tokens: number;
    temperature: number;
    history_message_count: number;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    knowledge_bases: KnowledgeBase[];
    toolsets: Toolset[];
}

export interface AgentListResponse {
    total_agents: number;
    agents: Agent[];
}

export interface CreateAgentPayload {
    name: string;
    description?: string | null;
    color?: string | null;
    prompt: string;
    contextualize_system_prompt: string;
    enum_model?: string;
    max_response_tokens?: number;
    temperature?: number;
    history_message_count?: number;
    knowledge_base_ids?: UUID[];
    toolset_ids?: UUID[];
}

export interface UpdateAgentPayload extends Partial<CreateAgentPayload> { }

export type AgentListQuery = PaginationQuery;

