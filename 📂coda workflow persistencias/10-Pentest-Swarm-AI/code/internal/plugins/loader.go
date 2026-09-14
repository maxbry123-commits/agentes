package plugins

import (
	"fmt"
	"os"
	"path/filepath"

	"go.yaml.in/yaml/v3"
)

// LoadPlaybook reads and parses a playbook YAML file.
func LoadPlaybook(path string) (*Playbook, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading playbook %s: %w", path, err)
	}

	var pb Playbook
	if err := yaml.Unmarshal(data, &pb); err != nil {
		return nil, fmt.Errorf("parsing playbook %s: %w", path, err)
	}

	if pb.Name == "" {
		return nil, fmt.Errorf("playbook %s: name is required", path)
	}
	if len(pb.Phases) == 0 {
		return nil, fmt.Errorf("playbook %s: at least one phase is required", path)
	}

	return &pb, nil
}

// LoadCustomTool reads and parses a custom tool YAML definition.
func LoadCustomTool(path string) (*CustomToolDef, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading tool def %s: %w", path, err)
	}

	var tool CustomToolDef
	if err := yaml.Unmarshal(data, &tool); err != nil {
		return nil, fmt.Errorf("parsing tool def %s: %w", path, err)
	}

	if tool.Name == "" || tool.Command == "" {
		return nil, fmt.Errorf("tool def %s: name and command are required", path)
	}

	return &tool, nil
}

// DiscoverPlaybooks finds all .yaml playbook files in a directory.
func DiscoverPlaybooks(dir string) ([]*Playbook, error) {
	var playbooks []*Playbook

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // skip errors
		}
		if info.IsDir() || filepath.Ext(path) != ".yaml" {
			return nil
		}

		pb, err := LoadPlaybook(path)
		if err != nil {
			return nil // skip invalid playbooks
		}

		playbooks = append(playbooks, pb)
		return nil
	})

	return playbooks, err
}

// DiscoverCustomTools finds all tool definitions in a directory.
func DiscoverCustomTools(dir string) ([]*CustomToolDef, error) {
	var tools []*CustomToolDef

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || filepath.Ext(path) != ".yaml" {
			return nil
		}

		tool, err := LoadCustomTool(path)
		if err != nil {
			return nil
		}

		tools = append(tools, tool)
		return nil
	})

	return tools, err
}
