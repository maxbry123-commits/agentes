package cli

import (
	"fmt"
	"os/exec"
	"runtime"

	"github.com/spf13/cobra"
)

// docsURL is the published documentation site (GitHub Pages).
const docsURL = "https://armur-ai.github.io/Pentest-Swarm-AI/"

var docsPrint bool

var docsCmd = &cobra.Command{
	Use:   "docs",
	Short: "Open the documentation site in your browser",
	Long: `Opens the Pentest Swarm AI documentation site in your default browser:
quickstart, provider setup, CLI reference, playbooks, and troubleshooting.

Use --print to just print the URL (e.g. on a headless box or to copy it).`,
	Example: `  pentestswarm docs
  pentestswarm docs --print`,
	RunE: func(cmd *cobra.Command, _ []string) error {
		if docsPrint {
			fmt.Println(docsURL)
			return nil
		}
		if err := openBrowser(docsURL); err != nil {
			// Never hard-fail just because we couldn't spawn a browser
			// (headless, no DISPLAY, sandboxed) — print the URL instead.
			fmt.Printf("  Open the docs at: %s\n", colorCyan(docsURL))
			return nil
		}
		fmt.Printf("  Opening docs → %s\n", colorCyan(docsURL))
		return nil
	},
}

func init() {
	docsCmd.Flags().BoolVar(&docsPrint, "print", false, "print the docs URL instead of opening a browser")
	rootCmd.AddCommand(docsCmd)
}

// openBrowser opens url in the OS default browser.
func openBrowser(url string) error {
	var cmd string
	var args []string
	switch runtime.GOOS {
	case "darwin":
		cmd = "open"
	case "windows":
		cmd = "rundll32"
		args = []string{"url.dll,FileProtocolHandler"}
	default: // linux, *bsd
		cmd = "xdg-open"
	}
	args = append(args, url)
	return exec.Command(cmd, args...).Start()
}
