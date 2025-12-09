import { Component, createSignal, createResource, For, Show, createEffect, Switch, Match } from "solid-js";
import { useParams, useNavigate } from "@solidjs/router";
import { createChat, getChat, askQuestion, listChats, streamQuestion } from "../api/routes/chats";
import { listAgents } from "../api/routes/agents";
import { Chat as ChatType, Message } from "../api/types/chats";

export const ChatPage: Component = () => {
    const params = useParams();
    const navigate = useNavigate();
    const [inputMessage, setInputMessage] = createSignal("");
    const [selectedAgentId, setSelectedAgentId] = createSignal<string>("");
    const [chatMessages, setChatMessages] = createSignal<Message[]>([]);
    const [isLoading, setIsLoading] = createSignal(false);
    const [expandedTools, setExpandedTools] = createSignal<Set<string>>(new Set());
    const [lastLoadedChatId, setLastLoadedChatId] = createSignal<string | null>(null);

    // Persist selected agent
    createEffect(() => {
        const id = selectedAgentId();
        if (id) {
            localStorage.setItem("chat_selected_agent_id", id);
        }
    });

    // Toggle tool card expansion
    const toggleToolExpansion = (toolId: string) => {
        setExpandedTools(prev => {
            const newSet = new Set(prev);
            if (newSet.has(toolId)) {
                newSet.delete(toolId);
            } else {
                newSet.add(toolId);
            }
            return newSet;
        });
    };

    // Resources
    const [agents] = createResource(async () => {
        const response = await listAgents({ pageSize: 100 });

        // After agents are loaded, restore the persisted selection
        const persistedAgentId = localStorage.getItem("chat_selected_agent_id");
        if (persistedAgentId) {
            const agent = response.agents.find(a => a.id === persistedAgentId);
            if (agent) {
                setSelectedAgentId(agent.id);
            } else if (response.agents.length > 0) {
                // If persisted agent doesn't exist, select the first one
                setSelectedAgentId(response.agents[0].id);
            }
        } else if (response.agents.length > 0) {
            // No persisted agent, select the first one
            setSelectedAgentId(response.agents[0].id);
        }

        return response.agents;
    });

    const [chat, { refetch: refetchChat }] = createResource(
        () => params.id,
        async (id) => {
            if (!id) return null;
            try {
                const chatData = await getChat(id);
                return chatData;
            } catch (e) {
                console.error("Failed to load chat", e);
                return null;
            }
        }
    );

    // Create a new chat if there's no chat ID in the URL
    createEffect(() => {
        const chatId = params.id;
        if (!chatId && !isLoading()) {
            // No chat ID in URL, create a new chat
            const createNewChat = async () => {
                try {
                    setIsLoading(true);
                    const newChat = await createChat({ title: "New Chat" });
                    navigate(`/chat/${newChat.id}`, { replace: true });
                } catch (err) {
                    console.error("Failed to create chat", err);
                } finally {
                    setIsLoading(false);
                }
            };
            createNewChat();
        }
    });

    // Effect to load messages when chat data is ready
    createEffect(() => {
        const currentChat = chat();
        if (!currentChat) {
            // No chat loaded, clear messages only if we're navigating away from a chat
            if (lastLoadedChatId() !== null) {
                setChatMessages([]);
                setLastLoadedChatId(null);
            }
            return;
        }

        // Only load messages from server if we're switching to a different chat
        const chatId = currentChat.id;
        if (lastLoadedChatId() !== chatId) {
            const serverMessages = (currentChat as any).messages || [];
            const currentMessages = chatMessages();

            // Don't overwrite optimistic messages with empty server response
            // This happens when creating a new chat - we have 1 optimistic message,
            // but server returns empty array since it just created the chat
            const shouldUpdate = serverMessages.length > 0 || currentMessages.length === 0;

            if (shouldUpdate) {
                setChatMessages(serverMessages);
            }

            setLastLoadedChatId(chatId);
        }
    });

    const handleSendMessage = async (e: Event) => {
        e.preventDefault();
        if (!inputMessage().trim()) return;

        const chatId = params.id;
        if (!chatId) {
            console.error("No chat ID available");
            return;
        }

        if (!selectedAgentId()) {
            alert("Please select an agent first");
            return;
        }

        const question = inputMessage();
        setInputMessage("");
        setIsLoading(true);

        // Optimistic UI update
        const tempId = Date.now();
        const optimisticMessage: Message = {
            id: tempId,
            sent_at: new Date().toISOString(),
            message: question,
            input_tokens: 0,
            reasoning_tokens: 0,
            output_tokens: 0,
            chat_id: chatId,
            response: "",
            steps: []
        };

        setChatMessages(prev => [...prev, optimisticMessage]);

        try {
            await streamQuestion(
                chatId,
                {
                    agent_id: selectedAgentId(),
                    question: question
                },
                (data) => {
                    setChatMessages(prev => {
                        const updated = prev.map(msg => {
                            if (msg.id !== tempId) return msg;

                            const newMsg = { ...msg, steps: [...(msg.steps || [])] };

                            switch (data.status) {
                                case "response":
                                    if (data.response) {
                                        const lastStep = newMsg.steps[newMsg.steps.length - 1];
                                        if (lastStep && lastStep.type === "text") {
                                            // Update last text step
                                            newMsg.steps[newMsg.steps.length - 1] = {
                                                ...lastStep,
                                                content: (lastStep.content || "") + data.response
                                            };
                                        } else {
                                            newMsg.steps.push({ type: "text", content: data.response });
                                        }
                                        newMsg.response = (newMsg.response || "") + data.response;
                                    }
                                    break;

                                case "tool_call":
                                    newMsg.steps.push({
                                        type: "tool",
                                        toolName: data.tool_name || "Unknown Tool",
                                        toolArgs: data.tool_args || undefined,
                                        isLoading: true
                                    });
                                    break;

                                case "tool_result":
                                    // Find the last running tool step
                                    for (let i = newMsg.steps.length - 1; i >= 0; i--) {
                                        if (newMsg.steps[i].type === "tool" && newMsg.steps[i].isLoading) {
                                            newMsg.steps[i] = {
                                                ...newMsg.steps[i],
                                                toolResult: data.tool_result || "",
                                                isLoading: false
                                            };
                                            break;
                                        }
                                    }
                                    break;
                            }
                            return newMsg;
                        });
                        return updated;
                    });
                },
                (err) => {
                    console.error("Stream error", err);
                    setIsLoading(false);
                },
                () => {
                    setIsLoading(false);
                    // Don't refetch - we already have the complete message from the stream
                    // The backend persists it in the background
                }
            );

        } catch (err) {
            console.error("Failed to send message", err);
            setIsLoading(false);
        }
    };

    let scrollContainer: HTMLDivElement | undefined;

    createEffect(() => {
        chatMessages(); // dependence
        if (scrollContainer) {
            scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
    });

    return (
        <div class="flex flex-col h-full bg-white relative">
            {/* Content Area */}
            <div
                ref={scrollContainer}
                class="flex-1 overflow-y-auto p-4 pb-16"
            >
                <Show
                    when={chatMessages().length > 0}
                    fallback={
                        <div class="h-full flex flex-col items-center justify-center text-gray-400">
                            <span class="text-4xl mb-4">👋</span>
                            <p class="text-lg">How can I help you today?</p>
                        </div>
                    }
                >
                    <div class="max-w-3xl mx-auto space-y-6">
                        <For each={chatMessages()}>
                            {(msg) => (
                                <>
                                    {/* User Message */}
                                    <div class="flex justify-end">
                                        <div class="bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-tr-sm max-w-[80%] shadow-sm">
                                            <p class="whitespace-pre-wrap">{msg.message}</p>
                                        </div>
                                    </div>

                                    {/* Agent Response */}
                                    <Show when={msg.steps && msg.steps.length > 0} fallback={
                                        <Show when={msg.response}>
                                            <div class="flex justify-start">
                                                <div class="bg-gray-100 text-gray-800 px-4 py-2 rounded-2xl rounded-tl-sm max-w-[80%] shadow-sm border border-gray-200">
                                                    <p class="whitespace-pre-wrap">{msg.response}</p>
                                                    <div class="mt-2 text-xs text-gray-400 flex gap-2">
                                                        <span>Tokens: {msg.input_tokens} in / {msg.output_tokens} out</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </Show>
                                    }>
                                        <div class="flex flex-col gap-2 max-w-[80%]">
                                            <For each={msg.steps}>
                                                {(step, index) => {
                                                    const toolId = `${msg.id}-${index()}`;
                                                    const isExpanded = () => expandedTools().has(toolId);

                                                    return (
                                                        <Switch>
                                                            <Match when={step.type === 'text'}>
                                                                <div class="bg-gray-100 text-gray-800 px-4 py-2 rounded-2xl rounded-tl-sm shadow-sm border border-gray-200 self-start">
                                                                    <p class="whitespace-pre-wrap">{step.content}</p>
                                                                </div>
                                                            </Match>
                                                            <Match when={step.type === 'tool'}>
                                                                <div class="bg-gray-50 border border-gray-200 rounded-lg text-sm self-start w-full shadow-sm">
                                                                    {/* Header - always visible, clickable */}
                                                                    <button
                                                                        class="w-full flex items-center justify-between gap-2 text-gray-600 p-3 hover:bg-gray-100 transition-colors rounded-t-lg"
                                                                        onClick={() => toggleToolExpansion(toolId)}
                                                                    >
                                                                        <div class="flex items-center gap-2 min-w-0">
                                                                            <span class="text-lg">🛠</span>
                                                                            <span class="font-bold font-mono">{step.toolName}</span>
                                                                            <span class="text-xs text-gray-400 truncate max-w-[400px]" title={step.toolArgs}>
                                                                                ({step.toolArgs ? (step.toolArgs.length > 100 ? step.toolArgs.substring(0, 100) + "..." : step.toolArgs) : ""})
                                                                            </span>
                                                                            <Show when={step.isLoading}>
                                                                                <div class="w-3 h-3 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"></div>
                                                                            </Show>
                                                                        </div>
                                                                        <svg
                                                                            class={`w-5 h-5 transition-transform flex-shrink-0 ${isExpanded() ? 'rotate-180' : ''}`}
                                                                            fill="none"
                                                                            stroke="currentColor"
                                                                            viewBox="0 0 24 24"
                                                                        >
                                                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                                                                        </svg>
                                                                    </button>

                                                                    {/* Expandable content */}
                                                                    <Show when={isExpanded()}>
                                                                        <div class="px-3 pb-3 space-y-2 border-t border-gray-200">
                                                                            {/* Tool Arguments */}
                                                                            <Show when={step.toolArgs}>
                                                                                <div class="pt-2">
                                                                                    <div class="text-xs font-semibold text-gray-500 uppercase mb-1">Arguments</div>
                                                                                    <div class="text-gray-800 bg-white p-2 rounded border border-gray-100 overflow-x-auto">
                                                                                        <pre class="whitespace-pre-wrap text-xs font-mono">{step.toolArgs}</pre>
                                                                                    </div>
                                                                                </div>
                                                                            </Show>

                                                                            {/* Tool Result */}
                                                                            <Show when={step.toolResult}>
                                                                                <div>
                                                                                    <div class="text-xs font-semibold text-gray-500 uppercase mb-1">Result</div>
                                                                                    <div class="text-gray-800 bg-white p-2 rounded border border-gray-100 overflow-x-auto max-h-60">
                                                                                        <pre class="whitespace-pre-wrap text-xs font-mono">{step.toolResult}</pre>
                                                                                    </div>
                                                                                </div>
                                                                            </Show>

                                                                            {/* Loading state inside expanded view */}
                                                                            <Show when={step.isLoading}>
                                                                                <div class="text-gray-400 italic flex items-center gap-2 text-xs pt-1">
                                                                                    Running...
                                                                                </div>
                                                                            </Show>
                                                                        </div>
                                                                    </Show>
                                                                </div>
                                                            </Match>
                                                        </Switch>
                                                    );
                                                }}
                                            </For>
                                        </div>
                                    </Show>
                                </>
                            )}
                        </For>
                        {/* Loading Indicator */}
                        <Show when={isLoading()}>
                            <div class="flex justify-start animate-pulse">
                                <div class="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-sm w-16 flex justify-center gap-1">
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ "animation-delay": "0ms" }}></div>
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ "animation-delay": "150ms" }}></div>
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ "animation-delay": "300ms" }}></div>
                                </div>
                            </div>
                        </Show>
                    </div>
                </Show>
            </div>

            {/* Textbar Area */}
            <div class="bg-white border-t border-gray-200 p-4">
                <div class="max-w-3xl mx-auto flex flex-col gap-2">
                    {/* Agent Selector */}
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-semibold text-gray-500 uppercase">Chat with:</span>
                        <select
                            class="text-sm border-none bg-gray-50 text-gray-700 py-1 px-2 rounded focus:ring-1 focus:ring-blue-500 outline-none"
                            value={selectedAgentId()}
                            onChange={(e) => setSelectedAgentId(e.currentTarget.value)}
                            disabled={isLoading()}
                        >
                            <option value="" disabled>Select an Agent</option>
                            <For each={agents()}>
                                {(agent) => <option value={agent.id} selected={agent.id === selectedAgentId()}>{agent.name}</option>}
                            </For>
                        </select>
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleSendMessage} class="relative">
                        <textarea
                            class="w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-3 pr-12 resize-none outline-none shadow-sm"
                            placeholder="Type your message here..."
                            rows={2}
                            value={inputMessage()}
                            onInput={(e) => setInputMessage(e.currentTarget.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSendMessage(e);
                                }
                            }}
                            disabled={isLoading()}
                        />
                        <button
                            type="submit"
                            class="absolute bottom-2.5 right-2.5 text-blue-600 hover:text-blue-800 p-1 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={!inputMessage().trim() || isLoading() || !selectedAgentId()}
                        >
                            <svg class="w-6 h-6 rotate-90" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z"></path></svg>
                        </button>
                    </form>
                    <div class="text-center text-xs text-gray-400">
                        AI can make mistakes. Consider checking important information.
                    </div>
                </div>
            </div>
        </div>
    );
};
