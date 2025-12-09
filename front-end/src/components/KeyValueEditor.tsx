import type { Component } from "solid-js";
import { createEffect, createMemo, createSignal, For, Show, Index, on } from "solid-js";
import { TbTrash } from "solid-icons/tb";
import { IoAdd, IoChevronDown, IoChevronForward } from "solid-icons/io";
import { SimpleSearchBar } from "../UsefulComponents";

interface KeyValueEditorProps {
    title: string;
    keyValuePairs: Record<string, string>;
    setKeyValuePairs: (keyValuePairs: Record<string, string>) => void;
    /** Texto do botão de adicionar (default: "Adicionar header") */
    addButtonLabel?: string;
    /** Texto do estado vazio (default: "Nenhum header adicionado.") */
    emptyStateText?: string;
    /** Inicia colapsado (default: false) */
    initialCollapsed?: boolean;
    /** Define se inicia em modo editável (default: true) */
    editable?: boolean;
    handleIsEditing?: () => void;
}

type KeyValuePair = { id: string; key: string; value: string };

type InputEvt = InputEvent & {
    currentTarget: HTMLInputElement;
    target: Element;
};

const KeyValueEditor: Component<KeyValueEditorProps> = (props) => {
    const initialPairs = (): KeyValuePair[] =>
        Object.entries(props.keyValuePairs).map(([key, value]) => ({
            id: `hdr-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            key,
            value,
        }));

    const [internalKeyValuePairs, setInternalKeyValuePairs] =
        createSignal<KeyValuePair[]>(initialPairs());
    const [collapsed, setCollapsed] = createSignal<boolean>(
        !!props.initialCollapsed
    );
    const headerBodyId = createMemo(
        () => `kv-body-${Math.random().toString(36).slice(2)}`
    );
    const [isEditing, setIsEditing] = createSignal<boolean>(
        props.editable ?? true
    );

    createEffect(() => {
        setIsEditing(props.editable ?? true);
    });

    const addButtonLabel = () => props.addButtonLabel ?? "Adicionar";
    const emptyStateText = () =>
        props.emptyStateText ?? "Nenhum item adicionado.";

    // Build a record from internal pairs, filtering out empty keys
    const toRecord = (rows: KeyValuePair[]): Record<string, string> => {
        const acc: Record<string, string> = {};
        for (const { key, value } of rows) {
            const k = key.trim();
            if (!k) continue;
            acc[k] = value;
        }
        return acc;
    };

    // Sync from parent prop to local state, reusing ids when possible and avoiding unnecessary resets
    createEffect(
        on(
            () => props.keyValuePairs,
            (newProps) => {
                const currentRecord = toRecord(internalKeyValuePairs());
                if (JSON.stringify(currentRecord) === JSON.stringify(newProps)) {
                    return;
                }

                const currentByKey = new Map(
                    internalKeyValuePairs().map((r) => [r.key, r.id])
                );
                const nextInternal: KeyValuePair[] = Object.entries(newProps).map(
                    ([key, value]) => ({
                        id:
                            currentByKey.get(key) ||
                            `hdr-${Date.now()}-${Math.random().toString(36).slice(2)}`,
                        key,
                        value,
                    })
                );

                // Compare shallow equality on ordered list of [key,value]
                const prev = internalKeyValuePairs();
                const same =
                    nextInternal.length === prev.length &&
                    nextInternal.every(
                        (n, i) =>
                            prev[i] && prev[i].key === n.key && prev[i].value === n.value
                    );
                if (!same) setInternalKeyValuePairs(nextInternal);
            }
        )
    );

    // Push updates up when internal changes, but only if different from prop
    createEffect(() => {
        const next = toRecord(internalKeyValuePairs());
        const same = JSON.stringify(next) === JSON.stringify(props.keyValuePairs);
        if (!same) props.setKeyValuePairs(next);
    });

    const addKeyValuePair = () => {
        const id = `hdr-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        setInternalKeyValuePairs((prev) => [{ id, key: "", value: "" }, ...prev]);
    };

    const updateKeyValuePair = (id: string, updates: Partial<KeyValuePair>) => {
        setInternalKeyValuePairs((prev) =>
            prev.map((r) => (r.id === id ? { ...r, ...updates } : r))
        );
    };

    const removeKeyValuePair = (id: string) => {
        setInternalKeyValuePairs((prev) => prev.filter((r) => r.id !== id));
    };

    const toggleCollapsed = () => setCollapsed((prev) => !prev);
    const onHeaderKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleCollapsed();
        }
    };

    return (
        <div class="border border-gray-200 rounded-lg bg-white">
            <div class="p-2">
                <div class="space-y-1">
                    <div class="flex items-stretch justify-center">
                        <button
                            type="button"
                            aria-expanded={!collapsed()}
                            aria-controls={headerBodyId()}
                            onClick={toggleCollapsed}
                            onKeyDown={onHeaderKeyDown}
                            class="flex items-center justify-center text-gray-600 hover:text-gray-800 p-1 cursor-pointer"
                            title={collapsed() ? "Expandir" : "Recolher"}
                        >
                            <Show
                                when={collapsed()}
                                fallback={<IoChevronDown size={18} class="text-blue-600" />}
                            >
                                <IoChevronForward
                                    size={18}
                                    class="text-blue-600"
                                />
                            </Show>
                        </button>
                        <div class="flex-1 min-w-0 flex items-stretch gap-2">
                            <div class="truncate text-sm leading-5 px-3 py-2 rounded-lg flex items-center">
                                {props.title}
                            </div>
                            <Show when={!isEditing() && !collapsed()}>
                                <div class="ml-auto flex items-center">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            props.handleIsEditing?.();
                                            setIsEditing(true);
                                        }}
                                        class="px-3 py-1 text-xs text-blue-600 hover:text-blue-700 cursor-pointer"
                                        title="Editar"
                                    >
                                        Editar
                                    </button>
                                </div>
                            </Show>
                        </div>
                    </div>
                </div>
            </div>
            <div
                id={headerBodyId()}
                class={`overflow-hidden transition-all duration-300 ease-in-out ${collapsed() ? "max-h-0 opacity-0" : "max-h-[3000px] opacity-100"
                    }`}
            >
                <div class="px-3 pt-0 pb-3">
                    <div class="space-y-2">
                        <div
                            class={`border border-gray-200 rounded-md overflow-hidden bg-white ${!isEditing() ? "opacity-60 pointer-events-none" : ""
                                }`}
                        >
                            <div
                                class={`relative bg-gray-50 flex text-[11px] font-medium text-gray-600 ${isEditing() ? "pr-32" : ""
                                    }`}
                            >
                                <div class="py-2 px-3 flex-[2]">Chave</div>
                                <div class="py-2 px-3 flex-[7]">Valor</div>
                                <div class="py-2 px-3 w-10" />
                                <Show when={isEditing()}>
                                    <div class="absolute right-2 inset-y-0 flex items-center">
                                        <button
                                            type="button"
                                            onClick={addKeyValuePair}
                                            class="flex items-center text-xs text-blue-600 hover:text-blue-700 cursor-pointer"
                                        >
                                            <IoAdd size={14} class="mr-1" />
                                            <span>{addButtonLabel()}</span>
                                        </button>
                                    </div>
                                </Show>
                            </div>
                            <div>
                                <Index each={internalKeyValuePairs()}>
                                    {(row) => (
                                        <div class="border-t border-gray-200 flex items-center">
                                            <div class="py-2 px-3 flex-[2]">
                                                <SimpleSearchBar
                                                    value={row().key}
                                                    showIcon={false}
                                                    onInput={(e: InputEvt) =>
                                                        updateKeyValuePair(row().id, {
                                                            key: e.currentTarget.value,
                                                        })
                                                    }
                                                    placeholder="ex: Authorization"
                                                />
                                            </div>
                                            <div class="py-2 flex-[7]">
                                                <SimpleSearchBar
                                                    value={row().value}
                                                    showIcon={false}
                                                    onInput={(e: InputEvt) =>
                                                        updateKeyValuePair(row().id, {
                                                            value: e.currentTarget.value,
                                                        })
                                                    }
                                                    placeholder="ex: Bearer <token>"
                                                />
                                            </div>
                                            <div class="w-10 px-2 flex items-center justify-center">
                                                <button
                                                    type="button"
                                                    class="text-red-500 hover:text-red-700 p-1 cursor-pointer"
                                                    onClick={() => removeKeyValuePair(row().id)}
                                                    aria-label="Remover"
                                                    title="Remover"
                                                >
                                                    <TbTrash size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </Index>
                                <Show when={internalKeyValuePairs().length === 0}>
                                    <div class="w-full flex items-center justify-center px-2 py-3 text-gray-500 text-xs text-center">
                                        {emptyStateText()}
                                    </div>
                                </Show>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KeyValueEditor;
