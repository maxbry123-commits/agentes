package cli

import (
	"context"
	"fmt"
	"os"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/keychain"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/importer"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/importer/bugcrowd"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/importer/hackerone"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope/importer/intigriti"
	"github.com/spf13/cobra"
	"go.yaml.in/yaml/v3"
)

var scopeDiffCmd = &cobra.Command{
	Use:   "diff <prev.yaml> <current.yaml>",
	Short: "Diff two scope files — what assets were added or removed",
	Long: `Reports the set-difference between two scope.yaml files. Useful for
cron-driven ASM runs: re-import the program's scope every day, diff
against yesterday's file, scan only the new assets.

Exit code 0 = identical, 1 = changes found. Fits shell pipelines.`,
	Args: cobra.ExactArgs(2),
	Example: `  pentestswarm scope diff yesterday.yaml today.yaml
  pentestswarm scope diff yesterday.yaml today.yaml --json`,
	RunE: runScopeDiff,
}

func runScopeDiff(cmd *cobra.Command, args []string) error {
	prev, err := readScope(args[0])
	if err != nil {
		return err
	}
	cur, err := readScope(args[1])
	if err != nil {
		return err
	}
	d := scope.Compare(*prev, *cur)

	if asJSON, _ := cmd.Flags().GetBool("json"); asJSON {
		buf, _ := yaml.Marshal(d)
		fmt.Print(string(buf))
	} else {
		renderDiff(d)
	}
	if d.HasChanges() {
		// Non-zero exit signals "scope changed" to shell pipelines.
		return fmt.Errorf("scope changed")
	}
	return nil
}

func readScope(path string) (*scope.ScopeDefinition, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	var def scope.ScopeDefinition
	if err := yaml.Unmarshal(data, &def); err != nil {
		return nil, fmt.Errorf("parse %s: %w", path, err)
	}
	return &def, nil
}

func renderDiff(d scope.Diff) {
	if !d.HasChanges() {
		fmt.Println("  " + colorGreen("[ok]") + " scope unchanged")
		return
	}
	for _, added := range d.AddedDomains {
		fmt.Printf("  %s %s\n", colorGreen("+"), added)
	}
	for _, added := range d.AddedCIDRs {
		fmt.Printf("  %s %s\n", colorGreen("+"), added)
	}
	for _, removed := range d.RemovedDomains {
		fmt.Printf("  %s %s\n", colorRed("-"), removed)
	}
	for _, removed := range d.RemovedCIDRs {
		fmt.Printf("  %s %s\n", colorRed("-"), removed)
	}
	fmt.Printf("\n  %d unchanged, %d added, %d removed\n",
		d.Unchanged,
		len(d.AddedDomains)+len(d.AddedCIDRs),
		len(d.RemovedDomains)+len(d.RemovedCIDRs))
}

var scopeCmd = &cobra.Command{
	Use:   "scope",
	Short: "Manage bug-bounty program scope — import, diff, validate",
}

var scopeImportCmd = &cobra.Command{
	Use:   "import <platform> <program-slug>",
	Short: "Import scope from a bug-bounty platform",
	Long: `Pulls the in-scope asset list for a program from the named platform
and writes it to scope.yaml (or the path given by --out).

Platforms: h1 | bugcrowd | intigriti

Tokens come from the OS keychain (see 'pentestswarm init' and
'pentestswarm scope login'). Falls back to HACKERONE_* /
BUGCROWD_API_TOKEN / INTIGRITI_API_TOKEN env vars for CI.`,
	Args: cobra.ExactArgs(2),
	Example: `  pentestswarm scope import h1 shopify
  pentestswarm scope import bugcrowd tesla --out /tmp/tesla.yaml
  pentestswarm scope import intigriti acme-corp`,
	RunE: runScopeImport,
}

func runScopeImport(cmd *cobra.Command, args []string) error {
	platform := args[0]
	slug := args[1]
	outPath, _ := cmd.Flags().GetString("out")
	if outPath == "" {
		outPath = "scope.yaml"
	}

	imp, err := buildImporter(platform)
	if err != nil {
		return err
	}
	fmt.Printf("  %s importing %s/%s ...\n", colorCyan("[scope]"), platform, slug)
	def, err := imp.Import(context.Background(), slug)
	if err != nil {
		return fmt.Errorf("import: %w", err)
	}

	buf, err := yaml.Marshal(def)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	if err := os.WriteFile(outPath, buf, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", outPath, err)
	}

	fmt.Printf("  %s wrote %d domains + %d CIDRs to %s\n",
		colorGreen("[ok]"),
		len(def.AllowedDomains), len(def.AllowedCIDRs),
		colorCyan(outPath))
	fmt.Println()
	fmt.Println("  Next:")
	fmt.Printf("    %s\n", colorCyan("pentestswarm scan "+firstHost(def.AllowedDomains)+" --scope "+outPath+" --swarm"))
	return nil
}

// buildImporter returns the right Importer for a platform slug + auth.
// Auth order matches the scan command's API key resolution: env first
// (CI-friendly), then OS keychain (what 'init' stashes to).
func buildImporter(platform string) (importer.Importer, error) {
	switch platform {
	case "h1", "hackerone":
		user := os.Getenv("HACKERONE_API_USER")
		token := os.Getenv("HACKERONE_API_TOKEN")
		if token == "" {
			if v, err := keychain.Get(keychain.KeyHackerOneToken); err == nil {
				token = v
			}
		}
		return hackerone.NewClient(hackerone.Config{APIUser: user, APIToken: token}), nil

	case "bugcrowd":
		token := os.Getenv("BUGCROWD_API_TOKEN")
		if token == "" {
			if v, err := keychain.Get(keychain.KeyBugcrowdToken); err == nil {
				token = v
			}
		}
		return bugcrowd.NewClient(bugcrowd.Config{Token: token}), nil

	case "intigriti":
		token := os.Getenv("INTIGRITI_API_TOKEN")
		if token == "" {
			if v, err := keychain.Get(keychain.KeyIntigritiToken); err == nil {
				token = v
			}
		}
		return intigriti.NewClient(intigriti.Config{Token: token}), nil

	default:
		return nil, fmt.Errorf("unknown platform %q — use h1, bugcrowd, or intigriti", platform)
	}
}

func firstHost(domains []string) string {
	if len(domains) > 0 {
		return domains[0]
	}
	return "example.com"
}

func init() {
	scopeImportCmd.Flags().String("out", "scope.yaml", "output scope file path")
	scopeDiffCmd.Flags().Bool("json", false, "emit diff as JSON for pipelines")
	scopeCmd.AddCommand(scopeImportCmd)
	scopeCmd.AddCommand(scopeDiffCmd)
	rootCmd.AddCommand(scopeCmd)
}
