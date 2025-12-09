import { api } from "../api";
import {
    CreateKnowledgeBasePayload,
    FileListResponse,
    KnowledgeBase,
    KnowledgeBaseFile,
    KnowledgeBaseFileListQuery,
    KnowledgeBaseListQuery,
    KnowledgeBaseListResponse,
    UpdateFilePayload,
    UpdateKnowledgeBasePayload,
    UploadKnowledgeBaseFilePayload,
} from "../types/knowledgeBases";
import { buildQueryString } from "./utils";

export async function createKnowledgeBase(payload: CreateKnowledgeBasePayload): Promise<KnowledgeBase> {
    return api.post<KnowledgeBase>("/knowledge-bases", { data: payload });
}

export async function listKnowledgeBases(query?: KnowledgeBaseListQuery): Promise<KnowledgeBaseListResponse> {
    const qs = buildQueryString({
        page_number: query?.pageNumber,
        page_size: query?.pageSize,
    });
    return api.get<KnowledgeBaseListResponse>(`/knowledge-bases${qs}`);
}

export async function getKnowledgeBase(knowledgeBaseId: string): Promise<KnowledgeBase> {
    return api.get<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`);
}

export async function updateKnowledgeBase(
    knowledgeBaseId: string,
    payload: UpdateKnowledgeBasePayload
): Promise<KnowledgeBase> {
    return api.patch<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`, { data: payload });
}

export async function deleteKnowledgeBase(knowledgeBaseId: string): Promise<void> {
    await api.delete(`/knowledge-bases/${knowledgeBaseId}`);
}

export async function uploadKnowledgeBaseFile(
    payload: UploadKnowledgeBaseFilePayload
): Promise<KnowledgeBaseFile> {
    const { knowledgeBaseId, file, enum_status, enum_type, summary, num_pages } = payload;
    const formData = new FormData();
    formData.append("file", file);

    if (enum_status !== undefined && enum_status !== null) {
        formData.append("enum_status", enum_status);
    }
    if (enum_type !== undefined && enum_type !== null) {
        formData.append("enum_type", enum_type);
    }
    if (summary !== undefined && summary !== null) {
        formData.append("summary", summary);
    }
    if (num_pages !== undefined && num_pages !== null) {
        formData.append("num_pages", String(num_pages));
    }

    return api.post<KnowledgeBaseFile>(`/knowledge-bases/${knowledgeBaseId}/files`, {
        rawBody: formData,
    });
}

export async function listKnowledgeBaseFiles(
    knowledgeBaseId: string,
    query?: KnowledgeBaseFileListQuery
): Promise<FileListResponse> {
    const qs = buildQueryString({
        page_number: query?.pageNumber,
        page_size: query?.pageSize,
    });
    return api.get<FileListResponse>(`/knowledge-bases/${knowledgeBaseId}/files${qs}`);
}

export async function getKnowledgeBaseFile(fileId: string): Promise<KnowledgeBaseFile> {
    return api.get<KnowledgeBaseFile>(`/files/${fileId}`);
}

export async function updateKnowledgeBaseFile(
    fileId: string,
    payload: UpdateFilePayload
): Promise<KnowledgeBaseFile> {
    return api.patch<KnowledgeBaseFile>(`/files/${fileId}`, { data: payload });
}

export async function deleteKnowledgeBaseFile(fileId: string): Promise<void> {
    await api.delete(`/files/${fileId}`);
}

