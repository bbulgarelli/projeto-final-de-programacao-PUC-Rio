import { api } from "../api";
import { AvailableModel } from "../types/models";

export async function listAvailableModels(): Promise<AvailableModel[]> {
    return api.get<AvailableModel[]>("/available-models");
}

