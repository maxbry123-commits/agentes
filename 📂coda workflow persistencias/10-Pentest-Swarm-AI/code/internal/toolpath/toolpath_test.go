package toolpath

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestManagedToolBinDir_CreatesDirectory(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", tmp) // os.UserConfigDir() honors this on linux/darwin via unix build
	if runtime.GOOS == "windows" {
		t.Skip("XDG_CONFIG_HOME override doesn't apply on windows")
	}

	dir, err := ManagedToolBinDir()
	if err != nil {
		t.Fatalf("ManagedToolBinDir: %v", err)
	}
	if !filepath.IsAbs(dir) {
		t.Errorf("expected absolute path, got %q", dir)
	}
	info, err := os.Stat(dir)
	if err != nil {
		t.Fatalf("expected directory to be created: %v", err)
	}
	if !info.IsDir() {
		t.Errorf("expected %q to be a directory", dir)
	}
}

func TestCandidateDirs_Deduplicated(t *testing.T) {
	dirs := CandidateDirs()
	seen := make(map[string]bool)
	for _, d := range dirs {
		if seen[d] {
			t.Errorf("duplicate directory in CandidateDirs: %q", d)
		}
		seen[d] = true
	}
	if len(dirs) == 0 {
		t.Error("expected at least one candidate directory")
	}
}

func TestResolve_FindsBinaryInCandidateDir(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", tmp)
	if runtime.GOOS == "windows" {
		t.Skip("exec bit semantics differ on windows")
	}

	managed, err := ManagedToolBinDir()
	if err != nil {
		t.Fatalf("ManagedToolBinDir: %v", err)
	}

	toolPath := filepath.Join(managed, "faketool")
	if err := os.WriteFile(toolPath, []byte("#!/bin/sh\necho hi\n"), 0o755); err != nil {
		t.Fatalf("writing fake tool: %v", err)
	}

	// Ensure it isn't already resolvable via PATH so this actually
	// exercises the CandidateDirs fallback.
	t.Setenv("PATH", "/nonexistent-path-for-test")

	resolved, ok := Resolve("faketool")
	if !ok {
		t.Fatal("expected Resolve to find faketool in the managed toolbin")
	}
	if resolved != toolPath {
		t.Errorf("resolved = %q, want %q", resolved, toolPath)
	}
}

func TestResolve_MissingToolReturnsFalse(t *testing.T) {
	_, ok := Resolve("definitely-not-a-real-tool-xyz123")
	if ok {
		t.Error("expected Resolve to fail for a nonexistent tool")
	}
}

func TestAugmentedPATH_PrependsExistingDirs(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", tmp)
	t.Setenv("PATH", "/usr/bin")
	if runtime.GOOS == "windows" {
		t.Skip("PATH separator semantics differ on windows")
	}

	managed, err := ManagedToolBinDir()
	if err != nil {
		t.Fatalf("ManagedToolBinDir: %v", err)
	}

	augmented := AugmentedPATH()
	if augmented == "" {
		t.Fatal("expected non-empty augmented PATH")
	}
	if !strings.Contains(augmented, managed) {
		t.Errorf("expected augmented PATH %q to contain managed dir %q", augmented, managed)
	}
	if !strings.Contains(augmented, "/usr/bin") {
		t.Errorf("expected augmented PATH %q to retain original PATH entry", augmented)
	}
}
