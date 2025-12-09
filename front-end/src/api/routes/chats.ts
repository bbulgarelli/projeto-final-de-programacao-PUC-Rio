import { api } from "../api";
import {
    AskQuestionPayload,
    Chat,
    ChatListQuery,
    ChatListResponse,
    CreateChatPayload,
    Message,
    UpdateChatPayload,
    StreamMessageResponse
} from "../types/chats";
import { buildQueryString } from "./utils";

/**
 * Parse Python-like object string to JavaScript object
 * Example: "status='response' error=None response='hello' tool_name=None"
 */
function parsePythonObject(pythonStr: string): StreamMessageResponse {
    const result: any = {
        status: "",
        response: "",
        error: null,
        tool_name: null,
        tool_args: null,
        tool_result: null,
        info: null
    };

    // Match key=value patterns
    // Handles: key='value', key="value", key=None, key=True/False
    const regex = /(\w+)=('([^']*)'|"([^"]*)"|None|True|False|\w+)/g;
    let match;

    while ((match = regex.exec(pythonStr)) !== null) {
        const key = match[1];
        const fullValue = match[2];
        let value: any;

        if (match[3] !== undefined) {
            // Single quoted string
            value = match[3];
        } else if (match[4] !== undefined) {
            // Double quoted string
            value = match[4];
        } else if (fullValue === "None") {
            value = null;
        } else if (fullValue === "True") {
            value = true;
        } else if (fullValue === "False") {
            value = false;
        } else {
            // Other value (keep as string or try to parse as number)
            value = fullValue;
            const num = Number(fullValue);
            if (!isNaN(num)) {
                value = num;
            }
        }

        result[key] = value;
    }

    return result as StreamMessageResponse;
}

export async function createChat(payload: CreateChatPayload): Promise<Chat> {
    return api.post<Chat>("/chats", { data: payload });
}

export async function listChats(query?: ChatListQuery): Promise<ChatListResponse> {
    const qs = buildQueryString({
        page_number: query?.pageNumber,
        page_size: query?.pageSize,
    });
    return api.get<ChatListResponse>(`/chats${qs}`);
}

export async function getChat(chatId: string): Promise<Chat> {
    return api.get<Chat>(`/chats/${chatId}`);
}

export async function updateChat(chatId: string, payload: UpdateChatPayload): Promise<Chat> {
    return api.patch<Chat>(`/chats/${chatId}`, { data: payload });
}

export async function deleteChat(chatId: string): Promise<void> {
    await api.delete(`/chats/${chatId}`);
}

export async function askQuestion(chatId: string, payload: AskQuestionPayload): Promise<Message> {
    return api.post<Message>(`/chats/${chatId}/messages`, { data: payload });
}

export async function streamQuestion(
    chatId: string,
    payload: AskQuestionPayload,
    onMessage: (data: StreamMessageResponse) => void,
    onError: (error: any) => void,
    onComplete: () => void
): Promise<void> {
    try {
        const response = await api.post_full_response(`/chats/${chatId}/messages/stream`, { data: payload });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("HTTP error response:", errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
            throw new Error("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let currentEvent = "message"; // default event type

        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                onComplete();
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            // Split by double newline for SSE message boundaries, or single newline for line-by-line
            const lines = buffer.split("\n");

            // Keep the last incomplete line in buffer
            buffer = lines.pop() || "";

            for (const line of lines) {
                // Skip empty lines and comments
                if (line === "" || line.startsWith(":")) {
                    continue;
                }

                // Parse event type
                if (line.startsWith("event:")) {
                    currentEvent = line.slice(6).trim();
                    continue;
                }

                // Parse data
                if (line.startsWith("data:")) {
                    const dataStr = line.slice(5).trim();

                    // Skip empty or null data
                    if (dataStr === "" || dataStr === "null") {
                        continue;
                    }

                    // Only process "message" events
                    if (currentEvent === "message") {
                        try {
                            let data: StreamMessageResponse;

                            // Try JSON first, then fall back to Python object format
                            if (dataStr.startsWith("{")) {
                                data = JSON.parse(dataStr);
                            } else {
                                // Parse Python-like object string
                                data = parsePythonObject(dataStr);
                            }

                            onMessage(data);
                        } catch (e) {
                            console.error("Failed to parse stream data:", dataStr, e);
                        }
                    }

                    // Reset event type to default after processing
                    currentEvent = "message";
                }
            }
        }
    } catch (error) {
        console.error("Stream error:", error);
        onError(error);
    }
}
