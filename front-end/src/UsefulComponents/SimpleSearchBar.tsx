import type { Component, JSX } from "solid-js";

interface SimpleSearchBarProps {
    value: string;
    placeholder?: string;
    showIcon?: boolean;
    inputClassName?: string;
    class?: string;
    onInput?: JSX.EventHandlerUnion<HTMLInputElement, InputEvent>;
    onChange?: JSX.EventHandlerUnion<HTMLInputElement, Event>;
}

const SimpleSearchBar: Component<SimpleSearchBarProps> = (props) => {
    return (
        <div class={props.class}>
            <div class="flex items-center w-full">
                {props.showIcon && (
                    <span class="mr-2 text-gray-400" aria-hidden="true">
                        🔍
                    </span>
                )}
                <input
                    class={`w-full border border-gray-300 rounded-md px-3 py-2 text-sm bg-white text-gray-600 outline-none focus:ring-1 focus:ring-blue-600 ${props.inputClassName ?? ""
                        }`}
                    value={props.value}
                    placeholder={props.placeholder}
                    onInput={props.onInput}
                    onChange={props.onChange}
                />
            </div>
        </div>
    );
};

export default SimpleSearchBar;

