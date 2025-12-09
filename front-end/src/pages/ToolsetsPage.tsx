import { Component, createResource, For, createSignal, Show } from "solid-js";
import { A, useNavigate } from "@solidjs/router";
import { deleteToolset, listToolsets } from "../api/routes/toolsets";

export const ToolsetsPage: Component = () => {
    const [toolsets, { refetch }] = createResource(async () => {
        const response = await listToolsets({ pageSize: 100 });
        return response.toolsets;
    });

    const handleDelete = async (id: string, name: string) => {
        if (confirm(`Are you sure you want to delete toolset "${name}"?`)) {
            try {
                await deleteToolset(id);
                refetch();
            } catch (e) {
                console.error(e);
                alert("Failed to delete toolset.");
            }
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-2xl font-bold text-gray-800">Toolsets</h1>
                <A
                    href="/toolsets/form"
                    class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded shadow transition-colors flex items-center gap-2"
                >
                    <span>+</span> Create Toolset
                </A>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <For each={toolsets()} fallback={<div class="col-span-full text-center py-10 text-gray-500">No toolsets found.</div>}>
                    {(toolset) => (
                        <div class="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col">
                            <div class="flex justify-between items-start mb-2">
                                <h3 class="text-lg font-semibold text-gray-900 truncate" title={toolset.name}>{toolset.name}</h3>
                                <div class="flex gap-2">
                                    <A href={`/toolsets/form/${toolset.id}`} class="text-gray-400 hover:text-blue-600 p-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                                    </A>
                                    <button onClick={() => handleDelete(toolset.id, toolset.name)} class="text-gray-400 hover:text-red-600 p-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                    </button>
                                </div>
                            </div>
                            <p class="text-sm text-gray-500 mb-4 line-clamp-3 flex-1">{toolset.description || "No description provided."}</p>

                            <div class="mt-auto flex justify-between items-center text-xs text-gray-400 pt-4 border-t border-gray-100">
                                <span class="px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-medium">
                                    {toolset.toolset_type}
                                </span>
                                <span>{toolset.tools.length} Tools</span>
                            </div>
                        </div>
                    )}
                </For>
            </div>
        </div>
    );
};
