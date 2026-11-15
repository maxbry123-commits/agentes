package cli

import (
	"os"
	"os/exec"
	"regexp"
	"strings"

	"golang.org/x/term"
)

// ansiEscape strips ANSI SGR sequences so paged output can honor
// NO_COLOR even when the caller already embedded color codes.
var ansiEscape = regexp.MustCompile("\x1b\\[[0-9;]*m")

// Page prints content directly when it fits on screen (or stdout isn't
// an interactive terminal), and otherwise pipes it through a pager so
// long output — help text, reports, listings — doesn't blow past the
// scrollback. It degrades to a plain print whenever a pager can't be
// found or fails to run; it never errors or blocks the caller.
func Page(content string) {
	if os.Getenv("NO_COLOR") != "" {
		content = ansiEscape.ReplaceAllString(content, "")
	}

	fd := int(os.Stdout.Fd())
	if !term.IsTerminal(fd) {
		writeContent(content)
		return
	}
	_, height, err := term.GetSize(fd)
	if err != nil || strings.Count(content, "\n")+1 <= height {
		writeContent(content)
		return
	}

	candidates := []string{os.Getenv("PAGER"), "less -R", "more"}
	for _, c := range candidates {
		fields := strings.Fields(c)
		if len(fields) == 0 {
			continue
		}
		path, err := exec.LookPath(fields[0])
		if err != nil {
			continue
		}
		cmd := exec.Command(path, fields[1:]...)
		cmd.Stdin = strings.NewReader(content)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if cmd.Run() == nil {
			return
		}
	}
	writeContent(content)
}

// writeContent is the "just show it" fallback shared by every early-out
// above.
func writeContent(content string) {
	os.Stdout.WriteString(content)
}
