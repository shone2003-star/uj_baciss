import { EmptyState } from "@/components/shared/empty-state";
import { QueryBoundary } from "@/components/shared/query-boundary";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ReportSummary } from "@/features/review/components/report-summary";
import { useReportDetail } from "@/features/review/hooks";
import { formatDateTime, humanize } from "@/lib/format";

const DetailsBody = ({ reportId }: { reportId: string }) => {
  const detail = useReportDetail(reportId);

  return (
    <QueryBoundary query={detail}>
      {({ report, details, draft, has_photo }) => (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {humanize(report.status)} · created {formatDateTime(report.created_at)}
          </p>
          {details ? (
            <ReportSummary
              reportId={reportId}
              payload={{ text: report.text, ...details }}
              hasPhoto={has_photo}
            />
          ) : (
            <>
              <p className="text-sm whitespace-pre-wrap">{report.text}</p>
              <EmptyState message="The agents' findings are not available for this report." />
            </>
          )}
          {details && details.reviews.length > 0 && (
            <section aria-label="Review decisions" className="space-y-1 text-sm">
              <h3 className="font-medium">Review decisions</h3>
              <ul className="list-disc pl-5">
                {details.reviews.map((review) => (
                  <li key={review.created_at}>
                    {humanize(review.action)} ({formatDateTime(review.created_at)}){" "}
                    {[review.category, review.urgency, review.department]
                      .filter(Boolean)
                      .join(", ")}
                    {review.note && ` Note: ${review.note}`}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {draft && (
            <section aria-label="Reply" className="space-y-1 text-sm">
              <h3 className="font-medium">Reply</h3>
              <p className="whitespace-pre-wrap">{draft}</p>
            </section>
          )}
        </div>
      )}
    </QueryBoundary>
  );
};

/** A read-only window with everything known about a report, in any status. */
export const ReportDetailsDialog = ({
  reportId,
  onClose,
}: {
  reportId: string | null; // null: closed
  onClose: () => void;
}) => {
  return (
    <Dialog open={reportId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Report details</DialogTitle>
          <DialogDescription>Everything known about this report. Read-only.</DialogDescription>
        </DialogHeader>
        {reportId && <DetailsBody reportId={reportId} />}
      </DialogContent>
    </Dialog>
  );
};
