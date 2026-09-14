package cli

import (
	"os"
	"testing"
)

// withStdin temporarily replaces os.Stdin for the duration of fn, then
// restores it. Used to simulate a non-interactive (piped) stdin without
// depending on how the test runner itself is invoked.
func withStdin(t *testing.T, r *os.File, fn func()) {
	t.Helper()
	orig := os.Stdin
	os.Stdin = r
	defer func() { os.Stdin = orig }()
	fn()
}

func TestConfirm_AssumeYes(t *testing.T) {
	orig := assumeYes
	assumeYes = true
	defer func() { assumeYes = orig }()

	// --yes must short-circuit before ever touching stdin.
	if !Confirm("proceed?") {
		t.Fatal("Confirm() = false, want true when assumeYes is set")
	}
}

func TestConfirm_NonTTYDefaultsToFalse(t *testing.T) {
	orig := assumeYes
	assumeYes = false
	defer func() { assumeYes = orig }()

	r, w, err := os.Pipe()
	if err != nil {
		t.Fatalf("os.Pipe: %v", err)
	}
	defer r.Close()
	defer w.Close()

	// A pipe is never a TTY, so Confirm must return false immediately
	// (safe default) instead of blocking on a read that will never
	// resolve to an explicit "yes".
	withStdin(t, r, func() {
		if Confirm("proceed?") {
			t.Fatal("Confirm() = true, want false for a non-TTY stdin")
		}
	})
}
