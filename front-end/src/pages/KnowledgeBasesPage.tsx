import { Component, createResource, For, createSignal, Show } from "solid-js";
import { A } from "@solidjs/router";
import { createKnowledgeBase, deleteKnowledgeBase, listKnowledgeBases, updateKnowledgeBase } from "../api/routes/knowledge-bases";
import { CreateKnowledgeBasePayload, KnowledgeBase } from "../api/types/knowledgeBases";

export const KnowledgeBasesPage: Component = () => {
    const [knowledgeBases, { refetch }] = createResource(async () => {
        const response = await listKnowledgeBases({ pageSize: 100 });
        return response.knowledge_bases;
    });

    const [isModalOpen, setIsModalOpen] = createSignal(false);
    const [editingKb, setEditingKb] = createSignal<KnowledgeBase | null>(null);
    const [formData, setFormData] = createSignal<CreateKnowledgeBasePayload>({ name: "", description: "" });

    const openModal = (kb?: KnowledgeBase) => {
        if (kb) {
            setEditingKb(kb);
            setFormData({ name: kb.name, description: kb.description || "" });
        } else {
            setEditingKb(null);
            setFormData({ name: "", description: "" });
        }
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditingKb(null);
    };

    const handleDelete = async (id: string, name: string) => {
        if (confirm(`Are you sure you want to delete knowledge base "${name}"?`)) {
            try {
                await deleteKnowledgeBase(id);
                refetch();
            } catch (e) {
                console.error(e);
                alert("Failed to delete knowledge base.");
            }
        }
    };

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        try {
            if (editingKb()) {
                await updateKnowledgeBase(editingKb()!.id, formData());
            } else {
                await createKnowledgeBase(formData());
            }
            refetch();
            closeModal();
        } catch (e) {
            console.error(e);
            alert("Failed to save knowledge base.");
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-2xl font-bold text-gray-800">Knowledge Bases</h1>
                <button
                    onClick={() => openModal()}
                    class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded shadow transition-colors flex items-center gap-2"
                >
                    <span>+</span> Create Knowledge Base
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <For each={knowledgeBases()} fallback={<div class="col-span-full text-center py-10 text-gray-500">No knowledge bases found.</div>}>
                    {(kb) => (
                        <div class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col">
                            <div class="flex justify-between items-start mb-2">
                                <h3 class="text-lg font-semibold text-gray-900 truncate" title={kb.name}>{kb.name}</h3>
                                <div class="flex gap-2">
                                    <button onClick={() => openModal(kb)} class="text-gray-400 hover:text-blue-600 p-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                                    </button>
                                    <button onClick={() => handleDelete(kb.id, kb.name)} class="text-gray-400 hover:text-red-600 p-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                    </button>
                                </div>
                            </div>
                            <p class="text-sm text-gray-500 mb-4 line-clamp-3 flex-1">{kb.description || "No description provided."}</p>

                            <div class="mt-auto flex justify-between items-center text-xs text-gray-400 pt-4 border-t border-gray-100">
                                <span>{kb.files.length} Files</span>
                                <A href={`/knowledge-bases/${kb.id}`} class="text-blue-600 hover:underline">View Files →</A>
                            </div>
                        </div>
                    )}
                </For>
            </div>

            {/* Modal */}
            <Show when={isModalOpen()}>
                <div class="fixed inset-0 z-40 flex items-center justify-center px-4 py-6">
                    <div class="fixed inset-0 bg-black/50" onClick={closeModal}></div>
                    <div
                        class="relative z-50 inline-block align-middle bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all w-full max-w-lg"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <form onSubmit={handleSubmit}>
                            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                                    {editingKb() ? 'Edit Knowledge Base' : 'New Knowledge Base'}
                                </h3>
                                <div class="space-y-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                        <input
                                            type="text"
                                            required
                                            class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                            value={formData().name}
                                            onInput={(e) => setFormData(prev => ({ ...prev, name: e.currentTarget.value }))}
                                        />
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                        <textarea
                                            rows={3}
                                            class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                            value={formData().description || ""}
                                            onInput={(e) => setFormData(prev => ({ ...prev, description: e.currentTarget.value }))}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                                <button
                                    type="submit"
                                    class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Save
                                </button>
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </Show>
        </div>
    );
};

