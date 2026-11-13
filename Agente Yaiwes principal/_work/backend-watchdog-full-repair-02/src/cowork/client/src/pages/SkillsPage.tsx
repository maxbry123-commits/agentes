import { useState, useEffect } from "react";
import YAML from "yaml";
import { api } from "../utils/api";
import "./PageStyles.css";

interface Skill {
  id?: string;
  name: string;
  description: string;
  source: string;
  script: string;
  enabled?: boolean;
  installedAt?: string;
  reviewStatus?: "pending" | "approved" | "rejected";
  autoMeta?: {
    kind: "create" | "update";
    basedOn?: string[];
    generatedAt?: string;
    model?: string;
    proposedPath?: string;
    rationale?: string;
  };
}

export default function SkillsPage() {
  const [installed, setInstalled] = useState<Skill[]>([]);
  const [catalog, setCatalog] = useState<Skill[]>([]);
  const [tab, setTab] = useState<"installed" | "auto" | "catalog" | "clawhub" | "custom">("installed");
  const [diffOpen, setDiffOpen] = useState<string | null>(null);
  const [diffData, setDiffData] = useState<{ current: string; proposed: string } | null>(null);
  const [autoBusy, setAutoBusy] = useState<string | null>(null);
  const [runNowBusy, setRunNowBusy] = useState(false);
  const [customForm, setCustomForm] = useState({ name: "", description: "", script: "" });
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPreview, setUploadPreview] = useState<{ name: string; description: string; body: string } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [clawhubQuery, setClawhubQuery] = useState("");
  const [clawhubResults, setClawhubResults] = useState("");
  const [clawhubLoading, setClawhubLoading] = useState(false);
  const [clawhubInstalling, setClawhubInstalling] = useState<string | null>(null);
  const [detailSlug, setDetailSlug] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<{ content: string; meta: any; installed: boolean } | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [viewSkillId, setViewSkillId] = useState<string | null>(null);
  const [viewSkillData, setViewSkillData] = useState<{ content: string; supportingFiles: string[]; source: string; skillDir: string } | null>(null);
  const [viewSkillLoading, setViewSkillLoading] = useState(false);
  const [viewRaw, setViewRaw] = useState(false);

  useEffect(() => {
    api.getSkills().then(setInstalled);
    api.getSkillCatalog().then(setCatalog);
  }, []);

  const searchClawhub = async () => {
    if (!clawhubQuery.trim()) return;
    setClawhubLoading(true);
    setClawhubResults("");
    try {
      const res = await api.clawhubSearch(clawhubQuery.trim(), 20);
      setClawhubResults(res.output || res.error || "No results");
    } catch (err: any) {
      setClawhubResults("Error: " + (err.message || "Search failed"));
    }
    setClawhubLoading(false);
  };

  const installFromClawhub = async (slug: string) => {
    setClawhubInstalling(slug);
    try {
      const res = await api.clawhubInstall(slug);
      if (res.ok && res.installed) {
        setClawhubResults((prev) => prev + `\n\nInstalled "${slug}" successfully!`);
        api.getSkills().then(setInstalled);
      } else if (res.ok && !res.installed) {
        setClawhubResults((prev) => prev + `\n\nFailed to install "${slug}": skill files were not created. ${res.output || ""}`);
      } else {
        setClawhubResults((prev) => prev + `\n\nFailed to install "${slug}": ${res.error || res.output}`);
      }
    } catch (err: any) {
      setClawhubResults((prev) => prev + `\n\nInstall error: ${err.message}`);
    }
    setClawhubInstalling(null);
  };

  const toggleSkillView = async (id: string) => {
    if (viewSkillId === id) {
      setViewSkillId(null);
      setViewSkillData(null);
      setViewRaw(false);
      return;
    }
    setViewSkillId(id);
    setViewSkillLoading(true);
    setViewSkillData(null);
    setViewRaw(false);
    try {
      const res = await api.getSkillContent(id);
      if (res?.ok) {
        setViewSkillData({
          content: res.content || "",
          supportingFiles: res.supportingFiles || [],
          source: res.source || "",
          skillDir: res.skillDir || "",
        });
      } else {
        setViewSkillData({
          content: `_Could not load skill: ${res?.error || "unknown error"}_`,
          supportingFiles: [],
          source: "",
          skillDir: "",
        });
      }
    } catch (err: any) {
      setViewSkillData({
        content: `_Error loading skill: ${err.message || "unknown"}_`,
        supportingFiles: [],
        source: "",
        skillDir: "",
      });
    }
    setViewSkillLoading(false);
  };

  const viewDetail = async (slug: string) => {
    if (detailSlug === slug) {
      setDetailSlug(null);
      setDetailData(null);
      return;
    }
    setDetailSlug(slug);
    setDetailLoading(true);
    setDetailData(null);
    try {
      const res = await api.clawhubInfo(slug);
      if (res.ok) {
        setDetailData({
          content: res.output || "No details available",
          meta: res.meta || {},
          installed: res.installed || false,
        });
      } else {
        setDetailData({ content: res.error || "Could not load details", meta: {}, installed: false });
      }
    } catch (err: any) {
      setDetailData({ content: "Error loading details: " + err.message, meta: {}, installed: false });
    }
    setDetailLoading(false);
  };

  /** Parse SKILL.md frontmatter (---\nkey: value\n---) */
  const parseFrontmatter = (content: string) => {
    const fm: Record<string, string> = {};
    let body = content;
    const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    if (match) {
      try {
        const parsed = YAML.parse(match[1]);
        if (parsed && typeof parsed === "object") {
          for (const [k, v] of Object.entries(parsed)) {
            if (typeof v === "string") fm[k] = v.replace(/\s+/g, " ").trim();
          }
        }
      } catch {
        // fall through with empty fm
      }
      body = match[2];
    }
    return { fm, body };
  };

  /** Simple markdown-to-HTML for SKILL.md preview */
  const renderMarkdown = (text: string) => {
    return text
      // Headers
      .replace(/^### (.+)$/gm, '<h4 style="margin:12px 0 4px;font-size:14px">$1</h4>')
      .replace(/^## (.+)$/gm, '<h3 style="margin:14px 0 6px;font-size:15px;border-bottom:1px solid var(--border,#ddd);padding-bottom:4px">$1</h3>')
      .replace(/^# (.+)$/gm, '<h2 style="margin:14px 0 6px;font-size:17px">$1</h2>')
      // Code blocks
      .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre style="background:#1e1e2e;color:#cdd6f4;padding:10px 12px;border-radius:6px;overflow-x:auto;font-size:12px;margin:6px 0"><code>$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code style="background:#e8e8e8;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>')
      // Bold
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // Tables (basic)
      .replace(/^\|(.+)\|$/gm, (_, row) => {
        const cells = row.split("|").map((c: string) => c.trim());
        return '<tr>' + cells.map((c: string) => `<td style="padding:4px 8px;border:1px solid var(--border,#ddd)">${c}</td>`).join("") + '</tr>';
      })
      // List items
      .replace(/^- (.+)$/gm, '<div style="padding-left:16px;margin:2px 0">• $1</div>')
      .replace(/^\d+\. (.+)$/gm, '<div style="padding-left:16px;margin:2px 0">$1</div>')
      // Line breaks
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
  };

  const installSkill = async (skill: Skill) => {
    const result = await api.installSkill(skill);
    setInstalled((prev) => [...prev, result]);
  };

  const toggleSkill = async (skill: Skill) => {
    if (!skill.id) return;
    const updated = await api.updateSkill(skill.id, { enabled: !skill.enabled });
    setInstalled((prev) => prev.map((s) => (s.id === skill.id ? updated : s)));
  };

  const uninstallSkill = async (id: string) => {
    await api.deleteSkill(id);
    setInstalled((prev) => prev.filter((s) => s.id !== id));
  };

  const refreshInstalled = async () => {
    const fresh = await api.getSkills();
    setInstalled(fresh);
  };

  const approveAuto = async (id: string) => {
    setAutoBusy(id);
    try {
      const res = await api.approveSkill(id);
      if (!res?.ok) alert("Approve failed: " + (res?.error || "unknown"));
      await refreshInstalled();
      if (diffOpen === id) { setDiffOpen(null); setDiffData(null); }
    } catch (err: any) { alert("Approve error: " + err.message); }
    setAutoBusy(null);
  };

  const rejectAuto = async (id: string) => {
    if (!confirm("Reject this auto-generated skill? For new skills this deletes the SKILL.md folder.")) return;
    setAutoBusy(id);
    try {
      const res = await api.rejectSkill(id);
      if (!res?.ok) alert("Reject failed: " + (res?.error || "unknown"));
      await refreshInstalled();
      if (diffOpen === id) { setDiffOpen(null); setDiffData(null); }
    } catch (err: any) { alert("Reject error: " + err.message); }
    setAutoBusy(null);
  };

  const toggleDiff = async (id: string) => {
    if (diffOpen === id) { setDiffOpen(null); setDiffData(null); return; }
    setDiffOpen(id);
    setDiffData(null);
    try {
      const res = await api.getSkillProposedDiff(id);
      if (res?.ok) setDiffData({ current: res.current || "", proposed: res.proposed || "" });
      else setDiffData({ current: "", proposed: `Error: ${res?.error || "unknown"}` });
    } catch (err: any) {
      setDiffData({ current: "", proposed: `Error: ${err.message}` });
    }
  };

  const runAutoNow = async () => {
    setRunNowBusy(true);
    try {
      const res = await api.runAutoSkillNow();
      if (!res?.ok) {
        alert("Run failed: " + (res?.error || "unknown"));
      } else {
        const created = res.created ?? 0;
        const updated = res.updated ?? 0;
        const skipped = res.skipped ?? 0;
        const reasons: string[] = Array.isArray(res.reasons) ? res.reasons : [];
        const summary = `created=${created} updated=${updated} skipped=${skipped}`;
        if (created + updated === 0) {
          alert(`Run finished with no changes. ${summary}${reasons.length ? `\nReasons: ${reasons.join("; ")}` : ""}`);
        } else {
          alert(`Run done: ${summary}${reasons.length ? `\nReasons: ${reasons.join("; ")}` : ""}`);
        }
      }
      await refreshInstalled();
    } catch (err: any) {
      alert("Run error: " + err.message);
    }
    setRunNowBusy(false);
  };

  const installCustom = async () => {
    const result = await api.installSkill({ ...customForm, source: "custom" });
    setInstalled((prev) => [...prev, result]);
    setCustomForm({ name: "", description: "", script: "" });
    setTab("installed");
  };

  const handleSkillFile = (file: File) => {
    setUploadFile(file);
    const isZip = file.name.toLowerCase().endsWith(".zip");
    if (isZip) {
      // For zip files, show basic info without parsing content
      setUploadPreview({
        name: file.name.replace(/\.zip$/i, ""),
        description: `Skill folder (${(file.size / 1024).toFixed(1)} KB zip)`,
        body: `**Zip archive** containing skill folder with supporting files.\nFiles will be extracted to the skills directory upon install.`,
      });
    } else {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const { fm, body } = parseFrontmatter(content);
        setUploadPreview({
          name: fm.name || file.name.replace(/\.[^.]+$/, ""),
          description: fm.description || "",
          body,
        });
      };
      reader.readAsText(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleSkillFile(file);
  };

  const installUploadedSkill = async () => {
    if (!uploadFile) return;
    setUploading(true);
    try {
      const result = await api.uploadSkill(uploadFile);
      if (result.error) {
        alert("Upload failed: " + result.error);
      } else {
        setInstalled((prev) => {
          const exists = prev.some((s) => s.id === result.id);
          return exists ? prev.map((s) => (s.id === result.id ? result : s)) : [...prev, result];
        });
        setUploadFile(null);
        setUploadPreview(null);
        setTab("installed");
      }
    } catch (err: any) {
      alert("Upload error: " + err.message);
    }
    setUploading(false);
  };

  const getInstallButtonLabel = () => {
    if (uploading) return "Installing...";
    if (uploadFile?.name.toLowerCase().endsWith(".zip")) return "Install Skill Folder";
    return "Install Skill";
  };

  const isInstalled = (name: string) => installed.some((s) => s.name === name);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Skills</h1>
        <div className="tab-bar">
          {(["installed", "auto", "catalog", "clawhub", "custom"] as const).map((t) => {
            const autoCount = installed.filter((s) => s.source === "auto").length;
            const pendingCount = installed.filter((s) => s.source === "auto" && s.reviewStatus === "pending").length;
            const label =
              t === "installed" ? `Installed (${installed.length})`
              : t === "auto" ? `Auto-Generated${autoCount ? ` (${autoCount}${pendingCount ? ` · ${pendingCount} pending` : ""})` : ""}`
              : t === "catalog" ? "Built-in"
              : t === "clawhub" ? "Clawhub" : "Custom Skill";
            return (
              <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "installed" && (
        <div className="card-list">
          {installed.map((skill) => (
            <div key={skill.id} className="card">
              <div className="card-header">
                <div className="card-title-row">
                  <h3>{skill.name}</h3>
                  <span className={`source-badge ${skill.source}`}>{skill.source}</span>
                  {skill.source === "auto" && skill.reviewStatus === "pending" && (
                    <span className="status-badge inactive" style={{ background: "#fef7e0", color: "#ea8600", border: "1px solid #f9c97a" }}>Pending review</span>
                  )}
                  <span className={`status-badge ${skill.enabled ? "active" : "inactive"}`}>
                    {skill.enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
                <div className="card-actions">
                  <button className="btn btn-ghost btn-sm" onClick={() => toggleSkillView(skill.id!)}>
                    {viewSkillId === skill.id ? "Hide" : "View"}
                  </button>
                  <a className="btn btn-ghost btn-sm" href={api.skillDownloadUrl(skill.id!)} download title="Download SKILL.md or zip of skill folder">
                    Download
                  </a>
                  <button className="btn btn-ghost btn-sm" onClick={() => toggleSkill(skill)}>
                    {skill.enabled ? "Disable" : "Enable"}
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => uninstallSkill(skill.id!)}>Uninstall</button>
                </div>
              </div>
              <p className="card-desc">{skill.description}</p>
              {viewSkillId === skill.id && (
                <SkillViewer
                  loading={viewSkillLoading}
                  data={viewSkillData}
                  raw={viewRaw}
                  onToggleRaw={() => setViewRaw((v) => !v)}
                  parseFrontmatter={parseFrontmatter}
                  renderMarkdown={renderMarkdown}
                />
              )}
            </div>
          ))}
          {installed.length === 0 && <div className="empty-state-full"><p>No skills installed</p><p className="hint">Browse the catalog to install skills</p></div>}
        </div>
      )}

      {tab === "auto" && (
        <div className="card-list">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <p className="hint" style={{ margin: 0 }}>
              Skills authored automatically by the AI from recent successful chats. Configure in Settings → Skill Auto-Update Loop.
            </p>
            <button className="btn btn-ghost btn-sm" onClick={runAutoNow} disabled={runNowBusy}>
              {runNowBusy ? "Running..." : "Run now"}
            </button>
          </div>
          {installed.filter((s) => s.source === "auto").length === 0 && (
            <div className="empty-state-full">
              <p>No auto-generated skills yet</p>
              <p className="hint">Enable the loop in Settings, chat with the agent, then click "Run now" or wait for the next tick.</p>
            </div>
          )}
          {installed.filter((s) => s.source === "auto").map((skill) => {
            const meta = skill.autoMeta;
            const isUpdate = meta?.kind === "update";
            const hasProposedFile = !!meta?.proposedPath;
            const isPending = skill.reviewStatus === "pending";
            return (
              <div key={skill.id} className="card">
                <div className="card-header">
                  <div className="card-title-row">
                    <h3>{skill.name}</h3>
                    <span className="source-badge auto">auto</span>
                    <span className="status-badge inactive" style={{ background: meta?.kind === "update" ? "#e8f0fe" : "#e6f4ea", color: meta?.kind === "update" ? "#1967d2" : "#137333" }}>
                      {meta?.kind === "update" ? "Update" : "Create"}
                    </span>
                    {isPending && (
                      <span className="status-badge inactive" style={{ background: "#fef7e0", color: "#ea8600" }}>
                        Pending review
                      </span>
                    )}
                    {!isPending && skill.reviewStatus === "approved" && (
                      <span className="status-badge active">Approved</span>
                    )}
                  </div>
                  <div className="card-actions">
                    {(isUpdate || skill.reviewStatus === "pending") && (
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleDiff(skill.id!)}>
                        {diffOpen === skill.id ? "Hide diff" : isUpdate ? "View diff" : "View content"}
                      </button>
                    )}
                    {!isPending && (
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleSkillView(skill.id!)}>
                        {viewSkillId === skill.id ? "Hide" : "View"}
                      </button>
                    )}
                    <a className="btn btn-ghost btn-sm" href={api.skillDownloadUrl(skill.id!)} download title="Download SKILL.md or zip of skill folder">
                      Download
                    </a>
                    {isPending && (
                      <button className="btn btn-primary btn-sm" disabled={autoBusy === skill.id} onClick={() => approveAuto(skill.id!)}>
                        {autoBusy === skill.id ? "..." : "Approve"}
                      </button>
                    )}
                    <button className="btn btn-danger btn-sm" disabled={autoBusy === skill.id} onClick={() => rejectAuto(skill.id!)}>
                      {autoBusy === skill.id ? "..." : isPending ? "Reject" : "Delete"}
                    </button>
                  </div>
                </div>
                <p className="card-desc">{skill.description}</p>
                {meta?.rationale && (
                  <p className="card-desc" style={{ opacity: 0.7, fontSize: 12, marginTop: 4 }}>
                    <strong>Rationale:</strong> {meta.rationale}
                  </p>
                )}
                {meta?.basedOn && meta.basedOn.length > 0 && (
                  <p className="card-desc" style={{ opacity: 0.6, fontSize: 11, marginTop: 4 }}>
                    Based on session{meta.basedOn.length > 1 ? "s" : ""}: {meta.basedOn.map((s) => s.slice(0, 8)).join(", ")}
                  </p>
                )}
                {meta?.generatedAt && (
                  <p className="card-desc" style={{ opacity: 0.5, fontSize: 11, marginTop: 2 }}>
                    Generated {new Date(meta.generatedAt).toLocaleString()}{meta.model ? ` · ${meta.model}` : ""}
                  </p>
                )}
                {hasProposedFile && isPending && (
                  <p className="card-desc" style={{ opacity: 0.6, fontSize: 11, marginTop: 2 }}>
                    Proposed file: <code>{meta?.proposedPath}</code>
                  </p>
                )}
                {diffOpen === skill.id && (
                  <div style={{ marginTop: 10, display: "grid", gridTemplateColumns: isUpdate ? "1fr 1fr" : "1fr", gap: 12 }}>
                    {isUpdate && (
                      <div>
                        <strong style={{ fontSize: 12, opacity: 0.7 }}>Current SKILL.md</strong>
                        <pre style={{ maxHeight: 400, overflow: "auto", fontSize: 11, padding: 10, background: "var(--bg-secondary,#f8f9fa)", border: "1px solid var(--border,#ddd)", borderRadius: 6, whiteSpace: "pre-wrap" }}>
                          {diffData?.current ?? "(loading...)"}
                        </pre>
                      </div>
                    )}
                    <div>
                      <strong style={{ fontSize: 12, opacity: 0.7 }}>{isUpdate ? "Proposed update" : "Generated content"}</strong>
                      <pre style={{ maxHeight: 400, overflow: "auto", fontSize: 11, padding: 10, background: "var(--bg-secondary,#f8f9fa)", border: "1px solid var(--border,#ddd)", borderRadius: 6, whiteSpace: "pre-wrap" }}>
                        {diffData?.proposed ?? "(loading...)"}
                      </pre>
                    </div>
                  </div>
                )}
                {viewSkillId === skill.id && !isPending && (
                  <SkillViewer
                    loading={viewSkillLoading}
                    data={viewSkillData}
                    raw={viewRaw}
                    onToggleRaw={() => setViewRaw((v) => !v)}
                    parseFrontmatter={parseFrontmatter}
                    renderMarkdown={renderMarkdown}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {tab === "catalog" && (
        <div className="card-list">
          {catalog.map((skill) => (
            <div key={skill.name} className="card">
              <div className="card-header">
                <div className="card-title-row">
                  <h3>{skill.name}</h3>
                  <span className={`source-badge ${skill.source}`}>{skill.source}</span>
                </div>
                <button
                  className={`btn ${isInstalled(skill.name) ? "btn-ghost" : "btn-primary"} btn-sm`}
                  onClick={() => installSkill(skill)}
                  disabled={isInstalled(skill.name)}
                >
                  {isInstalled(skill.name) ? "Installed" : "Install"}
                </button>
              </div>
              <p className="card-desc">{skill.description}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "clawhub" && (
        <div className="card form-card">
          <h3>Clawhub Marketplace</h3>
          <p className="hint" style={{ marginBottom: 12 }}>Search and install skills from the Clawhub / OpenClaw marketplace</p>
          <div className="form-group" style={{ display: "flex", gap: 8 }}>
            <input
              value={clawhubQuery}
              onChange={(e) => setClawhubQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && searchClawhub()}
              placeholder="Search skills... (e.g. web, deploy, search)"
              style={{ flex: 1 }}
            />
            <button className="btn btn-primary" onClick={searchClawhub} disabled={clawhubLoading}>
              {clawhubLoading ? "Searching..." : "Search"}
            </button>
          </div>
          {clawhubResults && (
            <div style={{ marginTop: 12 }}>
              {(() => {
                let rank = 0;
                return clawhubResults.split("\n").filter(Boolean).map((line, i) => {
                  // Match various formats: "slug Description (1.0.0)", "slug Description", "slug"
                  const slugMatch = line.match(/^([a-z0-9][a-z0-9-]*)\s*(.*?)(?:\s+\([\d.]+\))?$/);
                  // Extract version or score if present (e.g. "(3.711)")
                  const scoreMatch = line.match(/\(([\d.]+)\)\s*$/);
                  const score = scoreMatch ? parseFloat(scoreMatch[1]) : null;

                  if (slugMatch && slugMatch[1] && !line.startsWith("-") && !line.startsWith(" ") && !line.includes("Installed") && !line.includes("error")) {
                    rank++;
                    const [, slug, title] = slugMatch;
                    const alreadyInstalled = installed.some((s) => s.name === slug);
                    const isDetailOpen = detailSlug === slug;
                    return (
                      <div key={i} style={{ marginBottom: 8 }}>
                        <div className="card" style={{
                          padding: "10px 14px",
                          display: "flex",
                          alignItems: "center",
                          gap: 10,
                          borderBottom: isDetailOpen ? "none" : undefined,
                          borderBottomLeftRadius: isDetailOpen ? 0 : undefined,
                          borderBottomRightRadius: isDetailOpen ? 0 : undefined,
                        }}>
                          <span style={{
                            minWidth: 28, height: 28, borderRadius: "50%",
                            background: rank <= 3 ? "#1967d2" : "var(--border)",
                            color: rank <= 3 ? "#fff" : "inherit",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 13, fontWeight: 700, flexShrink: 0,
                          }}>
                            #{rank}
                          </span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <strong>{slug}</strong>
                              {score !== null && (
                                <span style={{
                                  fontSize: 11, padding: "1px 6px", borderRadius: 4, fontWeight: 600,
                                  background: score >= 3.5 ? "#e6f4ea" : score >= 2.5 ? "#fef7e0" : "#fce8e6",
                                  color: score >= 3.5 ? "#137333" : score >= 2.5 ? "#ea8600" : "#c5221f",
                                }}>
                                  {score.toFixed(1)}
                                </span>
                              )}
                            </div>
                            {title && <div style={{ fontSize: 12, opacity: 0.6, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{title.replace(/\([\d.]+\)\s*$/, "").trim()}</div>}
                          </div>
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => viewDetail(slug)}
                            style={{ flexShrink: 0 }}
                          >
                            {isDetailOpen ? "Hide" : "Detail"}
                          </button>
                          <button
                            className={`btn ${alreadyInstalled ? "btn-ghost" : "btn-primary"} btn-sm`}
                            onClick={() => installFromClawhub(slug)}
                            disabled={clawhubInstalling === slug || alreadyInstalled}
                            style={{ flexShrink: 0 }}
                          >
                            {alreadyInstalled ? "Installed" : clawhubInstalling === slug ? "Installing..." : "Install"}
                          </button>
                        </div>
                        {isDetailOpen && (
                          <div className="card" style={{
                            padding: "14px 18px",
                            borderTop: "1px dashed var(--border)",
                            borderTopLeftRadius: 0,
                            borderTopRightRadius: 0,
                            fontSize: 13,
                            background: "var(--bg-secondary, #f8f9fa)",
                            maxHeight: 500,
                            overflow: "auto",
                          }}>
                            {detailLoading ? (
                              <div style={{ textAlign: "center", padding: 20, opacity: 0.6 }}>
                                Loading skill details...
                              </div>
                            ) : detailData ? (() => {
                              const { fm, body } = parseFrontmatter(detailData.content);
                              return (
                                <div>
                                  {/* Frontmatter info bar */}
                                  {Object.keys(fm).length > 0 && (
                                    <div style={{
                                      display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12,
                                      padding: "8px 12px", background: "#fff", borderRadius: 6,
                                      border: "1px solid var(--border, #ddd)",
                                    }}>
                                      {fm.name && (
                                        <span style={{ fontWeight: 700, fontSize: 14 }}>{fm.name}</span>
                                      )}
                                      {fm.description && (
                                        <span style={{ opacity: 0.7, flex: 1, minWidth: 200 }}>{fm.description}</span>
                                      )}
                                      {fm["allowed-tools"] && (
                                        <div style={{ width: "100%", marginTop: 4 }}>
                                          <span style={{ fontSize: 11, fontWeight: 600, opacity: 0.5, marginRight: 4 }}>TOOLS:</span>
                                          {fm["allowed-tools"].split(",").map((t, ti) => (
                                            <span key={ti} style={{
                                              display: "inline-block", fontSize: 11, padding: "1px 6px",
                                              background: "#e8f0fe", color: "#1967d2", borderRadius: 4,
                                              marginRight: 4, marginBottom: 2,
                                            }}>{t.trim()}</span>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                  {/* Meta info */}
                                  {detailData.meta && (detailData.meta.version || detailData.meta.ownerId) && (
                                    <div style={{ display: "flex", gap: 12, marginBottom: 10, fontSize: 12, opacity: 0.6 }}>
                                      {detailData.meta.version && <span>v{detailData.meta.version}</span>}
                                      {detailData.meta.publishedAt && (
                                        <span>Published: {new Date(detailData.meta.publishedAt).toLocaleDateString()}</span>
                                      )}
                                      {detailData.installed && (
                                        <span style={{ color: "#137333", fontWeight: 600 }}>Installed</span>
                                      )}
                                    </div>
                                  )}
                                  {/* Rendered body */}
                                  <div
                                    style={{ lineHeight: 1.6 }}
                                    dangerouslySetInnerHTML={{ __html: renderMarkdown(body) }}
                                  />
                                </div>
                              );
                            })() : null}
                          </div>
                        )}
                      </div>
                    );
                  }
                  return <div key={i} style={{ padding: "2px 0", opacity: line.startsWith("-") ? 0.5 : 1 }}>{line}</div>;
                });
              })()}
            </div>
          )}
        </div>
      )}

      {/* (custom tab below) */}
      {tab === "custom" && (
        <div className="card form-card">
          <h3>Upload Skill</h3>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => { const inp = document.createElement("input"); inp.type = "file"; inp.accept = ".md,.txt,.zip"; inp.onchange = (e) => { const f = (e.target as HTMLInputElement).files?.[0]; if (f) handleSkillFile(f); }; inp.click(); }}
            style={{
              border: `2px dashed ${dragOver ? "#1967d2" : "var(--border, #ccc)"}`,
              borderRadius: 8,
              padding: "28px 16px",
              textAlign: "center",
              cursor: "pointer",
              background: dragOver ? "rgba(25,103,210,0.05)" : "transparent",
              transition: "all 0.2s",
              marginBottom: 12,
            }}
          >
            {uploadFile ? (
              <div>
                <strong>{uploadFile.name}</strong>
                <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.6 }}>({(uploadFile.size / 1024).toFixed(1)} KB)</span>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>Drop skill file here or click to browse</div>
                <div style={{ fontSize: 12, opacity: 0.5, marginTop: 4 }}>Supports SKILL.md or .zip folder (with supporting files)</div>
              </div>
            )}
          </div>
          {uploadPreview && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                <strong>{uploadPreview.name}</strong>
                {uploadPreview.description && <span style={{ fontSize: 12, opacity: 0.6 }}>— {uploadPreview.description}</span>}
              </div>
              <div style={{
                maxHeight: 200, overflow: "auto", fontSize: 12, padding: "10px 14px",
                background: "var(--bg-secondary, #f8f9fa)", borderRadius: 6,
                border: "1px solid var(--border, #ddd)", lineHeight: 1.6,
              }}
                dangerouslySetInnerHTML={{ __html: renderMarkdown(uploadPreview.body.slice(0, 2000)) }}
              />
              <div className="form-actions" style={{ marginTop: 10 }}>
                <button className="btn btn-primary" onClick={installUploadedSkill} disabled={uploading}>
                  {getInstallButtonLabel()}
                </button>
                <button className="btn btn-ghost" onClick={() => { setUploadFile(null); setUploadPreview(null); }}>
                  Clear
                </button>
              </div>
            </div>
          )}

          <hr style={{ border: "none", borderTop: "1px solid var(--border, #ddd)", margin: "16px 0" }} />

          <h3>Create Custom Skill</h3>
          <div className="form-group">
            <label>Name</label>
            <input value={customForm.name} onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })} placeholder="My Custom Skill" />
          </div>
          <div className="form-group">
            <label>Description</label>
            <input value={customForm.description} onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })} placeholder="What this skill does" />
          </div>
          <div className="form-group">
            <label>Script / Command</label>
            <textarea value={customForm.script} onChange={(e) => setCustomForm({ ...customForm, script: e.target.value })} placeholder="python3 my_skill.py" rows={5} />
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={installCustom} disabled={!customForm.name}>Install</button>
          </div>
        </div>
      )}
    </div>
  );
}

interface SkillViewerProps {
  loading: boolean;
  data: { content: string; supportingFiles: string[]; source: string; skillDir: string } | null;
  raw: boolean;
  onToggleRaw: () => void;
  parseFrontmatter: (content: string) => { fm: Record<string, string>; body: string };
  renderMarkdown: (text: string) => string;
}

function SkillViewer({ loading, data, raw, onToggleRaw, parseFrontmatter, renderMarkdown }: SkillViewerProps) {
  if (loading) {
    return (
      <div style={{ marginTop: 10, padding: 14, background: "var(--bg-secondary, #f8f9fa)", border: "1px solid var(--border, #ddd)", borderRadius: 6, fontSize: 13, opacity: 0.6, textAlign: "center" }}>
        Loading SKILL.md...
      </div>
    );
  }
  if (!data) return null;
  const { fm, body } = parseFrontmatter(data.content);
  return (
    <div style={{ marginTop: 10, padding: 14, background: "var(--bg-secondary, #f8f9fa)", border: "1px solid var(--border, #ddd)", borderRadius: 6, fontSize: 13, maxHeight: 500, overflow: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10, gap: 8, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {data.source && (
            <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 4, background: "#e8f0fe", color: "#1967d2", fontWeight: 600 }}>
              {data.source}
            </span>
          )}
          {data.skillDir && (
            <code style={{ fontSize: 11, opacity: 0.6 }}>{data.skillDir}</code>
          )}
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onToggleRaw} title={raw ? "Show rendered" : "Show raw markdown"}>
          {raw ? "Rendered" : "Raw"}
        </button>
      </div>
      {!raw && Object.keys(fm).length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12, padding: "8px 12px", background: "#fff", borderRadius: 6, border: "1px solid var(--border, #ddd)" }}>
          {fm.name && <span style={{ fontWeight: 700, fontSize: 14 }}>{fm.name}</span>}
          {fm.description && <span style={{ opacity: 0.7, flex: 1, minWidth: 200 }}>{fm.description}</span>}
          {fm["allowed-tools"] && (
            <div style={{ width: "100%", marginTop: 4 }}>
              <span style={{ fontSize: 11, fontWeight: 600, opacity: 0.5, marginRight: 4 }}>TOOLS:</span>
              {fm["allowed-tools"].split(",").map((t, ti) => (
                <span key={ti} style={{ display: "inline-block", fontSize: 11, padding: "1px 6px", background: "#e8f0fe", color: "#1967d2", borderRadius: 4, marginRight: 4, marginBottom: 2 }}>
                  {t.trim()}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
      {raw ? (
        <pre style={{ fontSize: 11, padding: 10, background: "#fff", border: "1px solid var(--border, #ddd)", borderRadius: 6, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0 }}>
          {data.content}
        </pre>
      ) : (
        <div style={{ lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: renderMarkdown(body) }} />
      )}
      {data.supportingFiles.length > 0 && (
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: "1px solid var(--border, #ddd)" }}>
          <strong style={{ fontSize: 12, opacity: 0.7 }}>Supporting files ({data.supportingFiles.length})</strong>
          <ul style={{ margin: "6px 0 0", paddingLeft: 20, fontSize: 12, opacity: 0.8 }}>
            {data.supportingFiles.map((f) => <li key={f}><code>{f}</code></li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
