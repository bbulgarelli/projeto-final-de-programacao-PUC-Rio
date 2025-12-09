import { API_URL } from "../constants";

export type RequestOptions = Omit<RequestInit, "body" | "method">;

export interface RequestParams {
    processJson?: boolean;
}

interface GetRequestOptions extends RequestOptions, RequestParams { }

export interface RequestOptionsWithData extends RequestOptions, RequestParams {
    data?: unknown;
    rawBody?: BodyInit | null;
}

export interface ErrorBody {
    errorStatus: string;
    detail: string;
}

export class ResponseError extends Error {
    constructor(message: string, public readonly status?: number) {
        super(message);
        this.name = "ResponseError";
    }
}

class NPLabsAPI {
    /**
     * Performs a low-level fetch call.
     * This function is the base for the #request method.
     */
    private async rawRequest<T>(
        path: string,
        options: RequestInit,
        processJson: boolean = true
    ): Promise<T> {
        const url = path.startsWith("http") ? path : `${API_URL}${path}`;

        const response = await fetch(url, { ...options });

        if (response.ok) {
            if (!processJson) {
                return response as unknown as T;
            }

            if (response.status === 204) {
                return {} as T;
            }
            return await response.json();
        }

        try {
            const errorBody = (await response.json()) as ErrorBody;
            const errorMessage =
                typeof errorBody.detail === "string"
                    ? errorBody.detail
                    : JSON.stringify(errorBody.detail);
            throw new ResponseError(errorMessage, response.status);
        } catch (error) {
            if (error instanceof ResponseError) {
                throw error;
            }
            throw new ResponseError(response.statusText, response.status);
        }
    }

    /**
     * Request orchestrator. Centralizes request configuration before dispatch.
     */
    async #request<T>(
        method: "GET" | "POST" | "PATCH" | "DELETE",
        path: string,
        options: RequestOptionsWithData = { processJson: true }
    ): Promise<T> {
        const {
            data,
            rawBody = null,
            headers,
            processJson = true,
            ...restOptions
        } = options ?? {};

        const normalizedHeaders = mergeHeaders(headers);

        const body =
            rawBody !== null && rawBody !== undefined
                ? rawBody
                : data !== undefined
                    ? JSON.stringify(data)
                    : undefined;

        if (data !== undefined && rawBody == null && !normalizedHeaders["Content-Type"]) {
            normalizedHeaders["Content-Type"] = "application/json";
        }

        if (typeof FormData !== "undefined" && body instanceof FormData) {
            delete normalizedHeaders["Content-Type"];
        }

        return this.rawRequest<T>(
            path,
            {
                method,
                headers: normalizedHeaders,
                body,
                ...restOptions,
            },
            processJson
        );
    }

    public get<T>(path: string, options?: GetRequestOptions): Promise<T> {
        return this.#request<T>("GET", path, options);
    }

    public post<T>(path: string, options?: RequestOptionsWithData): Promise<T> {
        return this.#request<T>("POST", path, options);
    }

    public post_full_response(
        path: string,
        options?: Omit<RequestOptionsWithData, "processJson">
    ): Promise<Response> {
        return this.#request<Response>("POST", path, {
            ...options,
            processJson: false,
        });
    }

    public patch<T>(path: string, options?: RequestOptionsWithData): Promise<T> {
        return this.#request<T>("PATCH", path, options);
    }

    public delete<T>(path: string, options?: RequestOptionsWithData): Promise<T> {
        return this.#request<T>("DELETE", path, options);
    }
}

export const api = new NPLabsAPI();

export async function get<T>(
    path: string,
    options?: GetRequestOptions
): Promise<T> {
    return api.get(path, options);
}
export async function post<T>(
    path: string,
    options?: RequestOptionsWithData
): Promise<T> {
    return api.post(path, options);
}

export async function patch<T>(
    path: string,
    options?: RequestOptionsWithData
): Promise<T> {
    return api.patch(path, options);
}

export async function delete_<T>(
    path: string,
    options?: RequestOptionsWithData
): Promise<T> {
    return api.delete(path, options);
}

export async function post_full_response(
    path: string,
    options?: RequestOptionsWithData
): Promise<Response> {
    return api.post_full_response(path, options);
}

function mergeHeaders(headers?: HeadersInit): Record<string, string> {
    if (!headers) return {};
    if (headers instanceof Headers) {
        return Object.fromEntries(headers.entries());
    }
    if (Array.isArray(headers)) {
        return headers.reduce<Record<string, string>>((acc, [key, value]) => {
            acc[key] = value;
            return acc;
        }, {});
    }
    return { ...headers };
}
