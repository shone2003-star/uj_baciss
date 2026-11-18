import { z } from "zod";

import {
  messageSchema,
  myThreadSchema,
  suggestionSchema,
  threadDetailSchema,
  threadSchema,
  threadSummarySchema,
} from "@/features/chat/schemas";
import { apiJson, jsonBody } from "@/lib/api-client";

/** The admin's list filter. "attention" means the citizen spoke last or marked it fixed. */
export type ThreadFilter = "attention" | "open" | "closed" | "all";

const QUERY: Record<ThreadFilter, string> = {
  attention: "?attention=true",
  open: "?status=open",
  closed: "?status=closed",
  all: "",
};

export const fetchThreads = (filter: ThreadFilter) =>
  apiJson(`/threads${QUERY[filter]}`, z.array(threadSummarySchema));

export const fetchMyThreads = () => apiJson("/my/threads", z.array(myThreadSchema));

export const fetchThread = (id: string) => apiJson(`/threads/${id}`, threadDetailSchema);

export type NewMessage = { body: string; allow_unfiltered?: boolean };

export const sendMessage = (id: string, message: NewMessage) =>
  apiJson(`/threads/${id}/messages`, messageSchema, jsonBody(message));

export const markFixed = (id: string) =>
  apiJson(`/threads/${id}/fixed`, threadSchema, { method: "POST" });

export const suggestReply = (id: string) =>
  apiJson(`/threads/${id}/suggest`, suggestionSchema, { method: "POST" });

export const closeThread = (id: string) =>
  apiJson(`/threads/${id}/close`, threadSchema, { method: "POST" });
