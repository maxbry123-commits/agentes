package cli

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/keychain"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/importer/hackerone"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/programterms"
	"github.com/spf13/cobra"
	"go.yaml.in/yaml/v3"
)

var programCmd = &cobra.Command{
	Use:   "program",
	Short: "Inspect bug-bounty program rules-of-engagement",
}

var programInspectCmd = &cobra.Command{
	Use:   "inspect <platform>:<slug>",
	Short: "Pull a program's policy text and print extracted constraints",
	Long: `Fetches the program's published rules-of-engagement and runs the
heuristic parser over it. Prints rate limits, banned techniques,
required headers, and disallowed paths.

Use --yaml to emit a config fragment that can be merged into a scan
config file (so 'no automated scanning' programs auto-enable safe-mode,
rate limits propagate, etc.).`,
	Args: cobra.ExactArgs(1),
	Example: `  pentestswarm program inspect h1:shopify
  pentestswarm program inspect h1:gitlab --yaml > program-config.yaml`,
	RunE: runProgramInspect,
}

func runProgramInspect(cmd *cobra.Command, args []string) error {
	platform, slug, ok := strings.Cut(args[0], ":")
	if !ok {
		return fmt.Errorf("expected <platform>:<slug>, got %q", args[0])
	}

	policy, err := fetchPolicy(platform, slug)
	if err != nil {
		return err
	}

	c := programterms.Parse(policy)

	if asYAML, _ := cmd.Flags().GetBool("yaml"); asYAML {
		buf, _ := yaml.Marshal(c)
		fmt.Print(string(buf))
		return nil
	}

	renderConstraints(platform, slug, c)
	return nil
}

func fetchPolicy(platform, slug string) (string, error) {
	switch platform {
	case "h1", "hackerone":
		user := os.Getenv("HACKERONE_API_USER")
		token := os.Getenv("HACKERONE_API_TOKEN")
		if token == "" {
			if v, err := keychain.Get(keychain.KeyHackerOneToken); err == nil {
				token = v
			}
		}
		client := hackerone.NewClient(hackerone.Config{APIUser: user, APIToken: token})
		return client.Policy(context.Background(), slug)
	default:
		// Bugcrowd / Intigriti expose policy via web pages, not API — punt
		// for now and surface a clear error so users see why it didn't work.
		return "", fmt.Errorf("policy fetch for %q is not yet implemented (h1 only)", platform)
	}
}

func renderConstraints(platform, slug string, c programterms.Constraints) {
	fmt.Printf("\n  %s %s/%s\n", colorCyan("[program]"), platform, slug)
	fmt.Println(colorDim("  ─────────────────────────────────────────────"))

	bool2 := func(label string, v bool) {
		mark := colorGreen("ok")
		if v {
			mark = colorRed("FORBIDDEN")
		}
		fmt.Printf("  %-22s %s\n", label, mark)
	}
	bool2("Automated scanning", c.NoAutomatedScanning)
	bool2("Brute force", c.NoBruteForce)
	bool2("Denial of service", c.NoDoS)
	bool2("Social engineering", c.NoSocialEngineering)
	bool2("Physical security", c.NoPhysical)

	if c.MaxRequestsPerSecond > 0 {
		fmt.Printf("  %-22s %s\n", "Max RPS", colorYellow(fmt.Sprintf("%.2f", c.MaxRequestsPerSecond)))
	} else {
		fmt.Printf("  %-22s %s\n", "Max RPS", colorDim("not specified"))
	}

	if len(c.RequiredHeaders) > 0 {
		fmt.Println("\n  Required headers:")
		for k, v := range c.RequiredHeaders {
			fmt.Printf("    %s: %s\n", colorCyan(k), v)
		}
	}

	if len(c.DisallowedPaths) > 0 {
		fmt.Println("\n  Disallowed paths:")
		for _, p := range c.DisallowedPaths {
			fmt.Printf("    %s %s\n", colorRed("-"), p)
		}
	}

	fmt.Println()
	if c.NoAutomatedScanning {
		fmt.Printf("  %s This program forbids automated scanning. Re-run with %s.\n",
			colorYellow("[advisory]"),
			colorCyan("--safe-mode"))
	}
}

func init() {
	programInspectCmd.Flags().Bool("yaml", false, "emit constraints as YAML for shell pipelines")
	programCmd.AddCommand(programInspectCmd)
	rootCmd.AddCommand(programCmd)
}
