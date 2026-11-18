import { z } from "zod";

import { apiJson } from "@/lib/api-client";
import { reportRecordSchema } from "@/schemas/report";

export const fetchAllReports = () => apiJson("/reports", z.array(reportRecordSchema));
