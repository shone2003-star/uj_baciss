"use client";

import { useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { QueryBoundary } from "@/components/shared/query-boundary";
import { UrgencyBadge } from "@/components/shared/urgency-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ThreadFilter } from "@/features/chat/api";
import { AdminConversation } from "@/features/chat/components/admin-conversation";
import { ThreadList } from "@/features/chat/components/thread-list";
import { useThreads } from "@/features/chat/hooks";

const FILTERS: { value: ThreadFilter; label: string }[] = [
  { value: "attention", label: "Needs attention" },
  { value: "open", label: "Open" },
  { value: "closed", label: "Closed" },
  { value: "all", label: "All" },
];

/** The admin's conversations: who needs an answer, with the assistant's help. */
export const ConversationsScreen = () => {
  const [filter, setFilter] = useState<ThreadFilter>("attention");
  const threads = useThreads(filter);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = threads.data?.some((t) => t.report_id === selectedId) ? selectedId : null;

  return (
    <>
      <PageHeader
        title="Conversations"
        description="Follow up on resolved reports. Only you can close a conversation."
      />
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter conversations">
        {FILTERS.map(({ value, label }) => (
          <Button
            key={value}
            size="sm"
            variant={value === filter ? "default" : "outline"}
            onClick={() => setFilter(value)}
          >
            {label}
          </Button>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <QueryBoundary
          query={threads}
          isEmpty={(items) => items.length === 0}
          emptyMessage="No conversations here."
        >
          {(items) => (
            <ThreadList
              threads={items}
              selectedId={activeId}
              onSelect={setSelectedId}
              badges={(thread) => (
                <>
                  {thread.needs_attention && <Badge>Needs attention</Badge>}
                  <UrgencyBadge urgency={thread.urgency} />
                </>
              )}
            />
          )}
        </QueryBoundary>
        <section aria-label="Selected conversation">
          {activeId ? (
            <AdminConversation key={activeId} reportId={activeId} />
          ) : (
            <EmptyState message="Select a conversation to read it." />
          )}
        </section>
      </div>
    </>
  );
};
