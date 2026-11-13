// Package toolpath makes pentestswarm self-sufficient at finding the
// external security binaries it shells out to (httpx, nuclei, ffuf, ...)
// without requiring the user to add GOPATH/bin (or anything else) to
// their shell PATH.
//
// The #1 source of "tool not found" confusion for a freshly
// `go install`'d toolchain is that `go install` drops binaries into
// $GOBIN or $GOPATH/bin, and that directory is very often not on the
// user's PATH. This package builds an ordered list of "the places we
// know our tools could be" (see CandidateDirs) and searches it in
// addition to whatever PATH the process was started with, so both
// tool-presence checks (`pentestswarm doctor`) and actual tool
// execution (internal/tools) find binaries reliably.
package toolpath

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// managedSubdir is where `pentestswarm install-tools` installs its own
// copy of the Go-based security toolchain, relative to the user's
// config dir (os.UserConfigDir() — e.g. ~/Library/Application
// Support on macOS, ~/.config on Linux). Centralizing the path here
// means the CLI, doctor, and tool-execution path all agree on where
// to look.
const managedSubdir = "pentestswarm/tools"

// ManagedToolBinDir returns the directory `pentestswarm install-tools`
// installs into, creating it if it doesn't already exist. Use this
// when you're about to write into the directory; read-only lookups
// (Resolve, CandidateDirs) use the non-creating variant so a simple
// tool-presence check never has the side effect of creating
// directories.
func ManagedToolBinDir() (string, error) {
	dir, err := managedToolBinDirPath()
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	return dir, nil
}

// managedToolBinDirPath computes the managed toolbin path without
// creating it.
func managedToolBinDirPath() (string, error) {
	base, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, managedSubdir), nil
}

// CandidateDirs returns the ordered list of directories pentestswarm
// searches for security-tool binaries, independent of the invoking
// shell's PATH. First match wins when Resolve walks this list.
//
// Order:
//  1. `go env GOBIN`        — explicit GOBIN override, if set
//  2. `go env GOPATH`/bin   — the default `go install` target
//  3. ~/go/bin              — GOPATH fallback when `go` itself isn't
//     resolvable (e.g. running a distributed binary with no Go
//     toolchain installed)
//  4. the managed toolbin   — `pentestswarm install-tools` target
//  5. /opt/homebrew/bin     — Homebrew on Apple Silicon
//  6. /usr/local/bin        — Homebrew on Intel macOS / common Linux prefix
//  7. /usr/bin              — system-installed tools
//  8. the directory of the running executable
//
// Directories are deduplicated; nonexistent ones are still included
// (callers that care whether a directory exists, like AugmentedPATH,
// filter separately) since Resolve's os.Stat check handles that.
func CandidateDirs() []string {
	var dirs []string

	env := goEnv("GOBIN", "GOPATH")
	if gobin := env["GOBIN"]; gobin != "" {
		dirs = append(dirs, gobin)
	}
	if gopath := env["GOPATH"]; gopath != "" {
		dirs = append(dirs, filepath.Join(gopath, "bin"))
	} else if home, err := os.UserHomeDir(); err == nil {
		dirs = append(dirs, filepath.Join(home, "go", "bin"))
	}

	if managed, err := managedToolBinDirPath(); err == nil {
		dirs = append(dirs, managed)
	}

	dirs = append(dirs, "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin")

	if exe, err := os.Executable(); err == nil {
		if resolved, err := filepath.EvalSymlinks(exe); err == nil {
			exe = resolved
		}
		dirs = append(dirs, filepath.Dir(exe))
	}

	return dedup(dirs)
}

// Resolve finds the absolute path to a tool binary. It checks the
// current process's PATH first (so an explicit user override always
// wins), then falls back to CandidateDirs — the safety net for the
// common case where PATH doesn't include ~/go/bin or our managed
// toolbin.
func Resolve(tool string) (string, bool) {
	if path, err := exec.LookPath(tool); err == nil {
		return path, true
	}
	for _, dir := range CandidateDirs() {
		candidate := filepath.Join(dir, tool)
		info, err := os.Stat(candidate)
		if err != nil || info.IsDir() {
			continue
		}
		if isExecutable(info) {
			return candidate, true
		}
	}
	return "", false
}

// AugmentedPATH returns the current process's PATH with CandidateDirs
// prepended (existing directories only, deduplicated). Set this as a
// child process's PATH env so a tool that itself shells out to other
// binaries (e.g. testssl.sh calling openssl) can also find our
// managed/toolchain directories.
func AugmentedPATH() string {
	current := os.Getenv("PATH")

	var existing []string
	for _, d := range CandidateDirs() {
		if fi, err := os.Stat(d); err == nil && fi.IsDir() {
			existing = append(existing, d)
		}
	}
	if len(existing) == 0 {
		return current
	}

	prefix := strings.Join(existing, string(os.PathListSeparator))
	if current == "" {
		return prefix
	}
	return prefix + string(os.PathListSeparator) + current
}

// isExecutable reports whether info's mode bits mark it runnable.
// Windows doesn't use POSIX permission bits for this, so anything
// that isn't a directory counts there.
func isExecutable(info os.FileInfo) bool {
	if runtime.GOOS == "windows" {
		return true
	}
	return info.Mode()&0o111 != 0
}

// dedup removes duplicate and empty entries, preserving first-seen order.
func dedup(dirs []string) []string {
	seen := make(map[string]bool, len(dirs))
	out := make([]string, 0, len(dirs))
	for _, d := range dirs {
		if d == "" || seen[d] {
			continue
		}
		seen[d] = true
		out = append(out, d)
	}
	return out
}

// goEnv returns the requested `go env` variables, keyed by name, in a
// single subprocess call. Missing or failed lookups (e.g. the `go`
// toolchain isn't installed — plausible for a distributed binary) are
// tolerated: callers just get empty strings for those keys rather
// than an error, since the rest of CandidateDirs still applies.
func goEnv(vars ...string) map[string]string {
	result := make(map[string]string, len(vars))

	args := append([]string{"env"}, vars...)
	output, err := exec.Command("go", args...).Output()
	if err != nil {
		return result
	}

	lines := strings.Split(strings.TrimRight(string(output), "\n"), "\n")
	for i, v := range vars {
		if i < len(lines) {
			result[v] = strings.TrimSpace(lines[i])
		}
	}
	return result
}
