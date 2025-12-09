import type { Component, JSX } from "solid-js";
import { For } from "solid-js";

export interface SimpleDropdownOption {
    value: string;
    label: string;
}

interface SimpleDropdownProps {
    value: string;
    options: SimpleDropdownOption[];
    class?: string;
    onChange?: JSX.EventHandlerUnion<HTMLSelectElement, Event>;
}

const SimpleDropdown: Component<SimpleDropdownProps> = (props) => {
    return (
        <select
            class={`w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white text-gray-600 outline-none focus:ring-1 focus:ring-blue-600 ${props.class ?? ""
                }`}
            value={props.value}
            onChange={props.onChange}
        >
            <For each={props.options}>
                {(opt) => (
                    <option value={opt.value} selected={opt.value === props.value}>
                        {opt.label}
                    </option>
                )}
            </For>
        </select>
    );
};

export default SimpleDropdown;

