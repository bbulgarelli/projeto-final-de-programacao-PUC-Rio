import { Component, createSignal, createEffect, Show } from "solid-js";
import { CreateToolsetPayload } from "../../api/types/toolsets";
import KeyValueEditor from "../KeyValueEditor";
import { getMcpServerAuthHeader } from "../../api/routes/toolsets";

interface GeneralTabProps {
    toolset: Partial<CreateToolsetPayload> & { id?: string; mcp_server_auth_header?: Record<string, string> | null; encrypted_mcp_server_auth_header?: Record<string, string> | null };
    setToolset: (updates: Partial<CreateToolsetPayload>) => void;
}

export const GeneralTab: Component<GeneralTabProps> = (props) => {
    const isMcp = () => props.toolset.toolset_type === "MCP_SERVER";

    const [mcpHeaders, setMcpHeaders] = createSignal<Record<string, string>>({});

    createEffect(() => {
        if (props.toolset.mcp_server_auth_header) {
            setMcpHeaders(props.toolset.mcp_server_auth_header);
        } else if (props.toolset.encrypted_mcp_server_auth_header) {
            setMcpHeaders(props.toolset.encrypted_mcp_server_auth_header);
        } else {
            setMcpHeaders({});
        }
    });

    const handleMcpHeadersChange = (headers: Record<string, string>) => {
        setMcpHeaders(headers);
        props.setToolset({ mcp_server_auth_header: headers });
    };

    const handleIsEditingMcpHeaders = async () => {
        if (props.toolset.id) {
            try {
                const headers = await getMcpServerAuthHeader(props.toolset.id);
                if (headers) setMcpHeaders(headers);
            } catch (e) {
                console.error(e);
            }
        }
    };

    return (
        <div class="space-y-6 w-[70%] mx-auto">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                    <input
                        type="text"
                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                        value={props.toolset.name || ""}
                        onInput={(e) => props.setToolset({ name: e.currentTarget.value })}
                        placeholder="Enter toolset name"
                        required
                    />
                </div>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                    rows={3}
                    class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    value={props.toolset.description || ""}
                    onInput={(e) => props.setToolset({ description: e.currentTarget.value })}
                    placeholder="Brief description of the toolset"
                />
            </div>

            {/* Segmented control */}
            <div class="space-y-3">
                <label class="block text-sm font-medium text-gray-700">Toolset Type</label>
                <div class="w-full md:w-1/2">
                    <div class="relative grid grid-cols-2 rounded-lg border border-gray-300 bg-white overflow-hidden">
                        <button
                            type="button"
                            onClick={() =>
                                props.setToolset({
                                    toolset_type: "CUSTOM",
                                    mcp_server_url: props.toolset.mcp_server_url,
                                })
                            }
                            class={`relative px-3 py-2 text-sm transition-colors cursor-pointer ${!isMcp() ? 'bg-blue-600 text-white font-medium' : 'text-gray-700 hover:bg-gray-50'}`}
                        >
                            Custom
                        </button>
                        <button
                            type="button"
                            onClick={() =>
                                props.setToolset({
                                    toolset_type: "MCP_SERVER",
                                })
                            }
                            class={`relative px-3 py-2 text-sm transition-colors cursor-pointer ${isMcp() ? 'bg-blue-600 text-white font-medium' : 'text-gray-700 hover:bg-gray-50'}`}
                        >
                            MCP Server
                        </button>
                    </div>
                </div>
            </div>

            {/* MCP-specific fields */}
            <Show when={isMcp()}>
                <div class="space-y-4 pt-4 border-t border-gray-200">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                MCP Server URL
                            </label>
                            <input
                                type="text"
                                class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                value={props.toolset.mcp_server_url || ""}
                                onInput={(e) =>
                                    props.setToolset({
                                        mcp_server_url: e.currentTarget.value,
                                    })
                                }
                                placeholder="https://mcp.example.com"
                            />
                        </div>
                    </div>

                    <KeyValueEditor
                        title="MCP Server Headers"
                        keyValuePairs={mcpHeaders()}
                        setKeyValuePairs={handleMcpHeadersChange}
                        handleIsEditing={handleIsEditingMcpHeaders}
                        editable={!!props.toolset.mcp_server_auth_header || !!props.toolset.encrypted_mcp_server_auth_header}
                    />
                </div>
            </Show>
        </div>
    );
};

