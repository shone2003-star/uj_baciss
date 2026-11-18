"use client";

import { useState } from "react";

import { PageHeader } from "@/components/shared/page-header";
import { QueryBoundary } from "@/components/shared/query-boundary";
import { UrgencyBadge } from "@/components/shared/urgency-badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAllReports } from "@/features/history/hooks";
import { ReportDetailsDialog } from "@/features/review/components/report-details-dialog";
import { formatDateTime, humanize } from "@/lib/format";
import type { ReportRecord } from "@/schemas/report";

const HistoryTable = ({ reports }: { reports: ReportRecord[] }) => {
  const [status, setStatus] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const statuses = [...new Set(reports.map((report) => report.status))].sort();
  const shown = status ? reports.filter((report) => report.status === status) : reports;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
        <Button size="sm" variant={status === null ? "default" : "outline"} onClick={() => setStatus(null)}>
          All
        </Button>
        {statuses.map((value) => (
          <Button
            key={value}
            size="sm"
            variant={value === status ? "default" : "outline"}
            onClick={() => setStatus(value)}
          >
            {humanize(value)}
          </Button>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">{shown.length} reports, newest first.</p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Report</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Urgency</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Department</TableHead>
            <TableHead>Text</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {shown.map((report) => (
            <TableRow
              key={report.id}
              onClick={() => setOpenId(report.id)}
              className="cursor-pointer"
            >
              <TableCell className="font-medium">
                <button
                  type="button"
                  className="underline"
                  onClick={() => setOpenId(report.id)}
                  aria-label={`Show details of ${report.id}`}
                >
                  {report.id}
                </button>
              </TableCell>
              <TableCell>{formatDateTime(report.created_at)}</TableCell>
              <TableCell>{humanize(report.status)}</TableCell>
              <TableCell>
                <UrgencyBadge urgency={report.urgency} />
              </TableCell>
              <TableCell>{humanize(report.category)}</TableCell>
              <TableCell>{report.department}</TableCell>
              <TableCell className="max-w-xs truncate" title={report.text}>
                {report.text}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <ReportDetailsDialog reportId={openId} onClose={() => setOpenId(null)} />
    </div>
  );
};

/** Every report in any status: a read-only history, including closed ones. */
export const HistoryScreen = () => {
  const reports = useAllReports();

  return (
    <>
      <PageHeader
        title="All reports"
        description="Every report in any status, including rejected ones. Read-only."
      />
      <QueryBoundary
        query={reports}
        isEmpty={(data) => data.length === 0}
        emptyMessage="No reports yet."
      >
        {(data) => <HistoryTable reports={data} />}
      </QueryBoundary>
    </>
  );
};
