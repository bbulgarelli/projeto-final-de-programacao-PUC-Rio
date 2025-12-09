import type { Component, Setter } from "solid-js";
import { createEffect, createMemo, createSignal, For, Show, Index } from "solid-js";
import { TbTrash } from "solid-icons/tb";
import { IoAdd, IoChevronDown, IoChevronForward } from "solid-icons/io";
import {
    SimpleDropdown,
    SimpleDropdownOption,
    SimpleSearchBar,
} from "../UsefulComponents";

interface JsonSchemaEditorProps {
    jsonSchema: object | null;
    setJsonSchema: (jsonSchema: object) => void;
    type: "object" | "array" | "any";
    title: string;
    arrayAllowed: boolean;
    requireDescription: boolean;
    depthAllowed: number | null;
    allFieldsRequired: boolean;
    canAddProperties?: boolean;
    defaultDescription?: string;
    initialCollapsed?: boolean;
}

type PrimitiveType = "string" | "number" | "integer";
type AllowedType = PrimitiveType | "object" | "array";

type JsonSchemaNode =
    | { type: PrimitiveType; description?: string }
    | {
        type: "object";
        description?: string;
        properties: Record<string, JsonSchemaNode>;
        required?: string[];
    }
    | { type: "array"; description?: string; items: JsonSchemaNode };

const PRIMITIVE_TYPES: PrimitiveType[] = ["string", "number", "integer"];
const ALL_TYPES: AllowedType[] = ["object", "array", ...PRIMITIVE_TYPES];

type InputEvt = InputEvent & {
    currentTarget: HTMLInputElement;
    target: Element;
};

type SelectEvt = Event & {
    currentTarget: HTMLSelectElement;
    target: Element;
};

const isObject = (
    n: JsonSchemaNode
): n is Extract<JsonSchemaNode, { type: "object" }> => n.type === "object";
const isArray = (
    n: JsonSchemaNode
): n is Extract<JsonSchemaNode, { type: "array" }> => n.type === "array";

function cloneNode(node: JsonSchemaNode): JsonSchemaNode {
    if (isObject(node)) {
        const props: Record<string, JsonSchemaNode> = {};
        for (const k of Object.keys(node.properties))
            props[k] = cloneNode(node.properties[k]);
        return {
            type: "object",
            description: node.description,
            properties: props,
            required: node.required ? [...node.required] : undefined,
        };
    }
    if (isArray(node)) {
        return {
            type: "array",
            description: node.description,
            items: cloneNode(node.items),
        };
    }
    return { type: node.type, description: node.description };
}

function makeDefaultNode(type: AllowedType): JsonSchemaNode {
    if (type === "object")
        return { type: "object", properties: {}, required: [] };
    if (type === "array") return { type: "array", items: { type: "string" } };
    return { type, description: "" } as JsonSchemaNode;
}

function coerceRootToType(
    node: JsonSchemaNode | null,
    targetType: AllowedType
): JsonSchemaNode {
    if (!node || node.type !== targetType) return makeDefaultNode(targetType);
    return cloneNode(node);
}

function sanitizeIncomingSchema(
    schema: any,
    fallbackType: AllowedType
): JsonSchemaNode {
    if (!schema || typeof schema !== "object")
        return makeDefaultNode(fallbackType);
    const t = (schema as any).type as AllowedType | undefined;
    if (!t || !ALL_TYPES.includes(t)) return makeDefaultNode(fallbackType);

    if (t === "object") {
        const properties: Record<string, JsonSchemaNode> = {};
        const rawProps = (schema.properties ?? {}) as Record<string, any>;
        for (const key of Object.keys(rawProps)) {
            properties[key] = sanitizeIncomingSchema(rawProps[key], "string");
        }
        const required = Array.isArray(schema.required)
            ? (schema.required as string[])
            : [];
        return {
            type: "object",
            description: schema.description,
            properties,
            required,
        };
    }
    if (t === "array") {
        const items = sanitizeIncomingSchema(
            schema.items ?? { type: "string" },
            "string"
        );
        return { type: "array", description: schema.description, items };
    }
    return {
        type: t as PrimitiveType,
        description: schema.description,
    } as JsonSchemaNode;
}

function deepEqual(a: any, b: any): boolean {
    try {
        return JSON.stringify(a) === JSON.stringify(b);
    } catch {
        return false;
    }
}

function typeOptions(opts: {
    allowArray: boolean;
    allowComplex: boolean;
}): SimpleDropdownOption[] {
    const options: SimpleDropdownOption[] = [];
    if (opts.allowComplex) {
        options.push({ value: "object", label: "object" });
        if (opts.allowArray) options.push({ value: "array", label: "array" });
    }
    for (const p of PRIMITIVE_TYPES) options.push({ value: p, label: p });
    return options;
}

function enforceConstraintsOnNode(
    node: JsonSchemaNode,
    depth: number,
    rootDepth: number,
    arrayAllowed: boolean,
    depthAllowed: number | null,
    allFieldsRequired: boolean
): JsonSchemaNode {
    if (isArray(node) && !arrayAllowed && depth !== rootDepth) {
        return { type: "string", description: node.description };
    }
    if (
        (node.type === "object" || node.type === "array") &&
        depthAllowed != null &&
        depth > depthAllowed
    ) {
        return { type: "string", description: (node as any).description };
    }
    if (isObject(node)) {
        const nextProps: Record<string, JsonSchemaNode> = {};
        for (const [k, v] of Object.entries(node.properties)) {
            nextProps[k] = enforceConstraintsOnNode(
                v,
                depth + 1,
                rootDepth,
                arrayAllowed,
                depthAllowed,
                allFieldsRequired
            );
        }
        const nextReq = allFieldsRequired
            ? Object.keys(nextProps)
            : (node.required || []).filter((r) => nextProps[r] != null);
        return {
            type: "object",
            description: node.description,
            properties: nextProps,
            required: nextReq,
        };
    }
    if (isArray(node)) {
        return {
            type: "array",
            description: node.description,
            items: enforceConstraintsOnNode(
                node.items,
                depth + 1,
                rootDepth,
                arrayAllowed,
                depthAllowed,
                allFieldsRequired
            ),
        };
    }
    return node;
}

// Root controls component
interface RootControlsProps {
    node: JsonSchemaNode;
    depth: number;
    onChange: (n: JsonSchemaNode) => void;
    title: string;
    typeProp: "object" | "array" | "any";
    arrayAllowed: boolean;
    requireDescription: boolean;
    canAddComplexChild: (currentDepth: number) => boolean;
    collapsed: boolean;
    setCollapsed: Setter<boolean>;
    headerBodyId: string;
}

const RootControls: Component<RootControlsProps> = (props) => {
    const dropdownOptions = createMemo(() =>
        props.typeProp === "any"
            ? typeOptions({
                allowArray: props.arrayAllowed,
                allowComplex: props.canAddComplexChild(props.depth - 1),
            })
            : []
    );

    const onRootTypeChange = (nextType: AllowedType) => {
        const next = makeDefaultNode(nextType);
        next.description = props.node.description || "";
        props.onChange(next);
    };

    const toggleCollapsed = () => props.setCollapsed((c) => !c);

    const onHeaderKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleCollapsed();
        }
    };

    return (
        <div class="space-y-1">
            <div class="flex justify-center">
                <button
                    type="button"
                    aria-expanded={!props.collapsed}
                    aria-controls={props.headerBodyId}
                    onClick={toggleCollapsed}
                    onKeyDown={onHeaderKeyDown}
                    class="flex items-center justify-center text-blue-600 hover:text-gray-800 p-1 cursor-pointer"
                    title={props.collapsed ? "Expandir" : "Recolher"}
                >
                    <Show
                        when={props.collapsed}
                        fallback={<IoChevronDown size={18} />}
                    >
                        <IoChevronForward size={18} />
                    </Show>
                    <div class="truncate text-sm leading-5 px-3 py-2 rounded-lg flex items-center">
                        {props.title}
                    </div>
                </button>
                <div class="flex-1 min-w-0 flex items-stretch space-x-2">
                    <div class="flex-1 min-w-0">
                        <SimpleSearchBar
                            showIcon={false}
                            value={props.node.description || ""}
                            onInput={(e: InputEvt) =>
                                props.onChange({
                                    ...props.node,
                                    description: e.currentTarget.value,
                                })
                            }
                            placeholder="Descrição do Json"
                        />
                    </div>
                    <Show when={props.typeProp === "any"}>
                        <div class="w-40">
                            <SimpleDropdown
                                value={props.node.type}
                                onChange={(e: SelectEvt) =>
                                    onRootTypeChange(
                                        e.currentTarget.value as AllowedType
                                    )
                                }
                                options={dropdownOptions()}
                            />
                        </div>
                    </Show>
                </div>
            </div>
        </div>
    );
};

// Object editor component
interface ObjectEditorProps {
    node: Extract<JsonSchemaNode, { type: "object" }>;
    depth: number;
    onChange: (node: Extract<JsonSchemaNode, { type: "object" }>) => void;
    allFieldsRequired: boolean;
    requireDescription: boolean;
    arrayAllowed: boolean;
    canAddComplexChild: (currentDepth: number) => boolean;
    canAddProperties: boolean;
}

type PropertyRow = { id: string; key: string; value: JsonSchemaNode };

const ObjectEditor: Component<ObjectEditorProps> = (props) => {
    const initialRows = (): PropertyRow[] => {
        return Object.entries(props.node.properties).map(([key, value]) => ({
            id: `prop-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            key,
            value
        }));
    };

    const [rows, setRows] = createSignal<PropertyRow[]>(initialRows());

    // Sync from props to local state
    createEffect(() => {
        const currentAsObject: Record<string, JsonSchemaNode> = {};
        for (const r of rows()) {
            currentAsObject[r.key] = r.value;
        }

        // If props structure matches current local state structure, don't force update
        // This avoids resetting the component state when we are the ones who triggered the update
        if (deepEqual(currentAsObject, props.node.properties)) {
            return;
        }

        const currentByKey = new Map(rows().map(r => [r.key, r.id]));
        const nextRows: PropertyRow[] = Object.entries(props.node.properties).map(([key, value]) => ({
            id: currentByKey.get(key) || `prop-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            key,
            value
        }));

        // Check if actually different to avoid unnecessary re-renders
        // We use JSON stringify for a deep-ish comparison of the structure
        const prev = rows();
        const different = nextRows.length !== prev.length || nextRows.some((n, i) =>
            n.key !== prev[i].key || !deepEqual(n.value, prev[i].value)
        );

        if (different) {
            setRows(nextRows);
        }
    });

    const notifyChange = (newRows: PropertyRow[]) => {
        const nextProps: Record<string, JsonSchemaNode> = {};
        for (const row of newRows) {
            nextProps[row.key] = row.value;
        }

        let nextReq = props.node.required ? [...props.node.required] : [];
        if (props.allFieldsRequired) {
            nextReq = Object.keys(nextProps);
        } else {
            // Remove keys that no longer exist
            nextReq = nextReq.filter(k => nextProps[k] !== undefined);
            // If renaming happened, handleRequiredUpdate handles the add/remove in setRows logic? 
            // No, renaming logic needs to update required list too if needed.
        }

        props.onChange({
            ...props.node,
            properties: nextProps,
            required: nextReq
        });
    };

    const addProperty = () => {
        const base = "campo";
        let idx = 1;
        let key = `${base}_${idx}`;
        const currentKeys = new Set(rows().map(r => r.key));
        while (currentKeys.has(key)) {
            idx += 1;
            key = `${base}_${idx}`;
        }

        const newRow: PropertyRow = {
            id: `prop-${Date.now()}-${Math.random().toString(36).slice(2)}`,
            key,
            value: { type: "string", description: "Descrição padrão" }
        };

        const nextRows = [...rows(), newRow];
        setRows(nextRows);

        // Update parent
        // For 'required', we assume new fields aren't required unless allFieldsRequired is true
        const nextProps = { ...props.node.properties, [key]: newRow.value };
        const nextReq = props.allFieldsRequired ? Object.keys(nextProps) : props.node.required;

        props.onChange({
            ...props.node,
            properties: nextProps,
            required: nextReq
        });
    };

    const updateRowKey = (id: string, newKey: string) => {
        // Prevent empty keys or duplicates if desired, or handle validation UI
        // For now allowing it, assuming user will fix it
        const currentRows = rows();

        // Check for duplicates
        // If duplicate key exists, we still update local state but maybe show error

        const oldRow = currentRows.find(r => r.id === id);
        const oldKey = oldRow?.key;

        const nextRows = currentRows.map(r => r.id === id ? { ...r, key: newKey } : r);
        setRows(nextRows);

        // Update parent
        const nextProps: Record<string, JsonSchemaNode> = {};
        for (const row of nextRows) {
            // Last one wins if duplicate keys exist in the array temporarily
            nextProps[row.key] = row.value;
        }

        let nextReq = props.node.required ? [...props.node.required] : [];
        if (props.allFieldsRequired) {
            nextReq = Object.keys(nextProps);
        } else if (oldKey) {
            const idx = nextReq.indexOf(oldKey);
            if (idx !== -1) {
                // If we found the old key, replace it with the new key IF the new key is unique enough
                // Simpler approach: remove old, add new if it was required
                nextReq.splice(idx, 1, newKey);
            }
        }

        props.onChange({
            ...props.node,
            properties: nextProps,
            required: nextReq
        });
    };

    const updateRowValue = (id: string, newValue: JsonSchemaNode) => {
        const nextRows = rows().map(r => r.id === id ? { ...r, value: newValue } : r);
        setRows(nextRows);
        notifyChange(nextRows);
    };

    const removeRow = (id: string) => {
        const nextRows = rows().filter(r => r.id !== id);
        setRows(nextRows);
        notifyChange(nextRows);
    };

    const toggleRequired = (key: string, required: boolean) => {
        if (props.allFieldsRequired) return;
        const current = new Set(props.node.required || []);
        if (required) current.add(key);
        else current.delete(key);
        props.onChange({ ...props.node, required: Array.from(current) });
    };

    const allowComplex = () => props.canAddComplexChild(props.depth);

    return (
        <div class="space-y-2">
            <div class="border border-gray-200 rounded-md overflow-hidden bg-white">
                <div class="relative bg-gray-50 text-[11px] flex items-center px-2 py-2 pr-32 text-gray-600">
                    <div class="w-16 px-1">Obrigatório</div>
                    <div class="w-72 px-2">Propriedade</div>
                    <div class="w-40 px-2">Tipo</div>
                    <div class="flex-1 min-w-[280px] px-2">Descrição</div>
                    <div class="w-10 px-2" />
                    <Show when={props.canAddProperties}>
                        <div class="absolute right-2 inset-y-0 flex items-center">
                            <button
                                type="button"
                                onClick={addProperty}
                                class="flex items-center text-xs text-blue-600 cursor-pointer"
                            >
                                <IoAdd size={14} class="mr-1" />
                                <span>Adicionar propriedade</span>
                            </button>
                        </div>
                    </Show>
                </div>
                <Show
                    when={rows().length > 0}
                    fallback={
                        <div class="w-full flex items-center justify-center px-2 py-3 text-gray-500 text-xs text-center">
                            Nenhuma propriedade adicionada.
                        </div>
                    }
                >
                    <Index each={rows()}>
                        {(row) => {
                            const duplicate = () => rows().filter(r => r.key === row().key).length > 1;
                            const currentTypeOptions = createMemo(() => typeOptions({
                                allowArray: props.arrayAllowed,
                                allowComplex: allowComplex(),
                            }));
                            const isReq = () => (props.node.required || []).includes(row().key);

                            return (
                                <div class="px-2 py-2 border-t border-gray-200">
                                    <div class="flex items-center">
                                        <div class="w-16 flex items-center justify-center">
                                            <input
                                                type="checkbox"
                                                class="h-4 w-4 cursor-pointer"
                                                checked={props.allFieldsRequired ? true : isReq()}
                                                disabled={props.allFieldsRequired}
                                                onChange={(e) =>
                                                    toggleRequired(
                                                        row().key,
                                                        e.currentTarget.checked
                                                    )
                                                }
                                            />
                                        </div>
                                        <div class="w-72 px-2">
                                            <SimpleSearchBar
                                                showIcon={false}
                                                value={row().key}
                                                onInput={(e: InputEvt) =>
                                                    updateRowKey(
                                                        row().id,
                                                        e.currentTarget.value
                                                    )
                                                }
                                                placeholder="nome_da_propriedade"
                                                inputClassName={
                                                    duplicate() || !row().key.trim()
                                                        ? "border-red-500"
                                                        : ""
                                                }
                                            />
                                            <Show when={duplicate() || !row().key.trim()}>
                                                <div class="text-red-500 text-[11px] mt-1">
                                                    Nome inválido ou duplicado.
                                                </div>
                                            </Show>
                                        </div>
                                        <div class="w-40 px-2">
                                            <SimpleDropdown
                                                value={row().value.type}
                                                onChange={(e: SelectEvt) => {
                                                    const nextType =
                                                        e.currentTarget
                                                            .value as AllowedType;
                                                    const next =
                                                        makeDefaultNode(nextType);
                                                    next.description =
                                                        row().value.description || "";
                                                    updateRowValue(row().id, next);
                                                }}
                                                options={currentTypeOptions()}
                                            />
                                            <Show
                                                when={
                                                    !allowComplex() &&
                                                    (row().value.type === "object" ||
                                                        row().value.type === "array")
                                                }
                                            >
                                                <div class="text-red-500 text-[11px] mt-1">
                                                    Profundidade máxima atingida.
                                                </div>
                                            </Show>
                                            <Show when={!props.arrayAllowed && row().value.type === "array"}>
                                                <div class="text-red-500 text-[11px] mt-1">
                                                    Arrays não são permitidos.
                                                </div>
                                            </Show>
                                        </div>
                                        <div class="flex-1 min-w-[280px] px-2">
                                            <SimpleSearchBar
                                                showIcon={false}
                                                value={row().value.description || ""}
                                                onInput={(e: InputEvt) =>
                                                    updateRowValue(row().id, {
                                                        ...row().value,
                                                        description:
                                                            e.currentTarget.value,
                                                    })
                                                }
                                                placeholder="Descreva este campo"
                                                inputClassName={
                                                    props.requireDescription &&
                                                        !row().value.description
                                                        ? "border-red-500"
                                                        : ""
                                                }
                                            />
                                        </div>
                                        <div class="w-10 px-2 flex items-center justify-end">
                                            <Show when={props.canAddProperties}>
                                                <button
                                                    type="button"
                                                    class="text-red-500 hover:text-red-800 p-1 cursor-pointer"
                                                    onClick={() => removeRow(row().id)}
                                                    aria-label="Remover propriedade"
                                                    title="Remover"
                                                >
                                                    <TbTrash size={16} />
                                                </button>
                                            </Show>
                                        </div>
                                    </div>
                                    <Show when={isObject(row().value) || isArray(row().value)}>
                                        <div class="mt-2 pl-16 pr-2">
                                            <div class="border border-gray-200 rounded-md p-3 bg-gray-50">
                                                <Show when={isObject(row().value)}>
                                                    <ObjectEditor
                                                        node={row().value as Extract<
                                                            JsonSchemaNode,
                                                            { type: "object" }
                                                        >}
                                                        depth={props.depth + 1}
                                                        onChange={(n) =>
                                                            updateRowValue(row().id, n)
                                                        }
                                                        allFieldsRequired={
                                                            props.allFieldsRequired
                                                        }
                                                        requireDescription={
                                                            props.requireDescription
                                                        }
                                                        arrayAllowed={
                                                            props.arrayAllowed
                                                        }
                                                        canAddComplexChild={
                                                            props.canAddComplexChild
                                                        }
                                                        canAddProperties={
                                                            props.canAddProperties
                                                        }
                                                    />
                                                </Show>
                                                <Show when={isArray(row().value)}>
                                                    <ArrayEditor
                                                        node={row().value as Extract<
                                                            JsonSchemaNode,
                                                            { type: "array" }
                                                        >}
                                                        depth={props.depth + 1}
                                                        onChange={(n) =>
                                                            updateRowValue(row().id, n)
                                                        }
                                                        arrayAllowed={
                                                            props.arrayAllowed
                                                        }
                                                        requireDescription={
                                                            props.requireDescription
                                                        }
                                                        canAddComplexChild={
                                                            props.canAddComplexChild
                                                        }
                                                        canAddProperties={
                                                            props.canAddProperties
                                                        }
                                                    />
                                                </Show>
                                            </div>
                                        </div>
                                    </Show>
                                </div>
                            );
                        }}
                    </Index>
                </Show>
            </div>
        </div>
    );
};

// Array editor component
interface ArrayEditorProps {
    node: Extract<JsonSchemaNode, { type: "array" }>;
    depth: number;
    onChange: (node: Extract<JsonSchemaNode, { type: "array" }>) => void;
    arrayAllowed: boolean;
    requireDescription: boolean;
    canAddComplexChild: (currentDepth: number) => boolean;
    canAddProperties: boolean;
}

const ArrayEditor: Component<ArrayEditorProps> = (props) => {
    const allowComplex = () => props.canAddComplexChild(props.depth);

    const itemTypeOptions = createMemo(() =>
        typeOptions({
            allowArray: props.arrayAllowed,
            allowComplex: allowComplex(),
        })
    );

    const onItemTypeChange = (nextType: AllowedType) => {
        const nextItem = makeDefaultNode(nextType);
        nextItem.description = props.node.items.description || "";
        props.onChange({ ...props.node, items: nextItem });
    };

    return (
        <div class="space-y-1">
            <div class="flex flex-col md:flex-row gap-2 items-start">
                <div class="w-40">
                    <label class="block text-[11px] font-medium text-gray-500 mb-1">
                        Tipo dos itens
                    </label>
                    <SimpleDropdown
                        value={props.node.items.type}
                        onChange={(e: SelectEvt) =>
                            onItemTypeChange(
                                e.currentTarget.value as AllowedType
                            )
                        }
                        options={itemTypeOptions()}
                    />
                    <Show
                        when={
                            !allowComplex() &&
                            (props.node.items.type === "object" ||
                                props.node.items.type === "array")
                        }
                    >
                        <div class="text-red-500 text-[11px] mt-1">
                            Profundidade máxima atingida.
                        </div>
                    </Show>
                    <Show when={!props.arrayAllowed && props.node.items.type === "array"}>
                        <div class="text-red-500 text-[11px] mt-1">
                            Arrays não são permitidos.
                        </div>
                    </Show>
                </div>
                <div class="flex-1 min-w-[280px]">
                    <label class="block text-[11px] font-medium text-gray-500 mb-1">
                        Descrição dos itens{props.requireDescription ? " *" : ""}
                    </label>
                    <SimpleSearchBar
                        showIcon={false}
                        value={props.node.items.description || ""}
                        onInput={(e: InputEvt) =>
                            props.onChange({
                                ...props.node,
                                items: {
                                    ...props.node.items,
                                    description: e.currentTarget.value,
                                },
                            })
                        }
                        placeholder="Descreva os itens"
                        inputClassName={
                            props.requireDescription &&
                                !props.node.items.description
                                ? "border-red-500"
                                : ""
                        }
                    />
                </div>
            </div>

            <Show when={isObject(props.node.items)}>
                <div class="mt-2">
                    <ObjectEditor
                        node={props.node.items as Extract<
                            JsonSchemaNode,
                            { type: "object" }
                        >}
                        depth={props.depth + 1}
                        onChange={(n) => props.onChange({ ...props.node, items: n })}
                        allFieldsRequired={false}
                        requireDescription={props.requireDescription}
                        arrayAllowed={props.arrayAllowed}
                        canAddComplexChild={props.canAddComplexChild}
                        canAddProperties={props.canAddProperties}
                    />
                </div>
            </Show>
            <Show when={isArray(props.node.items)}>
                <div class="mt-2">
                    <ArrayEditor
                        node={props.node.items as Extract<
                            JsonSchemaNode,
                            { type: "array" }
                        >}
                        depth={props.depth + 1}
                        onChange={(n) => props.onChange({ ...props.node, items: n })}
                        arrayAllowed={props.arrayAllowed}
                        requireDescription={props.requireDescription}
                        canAddComplexChild={props.canAddComplexChild}
                        canAddProperties={props.canAddProperties}
                    />
                </div>
            </Show>
        </div>
    );
};

// Root editor component
interface RootEditorProps {
    node: JsonSchemaNode;
    onChange: (n: JsonSchemaNode) => void;
    title: string;
    typeProp: "object" | "array" | "any";
    arrayAllowed: boolean;
    requireDescription: boolean;
    canAddComplexChild: (currentDepth: number) => boolean;
    allFieldsRequired: boolean;
    canAddProperties: boolean;
    initialCollapsed: boolean;
}

const RootEditor: Component<RootEditorProps> = (props) => {
    const ROOT_DEPTH = 1;
    const [collapsed, setCollapsed] = createSignal<boolean>(
        !!props.initialCollapsed
    );
    const headerBodyId = createMemo(
        () => `schema-body-${Math.random().toString(36).slice(2)}`
    );
    return (
        <div class="space-y-1">
            <RootControls
                node={props.node}
                depth={ROOT_DEPTH}
                onChange={props.onChange}
                title={props.title}
                typeProp={props.typeProp}
                arrayAllowed={props.arrayAllowed}
                requireDescription={props.requireDescription}
                canAddComplexChild={props.canAddComplexChild}
                collapsed={collapsed()}
                setCollapsed={setCollapsed}
                headerBodyId={headerBodyId()}
            />
            <div
                id={headerBodyId()}
                class={`overflow-hidden transition-all duration-300 ease-in-out ${collapsed()
                    ? "max-h-0 opacity-0"
                    : "max-h-[3000px] opacity-100"
                    }`}
            >
                <div class="pt-0 pb-3">
                    <Show when={isObject(props.node)}>
                        <div class="p-0">
                            <ObjectEditor
                                node={props.node as Extract<
                                    JsonSchemaNode,
                                    { type: "object" }
                                >}
                                depth={ROOT_DEPTH}
                                onChange={(n) => props.onChange(n)}
                                allFieldsRequired={props.allFieldsRequired}
                                requireDescription={props.requireDescription}
                                arrayAllowed={props.arrayAllowed}
                                canAddComplexChild={props.canAddComplexChild}
                                canAddProperties={props.canAddProperties}
                            />
                        </div>
                    </Show>
                    <Show when={isArray(props.node)}>
                        <div class="p-0">
                            <ArrayEditor
                                node={props.node as Extract<
                                    JsonSchemaNode,
                                    { type: "array" }
                                >}
                                depth={ROOT_DEPTH}
                                onChange={(n) => props.onChange(n)}
                                arrayAllowed={props.arrayAllowed}
                                requireDescription={props.requireDescription}
                                canAddComplexChild={props.canAddComplexChild}
                                canAddProperties={props.canAddProperties}
                            />
                        </div>
                    </Show>
                </div>
            </div>
        </div>
    );
};

const JsonSchemaEditor: Component<JsonSchemaEditorProps> = (props) => {
    const ROOT_DEPTH = 1;

    const initialRootType = createMemo<AllowedType>(() =>
        props.type === "any" ? "object" : props.type
    );

    const defaultDescription = () => props.defaultDescription ?? "Descrição";

    const buildInitialSchema = () => {
        const sanitized = sanitizeIncomingSchema(
            props.jsonSchema,
            initialRootType()
        );
        const coerced = coerceRootToType(sanitized, initialRootType());
        if (!coerced.description && defaultDescription()) {
            coerced.description = defaultDescription();
        }
        return coerced;
    };

    const [schema, setSchema] =
        createSignal<JsonSchemaNode>(buildInitialSchema());

    const canAddComplexChild = (currentDepth: number) => {
        if (props.depthAllowed == null) return true;
        return currentDepth + 1 <= Math.max(1, props.depthAllowed);
    };

    // Sync from parent prop to local state if meaningfully different
    createEffect(() => {
        const sanitized = sanitizeIncomingSchema(
            props.jsonSchema,
            initialRootType()
        );
        const enforcedType =
            props.type === "any" ? sanitized.type : (props.type as AllowedType);
        const coerced = coerceRootToType(sanitized, enforcedType);
        if (!coerced.description && defaultDescription()) {
            coerced.description = defaultDescription();
        }
        if (!deepEqual(coerced, schema())) {
            setSchema(coerced);
        }
    });

    // Re-enforce constraints when flags change
    createEffect(() => {
        const next = enforceConstraintsOnNode(
            schema(),
            ROOT_DEPTH,
            ROOT_DEPTH,
            props.arrayAllowed,
            props.depthAllowed,
            props.allFieldsRequired
        );
        if (!deepEqual(next, schema())) setSchema(next);
    });

    const onRootChange = (next: JsonSchemaNode) => {
        const enforced = enforceConstraintsOnNode(
            next,
            ROOT_DEPTH,
            ROOT_DEPTH,
            props.arrayAllowed,
            props.depthAllowed,
            props.allFieldsRequired
        );
        if (!deepEqual(enforced, schema())) {
            setSchema(enforced);
            if (!deepEqual(props.jsonSchema, enforced)) {
                props.setJsonSchema(enforced as unknown as object);
            }
        }
    };

    const constrainedRoot = createMemo<JsonSchemaNode>(() => {
        if (props.type === "any") return schema();
        return coerceRootToType(schema(), props.type);
    });

    return (
        <RootEditor
            node={constrainedRoot()}
            onChange={onRootChange}
            title={props.title}
            typeProp={props.type}
            arrayAllowed={props.arrayAllowed}
            requireDescription={props.requireDescription}
            canAddComplexChild={canAddComplexChild}
            allFieldsRequired={props.allFieldsRequired}
            canAddProperties={props.canAddProperties ?? true}
            initialCollapsed={props.initialCollapsed ?? false}
        />
    );
};

export default JsonSchemaEditor;
