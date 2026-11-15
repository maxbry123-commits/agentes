package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/spf13/cobra"
	"github.com/spf13/cobra/doc"
)

var manDir string

var manCmd = &cobra.Command{
	Use:   "man",
	Short: "Generate man pages for the pentestswarm command tree",
	Long: `Generates a man page for pentestswarm and every subcommand into a
directory (default ./man). Point 'man -l' at a page to read it without
installing anything, or copy the pages into a directory on MANPATH to
install them system-wide.`,
	Example: `  pentestswarm man
  pentestswarm man --dir /usr/local/share/man/man1
  man -l ./man/pentestswarm.1`,
	RunE: runMan,
}

func init() {
	manCmd.Flags().StringVar(&manDir, "dir", "./man", "directory to write man pages into")
	rootCmd.AddCommand(manCmd)
}

// manResult is the JSON shape for `pentestswarm man --json`.
type manResult struct {
	Dir   string   `json:"dir"`
	Files []string `json:"files"`
}

func runMan(cmd *cobra.Command, args []string) error {
	if err := os.MkdirAll(manDir, 0o755); err != nil {
		return fmt.Errorf("creating %s: %w", manDir, err)
	}

	version, _, _ := buildVersionInfo()
	header := &doc.GenManHeader{
		Title:   "PENTESTSWARM",
		Section: "1",
		Source:  "pentestswarm " + version,
		Manual:  "Pentest Swarm AI",
	}

	if err := doc.GenManTree(rootCmd, header, manDir); err != nil {
		return fmt.Errorf("generating man pages: %w", err)
	}

	abs, err := filepath.Abs(manDir)
	if err != nil {
		abs = manDir
	}

	entries, err := os.ReadDir(abs)
	if err != nil {
		return fmt.Errorf("reading %s: %w", abs, err)
	}
	var files []string
	for _, e := range entries {
		if !e.IsDir() {
			files = append(files, e.Name())
		}
	}
	sort.Strings(files)

	if OutputIsJSON() {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(manResult{Dir: abs, Files: files})
	}

	fmt.Printf("  %s wrote %d man page(s) to %s\n", colorGreen("done."), len(files), colorBold(abs))
	fmt.Println()
	fmt.Println("  Read one without installing it:")
	fmt.Println("    " + colorCyan("man -l "+filepath.Join(abs, "pentestswarm.1")))
	fmt.Println()
	fmt.Println("  Or install system-wide (adjust the path for your platform):")
	fmt.Println("    " + colorCyan("sudo cp "+abs+"/*.1 /usr/local/share/man/man1/ && sudo mandb"))
	return nil
}
