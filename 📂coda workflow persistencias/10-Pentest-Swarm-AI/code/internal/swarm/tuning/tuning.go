// Package tuning loads per-finding-type pheromone settings (base weight
// + half-life) from YAML and applies a global exploration-bias multiplier.
//
// Agents use this to avoid hardcoding magic numbers at every blackboard
// Write call. Missing types fall back to the catch-all default, so adding
// a new finding type doesn't crash the swarm on startup.
package tuning

import (
	"embed"
	"fmt"
	"io"
	"os"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/swarm/blackboard"
	"go.yaml.in/yaml/v3"
)

//go:embed pheromones_default.yaml
var defaultFS embed.FS

// Settings is the decoded shape of config/pheromones.yaml.
type Settings struct {
	Types   map[string]Entry `yaml:"types"`
	Default Entry            `yaml:"default"`

	// bias is a multiplier applied to every Lookup().Base. Range (0, ∞);
	// defaults to 1.0. Set via WithBias.
	bias float64
}

// Entry is a single type's tuning.
type Entry struct {
	Base        float64 `yaml:"base"`
	HalfLifeSec int     `yaml:"half_life_sec"`
}

// Bias is the exploration-bias enum exposed via CLI.
type Bias string

const (
	BiasLow    Bias = "low"
	BiasMedium Bias = "med"
	BiasHigh   Bias = "high"
)

// Multiplier returns the pheromone scaling factor for each bias level.
// High bias surfaces more findings to downstream agents sooner (breadth
// first); low bias keeps the swarm focused on what it already has (depth
// first).
func (b Bias) Multiplier() float64 {
	switch b {
	case BiasLow:
		return 0.7
	case BiasHigh:
		return 1.3
	case BiasMedium, "":
		return 1.0
	default:
		return 1.0
	}
}

// Default returns the settings baked into the binary (embedded
// pheromones_default.yaml). Always safe — never returns an error.
func Default() *Settings {
	data, _ := defaultFS.ReadFile("pheromones_default.yaml")
	var s Settings
	_ = yaml.Unmarshal(data, &s)
	s.bias = 1.0
	return &s
}

// Load reads settings from the given file. If path is empty or the file
// doesn't exist, Default() is returned — callers don't need to gate on it.
func Load(path string) (*Settings, error) {
	if path == "" {
		return Default(), nil
	}
	f, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) {
			return Default(), nil
		}
		return nil, fmt.Errorf("open pheromones: %w", err)
	}
	defer f.Close()
	return parse(f)
}

func parse(r io.Reader) (*Settings, error) {
	data, err := io.ReadAll(r)
	if err != nil {
		return nil, err
	}
	var s Settings
	if err := yaml.Unmarshal(data, &s); err != nil {
		return nil, fmt.Errorf("parse pheromones: %w", err)
	}
	if s.bias == 0 {
		s.bias = 1.0
	}
	return &s, nil
}

// WithBias returns a copy of the settings with the exploration bias applied.
func (s *Settings) WithBias(b Bias) *Settings {
	out := *s
	out.bias = b.Multiplier()
	if len(s.Types) > 0 {
		out.Types = make(map[string]Entry, len(s.Types))
		for k, v := range s.Types {
			out.Types[k] = v
		}
	}
	return &out
}

// Lookup returns the tuned base + half-life for a finding type, with the
// current bias multiplier already applied to Base.
func (s *Settings) Lookup(t blackboard.FindingType) (base float64, halfLifeSec int) {
	if s == nil {
		return 1.0, 3600
	}
	if e, ok := s.Types[string(t)]; ok {
		return e.Base * s.bias, e.HalfLifeSec
	}
	def := s.Default
	if def.Base == 0 {
		def.Base = 0.5
	}
	if def.HalfLifeSec == 0 {
		def.HalfLifeSec = 3600
	}
	return def.Base * s.bias, def.HalfLifeSec
}

// LookupFor is a helper that returns a Finding pre-populated with the
// tuned pheromone values. Callers still set CampaignID / AgentName /
// Target / Data themselves.
func (s *Settings) LookupFor(t blackboard.FindingType) blackboard.Finding {
	b, h := s.Lookup(t)
	return blackboard.Finding{Type: t, PheromoneBase: b, HalfLifeSec: h}
}
