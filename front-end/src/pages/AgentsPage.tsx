import { Component, createResource, For } from "solid-js";
import { A } from "@solidjs/router";
import { deleteAgent, listAgents } from "../api/routes/agents";

export const AgentsPage: Component = () => {
    const [agents, { refetch }] = createResource(async () => {
        const response = await listAgents({ pageSize: 100 });
        return response.agents;
    });

    const handleDelete = async (id: string, name: string) => {
        if (confirm(`Are you sure you want to delete agent "${name}"?`)) {
            await deleteAgent(id);
            refetch();
        }
    };

    return (
        <div class="h-full flex flex-col p-6 bg-white overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-2xl font-bold text-gray-800">Agents</h1>
                <A
                    href="/agents/form"
                    class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded shadow transition-colors flex items-center gap-2"
                >
                    <span>+</span> Create Agent
                </A>
            </div>

            <div class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Name
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Model
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Description
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Actions
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        <For each={agents()} fallback={<tr><td colspan="5" class="px-6 py-4 text-center text-gray-500">No agents found.</td></tr>}>
                            {(agent) => (
                                <tr class="hover:bg-gray-50 transition-colors">
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <div class="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ "background-color": agent.color || "#3B82F6" }}>
                                                {agent.name.substring(0, 2).toUpperCase()}
                                            </div>
                                            <div class="ml-4">
                                                <div class="text-sm font-medium text-gray-900">{agent.name}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {agent.enum_model}
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={agent.description || ""}>
                                        {agent.description || "-"}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${agent.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {agent.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <A href={`/agents/form/${agent.id}`} class="text-blue-600 hover:text-blue-900 mr-4">Edit</A>
                                        <button
                                            onClick={() => handleDelete(agent.id, agent.name)}
                                            class="text-red-600 hover:text-red-900"
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

