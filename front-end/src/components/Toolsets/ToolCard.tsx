import { Component, createSignal, For, Show, createEffect } from "solid-js";
import { CreateToolPayload, Tool } from "../../api/types/toolsets";
import JsonSchemaEditor from "../JsonSchemaEditor";
import KeyValueEditor from "../KeyValueEditor";
import { getWebhookAuthHeader } from "../../api/routes/toolsets";
import { listAgents } from "../../api/routes/agents";
import { createResource } from "solid-js";

interface ToolCardProps {
    tool: CreateToolPayload & { id?: string; encrypted_webhook_auth_header?: Record<string, string> | null };
    index: number;
    updateTool: (updates: Partial<CreateToolPayload>) => void;
    removeTool: () => void;
    initialCollapsed?: boolean;
}

export const ToolCard: Component<ToolCardProps> = (props) => {
    const isWebhook = () => props.tool.tool_type === "WEBHOOK";
    const isAgent = () => props.tool.tool_type === "AGENT";
    const [collapsed, setCollapsed] = createSignal(props.initialCollapsed || false);
    const [isAdvancedOpen, setIsAdvancedOpen] = createSignal(false);

    const [headers, setHeaders] = createSignal<Record<string, string>>({});

    const [agents] = createResource(async () => {
        const res = await listAgents({ pageSize: 100 });
        return res.agents;
    });

    createEffect(() => {
        if (props.tool.webhook_auth_header) {
            setHeaders(props.tool.webhook_auth_header);
        } else if (props.tool.encrypted_webhook_auth_header) {
            setHeaders(props.tool.encrypted_webhook_auth_header);
        } else {
            setHeaders({});
        }
    });

    const handleHeadersChange = (newHeaders: Record<string, string>) => {
        setHeaders(newHeaders);
        props.updateTool({ webhook_auth_header: newHeaders });
    };

    const handleIsEditingHeaders = async () => {
        if (props.tool.id && !props.tool.id.startsWith("new_")) {
            try {
                const fetched = await getWebhookAuthHeader(props.tool.id);
                if (fetched) setHeaders(fetched);
            } catch (e) {
                console.error(e);
            }
        }
    };

    const extractPathParams = (url: string): string[] => {
        const names = new Set<string>();
        const regex = /\{([^}]+)\}/g;
        let match: RegExpExecArray | null;
        while ((match = regex.exec(url)) !== null) {
            const name = match[1].trim();
            if (name) names.add(name);
        }
        return Array.from(names);
    };

    const buildPathParamsSchema = (
        paramNames: string[],
        currentSchema: any
    ): Record<string, unknown> => {
        const currentIsObject =
            currentSchema &&
            typeof currentSchema === "object" &&
            (currentSchema as any).type === "object";
        const currentProps = currentIsObject
            ? (currentSchema as any).properties || {}
            : {};
        const description =
            (currentIsObject && (currentSchema as any).description) ||
            "Schema que define a estrutura dos path parameters de um webhook.";

        const properties: Record<string, any> = {};
        for (const p of paramNames) {
            const existing = currentProps[p];
            const next =
                existing && typeof existing === "object"
                    ? { ...existing }
                    : { type: "string", description: `Parâmetro de path '${p}'` };
            if (!next.type) next.type = "string";
            if (!next.description) next.description = `Parâmetro de path '${p}'`;
            properties[p] = next;
        }

        return {
            type: "object",
            description,
            properties,
            required: paramNames,
        };
    };

    const handleWebhookUrlChange = (url: string) => {
        const paramNames = extractPathParams(url);
        const nextPathSchema = buildPathParamsSchema(paramNames, props.tool.webhook_path_params_schema);

        props.updateTool({
            webhook_url: url,
            webhook_path_params_schema: nextPathSchema
        });
    };

    return (
        <div class="border border-gray-200 rounded-lg p-4 bg-gray-50 mb-4">
            {/* Header */}
            <div class="flex items-center gap-2 mb-2">
                <button
                    type="button"
                    onClick={() => setCollapsed(!collapsed())}
                    class="p-1 text-blue-600 hover:bg-blue-50 rounded cursor-pointer"
                >
                    <Show when={collapsed()} fallback={
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    }>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </Show>
                </button>
                <div class="flex-1">
                    <Show when={collapsed()} fallback={
                        <input
                            type="text"
                            class="w-full rounded border border-gray-300 p-1 text-sm focus:border-blue-500 outline-none"
                            value={props.tool.name || ""}
                            onInput={(e) => props.updateTool({ name: e.currentTarget.value })}
                            placeholder="Tool Name"
                        />
                    }>
                        <div class="text-sm font-medium text-gray-800 truncate">
                            {props.tool.name || "New Tool"}
                        </div>
                    </Show>
                </div>
                <button
                    type="button"
                    onClick={props.removeTool}
                    class="text-red-500 hover:text-red-700 p-1 cursor-pointer"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                </button>
            </div>

            <Show when={collapsed() && props.tool.description}>
                <div class="text-xs text-gray-500 mb-1 line-clamp-2 px-7">
                    {props.tool.description}
                </div>
            </Show>

            {/* Expanded Content */}
            <Show when={!collapsed()}>
                <div class="px-1 pt-2 space-y-4">
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1">Description</label>
                        <input
                            type="text"
                            class="w-full rounded border border-gray-300 p-2 text-sm focus:border-blue-500 outline-none"
                            value={props.tool.description || ""}
                            onInput={(e) => props.updateTool({ description: e.currentTarget.value })}
                            placeholder="Brief description"
                        />
                    </div>

                    {/* Type Selector */}
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1">Tool Type</label>
                        <div class="inline-flex rounded-md shadow-sm" role="group">
                            <button
                                type="button"
                                onClick={() => props.updateTool({ tool_type: "AGENT" })}
                                class={`px-4 py-2 text-sm font-medium border rounded-l-lg cursor-pointer ${isAgent() ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                            >
                                Agent
                            </button>
                            <button
                                type="button"
                                onClick={() => props.updateTool({ tool_type: "WEBHOOK" })}
                                class={`px-4 py-2 text-sm font-medium border rounded-r-lg cursor-pointer ${isWebhook() ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                            >
                                Webhook
                            </button>
                        </div>
                    </div>

                    {/* Webhook Config */}
                    <Show when={isWebhook()}>
                        <div class="space-y-4 p-4 border border-gray-200 rounded bg-white">
                            <div class="flex gap-4">
                                <div class="w-1/4">
                                    <label class="block text-xs font-medium text-gray-500 mb-1">Method</label>
                                    <select
                                        class="w-full border border-gray-300 rounded p-2 text-sm outline-none"
                                        value={props.tool.webhook_http_method || "POST"}
                                        onChange={(e) => props.updateTool({ webhook_http_method: e.currentTarget.value })}
                                    >
                                        <option value="GET">GET</option>
                                        <option value="POST">POST</option>
                                        <option value="PUT">PUT</option>
                                        <option value="PATCH">PATCH</option>
                                        <option value="DELETE">DELETE</option>
                                    </select>
                                </div>
                                <div class="flex-1">
                                    <label class="block text-xs font-medium text-gray-500 mb-1">Webhook URL</label>
                                    <input
                                        type="text"
                                        class="w-full border border-gray-300 rounded p-2 text-sm outline-none"
                                        value={props.tool.webhook_url || ""}
                                        onInput={(e) => handleWebhookUrlChange(e.currentTarget.value)}
                                        placeholder="https://api.example.com/webhook"
                                    />
                                </div>
                            </div>

                            <KeyValueEditor
                                title="Webhook Headers"
                                keyValuePairs={headers()}
                                setKeyValuePairs={handleHeadersChange}
                                initialCollapsed={true}
                                editable={!!props.tool.webhook_auth_header || !!props.tool.encrypted_webhook_auth_header}
                                handleIsEditing={handleIsEditingHeaders}
                            />

                            <button
                                type="button"
                                onClick={() => setIsAdvancedOpen(!isAdvancedOpen())}
                                class="text-sm text-blue-600 hover:underline flex items-center gap-1 mx-auto cursor-pointer"
                            >
                                {isAdvancedOpen() ? "Hide" : "Show"} Advanced Configuration
                                <svg class={`w-4 h-4 transform transition-transform ${isAdvancedOpen() ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </button>

                            <Show when={isAdvancedOpen()}>
                                <div class="space-y-4 pt-2">
                                    <JsonSchemaEditor
                                        jsonSchema={props.tool.webhook_query_params_schema || null}
                                        setJsonSchema={(schema) => props.updateTool({ webhook_query_params_schema: schema as Record<string, unknown> })}
                                        type="object"
                                        title="Query Params Schema"
                                        defaultDescription="Schema for query parameters"
                                        arrayAllowed={false}
                                        requireDescription={true}
                                        depthAllowed={1}
                                        allFieldsRequired={false}
                                        canAddProperties={true}
                                        initialCollapsed={true}
                                    />
                                    <JsonSchemaEditor
                                        jsonSchema={props.tool.webhook_path_params_schema || null}
                                        setJsonSchema={(schema) => props.updateTool({ webhook_path_params_schema: schema as Record<string, unknown> })}
                                        type="object"
                                        title="Path Params Schema"
                                        defaultDescription="Schema for path parameters"
                                        arrayAllowed={false}
                                        requireDescription={true}
                                        depthAllowed={1}
                                        allFieldsRequired={true}
                                        canAddProperties={false}
                                        initialCollapsed={true}
                                    />
                                    <JsonSchemaEditor
                                        jsonSchema={props.tool.webhook_body_params_schema || null}
                                        setJsonSchema={(schema) => props.updateTool({ webhook_body_params_schema: schema as Record<string, unknown> })}
                                        type="object"
                                        title="Body Params Schema"
                                        defaultDescription="Schema for body parameters"
                                        arrayAllowed={true}
                                        requireDescription={true}
                                        depthAllowed={1}
                                        allFieldsRequired={false}
                                        canAddProperties={true}
                                        initialCollapsed={true}
                                    />
                                </div>
                            </Show>
                        </div>
                    </Show>

                    {/* Agent Config */}
                    <Show when={isAgent()}>
                        <div class="space-y-2">
                            <label class="block text-xs font-medium text-gray-500 mb-1">Target Agent</label>
                            <select
                                class="w-full border border-gray-300 rounded p-2 text-sm outline-none bg-white"
                                value={props.tool.target_agent_id || ""}
                                onChange={(e) => props.updateTool({ target_agent_id: e.currentTarget.value })}
                            >
                                <option value="" disabled>Select an Agent</option>
                                <For each={agents()}>
                                    {(agent) => (
                                        <option value={agent.id}>{agent.name}</option>
                                    )}
                                </For>
                            </select>
                        </div>
                    </Show>
                </div>
            </Show>
        </div>
    );
};
