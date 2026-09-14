"use client";

import { useEffect, useState } from "react";
import { api, type Campaign, type Finding } from "@/lib/api";

interface Stats {
  campaigns: number;
  active_campaigns: number;
  total_findings: number;
  by_severity?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
    info?: number;
  };
  by_agent?: Record<string, number>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ campaigns: 0, active_campaigns: 0, total_findings: 0 });
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  useEffect(() => {
    const refresh = () => {
      api.stats().then((s) => setStats(s as Stats)).catch(() => {});
      api.campaigns.list().then((r) => setCampaigns(r.data || [])).catch(() => {});
    };
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <p className="text-gray-500 text-sm mt-1">Swarm activity overview</p>
        </div>
        <button className="px-4 py-2 bg-accent text-black font-medium rounded-lg hover:bg-accent/90 transition-colors">
          New Scan
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard title="Total Campaigns" value={String(stats.campaigns)} />
        <KPICard title="Active Scans" value={String(stats.active_campaigns)} active={stats.active_campaigns > 0} />
        <KPICard title="Total Findings" value={String(stats.total_findings)} />
        <KPICard title="Agents" value="5" subtitle="orchestrator + 4 specialists" />
      </div>

      {/* Campaigns Table */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Campaigns</h3>
        {campaigns.length === 0 ? (
          <div className="text-center py-12 text-gray-600">
            <p className="text-lg">No campaigns yet</p>
            <p className="text-sm mt-2">
              Run{" "}
              <code className="bg-background px-2 py-1 rounded text-accent">
                pentestswarm scan target.com --scope target.com
              </code>
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-xs text-gray-500 border-b border-border">
                <th className="text-left py-2 px-3">Target</th>
                <th className="text-left py-2 px-3">Status</th>
                <th className="text-left py-2 px-3">Objective</th>
                <th className="text-left py-2 px-3">Findings</th>
                <th className="text-left py-2 px-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => (
                <tr key={c.id} className="border-b border-border/50 hover:bg-surface-hover transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/campaigns/${c.id}`}>
                  <td className="py-3 px-3 font-medium">{c.target}</td>
                  <td className="py-3 px-3">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="py-3 px-3 text-sm text-gray-400 max-w-[200px] truncate">{c.objective}</td>
                  <td className="py-3 px-3 text-sm">{(c as any).findings || 0}</td>
                  <td className="py-3 px-3 text-sm text-gray-500">{new Date(c.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <div className="bg-surface rounded-lg border border-border p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Severity Distribution</h3>
          <SeverityChart bySeverity={stats.by_severity} />
        </div>

        {/* Agent Status */}
        <div className="bg-surface rounded-lg border border-border p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Agent Swarm Status</h3>
          <div className="space-y-3">
            <AgentRow name="Orchestrator" role="Plans & coordinates" status="ready" />
            <AgentRow name="Recon Agent" role="subfinder, httpx, nuclei, naabu, katana, dnsx, gau" status="ready" />
            <AgentRow name="Classifier" role="CVE mapping, CVSS scoring, FP filtering" status="ready" />
            <AgentRow name="Exploit Agent" role="Attack chain construction & execution" status="ready" />
            <AgentRow name="Report Agent" role="PDF, HTML, Markdown, JSON reports" status="ready" />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-3 gap-4">
        <QuickAction title="Scan a Target" description="Launch the full swarm" icon=">" />
        <QuickAction title="Run Playbook" description="OWASP Top 10, API Security" icon="P" />
        <QuickAction title="CTF Mode" description="Solve HackTheBox machines" icon="F" />
      </div>
    </div>
  );
}

function KPICard({ title, value, subtitle, trend, active }: {
  title: string; value: string; subtitle?: string; trend?: string; active?: boolean;
}) {
  return (
    <div className="bg-surface rounded-lg border border-border p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide">{title}</p>
      <div className="flex items-baseline gap-2 mt-2">
        <p className="text-2xl font-bold">{value}</p>
        {trend && <span className="text-xs text-green-400">{trend}</span>}
        {active && <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />}
      </div>
      {subtitle && <p className="text-xs text-gray-600 mt-1">{subtitle}</p>}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    planned: "bg-gray-500/20 text-gray-400",
    initializing: "bg-blue-500/20 text-blue-400",
    recon: "bg-cyan-500/20 text-cyan-400",
    classifying: "bg-purple-500/20 text-purple-400",
    planning: "bg-yellow-500/20 text-yellow-400",
    executing: "bg-orange-500/20 text-orange-400",
    reporting: "bg-indigo-500/20 text-indigo-400",
    complete: "bg-green-500/20 text-green-400",
    failed: "bg-red-500/20 text-red-400",
    aborted: "bg-red-500/20 text-red-400",
  };

  return (
    <span className={`text-xs px-2 py-1 rounded-full ${styles[status] || styles.planned}`}>
      {status}
    </span>
  );
}

function SeverityChart({
  bySeverity,
}: {
  bySeverity?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
    info?: number;
  };
}) {
  const b = bySeverity ?? {};
  const data = [
    { name: "Critical", value: b.critical ?? 0, color: "#EF4444" },
    { name: "High", value: b.high ?? 0, color: "#F97316" },
    { name: "Medium", value: b.medium ?? 0, color: "#EAB308" },
    { name: "Low", value: b.low ?? 0, color: "#22C55E" },
    { name: "Info", value: b.info ?? 0, color: "#6B7280" },
  ];

  const total = data.reduce((acc, d) => acc + d.value, 0);

  return (
    <div className="flex items-center gap-6">
      {/* Donut placeholder */}
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#1A1A2E" strokeWidth="12" />
          {total === 0 && (
            <circle cx="50" cy="50" r="40" fill="none" stroke="#333" strokeWidth="12" strokeDasharray="251.2" />
          )}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold">{total}</span>
        </div>
      </div>
      {/* Legend */}
      <div className="space-y-2">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
            <span className="text-sm text-gray-400">{d.name}</span>
            <span className="text-sm font-medium ml-auto">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AgentRow({ name, role, status }: { name: string; role: string; status: string }) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 bg-background rounded-lg">
      <span className={`w-2 h-2 rounded-full ${status === "active" ? "bg-green-500 animate-pulse" : "bg-gray-600"}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{name}</p>
        <p className="text-xs text-gray-500 truncate">{role}</p>
      </div>
      <span className="text-xs text-gray-500">{status}</span>
    </div>
  );
}

function QuickAction({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="bg-surface rounded-lg border border-border p-4 hover:border-accent/50 transition-colors cursor-pointer">
      <div className="flex items-center gap-3">
        <span className="w-8 h-8 rounded-lg bg-accent/20 text-accent flex items-center justify-center text-sm font-bold">{icon}</span>
        <div>
          <p className="text-sm font-medium">{title}</p>
          <p className="text-xs text-gray-500">{description}</p>
        </div>
      </div>
    </div>
  );
}
