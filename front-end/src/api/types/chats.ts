import { PaginationQuery, UUID } from "./common";

export interface Chat {
    id: UUID;
    title: string;
    created_at: string;
    updated_at: string;
    is_active: boolean;
}

export type StreamStatus =
    | "searching"
    | "tool_call"
    | "tool_running"
    | "tool_result"
    | "response"
    | "end_turn"
    | "keepalive"
    | "error";

export interface StreamMessageResponse {
    status: StreamStatus;
    error?: string | null;
    response: string;
    tool_name?: string | null;
    tool_args?: string | null;
    tool_result?: string | null;
    info?: string | null;
}

export interface StreamStep {
    type: "text" | "tool";
    content?: string;
    toolName?: string;
    toolArgs?: string;
    toolResult?: string;
    isLoading?: boolean;
}

export interface Message {
    id: number;
    sent_at: string;
    message: string;
    response?: string | null;
    input_tokens: number;
    reasoning_tokens: number;
    output_tokens: number;
    json_message_history?: Record<string, unknown> | unknown[] | null;
    chat_id: UUID;
    steps?: StreamStep[];
}

export interface ChatListResponse {
    total_chats: number;
    chats: Chat[];
}

export interface CreateChatPayload {
    title: string;
}

export interface UpdateChatPayload {
    title: string;
}

export interface AskQuestionPayload {
    agent_id: UUID;
    question: string;
}

export type ChatListQuery = PaginationQuery;
