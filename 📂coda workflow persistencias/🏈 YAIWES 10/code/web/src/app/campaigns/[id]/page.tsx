"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { api, connectWebSocket, type CampaignEvent } from "@/lib/api";

interface AgentState {
  name: string;
  status: "idle" | "active" | "complete" | "error";
  detail: string;
}

interface FindingDisplay {
  severity: string;
  title: string;
  time: string;
}

export default function CampaignLivePage() {
  const params = useParams();
  const id = params.id as string;

  const [events, setEvents] = useState<CampaignEvent[]>([]);
  const [agents, setAgents] = useState<Record<string, AgentState>>({
    orchestrator: { name: "Orchestrator", status: "active", detail: "Initializing..." },
    recon: { name: "Recon Agent", status: "idle", detail: "Waiting" },
    classifier: { name: "Classifier", status: "idle", detail: "Waiting" },
    exploit: { name: "Exploit Agent", status: "idle", detail: "Waiting" },
    report: { name: "Report Agent", status: "idle", detail: "Waiting" },
  });
  const [findings, setFindings] = useState<FindingDisplay[]>([]);
  const [severity, setSeverity] = useState({ critical: 0, high: 0, medium: 0, low: 0 });
  const [phase, setPhase] = useState("initializing");
  const [elapsed, setElapsed] = useState(0);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  // Timer
  useEffect(() => {
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection
  useEffect(() => {
    const ws = connectWebSocket(id, (event) => {
      setEvents((prev) => [...prev.slice(-200), event]);

      // Update agent status
      if (event.agent_name) {
        setAgents((prev) => ({
          ...prev,
          [event.agent_name]: {
            ...prev[event.agent_name],
            status: event.event_type === "error" ? "error" : "active",
            detail: event.detail?.slice(0, 60) || "",
          },
        }));
      }

      // Track findings
      if (event.event_type === "finding_discovered") {
        const sev = event.detail?.includes("CRITICAL") ? "critical"
          : event.detail?.includes("HIGH") ? "high"
          : event.detail?.includes("MEDIUM") ? "medium" : "low";
        setFindings((prev) => [...prev, { severity: sev, title: event.detail || "", time: new Date().toLocaleTimeString() }]);
        setSeverity((prev) => ({ ...prev, [sev]: prev[sev as keyof typeof prev] + 1 }));
      }

      // Track phase
      if (event.event_type === "state_change") {
        const d = event.detail?.toLowerCase() || "";
        if (d.includes("recon")) setPhase("recon");
        else if (d.includes("classif")) setPhase("classify");
        else if (d.includes("plan")) setPhase("plan");
        else if (d.includes("execut")) setPhase("execute");
        else if (d.includes("report")) setPhase("report");
        else if (d.includes("complete")) setPhase("complete");
      }
    });

    return () => ws.close();
  }, [id]);

  // Auto-scroll events
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const formatTime = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  return (
    <div className="h-full flex flex-col">
      {/* Phase Progress Bar */}
      <div className="bg-surface border-b border-border px-6 py-3 flex items-center gap-3">
        <span className="text-sm font-medium text-accent">Campaign {id.slice(0, 8)}</span>
        <span className="text-gray-600">|</span>
        <span className="text-sm text-gray-400">{formatTime(elapsed)}</span>
        <span className="text-gray-600">|</span>
        <div className="flex items-center gap-1">
          {["recon", "classify", "plan", "execute", "report"].map((p) => (
            <PhaseStep key={p} label={p} active={phase === p} done={phaseOrder(p) < phaseOrder(phase)} />
          ))}
        </div>
        <div className="flex-1" />
        <button className="px-3 py-1 bg-red-500/20 text-red-400 rounded text-xs border border-red-500/30 hover:bg-red-500/30">
          Stop
        </button>
      </div>

      {/* Main panels */}
      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        {/* Left: Agents */}
        <div className="col-span-3 border-r border-border overflow-y-auto p-4 space-y-2">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Agent Swarm</h3>
          {Object.entries(agents).map(([key, agent]) => (
            <AgentCard key={key} {...agent} />
          ))}
        </div>

        {/* Center: Event Log */}
        <div className="col-span-6 border-r border-border overflow-y-auto p-4">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Event Stream</h3>
          <div className="space-y-1 terminal-text text-xs">
            {events.map((e, i) => (
              <EventLine key={i} event={e} />
            ))}
            <div ref={eventsEndRef} />
          </div>
          {events.length === 0 && (
            <p className="text-gray-600 text-sm">Waiting for events...</p>
          )}
        </div>

        {/* Right: Findings */}
        <div className="col-span-3 overflow-y-auto p-4">
          <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Findings</h3>
          <div className="flex gap-3 mb-4">
            <SevCount label="C" count={severity.critical} color="bg-red-500" />
            <SevCount label="H" count={severity.high} color="bg-orange-500" />
            <SevCount label="M" count={severity.medium} color="bg-yellow-500" />
            <SevCount label="L" count={severity.low} color="bg-green-500" />
          </div>
          <div className="space-y-2">
            {findings.slice(-10).reverse().map((f, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
                  f.severity === "critical" ? "bg-red-500" :
                  f.severity === "high" ? "bg-orange-500" :
                  f.severity === "medium" ? "bg-yellow-500" : "bg-green-500"
                }`} />
                <span className="text-gray-300 truncate">{f.title}</span>
              </div>
            ))}
            {findings.length === 0 && <p className="text-xs text-gray-600">No findings yet</p>}
          </div>
        </div>
      </div>

      {/* Bottom metrics */}
      <div className="bg-surface border-t border-border px-6 py-2 flex items-center gap-8 text-xs text-gray-500">
        <span>Findings: <strong className="text-white">{findings.length}</strong></span>
        <span>Events: <strong className="text-white">{events.length}</strong></span>
        <span>Elapsed: <strong className="text-white">{formatTime(elapsed)}</strong></span>
        <span>Phase: <strong className="text-accent">{phase}</strong></span>
      </div>
    </div>
  );
}

function PhaseStep({ label, active, done }: { label: string; active?: boolean; done?: boolean }) {
  if (done) return <span className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400">{label} ✓</span>;
  if (active) return <span className="text-xs px-2 py-0.5 rounded bg-accent/20 text-accent animate-pulse">{label}</span>;
  return <span className="text-xs px-2 py-0.5 text-gray-600">{label}</span>;
}

function phaseOrder(p: string): number {
  return ["initializing", "recon", "classify", "plan", "execute", "report", "complete"].indexOf(p);
}

function AgentCard({ name, status, detail }: AgentState) {
  const borderClass = status === "active" ? "border-accent/50 agent-active" : "border-border";
  const dotColor = {
    active: "bg-accent animate-pulse",
    idle: "bg-gray-600",
    complete: "bg-green-500",
    error: "bg-red-500",
  }[status];

  return (
    <div className={`bg-background rounded-lg border ${borderClass} p-3`}>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${dotColor}`} />
        <span className="text-xs font-medium">{name}</span>
      </div>
      <p className="text-[10px] text-gray-500 mt-1 truncate terminal-text">{detail}</p>
    </div>
  );
}

function EventLine({ event }: { event: CampaignEvent }) {
  const ts = new Date(event.timestamp).toLocaleTimeString();
  const typeColors: Record<string, string> = {
    thought: "text-gray-400",
    tool_call: "text-yellow-400",
    tool_result: "text-green-400",
    finding_discovered: "text-red-400",
    state_change: "text-purple-400",
    step_executed: "text-yellow-300",
    error: "text-red-500",
    milestone: "text-green-500 font-bold",
  };

  const color = typeColors[event.event_type] || "text-gray-500";

  return (
    <div className="flex gap-2">
      <span className="text-gray-600 flex-shrink-0">{ts}</span>
      <span className={`${color} break-all`}>{event.detail}</span>
    </div>
  );
}

function SevCount({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="flex flex-col items-center">
      <div className={`w-6 h-6 rounded ${color}/20 flex items-center justify-center`}>
        <span className="text-[10px] font-bold">{count}</span>
      </div>
      <span className="text-[9px] text-gray-500 mt-1">{label}</span>
    </div>
  );
}
