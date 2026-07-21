export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'analyst';
  created_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface Incident {
  id: number;
  title: string;
  description: string;
  severity: string;
  status: string;
  source: string;
  assigned_to: string;
  created_at: string;
  updated_at: string;
}

export interface IOC {
  id: number;
  value: string;
  ioc_type: string;
  risk_score: number;
  verdict: string;
  blocked: boolean;
  source: string;
  created_at: string;
}

export interface EnrichResult {
  value: string;
  ioc_type: string;
  risk_score: number;
  verdict: string;
  recommendation: string;
  virustotal: {
    source: string;
    malicious: number;
    suspicious: number;
    harmless: number;
    undetected: number;
  };
  abuseipdb: {
    source: string;
    abuse_confidence_score: number;
    country: string;
    total_reports: number;
    mode?: string;
    fallback_reason?: string;
  } | null;
  enrichment_mode?: string;
  sources_used?: string[];
}

export interface Vulnerability {
  id: number;
  cve_id: string;
  title: string;
  severity: string;
  cvss_score: number;
  is_kev: boolean;
  affected_systems: string;
  status: string;
  discovered_at: string;
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  params: string[];
}

export interface PlaybookResult {
  playbook_id: string;
  name: string;
  description: string;
  status: string;
  result: string;
  mode?: string;
}

export interface DashboardStats {
  kpis: {
    active_alerts: number;
    blocked_ips: number;
    kev_vulnerabilities: number;
    total_incidents: number;
  };
  severity_distribution: { severity: string; count: number }[];
  hourly_events: { hour: string; events: number }[];
  audit_feed: {
    id: number;
    username: string;
    action: string;
    details: string;
    created_at: string;
  }[];
}
