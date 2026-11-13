package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

const latestReleaseURL = "https://api.github.com/repos/Armur-Ai/Pentest-Swarm-AI/releases/latest"

var upgradeCmd = &cobra.Command{
	Use:   "upgrade",
	Short: "Check for a newer pentestswarm release",
	Long: `Checks GitHub for the latest Armur-Ai/Pentest-Swarm-AI release and
compares it against the running build.

This command only detects and instructs — it never replaces the running
binary itself, since the right upgrade command depends on how you
installed pentestswarm in the first place (go install, Homebrew, or a
manual binary download).`,
	Example: `  pentestswarm upgrade
  pentestswarm upgrade --json`,
	RunE: runUpgrade,
}

func init() {
	rootCmd.AddCommand(upgradeCmd)
}

// githubRelease is the subset of GitHub's release API response we care about.
type githubRelease struct {
	TagName string `json:"tag_name"`
	HTMLURL string `json:"html_url"`
}

// upgradeResult is the JSON shape for `pentestswarm upgrade --json`.
type upgradeResult struct {
	CurrentVersion  string `json:"current_version"`
	LatestVersion   string `json:"latest_version,omitempty"`
	UpdateAvailable bool   `json:"update_available"`
	CheckFailed     bool   `json:"check_failed,omitempty"`
	ReleaseURL      string `json:"release_url,omitempty"`
	Message         string `json:"message"`
}

func runUpgrade(cmd *cobra.Command, args []string) error {
	current, _, _ := buildVersionInfo()

	req, err := http.NewRequest(http.MethodGet, latestReleaseURL, nil)
	if err != nil {
		return fmt.Errorf("building request: %w", err)
	}
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("User-Agent", "pentestswarm-cli")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return printUpgradeResult(upgradeResult{
			CurrentVersion: current,
			CheckFailed:    true,
			Message:        fmt.Sprintf("could not reach GitHub: %v", err),
		})
	}
	defer resp.Body.Close()

	switch resp.StatusCode {
	case http.StatusOK:
		// fall through to decode below
	case http.StatusNotFound:
		return printUpgradeResult(upgradeResult{
			CurrentVersion: current,
			CheckFailed:    true,
			Message:        "no releases published yet for Armur-Ai/Pentest-Swarm-AI",
		})
	case http.StatusForbidden, http.StatusTooManyRequests:
		return printUpgradeResult(upgradeResult{
			CurrentVersion: current,
			CheckFailed:    true,
			Message:        "hit GitHub's API rate limit — try again later, or check https://github.com/Armur-Ai/Pentest-Swarm-AI/releases directly",
		})
	default:
		body, _ := io.ReadAll(resp.Body)
		return printUpgradeResult(upgradeResult{
			CurrentVersion: current,
			CheckFailed:    true,
			Message:        fmt.Sprintf("unexpected response from GitHub (%d): %s", resp.StatusCode, strings.TrimSpace(string(body))),
		})
	}

	var rel githubRelease
	if err := json.NewDecoder(resp.Body).Decode(&rel); err != nil {
		return printUpgradeResult(upgradeResult{
			CurrentVersion: current,
			CheckFailed:    true,
			Message:        fmt.Sprintf("could not parse GitHub response: %v", err),
		})
	}

	result := upgradeResult{
		CurrentVersion: current,
		LatestVersion:  rel.TagName,
		ReleaseURL:     rel.HTMLURL,
	}

	latest := strings.TrimPrefix(rel.TagName, "v")
	curNorm := strings.TrimPrefix(current, "v")

	switch {
	case current == "" || current == "dev":
		result.Message = "running a development build — can't compare versions; latest release is " + rel.TagName
	case curNorm == latest:
		result.Message = "you're already on the latest version (" + current + ")"
	default:
		result.UpdateAvailable = true
		result.Message = "a newer version is available: " + rel.TagName
	}

	return printUpgradeResult(result)
}

func printUpgradeResult(r upgradeResult) error {
	if OutputIsJSON() {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(r)
	}

	fmt.Printf("  %s %s\n", colorDim("current:"), colorBold(r.CurrentVersion))
	if r.LatestVersion != "" {
		fmt.Printf("  %s %s\n", colorDim("latest: "), colorBold(r.LatestVersion))
	}
	fmt.Println()

	switch {
	case r.CheckFailed:
		fmt.Println("  " + colorYellow(r.Message))
	case r.UpdateAvailable:
		fmt.Println("  " + colorYellow("A newer version is available.") + " Upgrade with whichever method you installed with:")
		fmt.Println()
		fmt.Println("    " + colorCyan("go install github.com/Armur-Ai/Pentest-Swarm-AI/cmd/pentestswarm@latest"))
		fmt.Println("    " + colorCyan("brew upgrade pentestswarm"))
		if r.ReleaseURL != "" {
			fmt.Println()
			fmt.Println("  release notes: " + colorDim(r.ReleaseURL))
		}
	default:
		fmt.Println("  " + colorGreen(r.Message))
	}
	return nil
}
