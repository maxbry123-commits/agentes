package cli

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/config"
	livedash "github.com/Armur-Ai/Pentest-Swarm-AI/internal/dashboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/engine"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/keychain"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/llm"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

// preStartedDashboard, when non-nil, is a live dashboard the interactive
// launcher (`pentestswarm run`) started up front so localhost:7777 is
// available while the user is still picking options. runScan reuses it
// instead of starting a second server, then consumes it (sets it back to nil).
var preStartedDashboard *livedash.Server

var scanCmd = &cobra.Command{
	Use:   "scan <target>",
	Short: "Launch the swarm against a target",
	Long:  `Deploys the AI agent swarm to autonomously pentest the specified target.`,
	Args:  cobra.RangeArgs(0, 1),
	Example: `  pentestswarm scan example.com --scope example.com
  pentestswarm scan 10.0.0.0/24 --scope 10.0.0.0/24 --objective "find RCE"
  pentestswarm scan example.com --scope example.com --mode bugbounty --follow
  pentestswarm scan --lab --swarm --follow   # watch it work a bundled, legal target`,
	RunE: runScan,
}

func runScan(cmd *cobra.Command, args []string) error {
	lab, _ := cmd.Flags().GetBool("lab")
	demo, _ := cmd.Flags().GetBool("demo")

	// A scan needs exactly one target argument — validate up front so the
	// message is "you forgot the target", not a later config error. --lab and
	// --demo supply their own target, so they're exempt.
	if !lab && !demo && len(args) != 1 {
		return fmt.Errorf("scan needs a target.\n  Try:   %s\n  Or watch it work a bundled, legal practice target:   %s",
			colorCyan("pentestswarm scan example.com --scope example.com"),
			colorCyan("pentestswarm scan --lab"))
	}

	// target + scopeStr are resolved after the pre-flight checks below:
	// from --lab (a bundled local target) or from the CLI argument.
	var target, scopeStr string

	objective, _ := cmd.Flags().GetString("objective")
	mode, _ := cmd.Flags().GetString("mode")
	dryRun, _ := cmd.Flags().GetBool("dry-run")
	follow, _ := cmd.Flags().GetBool("follow")
	format, _ := cmd.Flags().GetString("format")
	output, _ := cmd.Flags().GetString("output")
	providerOverride, _ := cmd.Flags().GetString("provider")
	explorationBias, _ := cmd.Flags().GetString("exploration-bias")
	publishUnverified, _ := cmd.Flags().GetBool("publish-unverified")
	assist, _ := cmd.Flags().GetBool("assist")
	estimate, _ := cmd.Flags().GetBool("estimate")
	safeMode, _ := cmd.Flags().GetBool("safe-mode")
	targetClass, _ := cmd.Flags().GetString("target-class")
	nucleiSeverityStr, _ := cmd.Flags().GetString("nuclei-severity")
	activeScan, _ := cmd.Flags().GetBool("active-scan")

	// Mode shapes the campaign: it steers the objective the swarm pursues and,
	// for ASM, disables active exploitation (surface mapping only). A custom
	// --objective always wins; mode only fills in the default.
	objective, activeScan = applyMode(mode, objective, activeScan, cmd.Flags().Changed("active-scan"))

	// --estimate short-circuits everything: print expected cost and exit
	// without touching the network. Fires before config validation so it
	// works even without an API key.
	if estimate {
		modelName := "claude-sonnet-4-6"
		if cfg, err := config.Load(cfgFile); err == nil && cfg.Orchestrator.Model != "" {
			modelName = cfg.Orchestrator.Model
		}
		lo, hi := llm.PricingFor(modelName).EstimateUSD(targetClass)
		fmt.Println()
		fmt.Printf("  %s target class: %s\n", colorCyan("[estimate]"), fallback(targetClass, "medium"))
		fmt.Printf("  %s model:        %s\n", colorCyan("[estimate]"), modelName)
		fmt.Printf("  %s expected LLM spend: %s\n", colorCyan("[estimate]"),
			colorBold(fmt.Sprintf("$%.2f – $%.2f", lo, hi)))
		fmt.Println(colorDim("  (No packets sent. Remove --estimate to run the scan.)"))
		return nil
	}

	// Load config
	cfg, err := config.Load(cfgFile)
	if err != nil {
		// 4.8.3: every error message must end with a next-step. A bare
		// "loading config: ..." leaves the researcher guessing.
		return fmt.Errorf("loading config: %w\n  Fix: run %s to write a fresh config",
			err, colorCyan("pentestswarm init"))
	}

	// A --provider override takes effect for the pre-flight checks too, so
	// e.g. `--lab --provider ollama` (fully local) doesn't demand a Claude key.
	effectiveProvider := cfg.Orchestrator.Provider
	if providerOverride != "" {
		effectiveProvider = providerOverride
	}

	// --demo replays a canned crAPI campaign entirely offline (no network, no
	// LLM, no key). Skip API-key resolution/prompting and target/scope
	// requirements — nothing here reaches out.
	if demo {
		target = "crAPI · demo replay (offline)"
		scopeStr = "127.0.0.1/32,localhost"
	} else {
		// Resolve the API key: env first (CI-friendly), then OS keychain
		// (the path 'pentestswarm init' writes to), with config.yaml as the
		// last-resort fallback so old setups keep working.
		if cfg.Orchestrator.APIKey == "" {
			if key := os.Getenv("PENTESTSWARM_ORCHESTRATOR_API_KEY"); key != "" {
				cfg.Orchestrator.APIKey = key
			} else if key := os.Getenv("ANTHROPIC_API_KEY"); key != "" {
				cfg.Orchestrator.APIKey = key
			} else if key, err := keychain.Get(keychain.KeyClaudeAPI); err == nil && key != "" {
				cfg.Orchestrator.APIKey = key
			}
		}

		// First-run bootstrap: in an interactive terminal, prompt once instead
		// of failing. A researcher who just installed the tool deserves a
		// chance to paste their key without re-reading the docs.
		if cfg.Orchestrator.APIKey == "" && providerNeedsKey(effectiveProvider) {
			if !quiet && term.IsTerminal(int(os.Stdin.Fd())) {
				if key := promptForAPIKeyOnce(effectiveProvider); key != "" {
					cfg.Orchestrator.APIKey = key
				}
			}
		}

		if cfg.Orchestrator.APIKey == "" && providerNeedsKey(effectiveProvider) {
			return errors.New("no API key configured for provider '" + effectiveProvider + "'.\n" +
				"  Fix one of these, then re-run:\n" +
				"    1) " + colorCyan("pentestswarm init") + "   (one-shot interactive setup)\n" +
				"    2) " + colorCyan("export PENTESTSWARM_ORCHESTRATOR_API_KEY=…") + "\n" +
				"    3) " + colorCyan("pentestswarm run") + "   (interactive launcher — pick the provider and paste the key)")
		}
	}

	// Resolve target + scope. --lab spins up a bundled, intentionally-
	// vulnerable app (OWASP Juice Shop) on localhost and points the swarm
	// at it — a legal, zero-setup way to watch the swarm actually find
	// something. Otherwise the target is the CLI argument.
	if demo {
		// target/scope already set above; nothing to resolve.
	} else if lab {
		labTargetName, _ := cmd.Flags().GetString("lab-target")
		profile, profErr := resolveLabProfile(labTargetName)
		if profErr != nil {
			return profErr
		}
		t, s, teardown, labErr := startLab(profile, quiet)
		if labErr != nil {
			return labErr
		}
		defer teardown()
		target, scopeStr = t, s
	} else {
		if len(args) != 1 {
			return fmt.Errorf("scan needs a target.\n  Try:   %s\n  Or watch it work a bundled, legal practice target:   %s",
				colorCyan("pentestswarm scan example.com --scope example.com"),
				colorCyan("pentestswarm scan --lab"))
		}
		target = args[0]
		scopeStr, _ = cmd.Flags().GetString("scope")
		if scopeStr == "" {
			// Phase 4.8.5: default scope to the target itself when --scope is
			// omitted — the most common first-run failure. Single-target scope
			// is conservative (won't reach a sibling domain), so it's safe.
			scopeStr = target
			if !quiet {
				fmt.Printf("  %s no --scope set, defaulting to %s\n", colorDim("[scope]"), colorBold(target))
			}
		}
	}

	// Print banner
	if !quiet {
		printBanner()
		fmt.Println()
		fmt.Printf("  Target:     %s\n", colorBold(target))
		fmt.Printf("  Scope:      %s\n", scopeStr)
		fmt.Printf("  Objective:  %s\n", objective)
		fmt.Printf("  Mode:       %s %s\n", mode, colorDim("— "+modeSummary(mode)))
		fmt.Printf("  Provider:   %s\n", providerOrDefault(providerOverride, cfg.Orchestrator.Provider))
		if dryRun {
			fmt.Printf("  %s\n", colorYellow("DRY RUN — no exploitation commands will execute"))
		}
		fmt.Println()
		fmt.Println(colorDim("─────────────────────────────────────────────────────"))
		fmt.Println()
	}

	// Setup context with signal handling
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		fmt.Println("\n" + colorRed("Emergency stop — shutting down swarm..."))
		cancel()
	}()

	// Build campaign config. publishThreshold is the verified-PoC gate:
	// default 0.5 ('bugbounty' — only confirmed findings ship), 0.1 when
	// --publish-unverified is set ('aggressive' — suspected-but-not-
	// reproduced findings included with a warning).
	publishThreshold := 0.5
	if publishUnverified {
		publishThreshold = 0.1
	}
	// Spend cap + killswitch. --budget is a hard per-run USD limit; the swarm
	// winds down gracefully the moment cumulative LLM spend reaches it, so an
	// autonomous run can't quietly burn hundreds of dollars. stopCh is a manual
	// killswitch the web dashboard's Stop button closes.
	maxCostUSD, _ := cmd.Flags().GetFloat64("budget")
	stopCh := make(chan struct{})
	var stopOnce sync.Once
	triggerStop := func() { stopOnce.Do(func() { close(stopCh) }) }

	cc := engine.CampaignConfig{
		Target:           target,
		Scope:            strings.Split(scopeStr, ","),
		Objective:        objective,
		Mode:             mode,
		DryRun:           dryRun,
		OutputDir:        output,
		Format:           format,
		Provider:         providerOverride,
		PublishThreshold: publishThreshold,
		ExplorationBias:  explorationBias,
		Assist:           assist,
		SafeMode:         safeMode,
		NucleiSeverity:   splitCSV(nucleiSeverityStr),
		ActiveScan:       activeScan,
		MaxCostUSD:       maxCostUSD,
		StopRequested:    stopCh,
	}

	// Live dashboard: a self-contained localhost web view of the swarm. It
	// runs alongside the terminal output (which is unchanged), so the operator
	// can open a browser and watch agents activate, findings get graded, and
	// the report assemble in real time. Local-only, no external dependencies.
	useSwarm, _ := cmd.Flags().GetBool("swarm")
	dashOn, _ := cmd.Flags().GetBool("dashboard")
	tuiMode, _ := cmd.Flags().GetBool("tui")
	// Demo replay is a swarm-shaped event stream, so it needs the swarm code
	// path (dashboard + TUI wiring) regardless of the --swarm flag.
	if demo {
		useSwarm = true
	}
	// The full-screen TUI owns the terminal's *rendering*, but the web
	// dashboard is just a background HTTP server — the two coexist. So the TUI
	// and the web dashboard both run when selected; only a real terminal and a
	// real run engage the TUI.
	tuiMode = tuiMode && !dryRun && term.IsTerminal(int(os.Stdin.Fd()))
	var dash *livedash.Server
	if useSwarm && dashOn && !dryRun {
		if preStartedDashboard != nil {
			// The interactive launcher already started the dashboard so
			// localhost:7777 was live while the user picked options. Reuse it
			// and just fill in the campaign metadata now that we know it.
			dash = preStartedDashboard
			preStartedDashboard = nil
			dash.Publish(livedash.Event{Kind: "meta", Detail: target, Title: objective, Agent: mode})
			dash.PublishStatus("running")
			dash.OnStop(triggerStop)
		} else {
			dash = livedash.New(output)
			if url, derr := dash.Start(); derr == nil {
				dash.OnStop(triggerStop)
				dash.Publish(livedash.Event{Kind: "meta", Detail: target, Title: objective, Agent: mode})
				if !quiet {
					fmt.Printf("\n  %s  %s\n", colorBold("Live dashboard →"), colorCyan(url))
					// Be explicit when the preferred port was busy so the user
					// isn't confused about why it's not on :7777.
					if !strings.Contains(url, ":7777") {
						fmt.Printf("  %s\n", colorDim(":7777 was busy — using the port above instead."))
					}
				}
			} else {
				// All candidate ports were busy. Don't fail the run — say so and
				// carry on with terminal output only.
				dash = nil
				if !quiet {
					fmt.Printf("\n  %s %s\n", colorYellow("[note]"),
						colorDim("couldn't start the live dashboard (ports busy) — continuing with terminal output."))
				}
			}
		}
	}

	// Event handler for live output (terminal + optional dashboard). Always
	// installed (even when --quiet and not --follow) so findingsCount below
	// is accurate regardless of what gets printed — the exit code needs to
	// reflect reality even in scripted/quiet runs.
	findingsCount := 0
	onEvent := func(event pipeline.CampaignEvent) {
		if event.EventType == pipeline.EventFindingDiscovered {
			findingsCount++
		}
		if follow || !quiet {
			printEvent(event)
		}
		if dash != nil {
			publishToDashboard(dash, event)
		}
	}

	// Run the campaign
	var runnerOpts []engine.Option
	if strict, _ := cmd.Flags().GetBool("strict"); strict {
		runnerOpts = append(runnerOpts, engine.WithStrictLLM())
	}
	if assist {
		runnerOpts = append(runnerOpts, engine.WithAssistConfirmer(assistConfirm))
	}
	runner := engine.NewRunner(cfg, runnerOpts...)
	run := runner.Run
	if useSwarm {
		run = runner.RunSwarm
	}
	// --demo swaps in the offline replay in place of a real run; the dashboard
	// + TUI wiring below is identical, so both light up as if it were live.
	if demo {
		run = engine.RunDemoReplay
	}

	// Full-screen TUI live view: the Bubble Tea dashboard owns the terminal,
	// the swarm runs in a goroutine and streams events into it, and the user
	// quits with q (or Ctrl-C / s to stop). Replaces the scrolling output.
	if tuiMode {
		// The terminal shows the charted TUI; the web dashboard (if enabled)
		// keeps serving in the background and is fed the same events.
		return runCampaignTUI(ctx, cancel, run, cc, target, objective, dash, &ExitCode)
	}

	if err := run(ctx, cc, onEvent); err != nil {
		if dash != nil {
			dash.Stop()
		}
		if ctx.Err() != nil {
			fmt.Println(colorRed("\nCampaign aborted by user."))
			return nil
		}
		return fmt.Errorf("campaign failed: %w\n  Next: re-run with %s to abort on first error and surface the root cause",
			err, colorCyan("--strict"))
	}

	if !quiet {
		fmt.Println()
		fmt.Println(colorGreen("Campaign complete."))
	}

	// Keep the dashboard alive after the run so the operator can explore the
	// final graded report in the browser. Exits cleanly on Ctrl-C.
	if dash != nil {
		dash.PublishStatus("complete")
		if !quiet {
			fmt.Printf("\n  %s  %s   %s\n",
				colorBold("Dashboard live →"), colorCyan(dash.URL()), colorDim("(Ctrl-C to exit)"))
		}
		<-ctx.Done()
		dash.Stop()
	}

	// Meaningful exit code for scripting/CI: 0 = completed clean, 1 =
	// completed but the swarm reported findings, 2 = error (handled by the
	// `return err` paths above, via Execute() in root.go). findingsCount is
	// tallied from the same EventFindingDiscovered stream the dashboard and
	// terminal output already consume, so this doesn't reach into the engine.
	if findingsCount > 0 {
		ExitCode = 1
	}

	return nil
}

// publishToDashboard maps a campaign event onto the dashboard's live stream:
// graded findings, running LLM spend, and the color-coded activity feed.
func publishToDashboard(dash *livedash.Server, e pipeline.CampaignEvent) {
	if e.EventType == pipeline.EventFindingDiscovered && len(e.Data) > 0 {
		var d struct {
			Severity    string  `json:"severity"`
			Title       string  `json:"title"`
			Category    string  `json:"category"`
			Cvss        float64 `json:"cvss"`
			Confidence  string  `json:"confidence"`
			Description string  `json:"description"`
		}
		if json.Unmarshal(e.Data, &d) == nil && d.Title != "" {
			dash.PublishFinding(livedash.Event{
				Severity: d.Severity, Title: d.Title, Category: d.Category,
				Cvss: d.Cvss, Confidence: d.Confidence, Description: d.Description,
			})
			return
		}
	}
	if e.EventType == pipeline.EventEndpointDiscovered {
		dash.Publish(livedash.Event{Kind: "endpoint", Detail: e.Detail})
		return
	}
	if e.EventType == pipeline.EventChainStarted {
		var d struct {
			ID    string               `json:"id"`
			Name  string               `json:"name"`
			Steps []livedash.ChainStep `json:"steps"`
		}
		if json.Unmarshal(e.Data, &d) == nil {
			dash.Publish(livedash.Event{Kind: "chain", ChainID: d.ID, ChainName: d.Name, Steps: d.Steps})
		}
		return
	}
	if e.EventType == pipeline.EventProbe {
		// One BOLA probe work-unit — the exploit phase fanning out. Parse the
		// {"target","ok"} payload so the dashboard can spawn a mesh worker node.
		target, ok := e.Detail, false
		var d struct {
			Target string `json:"target"`
			Ok     bool   `json:"ok"`
		}
		if len(e.Data) > 0 && json.Unmarshal(e.Data, &d) == nil {
			if d.Target != "" {
				target = d.Target
			}
			ok = d.Ok
		}
		dash.Publish(livedash.Event{Kind: "probe", Detail: target, Ok: ok})
		return
	}
	if e.EventType == pipeline.EventChainStep {
		var d struct {
			ChainID string `json:"chain_id"`
			Step    string `json:"step"`
			Success bool   `json:"success"`
		}
		if json.Unmarshal(e.Data, &d) == nil {
			dash.Publish(livedash.Event{Kind: "chainstep", ChainID: d.ChainID, Step: d.Step, Ok: d.Success})
		}
		return
	}
	if e.AgentName == "cost" {
		dash.Publish(livedash.Event{Kind: "spend", Detail: e.Detail})
		return
	}
	dash.Publish(livedash.Event{
		Kind:   "log",
		Ts:     e.Timestamp.Format("15:04:05"),
		Type:   string(e.EventType),
		Agent:  e.AgentName,
		Detail: e.Detail,
	})
	if e.EventType == pipeline.EventMilestone && strings.Contains(strings.ToLower(e.Detail), "complete") {
		dash.PublishStatus("complete")
	}
}

func printEvent(event pipeline.CampaignEvent) {
	ts := event.Timestamp.Format("15:04:05")

	switch event.EventType {
	case pipeline.EventThought:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorCyan("[think]"), event.Detail)
	case pipeline.EventToolCall:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorYellow("[>>]"), event.Detail)
	case pipeline.EventToolResult:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorGreen("[<<]"), event.Detail)
	case pipeline.EventFindingDiscovered:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorRed("[!]"), event.Detail)
	case pipeline.EventEndpointDiscovered:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorDim("[surface]"), colorDim(event.Detail))
	case pipeline.EventChainStarted, pipeline.EventChainStep, pipeline.EventProbe:
		// Dashboard/TUI-only telemetry — the chain's steps already surface as
		// tool-call/result lines in the terminal, and probes are a high-volume
		// fan-out best shown as the live mesh, so don't spam the scroll feed.
	case pipeline.EventStateChange:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorMagenta("[*]"), event.Detail)
	case pipeline.EventStepExecuted:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorYellow("[>]"), event.Detail)
	case pipeline.EventError:
		fmt.Printf("  %s %s %s\n", colorDim(ts), colorRed("[ERR]"), event.Detail)
	case pipeline.EventMilestone:
		fmt.Printf("\n  %s %s\n", colorGreen("[DONE]"), colorBold(event.Detail))
	default:
		fmt.Printf("  %s [%s] %s\n", colorDim(ts), event.EventType, event.Detail)
	}
}

func printBanner() {
	// "SWARM" block wordmark, painted top-to-bottom in an amber gradient
	// (bright crest → deep ember) that matches banner/hero.svg.
	lines := []string{
		"  ██████  ██     ██  █████  ██████  ███    ███",
		"  ██      ██     ██ ██   ██ ██   ██ ████  ████",
		"  ███████ ██  █  ██ ███████ ██████  ██ ████ ██",
		"       ██ ██ ███ ██ ██   ██ ██   ██ ██  ██  ██",
		"  ███████  ███ ███  ██   ██ ██   ██ ██      ██",
	}
	shades := []string{
		"38;2;255;213;128", // crest
		"38;2;245;166;35",  // amber
		"38;2;245;166;35",  // amber
		"38;2;214;140;36",  // ember
		"38;2;153;96;29",   // deep ember
	}
	fmt.Println()
	for i, ln := range lines {
		fmt.Printf("\033[%sm%s\033[0m\n", shades[i], ln)
	}
	fmt.Println("  " + colorMuted("PENTEST") + "  " + colorAmber("SWARM") + "  " + colorMuted("AI") +
		colorMuted("   ·   swarms of agents, one mission"))
}

func colorBold(s string) string    { return "\033[1m" + s + "\033[0m" }
func colorDim(s string) string     { return "\033[2m" + s + "\033[0m" }
func colorRed(s string) string     { return "\033[31m" + s + "\033[0m" }
func colorGreen(s string) string   { return "\033[32m" + s + "\033[0m" }
func colorYellow(s string) string  { return "\033[33m" + s + "\033[0m" }
func colorCyan(s string) string    { return "\033[36m" + s + "\033[0m" }
func colorMagenta(s string) string { return "\033[35m" + s + "\033[0m" }

// Brand truecolor (24-bit) accents — exact tokens from banner/hero.svg,
// so the terminal output matches the README identity regardless of the
// viewer's terminal theme.
func colorAmber(s string) string { return "\033[38;2;245;166;35m" + s + "\033[0m" }
func colorMuted(s string) string { return "\033[38;2;138;147;166m" + s + "\033[0m" }

func providerOrDefault(override, def string) string {
	if override != "" {
		return override
	}
	return def
}

func fallback(s, def string) string {
	if s == "" {
		return def
	}
	return s
}

// splitCSV splits a comma-separated flag value into a trimmed, non-empty
// slice. Returns nil for an empty string so downstream code can treat "unset"
// distinctly from an explicit list.
func splitCSV(s string) []string {
	var out []string
	for _, part := range strings.Split(s, ",") {
		if p := strings.TrimSpace(part); p != "" {
			out = append(out, p)
		}
	}
	return out
}

// promptForAPIKeyOnce is the first-run escape hatch: if a researcher runs
// 'pentestswarm scan …' before 'pentestswarm init', offer them one prompt
// to paste a key and (optionally) stash it in the keychain so future runs
// don't ask again. Ctrl-C or an empty line skips without writing anything.
// providerNeedsKey reports whether a provider authenticates with an API key
// (as opposed to a local endpoint like ollama/lmstudio, which need none).
func providerNeedsKey(provider string) bool {
	switch provider {
	case "claude", "together", "openai", "gemini", "orcarouter":
		return true
	default:
		return false
	}
}

// defaultObjective is the --objective default; mode only rewrites the
// objective when the user left it at this default (a custom objective wins).
const defaultObjective = "find all vulnerabilities"

// applyMode turns the campaign mode into concrete behavior. Modes are LLM-
// steered via the objective (the swarm pursues what the objective says), plus
// one hard toggle: ASM is surface-mapping only, so it turns active exploitation
// off. A user-set --objective or explicit --active-scan is always respected.
func applyMode(mode, objective string, activeScan, activeScanSet bool) (string, bool) {
	obj := objective
	if objective == defaultObjective { // only fill in the default
		switch mode {
		case "bugbounty":
			obj = "find and prove real, reportable vulnerabilities suitable for a bug-bounty submission — prioritize by severity, prove exploitability with evidence, and avoid duplicates"
		case "ctf":
			obj = "capture the flag: gain an initial foothold, escalate privileges, and locate flag values (e.g. flag{...} / user & root flags)"
		case "asm":
			obj = "map and inventory the attack surface — hosts, endpoints, technologies, and exposures — without exploiting anything"
		}
	}
	// ASM is reconnaissance-only: no active attack tools unless the operator
	// explicitly asked for them.
	if mode == "asm" && !activeScanSet {
		activeScan = false
	}
	return obj, activeScan
}

// modeSummary is a one-line human description of what a mode does, for the CLI
// banner and the launcher.
func modeSummary(mode string) string {
	switch mode {
	case "bugbounty":
		return "reportable, deduped, severity-ranked findings"
	case "ctf":
		return "foothold → privesc → capture flags"
	case "asm":
		return "attack-surface mapping only (no exploitation)"
	default:
		return "find and prove all vulnerabilities"
	}
}

func promptForAPIKeyOnce(provider string) string {
	label := providerKeyLabel(provider)
	fmt.Println()
	fmt.Println(colorYellow("  No "+label+" found.") + " Paste one to continue, or Ctrl-C to cancel.")
	fmt.Println(colorDim("  Tip: next time, run ") + colorCyan("pentestswarm init") + colorDim(" to set this up once and forget it."))
	fmt.Print("  " + colorCyan("api key> "))
	scanner := bufio.NewScanner(os.Stdin)
	key := ""
	if scanner.Scan() {
		key = strings.TrimSpace(scanner.Text())
	}
	if key == "" {
		return ""
	}
	// Only Claude has a dedicated OS-keychain slot today; for other
	// providers use the key for this run (config.yaml / env persist it).
	if provider == "claude" {
		fmt.Print("  Save to OS keychain so we don't ask again? [Y/n] ")
		answer := ""
		if scanner.Scan() {
			answer = strings.ToLower(strings.TrimSpace(scanner.Text()))
		}
		if answer == "" || answer == "y" || answer == "yes" {
			if err := keychain.Set(keychain.KeyClaudeAPI, key); err != nil {
				fmt.Printf("  %s couldn't save to keychain (%s) — using this run only.\n", colorYellow("[warn]"), err)
			} else {
				fmt.Printf("  %s stored in keychain\n", colorGreen("[ok]"))
			}
		}
	}
	return key
}

// providerKeyLabel names the key a provider expects, for prompts.
func providerKeyLabel(provider string) string {
	switch provider {
	case "claude":
		return "Anthropic Claude API key"
	case "together":
		return "Together AI API key"
	case "gemini":
		return "Google Gemini API key"
	case "orcarouter":
		return "OrcaRouter API key"
	default:
		return "API key"
	}
}

func init() {
	scanCmd.Flags().String("scope", "", "CIDR or domain scope, comma-separated (required)")
	scanCmd.Flags().Bool("lab", false, "spin up a bundled, legal vulnerable target and scan it — no target/scope needed")
	scanCmd.Flags().String("lab-target", "juiceshop", "which bundled lab to run with --lab: juiceshop (single Node app) | crapi (multi-container API mesh)")
	scanCmd.Flags().String("objective", "find all vulnerabilities", "what to find")
	scanCmd.Flags().String("mode", "manual", "manual|bugbounty|asm|ctf")
	scanCmd.Flags().String("provider", "", "claude|together|openai|gemini|ollama|lmstudio|orcarouter (overrides config; 'together' = hosted Llama/Qwen/DeepSeek via Together AI)")
	scanCmd.Flags().String("nuclei-severity", "critical,high,medium", "comma-separated nuclei severity filter; add low,info to surface config findings (missing headers, exposed docs) at the cost of a longer scan")
	scanCmd.Flags().Bool("active-scan", true, "for web targets, run the active attack tools (dalfox/sqlmap/nikto/ffuf) that probe for exploitable XSS/SQLi; set false for passive-only recon")
	scanCmd.Flags().Bool("dry-run", false, "show planned commands without executing")
	scanCmd.Flags().String("output", "./reports", "output directory for report")
	scanCmd.Flags().String("format", "md", "report format: md|html|json|sarif|all")
	scanCmd.Flags().Bool("follow", false, "stream live output (default when interactive)")
	scanCmd.Flags().Bool("strict", false, "abort on any LLM error instead of degrading to heuristics")
	scanCmd.Flags().Bool("swarm", false, "use the stigmergic swarm scheduler (experimental); default is the sequential 5-phase runner")
	scanCmd.Flags().Bool("dashboard", true, "with --swarm, serve a live web dashboard on localhost (agents, findings, graded report); --dashboard=false to disable")
	scanCmd.Flags().Bool("tui", false, "watch the campaign in a full-screen terminal dashboard (live agents, phases, findings, event log) instead of scrolling output")
	scanCmd.Flags().String("exploration-bias", "med", "swarm pheromone scaling: low|med|high (breadth-first = high, depth-first = low)")
	scanCmd.Flags().Bool("publish-unverified", false, "include suspected-but-not-reproduced findings in the report (aggressive mode)")
	scanCmd.Flags().Bool("estimate", false, "print expected LLM spend in USD and exit without scanning")
	scanCmd.Flags().Float64("budget", 0, "hard per-run spend cap in USD; the swarm winds down gracefully once cumulative LLM cost reaches it (0 = no cap)")
	scanCmd.Flags().Bool("demo", false, "offline demo: replay a real crAPI campaign (no network, no LLM, no key) into the TUI + dashboard — for talks where the wifi can't be trusted")
	scanCmd.Flags().String("target-class", "medium", "estimate sizing: small | medium | large")
	scanCmd.Flags().Bool("safe-mode", false, "block destructive tokens (rm/DROP/kill/chmod/...) before execution; required by programs that disallow automated scanning")
	scanCmd.Flags().Bool("assist", false, "ask y/N before every executed step (human-in-the-loop)")

	// Note: --scope is no longer marked required. When omitted, we default
	// to the target itself (4.8.5: simplicity). Researchers wanting a wider
	// scope (CIDR / wildcards / multiple domains) still pass --scope.

	rootCmd.AddCommand(scanCmd)
}
