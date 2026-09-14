package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var (
	cfgFile      string
	apiURL       string
	jsonOut      bool
	outputFormat string
	quiet        bool
	verbose      bool
)

// ExitCode is the process exit code Execute() will return once rootCmd's
// RunE completes without error. Commands that want to signal something
// beyond "it ran without error" (e.g. `scan` distinguishing a clean run
// from one that produced findings) set this before returning nil from
// their RunE.
//
// Convention (documented for `scan`): 0 = success/no findings,
// 1 = success with findings, 2 = error (a RunE that returns a non-nil
// error still exits 2, same as before this var existed — it's the
// unqualified "something went wrong" code). Commands that don't care
// about the distinction leave ExitCode at its zero value (0).
var ExitCode int

// OutputIsJSON reports whether the operator asked for machine-readable
// output, via either the original --json bool or the newer --output json.
// Commands that can render as JSON should check this once and branch.
func OutputIsJSON() bool {
	return jsonOut || outputFormat == "json"
}

// rootCmd is the base command. The Long description is deliberately
// short (4.8.2 — help must fit on one laptop screen).
var rootCmd = &cobra.Command{
	Use:   "pentestswarm",
	Short: "Autonomous AI-Powered Penetration Testing",
	Long:  `Swarms of AI agents autonomously pentest a target — recon, exploitation, reporting.`,
	CompletionOptions: cobra.CompletionOptions{
		HiddenDefaultCmd: true, // declutter the help output (4.8.2)
	},
}

// Execute runs the root command.
func Execute(version, commit, date string) {
	rootCmd.Version = fmt.Sprintf("%s (commit: %s, built: %s)", version, commit, date)

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default: ./config.yaml)")
	rootCmd.PersistentFlags().StringVar(&apiURL, "api", "http://localhost:8080", "API server URL")
	rootCmd.PersistentFlags().BoolVar(&jsonOut, "json", false, "output in JSON format")
	rootCmd.PersistentFlags().StringVar(&outputFormat, "output", "text", "output format: text|json (--json is a shorthand for --output json)")
	rootCmd.PersistentFlags().BoolVar(&quiet, "quiet", false, "suppress decorative output")
	rootCmd.PersistentFlags().BoolVar(&verbose, "verbose", false, "enable debug logging")
	rootCmd.PersistentFlags().BoolVarP(&assumeYes, "yes", "y", false, "assume yes to confirmation prompts (non-interactive)")

	if err := rootCmd.Execute(); err != nil {
		os.Exit(2)
	}
	os.Exit(ExitCode)
}
