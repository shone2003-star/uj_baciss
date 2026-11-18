import type { Metadata } from "next";

import { HistoryScreen } from "@/features/history/components/history-screen";

export const metadata: Metadata = { title: "All reports" };

const ReportsPage = () => {
  return <HistoryScreen />;
};

export default ReportsPage;
