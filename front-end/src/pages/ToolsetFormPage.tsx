import { Component, createSignal, createResource, Show, createEffect } from "solid-js";
import { useParams, useNavigate, A } from "@solidjs/router";
import { createToolset, createTool, getToolset, updateToolset, deleteTool, updateTool } from "../api/routes/toolsets";
import { CreateToolPayload, CreateToolsetPayload } from "../api/types/toolsets";
import { GeneralTab } from "../components/Toolsets/GeneralTab";
import { ToolsTab } from "../components/Toolsets/ToolsTab";

export const ToolsetFormPage: Component = () => {
    const params = useParams();
    const navigate = useNavigate();
    const isEditing = () => !!params.id;
    const [activeTab, setActiveTab] = createSignal<"general" | "tools">("general");

    const [toolset, setToolset] = createSignal<Partial<CreateToolsetPayload> & { id?: string; mcp_server_auth_header?: Record<string, string> | null; encrypted_mcp_server_auth_header?: Record<string, string> | null }>({
        name: "",
        description: "",
        toolset_type: "CUSTOM",
        mcp_server_url: "",
    });

    const [tools, setTools] = createSignal<(CreateToolPayload & { id?: string })[]>([]);
    const [originalTools, setOriginalTools] = createSignal<(CreateToolPayload & { id?: string })[]>([]);

    const [fetchedToolset] = createResource(() => params.id, async (id) => {
        if (!id) return null;
        return await getToolset(id);
    });

    createEffect(() => {
        const data = fetchedToolset();
        if (data) {
            setToolset({
                id: data.id,
                name: data.name,
                description: data.description,
                toolset_type: data.toolset_type,
                mcp_server_url: data.mcp_server_url,
                // @ts-ignore
                encrypted_mcp_server_auth_header: data.mcp_server_auth_header // Backend returns encrypted header usually, assuming api types align or adapting
            });

            // Map existing tools to the form format
            const mappedTools = (data.tools || []).map(t => ({
                ...t,
                // Ensure optional fields exist
                webhook_query_params_schema: t.webhook_query_params_schema || null,
                webhook_path_params_schema: t.webhook_path_params_schema || null,
                webhook_body_params_schema: t.webhook_body_params_schema || null,
            }));

            setTools(mappedTools);
            setOriginalTools(mappedTools);
        }
    });

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        const currentToolset = toolset();

        if (!currentToolset.name?.trim()) {
            alert("Please provide a name for the toolset.");
            return;
        }

        try {
            if (isEditing() && params.id) {
                // Update Toolset
                await updateToolset(params.id, {
                    name: currentToolset.name,
                    description: currentToolset.description,
                    toolset_type: currentToolset.toolset_type,
                    mcp_server_url: currentToolset.mcp_server_url,
                    mcp_server_auth_header: currentToolset.mcp_server_auth_header || null
                });

                // Handle Tools Update Strategy:
                // Since we don't have a sophisticated diffing for tools in the reference,
                // the reference implementation deletes all old tools and recreates them.
                // We will attempt to be smarter: update existing, create new, delete removed.

                const currentTools = tools();
                const oldTools = originalTools();

                // 1. Delete removed tools
                const toolsToDelete = oldTools.filter(ot => !currentTools.find(ct => ct.id === ot.id));
                for (const t of toolsToDelete) {
                    if (t.id) await deleteTool(t.id);
                }

                // 2. Update or Create
                for (const t of currentTools) {
                    if (t.id && !t.id.startsWith("new_")) {
                        // Update existing
                        await updateTool(t.id, t);
                    } else {
                        // Create new
                        await createTool(params.id, t);
                    }
                }

            } else {
                // Create New Toolset
                const created = await createToolset({
                    name: currentToolset.name!,
                    description: currentToolset.description,
                    toolset_type: currentToolset.toolset_type,
                    mcp_server_url: currentToolset.mcp_server_url,
                    mcp_server_auth_header: currentToolset.mcp_server_auth_header,
                    tools: currentToolset.toolset_type === "MCP_SERVER" ? [] : tools()
                });
            }
            navigate("/toolsets");
        } catch (err) {
            console.error("Failed to save toolset", err);
            alert("Failed to save toolset.");
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex items-center gap-4 mb-6">
                <A href="/toolsets" class="text-gray-500 hover:text-gray-700">
                    ← Back
                </A>
                <h1 class="text-2xl font-bold text-gray-800">
                    {isEditing() ? "Edit Toolset" : "Create New Toolset"}
                </h1>
            </div>

            <div class="bg-white border border-gray-200 rounded-lg shadow-sm flex flex-col flex-1 overflow-hidden">
                {/* Tabs */}
                <div class="border-b border-gray-200 flex overflow-x-auto">
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap cursor-pointer ${activeTab() === 'general' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('general')}
                    >
                        General Configuration
                    </button>
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap cursor-pointer ${activeTab() === 'tools' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('tools')}
                    >
                        Tools
                    </button>
                </div>

                <form onSubmit={handleSubmit} class="flex flex-col flex-1 overflow-hidden">
                    <div class="flex-1 overflow-y-auto p-6">
                        <Show when={activeTab() === 'general'}>
                            <GeneralTab
                                toolset={toolset()}
                                setToolset={(updates) => setToolset(prev => ({ ...prev, ...updates }))}
                            />
                        </Show>
                        <Show when={activeTab() === 'tools'}>
                            <ToolsTab
                                toolset={toolset()}
                                tools={tools()}
                                setTools={setTools}
                            />
                        </Show>
                    </div>

                    <div class="p-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
                        <A href="/toolsets" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50">
                            Cancel
                        </A>
                        <button
                            type="submit"
                            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            Save Toolset
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

