package cli

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/cli/ui"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/config"
	livedash "github.com/Armur-Ai/Pentest-Swarm-AI/internal/dashboard"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/keychain"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/toolpath"
	"github.com/spf13/cobra"
	"golang.org/x/term"
)

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Interactive launcher — pick options and attack, no flags",
	Long: `Opens an interactive terminal UI: choose a target (a URL or a bundled
lab like crAPI), pick the scan mode, AI provider, and toggles, then launch.
A flag-free way to run the swarm — equivalent to 'pentestswarm scan …'.`,
	RunE: func(cmd *cobra.Command, _ []string) error { return launchInteractive() },
}

func init() {
	rootCmd.AddCommand(runCmd)
	// Bare `pentestswarm` in a terminal opens the launcher; otherwise (scripts,
	// pipes) it keeps printing help so nothing surprising happens in CI.
	rootCmd.RunE = func(cmd *cobra.Command, args []string) error {
		if len(args) == 0 && term.IsTerminal(int(os.Stdin.Fd())) {
			return launchInteractive()
		}
		return cmd.Help()
	}
}

// launchInteractive runs the TUI launcher, then hands the chosen configuration
// to the normal scan path (reusing all of runScan: config load, API-key
// resolution, lab boot, dashboard, and the swarm run).
func launchInteractive() error {
	if !term.IsTerminal(int(os.Stdin.Fd())) {
		return errors.New("the interactive launcher needs a terminal.\n  In scripts, use: " +
			colorCyan("pentestswarm scan <target> --scope <target> --swarm"))
	}

	def := ui.LaunchConfig{Mode: "manual", Swarm: true, ActiveScan: true, LiveView: "both"}
	// Together AI (hosted Llama/Qwen/DeepSeek) leads the list — the most
	// common "bring your own hosted open-weight model" choice.
	providers := []string{"together", "ollama", "claude", "openai", "gemini", "lmstudio", "orcarouter"}
	cfg, cfgErr := config.Load(cfgFile)
	if cfgErr == nil {
		if cfg.Orchestrator.Provider != "" {
			def.Provider = cfg.Orchestrator.Provider
		}
		def.KeyConfigured = anyAPIKeyAvailable(cfg)
	}
	// Start the live web dashboard NOW — before the launcher form — so
	// localhost:7777 is already serving the (empty) HUD while the user picks
	// options. runScan reuses this same server once the campaign launches,
	// and it fills in with data then. This is why the dashboard is up "as
	// soon as you run pentestswarm run", not only once the swarm starts.
	dashURL := ""
	if outDir, _ := scanCmd.Flags().GetString("output"); true {
		d := livedash.New(outDir)
		if url, derr := d.Start(); derr == nil {
			preStartedDashboard = d
			dashURL = url
			d.Publish(livedash.Event{Kind: "meta", Title: "awaiting launch", Detail: "configure the run in your terminal"})
			d.PublishStatus("idle")
		}
	}
	// Readiness is shown as an advisory panel INSIDE the launcher — the CLI
	// always starts; issues are surfaced as messages, never a hard failure.
	def.Status = launcherStatus(cfg, cfgErr)
	if dashURL != "" {
		def.Status = append(def.Status, ui.StatusItem{Label: "Dashboard", OK: true, Detail: "live now → " + dashURL})
	}

	choice, launched, err := ui.RunLauncher(providers, def)
	if err != nil {
		stopPreStartedDashboard()
		return err
	}
	if !launched {
		stopPreStartedDashboard()
		fmt.Println(colorDim("  cancelled."))
		return nil
	}

	// If the launcher collected a key, expose it to the scan path via the
	// env var it already reads (works for every key-based provider).
	if choice.APIKey != "" {
		_ = os.Setenv("PENTESTSWARM_ORCHESTRATOR_API_KEY", choice.APIKey)
	}

	// Translate the launcher choice into scan flags and reuse runScan.
	f := scanCmd.Flags()
	set := func(name, val string) { _ = f.Set(name, val) }
	set("mode", choice.Mode)
	set("provider", choice.Provider)
	set("swarm", strconv.FormatBool(choice.Swarm))
	set("active-scan", strconv.FormatBool(choice.ActiveScan))
	// Live view. The web dashboard (background HTTP server) and the terminal
	// TUI coexist, so "both" enables each.
	switch choice.LiveView {
	case "both":
		set("tui", "true")
		set("dashboard", "true")
	case "terminal":
		set("tui", "true")
		set("dashboard", "false")
	case "off":
		set("tui", "false")
		set("dashboard", "false")
	default: // "web"
		set("tui", "false")
		set("dashboard", "true")
	}
	if choice.BudgetUSD > 0 {
		set("budget", strconv.FormatFloat(choice.BudgetUSD, 'f', 2, 64))
	}
	set("follow", "true")
	set("format", "all")

	if choice.IsLab {
		set("lab", "true")
		set("lab-target", choice.Lab)
		return runScan(scanCmd, []string{})
	}

	if s := scopeFor(choice.Target); s != "" {
		set("scope", s)
	}
	return runScan(scanCmd, []string{choice.Target})
}

// stopPreStartedDashboard tears down the launcher-started dashboard when the
// run is cancelled before a campaign takes ownership of it.
func stopPreStartedDashboard() {
	if preStartedDashboard != nil {
		preStartedDashboard.Stop()
		preStartedDashboard = nil
	}
}

// scopeFor returns a sensible default scope for a target: loopback for a local
// target, otherwise empty (runScan then defaults scope to the target itself).
func scopeFor(target string) string {
	l := strings.ToLower(target)
	if strings.Contains(l, "localhost") || strings.Contains(l, "127.0.0.1") {
		return "127.0.0.1/32,localhost"
	}
	return ""
}

// launcherStatus builds the advisory readiness panel shown at the top of the
// interactive launcher. It is purely informational — nothing here can block
// the CLI from starting or prompt for input. Issues (Docker down, missing
// recon tools, no provider yet) are surfaced as in-UI messages, and the user
// can still launch: the scan degrades gracefully or the launcher collects
// what it needs (e.g. the API key). This is why the CLI "always starts."
func launcherStatus(cfg *config.Config, cfgErr error) []ui.StatusItem {
	items := make([]ui.StatusItem, 0, 4)

	_, goErr := exec.LookPath("go")
	items = append(items, ui.StatusItem{Label: "Go toolchain", OK: goErr == nil,
		Detail: pick(goErr == nil, "ready", "not found — installs of Go-based tools need it (go.dev/dl)")})

	dockerDetail, dockerOK := checkDocker()
	items = append(items, ui.StatusItem{Label: "Docker", OK: dockerOK,
		Detail: pick(dockerOK, dockerDetail, dockerDetail+" — only needed for --lab targets")})

	provOK := cfgErr == nil && hasAIProviderConfigured(cfg)
	items = append(items, ui.StatusItem{Label: "AI provider", OK: provOK,
		Detail: pick(provOK, "configured", "choose one below (paste a key, or pick a local model)")})

	missing := missingReconTools()
	if len(missing) == 0 {
		items = append(items, ui.StatusItem{Label: "Recon tools", OK: true, Detail: "httpx, nuclei, katana"})
	} else {
		items = append(items, ui.StatusItem{Label: "Recon tools", OK: false,
			Detail: "missing " + strings.Join(missing, ", ") + " · install: pentestswarm install-tools"})
	}
	return items
}

// pick returns a when cond is true, else b — a small ternary helper.
func pick(cond bool, a, b string) string {
	if cond {
		return a
	}
	return b
}

// anyAPIKeyAvailable reports whether an orchestrator API key can be found
// (config → env → keychain). Used to decide whether the launcher needs to
// prompt for one when a key-based provider is chosen.
func anyAPIKeyAvailable(cfg *config.Config) bool {
	if cfg.Orchestrator.APIKey != "" {
		return true
	}
	if os.Getenv("PENTESTSWARM_ORCHESTRATOR_API_KEY") != "" || os.Getenv("ANTHROPIC_API_KEY") != "" {
		return true
	}
	if key, err := keychain.Get(keychain.KeyClaudeAPI); err == nil && key != "" {
		return true
	}
	return false
}

// hasAIProviderConfigured mirrors the key-resolution order runScan uses
// (config → env → keychain) so the preflight check and the actual run
// never disagree about whether a key is set. Non-Claude providers (e.g.
// a local ollama) don't need an API key at all, so a configured provider
// name is sufficient for them.
func hasAIProviderConfigured(cfg *config.Config) bool {
	if cfg.Orchestrator.Provider == "" {
		return false
	}
	if cfg.Orchestrator.Provider != "claude" {
		return true
	}
	if cfg.Orchestrator.APIKey != "" {
		return true
	}
	if os.Getenv("PENTESTSWARM_ORCHESTRATOR_API_KEY") != "" || os.Getenv("ANTHROPIC_API_KEY") != "" {
		return true
	}
	if key, err := keychain.Get(keychain.KeyClaudeAPI); err == nil && key != "" {
		return true
	}
	return false
}

// missingReconTools reports which of the core recon binaries aren't
// resolvable via internal/toolpath (PATH plus our managed toolbin and
// the other well-known install locations).
func missingReconTools() []string {
	var missing []string
	for _, t := range []string{"httpx", "nuclei", "katana"} {
		if _, ok := toolpath.Resolve(t); !ok {
			missing = append(missing, t)
		}
	}
	return missing
}
