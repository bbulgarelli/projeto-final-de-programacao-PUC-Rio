import { PaginationQuery, UUID } from "./common";

export interface KnowledgeBase {
    id: UUID;
    name: string;
    description?: string | null;
    created_at: string;
    updated_at: string;
    is_active: boolean;
    files: KnowledgeBaseFile[];
}

export interface KnowledgeBaseFile {
    id: UUID;
    name: string;
    enum_status: string;
    enum_type?: string | null;
    num_pages?: number | null;
    summary?: string | null;
    created_at: string;
    updated_at: string;
    is_active: boolean;
    knowledge_base_id?: UUID | null;
    knowledge_base?: Pick<KnowledgeBase, "id" | "name"> | null;
    chunks: KnowledgeBaseChunk[];
}

export interface KnowledgeBaseChunk {
    id: UUID;
    content: string;
    page: number;
    seq_num: number;
    values: number[];
    num_tokens?: number | null;
    created_at: string;
    updated_at: string;
    file_id: UUID;
    file?: Pick<KnowledgeBaseFile, "id" | "name"> | null;
}

export interface KnowledgeBaseListResponse {
    total_knowledge_bases: number;
    knowledge_bases: KnowledgeBase[];
}

export interface FileListResponse {
    total_files: number;
    files: KnowledgeBaseFile[];
}

export interface CreateKnowledgeBasePayload {
    name: string;
    description?: string | null;
}

export interface UpdateKnowledgeBasePayload extends Partial<CreateKnowledgeBasePayload> { }

export interface UpdateFilePayload {
    name?: string | null;
    enum_status?: string | null;
    enum_type?: string | null;
    num_pages?: number | null;
    summary?: string | null;
}

export interface UploadKnowledgeBaseFilePayload {
    knowledgeBaseId: UUID;
    file: File;
    enum_status?: string;
    enum_type?: string | null;
    summary?: string | null;
    num_pages?: number | null;
}

export type KnowledgeBaseListQuery = PaginationQuery;
export type KnowledgeBaseFileListQuery = PaginationQuery;

