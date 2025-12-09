import { Component, createSignal, createResource, For, Show, createEffect } from "solid-js";
import { useParams, useNavigate, A } from "@solidjs/router";
import { createAgent, getAgent, updateAgent } from "../api/routes/agents";
import { listKnowledgeBases } from "../api/routes/knowledge-bases";
import { listToolsets } from "../api/routes/toolsets";
import { listAvailableModels } from "../api/routes/models";
import { CreateAgentPayload } from "../api/types/agents";

export const AgentFormPage: Component = () => {
    const params = useParams();
    const navigate = useNavigate();
    const isEditing = () => !!params.id;

    const [activeTab, setActiveTab] = createSignal<"general" | "kbs" | "toolsets" | "advanced">("general");

    // Form State
    const [formData, setFormData] = createSignal<CreateAgentPayload>({
        name: "",
        description: "",
        color: "#3B82F6",
        prompt: "",
        contextualize_system_prompt: "",
        enum_model: "chatgpt_3_5_turbo",
        max_response_tokens: 16000,
        temperature: 1.0,
        history_message_count: 10,
        knowledge_base_ids: [],
        toolset_ids: []
    });

    // Resources
    const [agent] = createResource(
        () => params.id,
        async (id) => {
            if (!id) return null;
            return await getAgent(id);
        }
    );

    const [knowledgeBases] = createResource(async () => {
        const res = await listKnowledgeBases({ pageSize: 100 });
        return res.knowledge_bases;
    });

    const [toolsets] = createResource(async () => {
        const res = await listToolsets({ pageSize: 100 });
        return res.toolsets;
    });

    const [availableModels] = createResource(async () => {
        return await listAvailableModels();
    });

    // Initialize form with existing agent data
    createEffect(() => {
        const data = agent();
        if (data) {
            setFormData({
                name: data.name,
                description: data.description || "",
                color: data.color || "#3B82F6",
                prompt: data.prompt,
                contextualize_system_prompt: data.contextualize_system_prompt,
                enum_model: data.enum_model,
                max_response_tokens: data.max_response_tokens,
                temperature: data.temperature,
                history_message_count: data.history_message_count,
                knowledge_base_ids: data.knowledge_bases.map(kb => kb.id),
                toolset_ids: data.toolsets.map(ts => ts.id)
            });
        }
    });

    // Ensure selected model matches available options; fall back to the first model.
    createEffect(() => {
        const models = availableModels();
        if (!models || models.length === 0) return;

        setFormData(prev => {
            const hasCurrent = models.some(m => m.model_key === prev.enum_model);
            if (hasCurrent) return prev;
            return { ...prev, enum_model: models[0].model_key };
        });
    });

    const updateField = (field: keyof CreateAgentPayload, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const toggleSelection = (field: "knowledge_base_ids" | "toolset_ids", id: string) => {
        setFormData(prev => {
            const current = prev[field] || [];
            const exists = current.includes(id);
            const newSelection = exists
                ? current.filter(item => item !== id)
                : [...current, id];
            return { ...prev, [field]: newSelection };
        });
    };

    const handleSubmit = async (e: Event) => {
        e.preventDefault();
        try {
            if (isEditing()) {
                await updateAgent(params.id!, formData());
            } else {
                await createAgent(formData());
            }
            navigate("/agents");
        } catch (err) {
            console.error("Failed to save agent", err);
            alert("Failed to save agent. Please check console for details.");
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex items-center gap-4 mb-6">
                <A href="/agents" class="text-gray-500 hover:text-gray-700">
                    ← Back
                </A>
                <h1 class="text-2xl font-bold text-gray-800">
                    {isEditing() ? "Edit Agent" : "Create New Agent"}
                </h1>
            </div>

            <div class="bg-white border border-gray-200 rounded-lg shadow-sm flex flex-col flex-1 overflow-hidden">
                {/* Tabs */}
                <div class="border-b border-gray-200 flex overflow-x-auto">
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap ${activeTab() === 'general' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('general')}
                    >
                        General
                    </button>
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap ${activeTab() === 'kbs' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('kbs')}
                    >
                        Knowledge Bases
                    </button>
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap ${activeTab() === 'toolsets' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('toolsets')}
                    >
                        Toolsets
                    </button>
                    <button
                        type="button"
                        class={`px-6 py-3 text-sm font-medium whitespace-nowrap ${activeTab() === 'advanced' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('advanced')}
                    >
                        Advanced
                    </button>
                </div>

                <form onSubmit={handleSubmit} class="flex flex-col flex-1 overflow-hidden">
                    <div class="flex-1 overflow-y-auto p-6">

                        {/* General Tab */}
                        <Show when={activeTab() === 'general'}>
                            <div class="space-y-6 max-w-2xl mx-auto">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                    <input
                                        type="text"
                                        required
                                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                        value={formData().name}
                                        onInput={(e) => updateField('name', e.currentTarget.value)}
                                    />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                    <textarea
                                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                        rows={3}
                                        value={formData().description || ""}
                                        onInput={(e) => updateField('description', e.currentTarget.value)}
                                    />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
                                    <textarea
                                        required
                                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none font-mono text-sm"
                                        rows={6}
                                        value={formData().prompt}
                                        onInput={(e) => updateField('prompt', e.currentTarget.value)}
                                        placeholder="You are a helpful AI assistant..."
                                    />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">Contextualize System Prompt</label>
                                    <textarea
                                        required
                                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none font-mono text-sm"
                                        rows={4}
                                        value={formData().contextualize_system_prompt}
                                        onInput={(e) => updateField('contextualize_system_prompt', e.currentTarget.value)}
                                    />
                                    <p class="text-xs text-gray-500 mt-1">Prompt used to contextualize the agent with provided knowledge and tools.</p>
                                </div>
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
                                        <select
                                            class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                            value={formData().enum_model}
                                            onChange={(e) => updateField('enum_model', e.currentTarget.value)}
                                            disabled={!availableModels() || availableModels()?.length === 0}
                                        >
                                            <Show when={availableModels()} fallback={<option disabled>Loading models...</option>}>
                                                <For each={availableModels()}>
                                                    {(model) => (
                                                        <option value={model.model_key}>{model.name}</option>
                                                    )}
                                                </For>
                                            </Show>
                                        </select>
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700 mb-1">Color (Hex)</label>
                                        <div class="flex gap-2">
                                            <input
                                                type="color"
                                                class="h-10 w-10 p-0 border-0 rounded overflow-hidden cursor-pointer"
                                                value={formData().color || "#3B82F6"}
                                                onInput={(e) => updateField('color', e.currentTarget.value)}
                                            />
                                            <input
                                                type="text"
                                                class="flex-1 rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                                value={formData().color || ""}
                                                onInput={(e) => updateField('color', e.currentTarget.value)}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Show>

                        {/* Knowledge Bases Tab */}
                        <Show when={activeTab() === 'kbs'}>
                            <div class="max-w-3xl mx-auto">
                                <h3 class="text-lg font-medium text-gray-800 mb-4">Select Knowledge Bases</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <For each={knowledgeBases()} fallback={<div class="text-gray-500">No knowledge bases found.</div>}>
                                        {(kb) => {
                                            const isSelected = () => formData().knowledge_base_ids?.includes(kb.id);
                                            return (
                                                <div
                                                    class={`border rounded-lg p-4 cursor-pointer transition-all ${isSelected() ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-200 hover:border-blue-300'}`}
                                                    onClick={() => toggleSelection('knowledge_base_ids', kb.id)}
                                                >
                                                    <div class="flex items-start gap-3">
                                                        <div class={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center ${isSelected() ? 'bg-blue-600 border-blue-600' : 'border-gray-400 bg-white'}`}>
                                                            <Show when={isSelected()}>
                                                                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                                                            </Show>
                                                        </div>
                                                        <div>
                                                            <h4 class="font-medium text-gray-900">{kb.name}</h4>
                                                            <p class="text-sm text-gray-500 line-clamp-2">{kb.description || "No description"}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        }}
                                    </For>
                                </div>
                            </div>
                        </Show>

                        {/* Toolsets Tab */}
                        <Show when={activeTab() === 'toolsets'}>
                            <div class="max-w-3xl mx-auto">
                                <h3 class="text-lg font-medium text-gray-800 mb-4">Select Toolsets</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <For each={toolsets()} fallback={<div class="text-gray-500">No toolsets found.</div>}>
                                        {(ts) => {
                                            const isSelected = () => formData().toolset_ids?.includes(ts.id);
                                            return (
                                                <div
                                                    class={`border rounded-lg p-4 cursor-pointer transition-all ${isSelected() ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-200 hover:border-blue-300'}`}
                                                    onClick={() => toggleSelection('toolset_ids', ts.id)}
                                                >
                                                    <div class="flex items-start gap-3">
                                                        <div class={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center ${isSelected() ? 'bg-blue-600 border-blue-600' : 'border-gray-400 bg-white'}`}>
                                                            <Show when={isSelected()}>
                                                                <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
                                                            </Show>
                                                        </div>
                                                        <div>
                                                            <h4 class="font-medium text-gray-900">{ts.name}</h4>
                                                            <div class="flex items-center gap-2 mt-1">
                                                                <span class="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">{ts.toolset_type}</span>
                                                            </div>
                                                            <p class="text-sm text-gray-500 mt-1 line-clamp-2">{ts.description || "No description"}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        }}
                                    </For>
                                </div>
                            </div>
                        </Show>

                        {/* Advanced Tab */}
                        <Show when={activeTab() === 'advanced'}>
                            <div class="space-y-6 max-w-2xl mx-auto">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Max Response Tokens
                                        <span class="ml-2 text-xs text-gray-500 font-normal">({formData().max_response_tokens})</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="1"
                                        max="32000"
                                        step="1"
                                        class="w-full"
                                        value={formData().max_response_tokens}
                                        onInput={(e) => updateField('max_response_tokens', parseInt(e.currentTarget.value))}
                                    />
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Temperature
                                        <span class="ml-2 text-xs text-gray-500 font-normal">({formData().temperature})</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="2"
                                        step="0.1"
                                        class="w-full"
                                        value={formData().temperature}
                                        onInput={(e) => updateField('temperature', parseFloat(e.currentTarget.value))}
                                    />
                                    <div class="flex justify-between text-xs text-gray-500">
                                        <span>Precise (0)</span>
                                        <span>Balanced (1.0)</span>
                                        <span>Creative (2.0)</span>
                                    </div>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        History Message Count
                                        <span class="ml-2 text-xs text-gray-500 font-normal">({formData().history_message_count})</span>
                                    </label>
                                    <input
                                        type="number"
                                        min="0"
                                        max="50"
                                        class="w-full rounded border border-gray-300 p-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                        value={formData().history_message_count}
                                        onInput={(e) => updateField('history_message_count', parseInt(e.currentTarget.value))}
                                    />
                                    <p class="text-xs text-gray-500 mt-1">Number of previous messages to include in the context window.</p>
                                </div>
                            </div>
                        </Show>
                    </div>

                    <div class="p-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
                        <A href="/agents" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50">
                            Cancel
                        </A>
                        <button
                            type="submit"
                            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            Save Agent
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

