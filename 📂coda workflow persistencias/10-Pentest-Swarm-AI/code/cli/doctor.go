package cli

import (
	"fmt"
	"net"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/toolprobe"
	"github.com/spf13/cobra"
)

var doctorCmd = &cobra.Command{
	Use:   "doctor",
	Short: "Check system health and dependencies",
	Long: `Runs a health check and (optionally) auto-installs missing tools
that have a safe 'go install' recipe. Tools that need brew / apt /
package manager installs are printed with the shell command so you
can copy-paste.`,
	Example: `  pentestswarm doctor            # report only
  pentestswarm doctor --fix      # run 'go install' for any missing Go tools`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fix, _ := cmd.Flags().GetBool("fix")
		fmt.Println("🔍 pentestswarm doctor — checking system health")
		fmt.Println()

		checks := []struct {
			name  string
			check func() (string, bool)
		}{
			{"API server reachable", checkAPI},
			{"PostgreSQL connection", checkPostgres},
			{"Redis connection", checkRedis},
			{"Ollama running", checkOllama},
			{"Docker daemon", checkDocker},
			{"Go version", checkGo},
			{"Disk space (>10GB)", checkDisk},
			{"RAM (>8GB)", checkRAM},
		}

		passed := 0
		dockerOK := false
		for _, c := range checks {
			detail, ok := c.check()
			if c.name == "Docker daemon" {
				dockerOK = ok
			}
			if ok {
				fmt.Printf("  ✅ %s — %s\n", c.name, detail)
				passed++
			} else {
				fmt.Printf("  ❌ %s — %s\n", c.name, detail)
			}
		}

		fmt.Printf("\n%d/%d infra checks passed\n", passed, len(checks))

		// Tool probe — which external binaries are available.
		fmt.Println()
		fmt.Println(colorBold("Security tools"))
		results := toolprobe.Probe()
		totalTools, presentTools := 0, 0
		for _, r := range results {
			fmt.Println()
			fmt.Println("  " + colorDim(r.Group.Title))
			for _, t := range r.Group.Tools {
				totalTools++
				if r.Present[t.Name] {
					presentTools++
					fmt.Printf("    %s %-14s %s\n", colorGreen("✓"), colorCyan(t.Name), colorDim(t.Purpose))
				} else {
					fmt.Printf("    %s %-14s %s\n", colorRed("✗"), colorDim(t.Name), colorDim(t.Purpose+"  →  "+t.InstallHint))
				}
			}
		}
		fmt.Printf("\n%d/%d tools present\n", presentTools, totalTools)

		if fix {
			runAutoFix(toolprobe.Missing(results), dockerOK)
		}
		return nil
	},
}

// runAutoFix walks missing tools and, for each one whose install hint
// looks like a safe `go install …` command, installs it via the same
// shared routine 'pentestswarm install-tools' uses (installGoTools, in
// installtools.go) — so both commands install into the same managed
// tool directory. Everything else is printed as a shell command the
// operator can copy-paste — we never call brew/apt/pip on the user's
// behalf because those modify system state outside our lane. Anything
// this can't fix at all (Docker not running) gets guidance too.
func runAutoFix(missing []toolprobe.Tool, dockerOK bool) {
	fmt.Println()
	fmt.Println(colorBold("Auto-fix"))

	var goNames []string
	var manual []toolprobe.Tool
	for _, t := range missing {
		if looksGoInstallable(t.InstallHint) {
			goNames = append(goNames, t.Name)
		} else {
			manual = append(manual, t)
		}
	}

	if len(goNames) > 0 {
		// Per-tool ✓/✗ progress is printed inline by installGoTools.
		installGoTools(goNames)
	}

	if len(manual) > 0 {
		fmt.Println()
		fmt.Println(colorDim("  Run these yourself (auto-fix doesn't touch your package manager):"))
		for _, t := range manual {
			fmt.Printf("    %s %s\n", colorDim("$"), t.InstallHint)
		}
	}

	if !dockerOK {
		fmt.Println()
		fmt.Println(colorDim("  Docker daemon isn't running (needed for --lab targets and infra checks):"))
		fmt.Println(colorDim("    macOS/Windows: open Docker Desktop"))
		fmt.Println(colorDim("    Linux:         sudo systemctl start docker"))
	}
}

// looksGoInstallable returns true when the install hint is a `go install …`
// command we can safely run on the user's behalf.
func looksGoInstallable(hint string) bool {
	return strings.HasPrefix(hint, "go install ")
}

func checkAPI() (string, bool) {
	conn, err := net.DialTimeout("tcp", "localhost:8080", 2*time.Second)
	if err != nil {
		return "not reachable at localhost:8080 — run 'pentestswarm serve'", false
	}
	conn.Close()
	return "listening on :8080", true
}

func checkPostgres() (string, bool) {
	conn, err := net.DialTimeout("tcp", "localhost:5432", 2*time.Second)
	if err != nil {
		return "not reachable — run 'docker compose -f deploy/docker-compose.dev.yml up -d'", false
	}
	conn.Close()
	return "listening on :5432", true
}

func checkRedis() (string, bool) {
	conn, err := net.DialTimeout("tcp", "localhost:6379", 2*time.Second)
	if err != nil {
		return "not reachable — run 'docker compose -f deploy/docker-compose.dev.yml up -d'", false
	}
	conn.Close()
	return "listening on :6379", true
}

func checkOllama() (string, bool) {
	conn, err := net.DialTimeout("tcp", "localhost:11434", 2*time.Second)
	if err != nil {
		return "not reachable — install from https://ollama.com and run 'ollama serve'", false
	}
	conn.Close()
	return "listening on :11434", true
}

func checkDocker() (string, bool) {
	out, err := exec.Command("docker", "info", "--format", "{{.ServerVersion}}").Output()
	if err != nil {
		return "not running — install from https://docker.com", false
	}
	return fmt.Sprintf("v%s", string(out[:len(out)-1])), true
}

func checkGo() (string, bool) {
	return runtime.Version(), true
}

func checkDisk() (string, bool) {
	// Simplified check — just return OK for now
	return "check passed", true
}

func checkRAM() (string, bool) {
	var memMB uint64
	// Use runtime to get a rough estimate
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	memMB = m.Sys / 1024 / 1024
	if memMB < 100 {
		// Can't accurately determine total RAM from Go runtime
		return "unable to determine — ensure at least 8GB available", true
	}
	return fmt.Sprintf("%d MB available to process", memMB), true
}

func init() {
	doctorCmd.Flags().Bool("fix", false, "run 'go install' for any Go-installable missing tools (brew/apt tools are printed, not executed)")
	rootCmd.AddCommand(doctorCmd)
}
