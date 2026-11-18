import type { ReactNode } from "react";

import { formatDateTime, humanize } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { MyThread } from "@/features/chat/schemas";

type Props<T extends MyThread> = {
  threads: T[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Extra badges per row (the admin adds urgency and "needs attention"). */
  badges?: (thread: T) => ReactNode;
};

/** The list of conversations, for both roles. */
export const ThreadList = <T extends MyThread>({
  threads,
  selectedId,
  onSelect,
  badges,
}: Props<T>) => {
  return (
    <ul className="space-y-2" aria-label="Conversations">
      {threads.map((thread) => (
        <li key={thread.report_id}>
          <button
            type="button"
            onClick={() => onSelect(thread.report_id)}
            aria-current={thread.report_id === selectedId}
            className={cn(
              "w-full rounded-lg border bg-card p-3 text-left text-sm transition-colors hover:bg-muted",
              thread.report_id === selectedId && "border-primary bg-muted",
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{thread.report_id}</span>
              <span className="flex items-center gap-1">{badges?.(thread)}</span>
            </div>
            <p className="mt-1 line-clamp-2 text-muted-foreground">{thread.text}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {humanize(thread.status)}
              {thread.marked_fixed && thread.status === "open" && " · Marked as fixed"} ·{" "}
              {thread.message_count} messages · {formatDateTime(thread.last_message_at)}
            </p>
          </button>
        </li>
      ))}
    </ul>
  );
};
