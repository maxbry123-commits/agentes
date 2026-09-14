package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"strings"

	"github.com/spf13/cobra"
)

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version, build, and runtime information",
	Long: `Prints the pentestswarm version along with the commit it was built
from, the build date, the Go toolchain version it was compiled with, and
the current OS/architecture.`,
	Example: `  pentestswarm version
  pentestswarm version --json`,
	RunE: runVersion,
}

func init() {
	rootCmd.AddCommand(versionCmd)
}

// versionInfo is the JSON shape for `pentestswarm version --json`.
type versionInfo struct {
	Version   string `json:"version"`
	Commit    string `json:"commit"`
	BuildDate string `json:"build_date"`
	GoVersion string `json:"go_version"`
	OS        string `json:"os"`
	Arch      string `json:"arch"`
}

func runVersion(cmd *cobra.Command, args []string) error {
	version, commit, date := buildVersionInfo()
	info := versionInfo{
		Version:   version,
		Commit:    commit,
		BuildDate: date,
		GoVersion: runtime.Version(),
		OS:        runtime.GOOS,
		Arch:      runtime.GOARCH,
	}

	if OutputIsJSON() {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(info)
	}

	fmt.Printf("  %s %s\n", colorBold("pentestswarm"), colorCyan(info.Version))
	fmt.Printf("    %s %s\n", colorDim("commit:"), info.Commit)
	fmt.Printf("    %s %s\n", colorDim("built:"), info.BuildDate)
	fmt.Printf("    %s %s\n", colorDim("go:"), info.GoVersion)
	fmt.Printf("    %s %s/%s\n", colorDim("os/arch:"), info.OS, info.Arch)
	return nil
}

// buildVersionInfo splits rootCmd.Version — set by Execute() as
// "<version> (commit: <commit>, built: <date>)" — back into its parts, so
// other commands (upgrade, version --json, man) can report the pieces
// individually without Execute needing to stash them anywhere else.
func buildVersionInfo() (version, commit, date string) {
	version, commit, date = "dev", "none", "unknown"

	v := strings.TrimSpace(rootCmd.Version)
	if v == "" {
		return
	}

	idx := strings.Index(v, " (")
	if idx < 0 || !strings.HasSuffix(v, ")") {
		version = v
		return
	}

	version = v[:idx]
	rest := strings.TrimSuffix(v[idx+len(" ("):], ")")
	for _, part := range strings.Split(rest, ", ") {
		switch {
		case strings.HasPrefix(part, "commit: "):
			commit = strings.TrimPrefix(part, "commit: ")
		case strings.HasPrefix(part, "built: "):
			date = strings.TrimPrefix(part, "built: ")
		}
	}
	return
}
