package plugins

import (
	"fmt"
	"regexp"
	"strings"
)

// ValidationReport is the result of running Validate. Empty Errors means
// the playbook is valid. Warnings are advisory only.
type ValidationReport struct {
	Errors   []string
	Warnings []string
}

// OK reports whether the playbook has no errors.
func (r *ValidationReport) OK() bool { return len(r.Errors) == 0 }

// Format produces a human-readable report.
func (r *ValidationReport) Format() string {
	var sb strings.Builder
	for _, e := range r.Errors {
		sb.WriteString("  ✗ " + e + "\n")
	}
	for _, w := range r.Warnings {
		sb.WriteString("  ⚠ " + w + "\n")
	}
	return sb.String()
}

// Validate runs a thorough validation pass. knownTools is the list of
// tools the current binary can execute (typically from the coordinator);
// tool references outside this set become warnings rather than errors
// because a custom tool definition may be loaded at runtime.
func Validate(pb *Playbook, knownTools []string) *ValidationReport {
	r := &ValidationReport{}
	if pb == nil {
		r.Errors = append(r.Errors, "playbook is nil")
		return r
	}

	// --- Core identity ---
	if pb.Name == "" {
		r.Errors = append(r.Errors, "name is required")
	}
	if pb.Version != "" && !semverLike.MatchString(pb.Version) {
		r.Warnings = append(r.Warnings, fmt.Sprintf("version %q is not semver-like (expected e.g. 1.0.0)", pb.Version))
	}
	if pb.Author.Name == "" {
		r.Warnings = append(r.Warnings, "author.name is empty — unowned playbooks are hard to maintain")
	}
	if pb.Description == "" {
		r.Warnings = append(r.Warnings, "description is empty — users skim the description to pick playbooks")
	}

	// --- Variables ---
	for name, v := range pb.Variables {
		if !variableName.MatchString(name) {
			r.Errors = append(r.Errors, fmt.Sprintf("variable %q: name must match /^[a-z][a-z0-9_]*$/", name))
		}
		if v.Required && v.Default != "" {
			r.Warnings = append(r.Warnings, fmt.Sprintf("variable %q: required + default is contradictory — pick one", name))
		}
		if v.Type != "" && !allowedVarTypes[v.Type] {
			r.Errors = append(r.Errors, fmt.Sprintf("variable %q: type %q is not one of string|int|bool|list|secret", name, v.Type))
		}
	}

	// --- Phases ---
	if len(pb.Phases) == 0 {
		r.Errors = append(r.Errors, "at least one phase is required")
	}
	seenPhases := map[string]struct{}{}
	toolSet := map[string]struct{}{}
	for _, t := range knownTools {
		toolSet[t] = struct{}{}
	}
	for i, p := range pb.Phases {
		label := fmt.Sprintf("phase[%d] (%q)", i, p.Name)
		if p.Name == "" {
			r.Errors = append(r.Errors, fmt.Sprintf("phase[%d]: name is required", i))
		}
		if _, dup := seenPhases[p.Name]; dup && p.Name != "" {
			r.Errors = append(r.Errors, fmt.Sprintf("%s: duplicate phase name", label))
		}
		seenPhases[p.Name] = struct{}{}

		if p.Strategy != "" && !allowedStrategies[p.Strategy] {
			r.Warnings = append(r.Warnings, fmt.Sprintf("%s: strategy %q unknown — falling back to default", label, p.Strategy))
		}

		// Tools and templated references.
		for j, tool := range p.Tools {
			toolLabel := fmt.Sprintf("%s.tools[%d]", label, j)
			if tool.Name == "" && tool.Command == "" {
				r.Errors = append(r.Errors, fmt.Sprintf("%s: either 'name' or 'command' is required", toolLabel))
			}
			if tool.Name != "" && len(knownTools) > 0 {
				if _, known := toolSet[tool.Name]; !known {
					r.Warnings = append(r.Warnings, fmt.Sprintf("%s: tool %q is not known to this binary — may be a custom-loaded tool", toolLabel, tool.Name))
				}
			}
			// Templated-variable references in options must match a declared variable.
			for key, val := range tool.Options {
				if s, ok := val.(string); ok {
					for _, ref := range extractTemplateRefs(s) {
						if _, ok := pb.Variables[ref]; !ok {
							r.Errors = append(r.Errors, fmt.Sprintf("%s.options.%s references undeclared variable %q", toolLabel, key, ref))
						}
					}
				}
			}
		}
	}

	return r
}

// --- heuristic helpers ---

var (
	semverLike   = regexp.MustCompile(`^\d+\.\d+\.\d+(?:[-+][\w.]+)?$`)
	variableName = regexp.MustCompile(`^[a-z][a-z0-9_]*$`)
	templateRef  = regexp.MustCompile(`{{\s*([a-z][a-z0-9_]*)\s*}}`)
)

var allowedVarTypes = map[string]bool{
	"string": true, "int": true, "bool": true, "list": true, "secret": true,
}

var allowedStrategies = map[string]bool{
	"": true, "sequential": true, "parallel": true, "best-effort": true,
}

// extractTemplateRefs returns the variable names referenced in {{ var }} syntax.
func extractTemplateRefs(s string) []string {
	var out []string
	for _, m := range templateRef.FindAllStringSubmatch(s, -1) {
		if len(m) > 1 {
			out = append(out, m[1])
		}
	}
	return out
}
