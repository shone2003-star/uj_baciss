"use client";

import { useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { QueryBoundary } from "@/components/shared/query-boundary";
import { CitizenConversation } from "@/features/chat/components/citizen-conversation";
import { ThreadList } from "@/features/chat/components/thread-list";
import { useMyThreads } from "@/features/chat/hooks";

/** The citizen's conversations about their resolved reports. */
export const MessagesScreen = () => {
  const threads = useMyThreads();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = threads.data?.some((t) => t.report_id === selectedId) ? selectedId : null;

  return (
    <>
      <PageHeader
        title="Messages"
        description="Talk to the municipality about a report that has a reply. Tell them if it is fixed."
      />
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <QueryBoundary
          query={threads}
          isEmpty={(items) => items.length === 0}
          emptyMessage="No conversations yet. One opens when your report has a reply."
        >
          {(items) => (
            <ThreadList threads={items} selectedId={activeId} onSelect={setSelectedId} />
          )}
        </QueryBoundary>
        <section aria-label="Selected conversation">
          {activeId ? (
            <CitizenConversation key={activeId} reportId={activeId} />
          ) : (
            <EmptyState message="Select a report to read the conversation." />
          )}
        </section>
      </div>
    </>
  );
};
