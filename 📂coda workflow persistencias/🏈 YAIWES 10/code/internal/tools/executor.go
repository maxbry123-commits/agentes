package tools

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/toolpath"
)

// RunCommand executes a shell command and returns the output.
// This is the fallback for tools not available as Go libraries.
func RunCommand(ctx context.Context, name string, args ...string) (string, error) {
	return RunCommandWithStdin(ctx, "", name, args...)
}

// RunCommandWithStdin executes a shell command with the given stdin
// payload (set to "" if the tool doesn't read stdin). Used by adapters
// such as dnsx and httpx that batch-process targets piped on stdin.
func RunCommandWithStdin(ctx context.Context, stdin, name string, args ...string) (string, error) {
	// Resolve the binary via toolpath's augmented search (GOBIN,
	// GOPATH/bin, our managed toolbin, common Homebrew/system
	// prefixes, ...) instead of relying solely on the process's PATH.
	// This is what lets the swarm find tools like httpx/nuclei right
	// after `go install` or `pentestswarm install-tools`, even when
	// the user never added that directory to their shell PATH. Fall
	// back to the bare name if we can't resolve it -- exec still
	// tries PATH itself and produces the usual "not found" error.
	binary := name
	if resolved, ok := toolpath.Resolve(name); ok {
		binary = resolved
	}

	cmd := exec.CommandContext(ctx, binary, args...)
	// Give the child process the same augmented PATH, in case it
	// shells out to other tools internally (e.g. testssl.sh calling
	// openssl).
	cmd.Env = append(os.Environ(), "PATH="+toolpath.AugmentedPATH())

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if stdin != "" {
		cmd.Stdin = bytes.NewReader([]byte(stdin))
	}

	err := cmd.Run()
	if err != nil {
		// Include stderr in error for debugging
		if stderr.Len() > 0 {
			return stdout.String(), fmt.Errorf("%s: %w (stderr: %s)", name, err, stderr.String())
		}
		return stdout.String(), fmt.Errorf("%s: %w", name, err)
	}

	return stdout.String(), nil
}

// IsCommandAvailable checks if a command exists, searching both PATH
// and toolpath's augmented candidate directories (GOBIN, GOPATH/bin,
// the managed toolbin, common install prefixes, ...). Every adapter's
// IsAvailable() goes through this, so a tool installed via
// `go install` or `pentestswarm install-tools` is found regardless of
// whether its directory made it onto the user's shell PATH.
func IsCommandAvailable(name string) bool {
	_, ok := toolpath.Resolve(name)
	return ok
}

// RunToolCommand runs a security tool with timeout and returns a ToolResult.
func RunToolCommand(ctx context.Context, toolName, target string, timeout time.Duration, cmdName string, args ...string) *ToolResult {
	return RunToolCommandWithStdin(ctx, toolName, target, "", timeout, cmdName, args...)
}

// RunToolCommandWithStdin is the stdin-aware variant of RunToolCommand.
// Used by adapters like dnsx where the binary expects targets piped in
// via stdin rather than passed as flags.
func RunToolCommandWithStdin(ctx context.Context, toolName, target, stdin string, timeout time.Duration, cmdName string, args ...string) *ToolResult {
	start := time.Now()

	if timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, timeout)
		defer cancel()
	}

	output, err := RunCommandWithStdin(ctx, stdin, cmdName, args...)

	result := &ToolResult{
		ToolName: toolName,
		Target:   target,
		Duration: time.Since(start),
	}

	if err != nil {
		result.Error = err
		result.RawOutput = output // may have partial output
		return result
	}

	result.RawOutput = output

	// Try to parse JSON lines from output
	result.ParsedFindings = parseJSONLines(output)

	return result
}

// parseJSONLines extracts JSON objects from newline-delimited output.
//
// Tools like httpx, naabu, dnsx, katana emit one JSON object per line. We
// json.Unmarshal each line into a generic map so downstream consumers
// (MergeToolResults, classifier) can read structured fields like "tech",
// "host", "url", "port" directly. Lines that fail to parse are kept as
// {"raw": <line>} so callers that only care about raw text still see
// something — this preserves backward-compatible behavior for tools
// whose output isn't strictly JSONL.
func parseJSONLines(output string) []map[string]any {
	var findings []map[string]any
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || line[0] != '{' {
			continue
		}
		var obj map[string]any
		if err := json.Unmarshal([]byte(line), &obj); err != nil {
			findings = append(findings, map[string]any{"raw": line})
			continue
		}
		findings = append(findings, obj)
	}
	return findings
}
