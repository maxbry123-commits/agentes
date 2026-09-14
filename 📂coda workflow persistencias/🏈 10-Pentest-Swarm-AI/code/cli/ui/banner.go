package ui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// Hero palette — the exact tokens from banner/hero.svg and the demo GIF
// (docs/demo-flashy.gif), so the interactive UI matches the README identity:
// amber pheromone accent, agent purple, an "executes" green, cyan recon.
var (
	hVoid   = lipgloss.Color("#0B0E14") // terminal void ground
	hInk    = lipgloss.Color("#E6E9EF") // primary text
	hMuted  = lipgloss.Color("#8A93A6") // secondary text
	hFaint  = lipgloss.Color("#5C6577") // tertiary / rules
	hAmber  = lipgloss.Color("#F5A623") // pheromone accent (primary)
	hCrest  = lipgloss.Color("#FFD580") // amber crest (banner top)
	hEmber  = lipgloss.Color("#99601D") // deep ember (banner base)
	hPurple = lipgloss.Color("#7F77DD") // agents
	hPurpLt = lipgloss.Color("#AFA9EC") // agents (light)
	hGreen  = lipgloss.Color("#3DDC97") // executes / ok
	hCyan   = lipgloss.Color("#57C7FF") // recon / info
	hRed    = lipgloss.Color("#FF6B6B") // danger

	// Semantic styles used across the interactive UI.
	stAmber  = lipgloss.NewStyle().Foreground(hAmber).Bold(true)
	stAmberF = lipgloss.NewStyle().Foreground(hAmber)
	stInk    = lipgloss.NewStyle().Foreground(hInk)
	stMuted  = lipgloss.NewStyle().Foreground(hMuted)
	stFaint  = lipgloss.NewStyle().Foreground(hFaint)
	stPurple = lipgloss.NewStyle().Foreground(hPurpLt)
	stGreen  = lipgloss.NewStyle().Foreground(hGreen)
	stCyan   = lipgloss.NewStyle().Foreground(hCyan)
	stRed    = lipgloss.NewStyle().Foreground(hRed)
)

// swarmWordmark is the "SWARM" block wordmark, painted top-to-bottom in the
// amber crest→ember gradient (same art + shading as the demo GIF banner).
var swarmArt = []string{
	"██████  ██     ██  █████  ██████  ███    ███",
	"██      ██     ██ ██   ██ ██   ██ ████  ████",
	"███████ ██  █  ██ ███████ ██████  ██ ████ ██",
	"     ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██",
	"███████  ███ ███  ██   ██ ██   ██ ██      ██",
}

var swarmShades = []lipgloss.Color{hCrest, hAmber, hAmber, lipgloss.Color("#D68C24"), hEmber}

// SwarmWordmark returns the gradient block wordmark as a multi-line string,
// each line indented by pad spaces.
func SwarmWordmark(pad int) string {
	indent := strings.Repeat(" ", pad)
	var b strings.Builder
	for i, ln := range swarmArt {
		b.WriteString(indent + lipgloss.NewStyle().Foreground(swarmShades[i]).Render(ln) + "\n")
	}
	return strings.TrimRight(b.String(), "\n")
}

// swarmConstellation is the product thesis as art: four specialist agents
// (recon / classify / exploit / report) converging on a shared blackboard
// core, with pheromone trails. Reads as a swarm, not a mascot.
func swarmConstellation() string {
	dotR := stCyan.Render("◍")   // recon
	dotC := stPurple.Render("◍") // classify
	dotX := stAmberF.Render("◍") // exploit
	dotP := stPurple.Render("◍") // report
	core := stAmber.Render("◈")
	trail := stFaint.Render("·")
	lines := []string{
		"  " + dotR + " recon " + trail + trail + stFaint.Render("╮") + "        " + stFaint.Render("╭") + trail + trail + " exploit " + dotX,
		"             " + core + " " + core + " " + core + "   " + stFaint.Render("blackboard"),
		"  " + dotC + " classify " + stFaint.Render("╯") + "        " + stFaint.Render("╰") + " report " + dotP,
	}
	return strings.Join(lines, "\n")
}

// agentStyle colors an agent node/label by its live status.
func agentStyle(state string) lipgloss.Style {
	switch state {
	case "active":
		return stAmber
	case "complete":
		return stGreen
	case "error":
		return stRed
	default:
		return stFaint
	}
}

// LiveConstellation renders the swarm architecture as a live diagram: the
// four specialist agents around the shared blackboard core, each lit by its
// current status (amber = active, green = complete, red = error, faint =
// idle). This is the "blackboard diagram" from the GIF, but animated by the
// real run. states keys: recon, classifier, exploit, report.
func LiveConstellation(states map[string]string) string {
	dot := func(id string) string { return agentStyle(states[id]).Render("◍") }
	lbl := func(id, name string) string { return agentStyle(states[id]).Render(name) }
	f := stFaint
	core := stAmber.Render("◈ ◈ ◈")
	lines := []string{
		"   " + dot("recon") + " " + padRight(lbl("recon", "RECON"), 9) + f.Render("╲") + "          " + f.Render("╱") + " " + dot("exploit") + " " + lbl("exploit", "EXPLOIT"),
		"                 " + f.Render("╲      ╱"),
		"            " + core + "  " + stMuted.Render("blackboard"),
		"                 " + f.Render("╱      ╲"),
		"   " + dot("classifier") + " " + padRight(lbl("classifier", "CLASSIFY"), 9) + f.Render("╱") + "          " + f.Render("╲") + " " + dot("report") + " " + lbl("report", "REPORT"),
	}
	return strings.Join(lines, "\n")
}

// LiveBlackboard is the animated, stigmergic evolution of LiveConstellation:
// the shared BLACKBOARD as a pulsing core showing the live item count (findings
// + attack surface), the four specialists around it, and pheromone-trail edges
// that visibly flow — inward on the top pair (recon/exploit depositing findings
// and surface onto the board) and outward on the bottom pair (the board cueing
// classify/report). Everything cycles off frame so the diagram is alive every
// tick; edges and nodes light by live agent status. width is advisory (the
// caller gates the panel on small terminals); the geometry is fixed and
// on-brand with the hero constellation.
func LiveBlackboard(states map[string]string, items, frame, width int) string {
	dot := func(id string) string {
		g := "◍"
		if states[id] == "active" && frame%2 == 1 {
			g = "◉" // active nodes pulse between ◍ and ◉
		}
		return agentStyle(states[id]).Render(g)
	}
	lbl := func(id, name string) string { return agentStyle(states[id]).Render(name) }
	arm := func(id, stroke string) string { return agentStyle(states[id]).Render(stroke) }

	// A single pheromone glyph walking across a 6-cell gap between the two
	// connector strokes; inward (toward the board) on the top pair, outward on
	// the bottom pair, so the trails visibly flow each frame.
	trail := []rune("·∴∵")
	gap := func(inward bool) string {
		const w = 6
		pos := frame % w
		if inward {
			pos = w - 1 - pos
		}
		var b strings.Builder
		for i := 0; i < w; i++ {
			if i == pos {
				b.WriteString(stAmberF.Render(string(trail[frame%len(trail)])))
			} else {
				b.WriteString(" ")
			}
		}
		return b.String()
	}

	// Pulsing core: the glyph shimmers and the crest/amber tint alternates so the
	// blackboard reads as a living, contended shared memory.
	coreGlyphs := []string{"◈ ◈ ◈", "◇ ◈ ◇", "◈ ◆ ◈", "◇ ◈ ◇"}
	coreSt := stAmber
	if frame%2 == 0 {
		coreSt = lipgloss.NewStyle().Foreground(hCrest).Bold(true)
	}
	core := coreSt.Render(coreGlyphs[frame%len(coreGlyphs)])
	itemsLbl := stMuted.Render(fmt.Sprintf("blackboard · %d live items", items))

	lines := []string{
		"   " + dot("recon") + " " + padRight(lbl("recon", "RECON"), 9) + arm("recon", "╲") + "          " + arm("exploit", "╱") + " " + dot("exploit") + " " + lbl("exploit", "EXPLOIT"),
		"                 " + arm("recon", "╲") + gap(true) + arm("exploit", "╱"),
		"            " + core + "  " + itemsLbl,
		"                 " + arm("classifier", "╱") + gap(false) + arm("report", "╲"),
		"   " + dot("classifier") + " " + padRight(lbl("classifier", "CLASSIFY"), 9) + arm("classifier", "╱") + "          " + arm("report", "╲") + " " + dot("report") + " " + lbl("report", "REPORT"),
	}
	return strings.Join(lines, "\n")
}

// SwarmCluster replaces the old stacked agent boxes with decentralized swarm
// imagery: a one-line pheromone MESH of the four specialists (plus the
// orchestrator) linked by animated trail glyphs — so it reads as many agents
// working at once, not a pipeline — followed by a compact, legible status row
// per agent with a live pulse tail sized by recent activity. Nodes and pulses
// light by status and cycle off frame. pulse[id] is a decaying recent-activity
// level per agent; width bounds the detail column.
func SwarmCluster(agents map[string]AgentStatus, pulse map[string]int, frame, width int) string {
	trail := []rune("·∴∵")
	node := func(id, short string) string {
		st := agentStyle(agents[id].Status)
		g := "◍"
		switch agents[id].Status {
		case "active":
			if (frame+len(id))%2 == 0 {
				g = "◉"
			}
		case "complete":
			g = "◈"
		case "error":
			g = "✗"
		}
		return st.Render(g + short)
	}
	link := func(i int) string { return stAmberF.Render(string(trail[(frame+i)%len(trail)])) }

	var b strings.Builder
	// Pheromone mesh — the swarm as a cluster, linked by flowing trails.
	b.WriteString("  " + node("recon", "RCN") + " " + link(0) + " " + node("classifier", "CLS") +
		" " + link(1) + " " + node("exploit", "XPL") + " " + link(2) + " " + node("report", "RPT") +
		"   " + agentStyle(agents["orchestrator"].Status).Render("◆ ORCH") + "\n")

	detailW := width - 26
	if detailW < 8 {
		detailW = 8
	}
	rows := []struct{ id, name string }{
		{"recon", "Recon"}, {"classifier", "Classifier"},
		{"exploit", "Exploit"}, {"report", "Report"},
	}
	for i, r := range rows {
		st := agentStyle(agents[r.id].Status)
		lvl := pulse[r.id]
		if agents[r.id].Status == "active" && lvl < 1 {
			lvl = 1 // a running agent always shows at least one pulse
		}
		if lvl > 5 {
			lvl = 5
		}
		var pb strings.Builder
		for j := 0; j < lvl; j++ {
			pb.WriteString(st.Render(string(trail[(frame+j+i)%len(trail)])))
		}
		b.WriteString(fmt.Sprintf("  %s %s %s\n",
			st.Render(padRight(r.name, 10)),
			stFaint.Render(truncateStr(agents[r.id].Detail, detailW)),
			pb.String()))
	}
	return strings.TrimRight(b.String(), "\n")
}

// ExploitFan renders the exploit phase's BOLA probe fan-out as a compact spray
// of tiny worker marks branching off the EXPLOIT node — the terminal echo of
// the dashboard's decentralized probe mesh. total is the lifetime probe count
// (shown as the label); recent is the current burst, which sets how wide the
// spray reaches. The leading (freshest) marks glow amber, the tail settles to
// green. width bounds the spray so it never wraps. Returns "" before any probe.
func ExploitFan(recent, total, width int) string {
	if total <= 0 {
		return ""
	}
	// Cap the spray to the space left after the label + stem so it never wraps.
	maxMarks := (width - 30) / 2
	if maxMarks < 4 {
		maxMarks = 4
	}
	if maxMarks > 30 {
		maxMarks = 30
	}
	n := recent
	if n < 3 {
		n = 3 // keep a small live fan visible while probing, even between bursts
	}
	if n > maxMarks {
		n = maxMarks
	}
	glyphs := []string{"·", "∴", "∵"}
	var spray strings.Builder
	for i := 0; i < n; i++ {
		g := glyphs[i%len(glyphs)]
		if i < recent/2 { // the freshest half of the burst is the live edge
			spray.WriteString(stAmberF.Render(g))
		} else {
			spray.WriteString(stGreen.Render(g))
		}
	}
	label := stFaint.Render(fmt.Sprintf("  %d probes", total))
	return "        " + stAmber.Render("EXPLOIT") + stFaint.Render(" ⟩⟩ ") + spray.String() + label
}

// sparkline renders vals as a compact Unicode block-graph (▁▂▃▄▅▆▇█) of at
// most width cells, showing the most recent `width` samples so the series
// scrolls left as it grows. Each cell is tinted in col, with the flat baseline
// (zero samples) dropped to faint so a quiet series still reads as "alive but
// idle" rather than empty. Peaks brighten toward the crest so a burst pops.
func sparkline(vals []int, width int, col lipgloss.Color) string {
	blocks := []rune("▁▂▃▄▅▆▇█")
	if width < 1 {
		width = 1
	}
	if len(vals) == 0 {
		return stFaint.Render(strings.Repeat("▁", width))
	}
	if len(vals) > width {
		vals = vals[len(vals)-width:]
	}
	maxV := 1
	for _, v := range vals {
		if v > maxV {
			maxV = v
		}
	}
	hot := lipgloss.NewStyle().Foreground(col)
	warm := lipgloss.NewStyle().Foreground(col).Faint(true)
	crest := lipgloss.NewStyle().Foreground(hCrest)
	var b strings.Builder
	for _, v := range vals {
		if v <= 0 {
			b.WriteString(stFaint.Render("▁"))
			continue
		}
		idx := v * (len(blocks) - 1) / maxV
		if idx < 0 {
			idx = 0
		}
		if idx >= len(blocks) {
			idx = len(blocks) - 1
		}
		ch := string(blocks[idx])
		switch {
		case idx >= 6:
			b.WriteString(crest.Render(ch))
		case idx >= 3:
			b.WriteString(hot.Render(ch))
		default:
			b.WriteString(warm.Render(ch))
		}
	}
	// Pad short series on the left so the graph is right-aligned (freshest at the
	// right edge), matching how a live trace scrolls.
	if pad := width - len(vals); pad > 0 {
		return stFaint.Render(strings.Repeat("▁", pad)) + b.String()
	}
	return b.String()
}

// agentBar is one row of the agent-activity chart: a label, its live status
// (idle/active/complete/error) and a 0..max activity level.
type agentBar struct {
	label  string
	status string
	level  int
	max    int
}

// agentActivityBars renders a small horizontal bar per agent in the SeverityBars
// visual idiom — length reflects recent activity, color reflects live status
// (amber active / green complete / red error / faint idle). barW is the bar's
// cell width.
func agentActivityBars(bars []agentBar, barW int) string {
	if barW < 4 {
		barW = 4
	}
	var b strings.Builder
	for _, r := range bars {
		st := agentStyle(r.status)
		max := r.max
		if max < 1 {
			max = 1
		}
		fill := r.level * barW / max
		if fill > barW {
			fill = barW
		}
		// An active agent with no recent pulse still shows a single lit cell so
		// the row reads as "running", not dead.
		if fill == 0 && r.status == "active" {
			fill = 1
		}
		bar := st.Render(strings.Repeat("█", fill)) + stFaint.Render(strings.Repeat("·", barW-fill))
		b.WriteString(fmt.Sprintf("  %s %s\n", st.Render(padRight(r.label, 9)), bar))
	}
	return strings.TrimRight(b.String(), "\n")
}

// RiskMeter renders a composite 0..100 risk score as a labeled bar (the
// SeverityBars look), tinted by band color. label is the band name (e.g.
// CRITICAL). width is the bar's cell width.
func RiskMeter(score int, label string, col lipgloss.Color, width int) string {
	if width < 6 {
		width = 6
	}
	if score < 0 {
		score = 0
	}
	if score > 100 {
		score = 100
	}
	fill := score * width / 100
	if score > 0 && fill == 0 {
		fill = 1
	}
	st := lipgloss.NewStyle().Foreground(col).Bold(true)
	bar := st.Render(strings.Repeat("█", fill)) + stFaint.Render(strings.Repeat("·", width-fill))
	return fmt.Sprintf("  %s %s %s", bar, st.Render(fmt.Sprintf("%3d", score)), st.Render(label))
}

// SpendMeter renders cumulative LLM spend as a bar. With a known budget cap it
// fills toward the cap (green→amber→red as it approaches); with no cap it grows
// against a soft rolling ceiling so it still animates upward.
func SpendMeter(spend, budget float64, width int) string {
	if width < 6 {
		width = 6
	}
	var frac float64
	var label string
	col := hGreen
	if budget > 0 {
		frac = spend / budget
		label = fmt.Sprintf("$%.3f / $%.2f", spend, budget)
		switch {
		case frac >= 0.9:
			col = hRed
		case frac >= 0.6:
			col = hAmber
		}
	} else {
		// Soft ceiling: a round number comfortably above the current spend so the
		// bar keeps room to climb.
		ceil := 0.10
		for ceil <= spend {
			ceil *= 2
		}
		frac = spend / ceil
		label = fmt.Sprintf("$%.3f spent", spend)
		col = hAmber
	}
	if frac < 0 {
		frac = 0
	}
	if frac > 1 {
		frac = 1
	}
	fill := int(frac * float64(width))
	if spend > 0 && fill == 0 {
		fill = 1
	}
	if fill > width {
		fill = width
	}
	st := lipgloss.NewStyle().Foreground(col)
	bar := st.Render(strings.Repeat("█", fill)) + stFaint.Render(strings.Repeat("░", width-fill))
	return fmt.Sprintf("  %s %s", bar, stMuted.Render(label))
}

// panelBox frames a rendered panel body in a recessive rounded border so the
// campaign screen reads as neat titled cards. totalW is the box's outer width;
// the body should already be sized to totalW-4 (2 border + 2 padding). The
// border is faint on purpose — the data is the hero, the chrome recedes.
func panelBox(body string, totalW int) string {
	iw := totalW - 4
	if iw < 10 {
		iw = 10
	}
	return lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(hFaint).
		Padding(0, 1).
		Width(iw).
		Render(body)
}

// SeverityBars renders a horizontal bar chart of finding counts by severity.
func SeverityBars(crit, high, med, low int) string {
	stHigh := lipgloss.NewStyle().Foreground(lipgloss.Color("#F97316"))
	rows := []struct {
		label string
		n     int
		st    lipgloss.Style
	}{
		{"CRIT", crit, stRed},
		{"HIGH", high, stHigh},
		{"MED ", med, stAmberF},
		{"LOW ", low, stGreen},
	}
	maxN := 1
	for _, r := range rows {
		if r.n > maxN {
			maxN = r.n
		}
	}
	const barW = 18
	var b strings.Builder
	for _, r := range rows {
		fill := r.n * barW / maxN
		if r.n > 0 && fill == 0 {
			fill = 1
		}
		bar := r.st.Render(strings.Repeat("█", fill)) + stFaint.Render(strings.Repeat("·", barW-fill))
		b.WriteString(fmt.Sprintf("  %s %s %s\n", r.st.Render(r.label), bar, stMuted.Render(fmt.Sprintf("%d", r.n))))
	}
	return strings.TrimRight(b.String(), "\n")
}

// ProgressBar renders a filled progress bar (done/total) of the given width.
func ProgressBar(done, total, width int) string {
	if total <= 0 {
		total = 1
	}
	if done > total {
		done = total
	}
	fill := done * width / total
	return stGreen.Render(strings.Repeat("█", fill)) + stFaint.Render(strings.Repeat("░", width-fill))
}

// swarmRule is a honeycomb "pheromone" divider of the given visible width,
// tinted in the amber accent.
func swarmRule(width int) string {
	if width < 8 {
		width = 8
	}
	cells := width / 2
	if cells < 4 {
		cells = 4
	}
	var b strings.Builder
	for i := 0; i < cells; i++ {
		if i%2 == 0 {
			b.WriteString("⬡")
		} else {
			b.WriteString("⬢")
		}
	}
	return stAmberF.Render(b.String())
}

// Banner renders the full hero for the launcher: wordmark + tagline +
// pheromone rule. When width is too narrow for the block art, it falls back
// to a compact one-line mark so nothing wraps into noise.
func Banner(width int) string {
	const artWidth = 46 // widest wordmark line + a little indent
	if width > 0 && width < artWidth+6 {
		return stAmber.Render("◢ PENTEST SWARM") + stMuted.Render("  ·  swarms of agents, one mission")
	}
	var b strings.Builder
	b.WriteString(SwarmWordmark(2) + "\n")
	b.WriteString("  " + stMuted.Render("PENTEST") + "  " + stAmber.Render("SWARM") + "  " +
		stMuted.Render("AI") + stFaint.Render("   ·   swarms of agents, one mission") + "\n")
	b.WriteString(swarmConstellation() + "\n")
	rw := width - 6
	if rw <= 0 || rw > 52 {
		rw = 52
	}
	b.WriteString("  " + swarmRule(rw))
	return b.String()
}
