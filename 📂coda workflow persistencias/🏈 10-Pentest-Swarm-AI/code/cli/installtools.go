package cli

import (
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/toolpath"
	"github.com/spf13/cobra"
)

// installToolsCmd is the "self-sufficient CLI" bootstrap: it makes
// pentestswarm work without the researcher ever manually running the
// Makefile's `tools` target or fiddling with PATH.
var installToolsCmd = &cobra.Command{
	Use:   "install-tools",
	Short: "Install the Go-based recon/scanning tool chain",
	Long: `Runs 'go install' for the core Go-based security tools (httpx, nuclei,
katana, subfinder, dnsx, naabu, gau, ffuf, gowitness) — the same list as
the repo Makefile's 'tools' target — into pentestswarm's own managed
tool directory. 'pentestswarm scan' finds them there automatically via
internal/toolpath, so no PATH edits are required.

Extras that need a package manager (nmap, sqlmap, semgrep, ...) aren't
installed by this command; run 'pentestswarm doctor' afterwards to see
what's still missing and how to get it.`,
	Example: `  pentestswarm install-tools`,
	RunE: func(cmd *cobra.Command, args []string) error {
		return runInstallTools()
	},
}

func init() {
	rootCmd.AddCommand(installToolsCmd)
}

// goTool is one entry in the Go-installable security tool chain.
type goTool struct {
	Name    string // the PATH binary name (matches toolprobe.Tool.Name)
	Package string // the 'go install <pkg>@latest' target
}

// goToolsList is the canonical Go-installable tool chain — kept in sync
// with the repo Makefile's 'tools' target so 'make tools',
// 'pentestswarm install-tools', and 'pentestswarm doctor --fix' never
// drift apart.
func goToolsList() []goTool {
	return []goTool{
		{Name: "httpx", Package: "github.com/projectdiscovery/httpx/cmd/httpx@latest"},
		{Name: "nuclei", Package: "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"},
		{Name: "katana", Package: "github.com/projectdiscovery/katana/cmd/katana@latest"},
		{Name: "subfinder", Package: "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"},
		{Name: "dnsx", Package: "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"},
		{Name: "naabu", Package: "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"},
		{Name: "gau", Package: "github.com/lc/gau/v2/cmd/gau@latest"},
		{Name: "ffuf", Package: "github.com/ffuf/ffuf/v2@latest"},
		{Name: "gowitness", Package: "github.com/sensepost/gowitness@latest"},
	}
}

// installGoTools installs the named tools (matched against goToolsList by
// binary name) via 'go install', with GOBIN pointed at pentestswarm's
// managed tool directory (toolpath.ManagedToolBinDir) rather than the
// default GOPATH/bin — so internal/toolpath (and therefore every
// internal/tools.IsCommandAvailable check) finds them without the
// researcher ever touching their shell PATH. An empty/nil names installs
// the full list.
//
// This is the single install routine shared by 'pentestswarm
// install-tools' and 'pentestswarm doctor --fix' so they can never
// disagree about where tools land.
//
// ran reports whether installation was even attempted: false means Go
// itself (or the managed directory) wasn't available and guidance was
// already printed to stdout — callers should treat that as a non-fatal
// no-op, not an error.
func installGoTools(names []string) (installed, failed []string, ran bool) {
	if _, err := exec.LookPath("go"); err != nil {
		fmt.Println("  " + colorRed("Go toolchain not found.") + " Installing tools needs 'go install'.")
		fmt.Println(colorDim("  Install Go from https://go.dev/dl/, then re-run: ") + colorCyan("pentestswarm install-tools"))
		return nil, nil, false
	}

	binDir, err := toolpath.ManagedToolBinDir()
	if err != nil {
		fmt.Printf("  %s preparing managed tool directory: %s\n", colorRed("✗"), err)
		return nil, nil, false
	}
	fmt.Println(colorDim("  installing into " + binDir))
	fmt.Println()

	all := goToolsList()
	selected := all
	if len(names) > 0 {
		want := make(map[string]bool, len(names))
		for _, n := range names {
			want[n] = true
		}
		selected = nil
		for _, t := range all {
			if want[t.Name] {
				selected = append(selected, t)
			}
		}
	}

	env := append(os.Environ(), "GOBIN="+binDir)
	for _, t := range selected {
		fmt.Printf("  %s %-10s %s\n", colorYellow("installing…"), t.Name, colorDim(t.Package))
		cmd := exec.Command("go", "install", t.Package)
		cmd.Env = env
		if runErr := cmd.Run(); runErr != nil {
			fmt.Printf("  %s %-10s %s\n", colorRed("✗"), t.Name, colorDim(runErr.Error()))
			failed = append(failed, t.Name)
			continue
		}
		fmt.Printf("  %s %-10s\n", colorGreen("✓"), t.Name)
		installed = append(installed, t.Name)
	}
	return installed, failed, true
}

// runInstallTools drives the 'pentestswarm install-tools' command:
// install the full Go tool chain and print a summary plus a pointer to
// the extras that need a package manager.
func runInstallTools() error {
	fmt.Println(colorBold("Installing Go-based security tools"))
	fmt.Println()

	installed, failed, ran := installGoTools(nil)
	if !ran {
		// Guidance already printed by installGoTools — nothing more to do,
		// and a missing optional toolchain shouldn't fail the CLI.
		return nil
	}

	fmt.Println()
	fmt.Printf("%d/%d tools installed\n", len(installed), len(installed)+len(failed))
	if len(failed) > 0 {
		fmt.Println("  " + colorRed("failed: ") + strings.Join(failed, ", "))
	}
	fmt.Println()
	fmt.Println(colorDim("Extras that need a package manager (not installed by this command):"))
	fmt.Println(colorDim("  brew install nmap sqlmap amass gobuster trufflehog gitleaks"))
	fmt.Println(colorDim("  pip install semgrep"))
	fmt.Println(colorDim("Then run ") + colorCyan("pentestswarm doctor") + colorDim(" to verify everything is wired up."))
	return nil
}
