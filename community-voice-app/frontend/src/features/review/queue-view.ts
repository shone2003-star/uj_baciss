import type { ReportRecord } from "@/schemas/report";

export const ALL = "all";

/** "urgent" is the order the API already sends: most urgent first, then oldest first. */
export type QueueSort = "urgent" | "newest" | "oldest";

export type QueueView = {
  sort: QueueSort;
  urgency: string;
  category: string;
  status: string;
};

export const DEFAULT_VIEW: QueueView = {
  sort: "urgent",
  urgency: ALL,
  category: ALL,
  status: ALL,
};

export const SORT_OPTIONS: { value: QueueSort; label: string }[] = [
  { value: "urgent", label: "Most urgent first" },
  { value: "newest", label: "Newest first" },
  { value: "oldest", label: "Oldest first" },
];

/** The reports that match the filters, in the chosen order (the queue is small). */
export const applyQueueView = <T extends ReportRecord>(reports: T[], view: QueueView): T[] => {
  const matches = (value: string, wanted: string) => wanted === ALL || value === wanted;
  const kept = reports.filter(
    (report) =>
      matches(report.urgency, view.urgency) &&
      matches(report.category, view.category) &&
      matches(report.status, view.status),
  );
  if (view.sort === "urgent") return kept;
  const direction = view.sort === "newest" ? -1 : 1;
  // ISO timestamps in one format sort correctly as text.
  return [...kept].sort((a, b) => direction * a.created_at.localeCompare(b.created_at));
};
