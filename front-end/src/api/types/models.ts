export interface AvailableModel {
    model_key: string;
    name: string;
    description: string;
    context_length: number;
    provider: string;
    legacy_model: boolean;
    output_tokens: number;
    temperature: number;
}

