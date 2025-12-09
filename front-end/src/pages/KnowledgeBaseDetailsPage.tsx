import { Component, createResource, For, createSignal, Show, onCleanup, onMount } from "solid-js";
import { useParams, A } from "@solidjs/router";
import { deleteKnowledgeBaseFile, getKnowledgeBase, listKnowledgeBaseFiles, updateKnowledgeBaseFile, uploadKnowledgeBaseFile } from "../api/routes/knowledge-bases";
import { KnowledgeBaseFile } from "../api/types/knowledgeBases";

export const KnowledgeBaseDetailsPage: Component = () => {
    const params = useParams();
    const [isDragging, setIsDragging] = createSignal(false);
    const [editingFile, setEditingFile] = createSignal<{ id: string, name: string } | null>(null);

    const [kb] = createResource(() => params.id, async (id) => {
        return await getKnowledgeBase(id);
    });

    const [files, { refetch: refetchFiles }] = createResource(() => params.id, async (id) => {
        const res = await listKnowledgeBaseFiles(id, { pageSize: 100 });
        return res.files;
    });

    onMount(() => {
        const intervalId = setInterval(() => refetchFiles(), 1000);
        onCleanup(() => clearInterval(intervalId));
    });

    const handleDragOver = (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e: DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
            await handleFiles(e.dataTransfer.files);
        }
    };

    const handleFileSelect = async (e: Event) => {
        const input = e.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            await handleFiles(input.files);
        }
    };

    const handleFiles = async (fileList: FileList) => {
        const kbId = params.id;
        if (!kbId) return;

        for (let i = 0; i < fileList.length; i++) {
            const file = fileList[i];
            try {
                await uploadKnowledgeBaseFile({
                    knowledgeBaseId: kbId,
                    file: file
                });
            } catch (err) {
                console.error(`Failed to upload ${file.name}`, err);
                alert(`Failed to upload ${file.name}`);
            }
        }
        refetchFiles();
    };

    const handleDeleteFile = async (id: string, name: string) => {
        if (confirm(`Are you sure you want to delete file "${name}"?`)) {
            await deleteKnowledgeBaseFile(id);
            refetchFiles();
        }
    };

    const startEditing = (file: KnowledgeBaseFile) => {
        setEditingFile({ id: file.id, name: file.name });
    };

    const saveFileName = async () => {
        const current = editingFile();
        if (!current) return;
        try {
            await updateKnowledgeBaseFile(current.id, { name: current.name });
            setEditingFile(null);
            refetchFiles();
        } catch (err) {
            console.error(err);
            alert("Failed to update file name");
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex items-center gap-4 mb-6">
                <A href="/knowledge-bases" class="text-gray-500 hover:text-gray-700">
                    ← Back
                </A>
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">
                        {kb()?.name || "Loading..."}
                    </h1>
                    <p class="text-sm text-gray-500">{kb()?.description}</p>
                </div>
            </div>

            {/* Drag & Drop Area */}
            <div
                class={`border-2 border-dashed rounded-lg p-10 text-center mb-8 transition-colors ${isDragging() ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <div class="flex flex-col items-center justify-center">
                    <svg class="w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                    <p class="text-gray-600 mb-2">Drag and drop files here, or click to select files</p>
                    <input
                        type="file"
                        multiple
                        class="hidden"
                        id="file-upload"
                        onChange={handleFileSelect}
                    />
                    <label for="file-upload" class="cursor-pointer text-blue-600 hover:underline">Browse Computer</label>
                </div>
            </div>

            {/* Files Table */}
            <div class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Name
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Type
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Pages
                            </th>
                            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <For each={files()} fallback={<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No files uploaded yet.</td></tr>}>
                            {(file) => (
                                <tr class="hover:bg-gray-50 transition-colors">
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        <Show when={editingFile()?.id === file.id} fallback={file.name}>
                                            <div class="flex items-center gap-2">
                                                <input
                                                    type="text"
                                                    class="border rounded px-2 py-1 text-sm outline-none focus:border-blue-500"
                                                    value={editingFile()?.name}
                                                    onInput={(e) => setEditingFile(prev => prev ? ({ ...prev, name: e.currentTarget.value }) : null)}
                                                    onKeyDown={(e) => e.key === 'Enter' && saveFileName()}
                                                />
                                                <button onClick={saveFileName} class="text-green-600 hover:text-green-800">Save</button>
                                                <button onClick={() => setEditingFile(null)} class="text-gray-500 hover:text-gray-700">Cancel</button>
                                            </div>
                                        </Show>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${file.enum_status === 'active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                            {file.enum_status}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {file.enum_type || "-"}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {file.num_pages || "-"}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button
                                            onClick={() => startEditing(file)}
                                            class="text-blue-600 hover:text-blue-900 mr-4"
                                            disabled={!!editingFile()}
                                        >
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDeleteFile(file.id, file.name)}
                                            class="text-red-600 hover:text-red-900"
                                            disabled={!!editingFile()}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            )}
                        </For>
                    </tbody>
                </table>
            </div>
        </div>
    );
};

