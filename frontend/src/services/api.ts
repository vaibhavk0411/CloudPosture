// API service layer - centralizes all backend HTTP calls.
// Design decision: single Axios instance with a base URL from VITE_API_URL,
// so we can point at a deployed backend without code changes.

import axios from "axios";

const baseURL =
  (import.meta.env.VITE_API_URL as string | undefined) ??
  "http://localhost:8000";

export const api = axios.create({
  baseURL,
  timeout: 60_000,
  headers: { "Content-Type": "application/json" },
});

// ---------- Types (mirror the FastAPI responses) ----------

export interface SecurityGroup {
  group_id: string;
  group_name: string;
}

export interface EC2Instance {
  instance_id: string;
  instance_type: string;
  region: string;
  state: string;
  public_ip: string | null;
  private_ip: string | null;
  security_groups: SecurityGroup[];
  launch_time?: string;
  vpc_id?: string;
  subnet_id?: string;
  tags?: Record<string, string>;
}

export interface S3Bucket {
  bucket_name: string;
  region: string;
  encryption_status: string;
  access_level: string;
  versioning?: string;
  creation_date?: string;
  public_access_block?: Record<string, boolean>;
}

export type CheckStatus = "PASS" | "FAIL" | "ERROR";
export type CheckSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface CISCheck {
  check_name: string;
  status: CheckStatus;
  resource: string;
  evidence: string;
  cis_id?: string;
  severity?: CheckSeverity;
  remediation?: string;
}

export interface CISSummary {
  total_checks: number;
  passed: number;
  failed: number;
  errors: number;
  compliance_score: number;
}

export interface CISResults {
  summary: CISSummary;
  checks: CISCheck[];
}

export interface ScanRecord {
  scan_id: string;
  timestamp: string;
  scan_type?: string;
  summary: CISSummary;
  checks?: CISCheck[];
}

export interface TrendPoint {
  scan_id: string;
  timestamp: string;
  compliance_score: number;
  passed: number;
  failed: number;
  total_checks: number;
}

export interface TrendResponse {
  total_scans: number;
  scans_in_trend: number;
  average_score: number;
  latest_score: number;
  oldest_score: number;
  improvement: number;
  trend: TrendPoint[];
}

export interface SummaryResponse {
  scan_id: string;
  timestamp: string;
  scan_type?: string;
  summary: CISSummary;
}

export interface FailedChecksResponse {
  scan_id?: string;
  timestamp?: string;
  total_failed: number;
  failed_checks: CISCheck[];
  message: string;
}

// ---------- API methods ----------

export const cloudApi = {
  getInstances: () => api.get<{ instances: EC2Instance[]; total: number }>("/instances").then((r) => r.data),
  getBuckets: () => api.get<{ buckets: S3Bucket[]; total: number }>("/buckets").then((r) => r.data),
  getCisResults: () => api.get<CISResults>("/cis-results").then((r) => r.data),
  runScan: () => api.post<ScanRecord>("/scan").then((r) => r.data),
  getScans: () => api.get<{ scans: ScanRecord[]; total: number }>("/scans").then((r) => r.data),
  getScan: (id: string) => api.get<ScanRecord>(`/scan/${id}`).then((r) => r.data),
  getSummary: () => api.get<SummaryResponse>("/summary").then((r) => r.data),
  getFailedChecks: () => api.get<FailedChecksResponse>("/failed-checks").then((r) => r.data),
  getTrend: (limit = 10) => api.get<TrendResponse>(`/trend?limit=${limit}`).then((r) => r.data),
};
