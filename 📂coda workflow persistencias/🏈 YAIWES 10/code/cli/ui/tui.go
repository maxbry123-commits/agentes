package ui

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Styles — hero palette (see banner.go) so the live campaign TUI matches the
// README demo GIF: amber pheromone accent, agent purple, execute-green, cyan.
var (
	titleStyle = lipgloss.NewStyle().Bold(true).Foreground(hAmber).Padding(0, 1)

	dimStyle = lipgloss.NewStyle().Foreground(hFaint)

	findingCritical = lipgloss.NewStyle().Foreground(hRed).Bold(true)
	findingHigh     = lipgloss.NewStyle().Foreground(lipgloss.Color("#F97316")).Bold(true)
	findingMedium   = lipgloss.NewStyle().Foreground(hAmber)
	findingLow      = lipgloss.NewStyle().Foreground(hGreen)

	phaseActive  = lipgloss.NewStyle().Background(hAmber).Foreground(hVoid).Padding(0, 1)
	phaseDone    = lipgloss.NewStyle().Background(hGreen).Foreground(hVoid).Padding(0, 1)
	phasePending = lipgloss.NewStyle().Foreground(hFaint).Padding(0, 1)

	footerStyle = lipgloss.NewStyle().Foreground(hFaint).Padding(0, 1)
)

// EventMsg delivers a campaign event to the TUI.
type EventMsg pipeline.CampaignEvent

// TickMsg triggers periodic UI updates.
type TickMsg time.Time

// Model is the bubbletea model for the campaign watch TUI.
type Model struct {
	// Campaign info
	campaignID string
	target     string
	objective  string
	startTime  time.Time

	// Agent status
	agents map[string]AgentStatus

	// Events log
	events   []pipeline.CampaignEvent
	viewport viewport.Model

	// Findings
	findings    []FindingDisplay
	severityMap map[pipeline.Severity]int

	// Phase tracking
	currentPhase string
	phases       []PhaseInfo

	// activity is the latest meaningful action, shown as a prominent
	// "NOW ▸ …" line so the operator always knows what the swarm is doing.
	activity string
	// tallies for the live counters row
	endpoints int
	chains    int
	// probes counts adaptive BOLA probe work-units (the exploit fan-out).
	// recentProbes decays each tick so the constellation fan reflects the
	// *current* burst of activity, not the lifetime total.
	probes       int
	recentProbes int

	// spend is the cumulative LLM cost in USD, parsed from the "cost" milestone
	// ("spent $X.XXX so far …"). BudgetUSD, when > 0, is the run's hard spend cap
	// (exported so the launcher can wire --budget through); the spend meter fills
	// toward it, else it grows against a soft rolling ceiling.
	spend     float64
	BudgetUSD float64

	// Live time-series, sampled once per TickMsg and capped to seriesCap so the
	// sparklines scroll rather than grow unbounded. These drive the animated
	// telemetry panels — findings/surface/probe-throughput — so the wait shows
	// visible motion long before the first finding lands.
	findingsSeries []int
	surfaceSeries  []int
	probeSeries    []int
	lastProbeCount int

	// agentPulse is a per-agent recent-activity level (keyed like agents), bumped
	// on each event touching that agent and decayed every tick, so the swarm
	// cluster and activity bars pulse with the *current* burst of work.
	agentPulse map[string]int

	// frame increments every TickMsg and drives all glyph/edge animation so the
	// blackboard, mesh and pheromone trails cycle even between events.
	frame int

	// UI
	spinner spinner.Model
	width   int
	height  int
	// DashboardURL, when set, is the live web dashboard running in parallel;
	// shown in the footer so the user knows the browser view is available.
	DashboardURL string
	quitting     bool
	done         bool
	doneErr      error
}

// DoneMsg tells the TUI the campaign finished (the swarm run returned). The
// view switches to a "complete — press q" state; err is non-nil if the run
// failed.
type DoneMsg struct{ Err error }

// AgentStatus tracks an agent's display state.
type AgentStatus struct {
	Name   string
	Status string // idle, active, complete, error
	Detail string
}

// FindingDisplay is a finding formatted for display.
type FindingDisplay struct {
	Severity pipeline.Severity
	Title    string
	Target   string
}

// PhaseInfo tracks phase progress.
type PhaseInfo struct {
	Name   string
	Status string // pending, active, done
}

// NewModel creates the TUI model.
func NewModel(campaignID, target, objective string) Model {
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(hAmber)

	vp := viewport.New(80, 20)

	return Model{
		campaignID: campaignID,
		target:     target,
		objective:  objective,
		startTime:  time.Now(),
		agents: map[string]AgentStatus{
			"orchestrator": {Name: "Orchestrator", Status: "active", Detail: "Initializing..."},
			"recon":        {Name: "Recon Agent", Status: "idle", Detail: "Waiting"},
			"classifier":   {Name: "Classifier", Status: "idle", Detail: "Waiting"},
			"exploit":      {Name: "Exploit Agent", Status: "idle", Detail: "Waiting"},
			"report":       {Name: "Report Agent", Status: "idle", Detail: "Waiting"},
		},
		severityMap: make(map[pipeline.Severity]int),
		agentPulse:  make(map[string]int),
		phases: []PhaseInfo{
			{Name: "Recon", Status: "pending"},
			{Name: "Classify", Status: "pending"},
			{Name: "Plan", Status: "pending"},
			{Name: "Execute", Status: "pending"},
			{Name: "Report", Status: "pending"},
		},
		currentPhase: "initializing",
		spinner:      s,
		viewport:     vp,
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick,
		tickCmd(),
	)
}

func tickCmd() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return TickMsg(t)
	})
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			m.quitting = true
			return m, tea.Quit
		case "s":
			// Emergency stop
			m.quitting = true
			return m, tea.Quit
		}

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.viewport.Width = msg.Width - 4
		m.viewport.Height = msg.Height - 20

	case EventMsg:
		event := pipeline.CampaignEvent(msg)
		m.events = append(m.events, event)
		m.handleEvent(event)
		m.updateViewport()

	case DoneMsg:
		m.done = true
		m.doneErr = msg.Err
		for id, a := range m.agents {
			if a.Status == "active" {
				a.Status = "complete"
				m.agents[id] = a
			}
		}
		for i := range m.phases {
			m.phases[i].Status = "done"
		}

	case TickMsg:
		// Decay the recent-probe window so the exploit fan reflects the current
		// burst rather than the lifetime total.
		if m.recentProbes > 0 {
			m.recentProbes = m.recentProbes * 2 / 3
		}
		// Advance the animation clock and sample the live time-series so every
		// telemetry panel scrolls and moves each second.
		m.frame++
		m.sampleSeries()
		// Decay per-agent activity so the swarm pulses reflect current work.
		for id, v := range m.agentPulse {
			if v > 0 {
				m.agentPulse[id] = v * 2 / 3
			}
		}
		cmds = append(cmds, tickCmd())

	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

func (m *Model) handleEvent(event pipeline.CampaignEvent) {
	// Update agent status based on event
	switch event.EventType {
	case pipeline.EventStateChange:
		if strings.Contains(event.Detail, "recon") {
			m.setPhase("Recon")
			m.agents["recon"] = AgentStatus{Name: "Recon Agent", Status: "active", Detail: "Scanning..."}
		} else if strings.Contains(event.Detail, "classif") {
			m.setPhase("Classify")
			m.agents["recon"] = AgentStatus{Name: "Recon Agent", Status: "complete", Detail: "Done"}
			m.agents["classifier"] = AgentStatus{Name: "Classifier", Status: "active", Detail: "Classifying..."}
		} else if strings.Contains(event.Detail, "plan") {
			m.setPhase("Plan")
			m.agents["classifier"] = AgentStatus{Name: "Classifier", Status: "complete", Detail: "Done"}
			m.agents["exploit"] = AgentStatus{Name: "Exploit Agent", Status: "active", Detail: "Building chains..."}
		} else if strings.Contains(event.Detail, "execut") {
			m.setPhase("Execute")
		} else if strings.Contains(event.Detail, "report") {
			m.setPhase("Report")
			m.agents["exploit"] = AgentStatus{Name: "Exploit Agent", Status: "complete", Detail: "Done"}
			m.agents["report"] = AgentStatus{Name: "Report Agent", Status: "active", Detail: "Writing report..."}
		} else if strings.Contains(event.Detail, "complete") {
			m.agents["report"] = AgentStatus{Name: "Report Agent", Status: "complete", Detail: "Done"}
		}

	case pipeline.EventFindingDiscovered:
		// Prefer the structured finding payload the swarm streams
		// ({"severity","title",...}); fall back to text if it's absent.
		title := event.Detail
		var sev pipeline.Severity = pipeline.SeverityMedium
		if len(event.Data) > 0 {
			var d struct {
				Severity string `json:"severity"`
				Title    string `json:"title"`
			}
			if json.Unmarshal(event.Data, &d) == nil {
				if d.Title != "" {
					title = d.Title
				}
				if d.Severity != "" {
					sev = pipeline.Severity(strings.ToLower(d.Severity))
				}
			}
		} else {
			switch {
			case strings.Contains(event.Detail, "CRITICAL"):
				sev = pipeline.SeverityCritical
			case strings.Contains(event.Detail, "HIGH"):
				sev = pipeline.SeverityHigh
			case strings.Contains(event.Detail, "LOW"):
				sev = pipeline.SeverityLow
			}
		}
		m.severityMap[sev]++
		m.findings = append(m.findings, FindingDisplay{Severity: sev, Title: title})
		m.bumpAgent("exploit")

	case pipeline.EventMilestone:
		// The scheduler streams cumulative spend as a "cost" milestone
		// ("spent $X.XXX so far …"); parse the dollar figure into the live meter.
		if event.AgentName == "cost" {
			if v, ok := parseSpend(event.Detail); ok {
				m.spend = v
			}
		}

	case pipeline.EventToolResult:
		m.bumpAgent(event.AgentName)
		if a, ok := m.agents[event.AgentName]; ok {
			a.Status = "active"
			a.Detail = truncateStr(event.Detail, 50)
			m.agents[event.AgentName] = a
		}

	case pipeline.EventError:
		if a, ok := m.agents[event.AgentName]; ok {
			a.Status = "error"
			a.Detail = truncateStr(event.Detail, 50)
			m.agents[event.AgentName] = a
		}

	case pipeline.EventThought:
		if event.AgentName != "" {
			m.bumpAgent(event.AgentName)
			if a, ok := m.agents[event.AgentName]; ok {
				a.Detail = truncateStr(event.Detail, 50)
				m.agents[event.AgentName] = a
			}
		}

	case pipeline.EventToolCall:
		if event.AgentName != "" {
			m.bumpAgent(event.AgentName)
			if a, ok := m.agents[event.AgentName]; ok {
				a.Status = "active"
				a.Detail = truncateStr(event.Detail, 50)
				m.agents[event.AgentName] = a
			}
		}

	case pipeline.EventEndpointDiscovered:
		m.endpoints++
		m.bumpAgent("recon")

	case pipeline.EventChainStarted:
		m.chains++
		m.bumpAgent("exploit")

	case pipeline.EventProbe:
		// Each probe is one concurrent BOLA work-unit fired by the exploit
		// phase — tally it and keep the exploit agent lit so the fan-out reads
		// as live activity on the EXPLOIT node.
		m.probes++
		m.recentProbes++
		m.bumpAgent("exploit")
		if a, ok := m.agents["exploit"]; ok {
			a.Status = "active"
			a.Detail = truncateStr("probing "+event.Detail, 50)
			m.agents["exploit"] = a
		}
	}

	// Keep a running "what's happening now" line from the most informative
	// events, so the progress area always shows the live action.
	switch event.EventType {
	case pipeline.EventToolCall, pipeline.EventToolResult, pipeline.EventStateChange,
		pipeline.EventChainStarted, pipeline.EventChainStep, pipeline.EventFindingDiscovered:
		if d := strings.TrimSpace(event.Detail); d != "" {
			m.activity = d
		}
	}
}

// seriesCap bounds each time-series so it scrolls instead of growing forever;
// sparklines only ever show the most recent render-width samples anyway.
const seriesCap = 240

// sampleSeries records one sample of each live metric. Cumulative counters
// (findings, surface) climb; probe throughput is the per-tick delta so the
// exploit fan-out reads as bursts. Called once per TickMsg.
func (m *Model) sampleSeries() {
	m.findingsSeries = appendCapped(m.findingsSeries, len(m.findings))
	m.surfaceSeries = appendCapped(m.surfaceSeries, m.endpoints)
	m.probeSeries = appendCapped(m.probeSeries, m.probes-m.lastProbeCount)
	m.lastProbeCount = m.probes
}

func appendCapped(s []int, v int) []int {
	s = append(s, v)
	if len(s) > seriesCap {
		s = s[len(s)-seriesCap:]
	}
	return s
}

// bumpAgent raises an agent's recent-activity pulse (clamped) so the swarm
// cluster and activity bars react immediately to its events.
func (m *Model) bumpAgent(id string) {
	if id == "" {
		return
	}
	if _, ok := m.agents[id]; !ok {
		return
	}
	m.agentPulse[id] += 2
	if m.agentPulse[id] > 12 {
		m.agentPulse[id] = 12
	}
}

// riskScore derives a composite 0..100 risk score: a floor set by the worst
// severity seen, plus a small volume bonus. Returns the score, its band label
// and band color for the RiskMeter gauge.
func (m Model) riskScore() (int, string, lipgloss.Color) {
	c := m.severityMap[pipeline.SeverityCritical]
	h := m.severityMap[pipeline.SeverityHigh]
	med := m.severityMap[pipeline.SeverityMedium]
	l := m.severityMap[pipeline.SeverityLow]
	base, band, col := 0, "NONE", hFaint
	switch {
	case c > 0:
		base, band, col = 85, "CRITICAL", hRed
	case h > 0:
		base, band, col = 65, "HIGH", lipgloss.Color("#F97316")
	case med > 0:
		base, band, col = 42, "MEDIUM", hAmber
	case l > 0:
		base, band, col = 18, "LOW", hGreen
	}
	if base == 0 {
		return 0, band, col
	}
	bonus := (c + h + med + l) * 3
	if bonus > 15 {
		bonus = 15
	}
	score := base + bonus
	if score > 100 {
		score = 100
	}
	return score, band, col
}

func (m *Model) setPhase(name string) {
	for i := range m.phases {
		if m.phases[i].Name == name {
			m.phases[i].Status = "active"
			m.currentPhase = name
		} else if m.phases[i].Status == "active" {
			m.phases[i].Status = "done"
		}
	}
}

func (m *Model) updateViewport() {
	var lines []string
	for _, e := range m.events {
		ts := e.Timestamp.Format("15:04:05")
		prefix := dimStyle.Render(ts)

		switch e.EventType {
		case pipeline.EventThought:
			lines = append(lines, fmt.Sprintf("%s [think] %s", prefix, e.Detail))
		case pipeline.EventToolCall:
			lines = append(lines, fmt.Sprintf("%s   [>>]  %s", prefix, e.Detail))
		case pipeline.EventToolResult:
			lines = append(lines, fmt.Sprintf("%s   [<<]  %s", prefix, e.Detail))
		case pipeline.EventFindingDiscovered:
			lines = append(lines, fmt.Sprintf("%s    [!]  %s", prefix, e.Detail))
		case pipeline.EventError:
			lines = append(lines, fmt.Sprintf("%s  [ERR]  %s", prefix, e.Detail))
		case pipeline.EventMilestone:
			lines = append(lines, fmt.Sprintf("%s [DONE]  %s", prefix, e.Detail))
		default:
			lines = append(lines, fmt.Sprintf("%s   [%s] %s", prefix, e.EventType, e.Detail))
		}
	}
	m.viewport.SetContent(strings.Join(lines, "\n"))
	m.viewport.GotoBottom()
}

func (m Model) View() string {
	if m.quitting {
		return ""
	}

	var b strings.Builder

	// Header — SWARM wordmark + campaign meta
	elapsed := time.Since(m.startTime).Round(time.Second)
	b.WriteString(SwarmWordmark(1) + "\n")
	b.WriteString(" " + stAmber.Render("PENTEST SWARM AI") + "   " +
		stInk.Render(m.target) + "   " + stMuted.Render(truncateStr(m.objective, 40)) +
		"   " + stFaint.Render(elapsed.String()) + "\n\n")

	// Phase progress bar + pips
	done := 0
	for _, p := range m.phases {
		if p.Status == "done" {
			done++
		}
	}
	b.WriteString(" " + stMuted.Render("progress ") + ProgressBar(done, len(m.phases), 26) +
		stMuted.Render(fmt.Sprintf("  %d/%d phases", done, len(m.phases))) + "\n")
	var phases []string
	for _, p := range m.phases {
		switch p.Status {
		case "done":
			phases = append(phases, phaseDone.Render(p.Name+" ✓"))
		case "active":
			phases = append(phases, phaseActive.Render(m.spinner.View()+" "+p.Name))
		default:
			phases = append(phases, phasePending.Render(p.Name))
		}
	}
	b.WriteString(" " + strings.Join(phases, stFaint.Render(" → ")) + "\n")

	// Live "what's happening now" line + counters — so progress is legible
	// at a glance without reading the event log.
	now := m.activity
	if now == "" {
		if m.done {
			now = "campaign complete"
		} else {
			now = "starting up…"
		}
	}
	b.WriteString(" " + stGreen.Render("NOW ▸ ") + stInk.Render(truncateStr(now, m.dividerWidth()-24)) + "\n")
	b.WriteString(" " + stFaint.Render(fmt.Sprintf("surface %d · chains %d · probes %d · findings %d",
		m.endpoints, m.chains, m.probes, len(m.findings))) + "\n")
	b.WriteString(dimStyle.Render(strings.Repeat("─", m.dividerWidth())) + "\n")

	// Architecture — the shared blackboard as the animated hero of the screen:
	// a pulsing stigmergic core with the live item count and flowing pheromone
	// edges, all driven off the frame counter.
	states := map[string]string{
		"recon": m.agents["recon"].Status, "classifier": m.agents["classifier"].Status,
		"exploit": m.agents["exploit"].Status, "report": m.agents["report"].Status,
	}
	b.WriteString(" " + stCyan.Render("ARCHITECTURE") + stFaint.Render("  ── stigmergic blackboard · live") + "\n")
	b.WriteString(LiveBlackboard(states, len(m.findings)+m.endpoints, m.frame, m.dividerWidth()) + "\n")
	// Exploit fan-out: the BOLA probe workers spraying off the EXPLOIT node.
	if fan := ExploitFan(m.recentProbes, m.probes, m.dividerWidth()); fan != "" {
		b.WriteString(fan + "\n")
	}
	b.WriteString(dimStyle.Render(strings.Repeat("─", m.dividerWidth())) + "\n")

	// Panel grid — swarm cluster, findings, and telemetry charts, laid out with
	// JoinHorizontal so ANSI-styled blocks align by visible width. Wide
	// terminals show all three side by side; narrower ones fall back to two
	// columns (findings beside a swarm+telemetry stack); the narrowest stacks
	// and drops the telemetry charts first.
	full := m.dividerWidth()
	switch {
	case full >= 108:
		colW := (full - 4) / 3
		iw := colW - 4
		b.WriteString(lipgloss.JoinHorizontal(lipgloss.Top,
			panelBox(m.renderSwarm(iw), colW), " ",
			panelBox(m.renderFindings(iw), colW), " ",
			panelBox(m.renderTelemetry(iw), colW)) + "\n")
	case full >= 64:
		colW := (full - 3) / 2
		if colW < 28 {
			colW = 28
		}
		iw := colW - 4
		left := lipgloss.JoinVertical(lipgloss.Left,
			panelBox(m.renderSwarm(iw), colW), panelBox(m.renderTelemetry(iw), colW))
		right := panelBox(m.renderFindings(iw), colW)
		b.WriteString(lipgloss.JoinHorizontal(lipgloss.Top, left, " ", right) + "\n")
	default:
		iw := full - 4
		b.WriteString(panelBox(m.renderSwarm(iw), full) + "\n")
		b.WriteString(panelBox(m.renderFindings(iw), full) + "\n")
	}

	b.WriteString(dimStyle.Render(strings.Repeat("─", m.dividerWidth())) + "\n")

	// Event log — trailing lines, count scaled to the terminal height so the
	// panels above always stay on screen.
	logN := 8
	if m.height > 0 {
		logN = m.height - 40
		if logN < 3 {
			logN = 3
		}
		if logN > 12 {
			logN = 12
		}
	}
	b.WriteString(dimStyle.Render(" Event Log") + "\n")
	start := 0
	if len(m.events) > logN {
		start = len(m.events) - logN
	}
	for _, e := range m.events[start:] {
		ts := dimStyle.Render(e.Timestamp.Format("15:04:05"))
		b.WriteString(fmt.Sprintf(" %s %s\n", ts, truncateStr(e.Detail, m.dividerWidth()-12)))
	}

	// Footer
	b.WriteString("\n")
	if m.DashboardURL != "" {
		b.WriteString(" " + stCyan.Render("web dashboard") + stFaint.Render(" → ") + stInk.Render(m.DashboardURL) + "\n")
	}
	if m.done {
		if m.doneErr != nil {
			b.WriteString(findingHigh.Render(" ✗ campaign failed: "+truncateStr(m.doneErr.Error(), 60)) + footerStyle.Render("   q:quit"))
		} else {
			b.WriteString(findingLow.Render(" ✓ campaign complete") + footerStyle.Render("   q:quit  ↑↓:scroll"))
		}
	} else {
		b.WriteString(footerStyle.Render(" q:quit  s:stop  ↑↓:scroll"))
	}

	return b.String()
}

// dividerWidth is the width for full-width rules and the two-column split:
// the live terminal width, floored so a tiny window doesn't collapse and
// defaulted before the first WindowSizeMsg arrives.
func (m Model) dividerWidth() int {
	w := m.width
	if w <= 0 {
		w = 72 // sensible default before the terminal reports its size
	}
	if w < 40 {
		w = 40
	}
	return w
}

// renderSwarm is the left panel: decentralized swarm imagery (a pheromone mesh
// of agent nodes with live status rows and pulse tails) plus a per-agent
// activity bar chart — replacing the old sequential stacked agent boxes.
func (m Model) renderSwarm(colW int) string {
	var b strings.Builder
	b.WriteString(stCyan.Render(" SWARM") + stFaint.Render("  decentralized agents") + "\n")
	b.WriteString(SwarmCluster(m.agents, m.agentPulse, m.frame, colW) + "\n\n")

	b.WriteString(stFaint.Render(" activity") + "\n")
	bars := []agentBar{
		{"recon", m.agents["recon"].Status, m.agentPulse["recon"], 12},
		{"classify", m.agents["classifier"].Status, m.agentPulse["classifier"], 12},
		{"exploit", m.agents["exploit"].Status, m.agentPulse["exploit"], 12},
		{"report", m.agents["report"].Status, m.agentPulse["report"], 12},
	}
	barW := colW - 16
	if barW < 8 {
		barW = 8
	}
	if barW > 24 {
		barW = 24
	}
	b.WriteString(agentActivityBars(bars, barW))
	return b.String()
}

// renderTelemetry is the charts panel: live sparklines (attack-surface growth,
// probe throughput, cumulative findings), a composite risk gauge and the spend
// meter. Every trace is sampled each tick so the panel animates continuously,
// showing motion during recon/exploit long before the first finding lands.
func (m Model) renderTelemetry(colW int) string {
	var b strings.Builder
	b.WriteString(stCyan.Render(" TELEMETRY") + stFaint.Render("  live traces") + "\n")

	sparkW := colW - 12
	if sparkW < 8 {
		sparkW = 8
	}
	if sparkW > 60 {
		sparkW = 60
	}
	row := func(label string, series []int, col lipgloss.Color) string {
		return "  " + stFaint.Render(padRight(label, 8)) + sparkline(series, sparkW, col)
	}
	b.WriteString(row("surface", m.surfaceSeries, hCyan) + "\n")
	b.WriteString(row("probes", m.probeSeries, hAmber) + "\n")
	b.WriteString(row("finds", m.findingsSeries, hRed) + "\n\n")

	// Meters carry a trailing label (score+band, or the dollar figure), so they
	// get a narrower bar than the sparklines to leave room for it without wrap.
	meterW := colW - 20
	if meterW < 6 {
		meterW = 6
	}
	if meterW > 30 {
		meterW = 30
	}
	score, band, col := m.riskScore()
	b.WriteString(stFaint.Render(" risk score") + "\n")
	b.WriteString(RiskMeter(score, band, col, meterW) + "\n\n")

	b.WriteString(stFaint.Render(" spend vs budget") + "\n")
	b.WriteString(SpendMeter(m.spend, m.BudgetUSD, meterW))
	return b.String()
}

func (m Model) renderFindings(colW int) string {
	var b strings.Builder
	b.WriteString(stCyan.Render(" Findings") + "\n")

	// Severity distribution — horizontal bar chart
	c := m.severityMap[pipeline.SeverityCritical]
	h := m.severityMap[pipeline.SeverityHigh]
	med := m.severityMap[pipeline.SeverityMedium]
	l := m.severityMap[pipeline.SeverityLow]
	b.WriteString(SeverityBars(c, h, med, l) + "\n\n")

	// Recent findings — as many as the column can show titles for.
	titleW := colW - 4
	if titleW < 16 {
		titleW = 16
	}
	start := 0
	if len(m.findings) > 6 {
		start = len(m.findings) - 6
	}
	for _, f := range m.findings[start:] {
		var style lipgloss.Style
		switch f.Severity {
		case pipeline.SeverityCritical:
			style = findingCritical
		case pipeline.SeverityHigh:
			style = findingHigh
		case pipeline.SeverityMedium:
			style = findingMedium
		default:
			style = findingLow
		}
		b.WriteString(" " + style.Render("●") + " " + truncateStr(f.Title, titleW) + "\n")
	}

	if len(m.findings) == 0 {
		b.WriteString(dimStyle.Render(" No findings yet") + "\n")
	}

	return b.String()
}

// parseSpend pulls the first dollar figure out of a cost milestone detail such
// as "spent $0.123 so far (…)" or "total spent $1.20 (…)". Returns false when
// no "$<number>" is present.
func parseSpend(detail string) (float64, bool) {
	i := strings.IndexByte(detail, '$')
	if i < 0 {
		return 0, false
	}
	j := i + 1
	for j < len(detail) {
		c := detail[j]
		if (c >= '0' && c <= '9') || c == '.' {
			j++
			continue
		}
		break
	}
	num := detail[i+1 : j]
	if num == "" || num == "." {
		return 0, false
	}
	v, err := strconv.ParseFloat(num, 64)
	if err != nil {
		return 0, false
	}
	return v, true
}

// truncateStr shortens s to at most max runes (ellipsised), counting by rune
// so multibyte titles aren't cut mid-character.
func truncateStr(s string, max int) string {
	if max < 1 {
		max = 1
	}
	r := []rune(s)
	if len(r) <= max {
		return s
	}
	if max <= 3 {
		return string(r[:max])
	}
	return string(r[:max-3]) + "..."
}
