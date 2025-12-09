import { Component, For, Show, createResource, createSignal } from "solid-js";
import { A, useLocation, useNavigate } from "@solidjs/router";
import { deleteChat, listChats, updateChat } from "../api/routes/chats";

export const Sidebar: Component = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const [editingChatId, setEditingChatId] = createSignal<string | null>(null);
    const [editingTitle, setEditingTitle] = createSignal("");
    const [actionChatId, setActionChatId] = createSignal<string | null>(null);

    const [chats, { mutate, refetch }] = createResource(async () => {
        const response = await listChats({ pageSize: 50 });
        return response.chats;
    });

    const startEditing = (id: string, title: string) => {
        setEditingChatId(id);
        setEditingTitle(title);
    };

    const cancelEditing = () => {
        setEditingChatId(null);
        setEditingTitle("");
    };

    const handleSaveTitle = async (chatId: string) => {
        const newTitle = editingTitle().trim();
        if (!newTitle) return;

        setActionChatId(chatId);
        try {
            await updateChat(chatId, { title: newTitle });
            mutate((prev) => prev?.map((chat) => chat.id === chatId ? { ...chat, title: newTitle } : chat) ?? prev);
            cancelEditing();
            refetch();
        } catch (err) {
            console.error("Failed to update chat title", err);
        } finally {
            setActionChatId(null);
        }
    };

    const handleDeleteChat = async (chatId: string) => {
        const confirmed = window.confirm("Delete this chat? This cannot be undone.");
        if (!confirmed) return;

        setActionChatId(chatId);
        try {
            await deleteChat(chatId);
            mutate((prev) => prev?.filter((chat) => chat.id !== chatId) ?? prev);
            if (location.pathname === `/chat/${chatId}`) {
                navigate("/", { replace: true });
            }
            refetch();
        } catch (err) {
            console.error("Failed to delete chat", err);
        } finally {
            setActionChatId(null);
        }
    };

    return (
        <aside class="w-64 h-screen bg-gray-900 text-white flex flex-col border-r border-gray-800">
            <div class="p-4 border-b border-gray-800">
                <h1 class="text-xl font-bold mb-4 text-blue-400">NPLabs</h1>
                <nav class="flex flex-col space-y-2">
                    <A href="/agents" class="px-3 py-2 rounded hover:bg-gray-800 transition-colors flex items-center gap-2" activeClass="bg-gray-800 text-blue-400">
                        <span>🤖</span> Agents
                    </A>
                    <A href="/toolsets" class="px-3 py-2 rounded hover:bg-gray-800 transition-colors flex items-center gap-2" activeClass="bg-gray-800 text-blue-400">
                        <span>🛠️</span> Toolsets
                    </A>
                    <A href="/knowledge-bases" class="px-3 py-2 rounded hover:bg-gray-800 transition-colors flex items-center gap-2" activeClass="bg-gray-800 text-blue-400">
                        <span>📚</span> Knowledge Bases
                    </A>
                </nav>
            </div>

            <div class="flex-1 overflow-y-auto p-4">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Recent Chats</h2>
                    <A href="/" class="text-xs text-blue-400 hover:text-blue-300">+ New Chat</A>
                </div>

                <ul class="space-y-1">
                    <For each={chats() || []}>
                        {(chat) => (
                            <li>
                                <div
                                    class="flex items-center gap-2 px-3 py-2 rounded text-sm text-gray-300 hover:bg-gray-800 transition-colors group"
                                    classList={{ "bg-gray-800": location.pathname === `/chat/${chat.id}` }}
                                >
                                    <Show
                                        when={editingChatId() === chat.id}
                                        fallback={
                                            <>
                                                <A
                                                    href={`/chat/${chat.id}`}
                                                    class="flex-1 truncate"
                                                    activeClass="text-white"
                                                >
                                                    {chat.title}
                                                </A>
                                                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        class="p-1 text-gray-400 hover:text-blue-400 transition-colors cursor-pointer"
                                                        onClick={() => startEditing(chat.id, chat.title)}
                                                        aria-label="Edit chat name"
                                                        title="Edit name"
                                                    >
                                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                                                        </svg>
                                                    </button>
                                                    <button
                                                        class="p-1 text-gray-400 hover:text-red-500 transition-colors cursor-pointer"
                                                        onClick={() => handleDeleteChat(chat.id)}
                                                        aria-label="Delete chat"
                                                        title="Delete chat"
                                                        disabled={actionChatId() === chat.id}
                                                    >
                                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                                        </svg>
                                                    </button>
                                                </div>
                                            </>
                                        }
                                    >
                                        <div class="flex w-full items-center gap-2">
                                            <input
                                                class="flex-1 bg-gray-800 text-white text-sm rounded px-2 py-1 outline-none border border-gray-700 focus:border-blue-400"
                                                value={editingTitle()}
                                                onInput={(e) => setEditingTitle(e.currentTarget.value)}
                                                disabled={actionChatId() === chat.id}
                                            />
                                            <button
                                                class="px-2 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-500 transition-colors disabled:opacity-60"
                                                onClick={() => handleSaveTitle(chat.id)}
                                                disabled={actionChatId() === chat.id}
                                            >
                                                Save
                                            </button>
                                            <button
                                                class="px-2 py-1 bg-gray-700 text-white rounded text-xs hover:bg-gray-600 transition-colors"
                                                onClick={cancelEditing}
                                                disabled={actionChatId() === chat.id}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </Show>
                                </div>
                            </li>
                        )}
                    </For>
                </ul>
            </div>
        </aside>
    );
};

