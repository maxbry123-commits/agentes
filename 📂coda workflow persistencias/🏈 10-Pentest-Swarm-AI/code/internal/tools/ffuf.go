package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/scope"
)

// FfufTool wraps ffuf for content discovery and parameter fuzzing.
// Output is streamed to a temp file in JSON mode, then parsed into
// structured findings. The FUZZ keyword can appear in the URL, in
// headers, or (via opts) in body parameters.
type FfufTool struct{}

// NewFfufTool constructs the adapter.
func NewFfufTool() *FfufTool { return &FfufTool{} }

// Name implements Tool.
func (f *FfufTool) Name() string { return "ffuf" }

// IsAvailable implements Tool.
func (f *FfufTool) IsAvailable() bool { return IsCommandAvailable("ffuf") }

// Run executes ffuf with sensible defaults: wordlist required (opts["wordlist"]),
// 40 threads, follow redirects, match 200/204/301/302/307/401/403.
func (f *FfufTool) Run(ctx context.Context, target string, opts Options) (*ToolResult, error) {
	if scopeDef := getScopeFromContext(ctx); scopeDef != nil {
		if err := scope.ValidateAndLog("ffuf", target, *scopeDef); err != nil {
			return nil, fmt.Errorf("scope violation in ffuf: %w", err)
		}
	}

	wordlist := opts.GetString("wordlist", "/usr/share/seclists/Discovery/Web-Content/common.txt")
	threads := opts.GetInt("threads", 40)
	timeout := time.Duration(opts.GetInt("timeout", 300)) * time.Second
	matchCodes := opts.GetString("match_codes", "200,204,301,302,307,401,403")

	outFile, err := os.CreateTemp("", "ffuf-*.json")
	if err != nil {
		return nil, fmt.Errorf("ffuf tmpfile: %w", err)
	}
	outFile.Close()
	defer os.Remove(outFile.Name())

	// ffuf expects FUZZ in the URL. If the caller didn't include it,
	// append /FUZZ so the adapter works with a bare hostname too.
	u := target
	if !strings.Contains(u, "FUZZ") {
		u = strings.TrimRight(u, "/") + "/FUZZ"
	}

	args := []string{
		"-u", u,
		"-w", wordlist,
		"-t", fmt.Sprintf("%d", threads),
		"-mc", matchCodes,
		"-of", "json",
		"-o", outFile.Name(),
		"-s", // silent mode — only write to file
	}
	result := RunToolCommand(ctx, f.Name(), target, timeout, "ffuf", args...)
	if result.Error != nil {
		return result, result.Error
	}

	data, err := os.ReadFile(outFile.Name())
	if err != nil {
		return result, nil
	}
	var parsed struct {
		Results []map[string]any `json:"results"`
	}
	if err := json.Unmarshal(data, &parsed); err == nil {
		result.ParsedFindings = parsed.Results
	}
	return result, nil
}
