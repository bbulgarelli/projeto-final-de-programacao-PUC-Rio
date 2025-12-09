import { Component, createSignal, For, Show } from "solid-js";
import { CreateToolPayload, CreateToolsetPayload } from "../../api/types/toolsets";
import { ToolCard } from "./ToolCard";
import { Index } from "solid-js";

interface ToolsTabProps {
    toolset: Partial<CreateToolsetPayload>;
    tools: (CreateToolPayload & { id?: string })[];
    setTools: (tools: (CreateToolPayload & { id?: string })[]) => void;
}

export const ToolsTab: Component<ToolsTabProps> = (props) => {
    const isMcp = () => props.toolset.toolset_type === "MCP_SERVER";

    const addTool = () => {
        const newId = `new_${Date.now()}_${Math.random().toString(36).slice(2)}`;
        const newTool: CreateToolPayload & { id: string } = {
            id: newId,
            name: "",
            description: "",
            tool_type: "WEBHOOK",
            webhook_url: "",
            webhook_http_method: "POST",
        };
        props.setTools([...props.tools, newTool]);
    };

    const removeTool = (index: number) => {
        const newTools = [...props.tools];
        newTools.splice(index, 1);
        props.setTools(newTools);
    };

    const updateTool = (index: number, updates: Partial<CreateToolPayload>) => {
        const newTools = [...props.tools];
        newTools[index] = { ...newTools[index], ...updates };
        props.setTools(newTools);
    };

    return (
        <div class="space-y-4 w-[70%] mx-auto">
            <Show when={isMcp()} fallback={
                <>
                    <div class="flex justify-between items-center">
                        <h3 class="text-sm font-medium text-gray-700">Tools (Optional)</h3>
                        <button
                            type="button"
                            onClick={addTool}
                            class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 cursor-pointer"
                        >
                            <span>+</span> Add Tool
                        </button>
                    </div>

                    <Show when={props.tools.length === 0}>
                        <div class="text-center py-8 border-2 border-dashed border-gray-200 rounded-lg">
                            <p class="text-gray-500 text-sm mb-2">No tools added yet</p>
                            <button
                                type="button"
                                onClick={addTool}
                                class="text-blue-600 hover:text-blue-800 text-sm font-medium cursor-pointer"
                            >
                                Create first tool
                            </button>
                        </div>
                    </Show>

                    <Index each={props.tools}>
                        {(tool, index) => (
                            <ToolCard
                                tool={tool()}
                                index={index}
                                updateTool={(updates) => updateTool(index, updates)}
                                removeTool={() => removeTool(index)}
                                initialCollapsed={!tool().id?.startsWith("new_")}
                            />
                        )}
                    </Index>

                    <Show when={props.tools.length > 0}>
                        <button
                            type="button"
                            onClick={addTool}
                            class="w-full py-2 border-2 border-dashed border-gray-200 rounded-lg text-gray-500 hover:text-blue-600 hover:border-blue-200 transition-colors text-sm cursor-pointer"
                        >
                            + Add Another Tool
                        </button>
                    </Show>
                </>
            }>
                <div class="text-center py-6 border border-dashed border-gray-200 rounded-lg bg-gray-50 text-sm text-gray-600">
                    MCP Servers cannot have their tools configured manually here. They will be discovered dynamically when you save the toolset.
                </div>
            </Show>
        </div>
    );
};
