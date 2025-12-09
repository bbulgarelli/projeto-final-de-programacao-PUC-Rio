import { Component, ParentProps } from "solid-js";
import { Sidebar } from "./Sidebar";

export const MainLayout: Component<ParentProps> = (props) => {
    return (
        <div class="flex h-screen w-screen bg-gray-100 overflow-hidden text-gray-900">
            <Sidebar />
            <main class="flex-1 flex flex-col h-full overflow-hidden relative">
                {props.children}
            </main>
        </div>
    );
};

