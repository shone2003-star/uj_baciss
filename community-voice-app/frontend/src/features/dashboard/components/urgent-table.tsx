import Link from "next/link";

import { UrgencyBadge } from "@/components/shared/urgency-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { humanize } from "@/lib/format";
import type { ReportRecord } from "@/schemas/report";

export const UrgentTable = ({
  reports,
  onShowDetails,
}: {
  reports: ReportRecord[];
  onShowDetails: (reportId: string) => void;
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Urgent, still waiting</CardTitle>
        <CardDescription>Open a report in the review queue, or see its details.</CardDescription>
      </CardHeader>
      <CardContent>
        {reports.length === 0 ? (
          <p className="text-sm text-muted-foreground">None.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Report</TableHead>
                <TableHead>Urgency</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>
                  <span className="sr-only">Details</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="font-medium">
                    <Link href={`/review?report=${report.id}`} className="underline">
                      {report.id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <UrgencyBadge urgency={report.urgency} />
                  </TableCell>
                  <TableCell>{humanize(report.category)}</TableCell>
                  <TableCell>{report.department}</TableCell>
                  <TableCell>{humanize(report.status)}</TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onShowDetails(report.id)}
                      aria-label={`Show details of ${report.id}`}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
};
