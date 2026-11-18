"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { QueryBoundary } from "@/components/shared/query-boundary";
import { QueueControls } from "@/features/review/components/queue-controls";
import { QueueList } from "@/features/review/components/queue-list";
import { ReportWorkspace } from "@/features/review/components/report-workspace";
import { useReviewQueue } from "@/features/review/hooks";
import { applyQueueView, DEFAULT_VIEW } from "@/features/review/queue-view";

export const ReviewScreen = () => {
  const queue = useReviewQueue();
  const [view, setView] = useState(DEFAULT_VIEW);
  // A link such as /review?report=r-1 (from the dashboard) opens that report.
  const [selectedId, setSelectedId] = useState<string | null>(
    useSearchParams().get("report"),
  );
  const shown = queue.data ? applyQueueView(queue.data, view) : [];
  // A finished or filtered-out report is no longer selected.
  const activeId = shown.some((r) => r.id === selectedId) ? selectedId : null;

  return (
    <>
      <PageHeader
        title="Review queue"
        description="Reports and drafted replies waiting for your decision."
      />
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div className="space-y-3">
          <QueryBoundary
            query={queue}
            isEmpty={(reports) => reports.length === 0}
            emptyMessage="Nothing is waiting for review."
          >
            {(reports) => (
              <>
                <QueueControls
                  view={view}
                  statuses={[...new Set(reports.map((r) => r.status))].sort()}
                  onChange={setView}
                />
                <p className="text-sm text-muted-foreground">
                  {shown.length} of {reports.length} reports
                </p>
                {shown.length === 0 ? (
                  <EmptyState message="No reports match these filters." />
                ) : (
                  <QueueList reports={shown} selectedId={activeId} onSelect={setSelectedId} />
                )}
              </>
            )}
          </QueryBoundary>
        </div>
        <section aria-label="Selected report">
          {activeId ? (
            <ReportWorkspace key={activeId} reportId={activeId} />
          ) : (
            <EmptyState message="Select a report to review it." />
          )}
        </section>
      </div>
    </>
  );
};
