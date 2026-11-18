import { z } from "zod";

import { categorySchema, urgencySchema } from "@/schemas/domain";

/** The same limit as the API. */
export const MAX_MESSAGE_CHARS = 1000;

export const senderSchema = z.enum(["citizen", "admin"]);

export const messageSchema = z.object({
  id: z.number(),
  report_id: z.string(),
  sender: senderSchema,
  body: z.string(),
  created_at: z.string(),
});

export const threadSchema = z.object({
  report_id: z.string(),
  status: z.enum(["open", "closed"]),
  marked_fixed: z.boolean(), // the citizen says it is fixed; only the admin closes
  created_at: z.string(),
  updated_at: z.string(),
});

const listFields = {
  text: z.string(),
  message_count: z.number(),
  last_sender: senderSchema,
  last_message_at: z.string(),
};

/** What a citizen sees in the list: never the AI's category, urgency or department. */
export const myThreadSchema = threadSchema.extend(listFields);

/** What the admin sees in the list. */
export const threadSummarySchema = myThreadSchema.extend({
  category: categorySchema,
  urgency: urgencySchema,
  department: z.string(),
  needs_attention: z.boolean(), // the citizen spoke last or marked it fixed
});

export const threadDetailSchema = z.object({
  thread: threadSchema,
  report_text: z.string(),
  messages: z.array(messageSchema),
});

/** The assistant's suggestion. Nothing is sent until the admin sends it. */
export const suggestionSchema = z.object({
  body: z.string(),
  looks_resolved: z.boolean(),
  reason: z.string(),
});

export type Message = z.infer<typeof messageSchema>;
export type MyThread = z.infer<typeof myThreadSchema>;
export type ThreadSummary = z.infer<typeof threadSummarySchema>;
export type ThreadDetail = z.infer<typeof threadDetailSchema>;
export type Suggestion = z.infer<typeof suggestionSchema>;
