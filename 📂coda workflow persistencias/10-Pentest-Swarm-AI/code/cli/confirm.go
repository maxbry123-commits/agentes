package cli

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"golang.org/x/term"
)

// assumeYes backs the global --yes/-y persistent flag (registered in
// Execute, cli/root.go). When set, Confirm treats every prompt as
// pre-approved — the non-interactive escape hatch for scripts and CI.
var assumeYes bool

// Confirm is the canonical gate for destructive/irreversible actions
// (installing tools, overwriting files, wiping state, etc). It:
//
//  1. returns true immediately if --yes/-y was passed;
//  2. returns false without prompting if stdin isn't an interactive
//     terminal — a script or pipe gets a safe "no" instead of a hang;
//  3. otherwise prints "<prompt> [y/N] " and reads one line from stdin,
//     treating anything but an explicit y/yes as "no".
//
// cli/run.go's promptYesNo predates this and does the same thing
// inline for one call site; it's left as-is per the task scope, but a
// future cleanup could have it delegate here.
func Confirm(prompt string) bool {
	if assumeYes {
		return true
	}
	if !term.IsTerminal(int(os.Stdin.Fd())) {
		return false
	}
	fmt.Print("  " + colorCyan(prompt+" [y/N] "))
	scanner := bufio.NewScanner(os.Stdin)
	if scanner.Scan() {
		answer := strings.ToLower(strings.TrimSpace(scanner.Text()))
		return answer == "y" || answer == "yes"
	}
	return false
}
