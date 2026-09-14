// Package programterms parses a bug-bounty program's rules-of-engagement
// text and extracts machine-readable constraints (rate limits, banned
// paths, required headers, prohibited techniques).
//
// This is a heuristic parser — programs write their policies in prose,
// not in machine-friendly formats, so we look for common patterns. When
// it can't classify a clause it skips it; over-extraction is worse than
// under-extraction here, because the wrong limit can either tank
// findings (too cautious) or get the researcher banned (too aggressive).
//
// Used by `pentestswarm program inspect h1:<slug>` to print the
// extracted constraints (or merge them into a scan config).
package programterms

import (
	"regexp"
	"strconv"
	"strings"
)

// Constraints is the structured view of a program's RoE.
type Constraints struct {
	// MaxRequestsPerSecond is the rate limit, in requests/sec. 0 = no limit found.
	MaxRequestsPerSecond float64

	// NoAutomatedScanning is true when the policy explicitly forbids
	// automated/active scanning. The runner should default to safe-mode
	// + assist mode when this is set.
	NoAutomatedScanning bool

	// NoBruteForce is true when password / credential brute-force is banned.
	NoBruteForce bool

	// NoDoS is true when stress testing / DoS-style probes are banned.
	NoDoS bool

	// NoSocialEngineering — phishing, pretexting, etc.
	NoSocialEngineering bool

	// NoPhysical — physical-security testing.
	NoPhysical bool

	// DisallowedPaths is a list of URL paths the scanner must skip.
	DisallowedPaths []string

	// RequiredHeaders is a map of header-name → value the program asks
	// you to include in every request (typical for private programs that
	// want to identify your traffic).
	RequiredHeaders map[string]string

	// Notes is a list of clauses the parser noticed but couldn't slot
	// into one of the structured fields above. Surfaced so the researcher
	// can read them manually.
	Notes []string
}

// Parse runs the regex extractors over policy text and returns a
// Constraints view. The text is expected to be the program's RoE in
// markdown / plaintext (HackerOne's `policy` field, Bugcrowd brief
// scrape, etc.).
func Parse(policy string) Constraints {
	c := Constraints{
		RequiredHeaders: map[string]string{},
	}
	lower := strings.ToLower(policy)

	if rxNoAutomated.MatchString(lower) {
		c.NoAutomatedScanning = true
	}
	if rxNoBrute.MatchString(lower) {
		c.NoBruteForce = true
	}
	if rxNoDoS.MatchString(lower) {
		c.NoDoS = true
	}
	if rxNoSocial.MatchString(lower) {
		c.NoSocialEngineering = true
	}
	if rxNoPhysical.MatchString(lower) {
		c.NoPhysical = true
	}

	if m := rxRPS.FindStringSubmatch(lower); len(m) == 3 {
		if v, err := strconv.ParseFloat(m[1], 64); err == nil {
			switch m[2] {
			case "minute":
				c.MaxRequestsPerSecond = v / 60.0
			case "hour":
				c.MaxRequestsPerSecond = v / 3600.0
			default: // "second"
				c.MaxRequestsPerSecond = v
			}
		}
	}

	for _, m := range rxHeader.FindAllStringSubmatch(policy, -1) {
		name := strings.TrimSpace(m[1])
		val := strings.TrimSpace(m[2])
		if name != "" && val != "" {
			c.RequiredHeaders[name] = val
		}
	}

	for _, m := range rxDisallowedPath.FindAllStringSubmatch(policy, -1) {
		path := strings.TrimSpace(m[1])
		if path != "" {
			c.DisallowedPaths = append(c.DisallowedPaths, path)
		}
	}

	return c
}

// regex dictionary — these are intentionally narrow. False positives
// here mean we'd auto-restrict scans for programs that don't ask us to,
// which is more costly than missing a constraint (the researcher will
// re-read the policy themselves anyway).
var (
	rxNoAutomated = regexp.MustCompile(`(?i)(no|do not|don'?t|prohibit\w*|forbid\w*).{0,40}(automat\w*|scanner\w*|scanning)`)
	rxNoBrute     = regexp.MustCompile(`(?i)(no|do not|don'?t|prohibit\w*|forbid\w*).{0,40}(brute[\s-]?force|password\s+guess\w*|credential\s+stuff\w*)`)
	rxNoDoS       = regexp.MustCompile(`(?i)(no|do not|don'?t|prohibit\w*|forbid\w*).{0,40}(denial[\s-]of[\s-]service|\bdos\b|stress[\s-]test\w*|load[\s-]test\w*)`)
	rxNoSocial    = regexp.MustCompile(`(?i)(no|do not|don'?t|prohibit\w*|forbid\w*).{0,40}(social[\s-]engineer\w*|phish\w*|pretext\w*)`)
	rxNoPhysical  = regexp.MustCompile(`(?i)(no|do not|don'?t|prohibit\w*|forbid\w*).{0,40}(physical[\s-]securit\w*|tailgat\w*)`)

	// "5 requests per second", "100 req/min", "60 rps"
	rxRPS = regexp.MustCompile(`(?i)(\d+(?:\.\d+)?)\s*(?:requests?|req|rps|qps)\s*(?:per|/)\s*(second|minute|hour)`)

	// `X-Bugbounty-User: <yourname>` — backtick-quoted in markdown policies
	rxHeader = regexp.MustCompile("(?i)`([A-Za-z][A-Za-z0-9-]+)\\s*:\\s*([^`]+)`")

	// "do not scan /admin", "out of scope: /internal"
	rxDisallowedPath = regexp.MustCompile(`(?i)(?:do not (?:scan|test)|out[\s-]of[\s-]scope:?)\s*(/[A-Za-z0-9_\-/]+)`)
)
