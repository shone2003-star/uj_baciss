import { z } from "zod";

export const runStepSchema = z.object({
  node: z.string(),
  message: z.string(),
  hint: z.string().nullish(), // what runs next, shown while waiting
});

/** The events the API streams while a report moves through the agents. */
export const runEventSchema = z.discriminatedUnion("event", [
  z.object({
    event: z.literal("started"),
    data: z.object({ report_id: z.string() }),
  }),
  z.object({ event: z.literal("step"), data: runStepSchema }),
  z.object({ event: z.literal("paused"), data: z.object({ waiting_for: z.string() }) }),
  z.object({ event: z.literal("done"), data: z.object({ status: z.string() }) }),
  z.object({
    event: z.literal("error"),
    // code "privacy_unavailable": the local privacy filter is down; ask for consent.
    data: z.object({ message: z.string(), code: z.string().nullish() }),
  }),
]);

export type RunStep = z.infer<typeof runStepSchema>;
