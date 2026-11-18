import { useQuery } from "@tanstack/react-query";

import { fetchAllReports } from "@/features/history/api";
import { queryKeys } from "@/lib/query-keys";

export const useAllReports = () =>
  useQuery({ queryKey: queryKeys.history, queryFn: fetchAllReports, refetchInterval: 30_000 });
