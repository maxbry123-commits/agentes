package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/spf13/cobra"
)

// A workspace is just a named config.yaml living under the OS config dir,
// plus a small "active" marker file recording which one is current. It
// lets a researcher switch between client/target setups (different
// orchestrator keys, endpoints, etc.) without hand-editing --config every
// time. See resolveActiveWorkspaceConfig below for how the active
// workspace is wired into config.Load(cfgFile) calls across the CLI.
var workspaceCmd = &cobra.Command{
	Use:   "workspace",
	Short: "Manage named config workspaces (switch between target setups)",
	Long: `A workspace is a named config file pentestswarm can point at instead of
the default config.yaml — handy for switching between clients,
environments, or target setups without juggling --config by hand.

Workspace files live under the OS config directory (see
'pentestswarm workspace list' for the exact path) and 'workspace use
<name>' marks one active for every command that doesn't pass an
explicit --config.`,
}

var workspaceListCmd = &cobra.Command{
	Use:     "list",
	Short:   "List saved workspaces",
	Example: "  pentestswarm workspace list",
	RunE: func(cmd *cobra.Command, args []string) error {
		names, err := listWorkspaces()
		if err != nil {
			return err
		}
		active, err := activeWorkspaceName()
		if err != nil {
			return err
		}

		if OutputIsJSON() {
			type entry struct {
				Name   string `json:"name"`
				Active bool   `json:"active"`
			}
			entries := make([]entry, 0, len(names))
			for _, n := range names {
				entries = append(entries, entry{Name: n, Active: n == active})
			}
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(entries)
		}

		if len(names) == 0 {
			fmt.Println(colorDim("  No workspaces yet — create one with 'pentestswarm workspace use <name>'"))
			return nil
		}
		for _, n := range names {
			if n == active {
				fmt.Printf("  %s %s\n", colorGreen("*"), colorCyan(n))
			} else {
				fmt.Printf("    %s\n", n)
			}
		}
		return nil
	},
}

var workspaceCurrentCmd = &cobra.Command{
	Use:     "current",
	Short:   "Print the active workspace",
	Example: "  pentestswarm workspace current",
	RunE: func(cmd *cobra.Command, args []string) error {
		active, err := activeWorkspaceName()
		if err != nil {
			return err
		}

		if active == "" {
			if OutputIsJSON() {
				enc := json.NewEncoder(os.Stdout)
				enc.SetIndent("", "  ")
				return enc.Encode(map[string]any{"active": nil})
			}
			fmt.Println(colorDim("  No active workspace — using the default config resolution (--config / ./config.yaml / ~/.pentestswarm/config.yaml)."))
			return nil
		}

		path, err := workspaceFilePath(active)
		if err != nil {
			return err
		}
		if OutputIsJSON() {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{"active": active, "path": path})
		}
		fmt.Printf("  %s  %s\n", colorGreen(active), colorDim(path))
		return nil
	},
}

var workspaceUseCmd = &cobra.Command{
	Use:   "use <name>",
	Short: "Switch to (or create) a named workspace",
	Long: `Marks <name> as the active workspace. Commands that don't pass an
explicit --config will load that workspace's config file instead of the
usual default (./config.yaml, ~/.pentestswarm/config.yaml, ...).

If the workspace doesn't exist yet, it's created by copying whatever
config pentestswarm currently resolves to (or a minimal default config
if none is found).`,
	Args:    cobra.ExactArgs(1),
	Example: "  pentestswarm workspace use client-acme\n  pentestswarm workspace use staging",
	RunE: func(cmd *cobra.Command, args []string) error {
		name := args[0]
		if err := validWorkspaceName(name); err != nil {
			return err
		}

		path, err := workspaceFilePath(name)
		if err != nil {
			return err
		}

		created := false
		if _, statErr := os.Stat(path); os.IsNotExist(statErr) {
			if err := createWorkspaceFrom(path); err != nil {
				return err
			}
			created = true
		}

		if err := setActiveWorkspaceName(name); err != nil {
			return err
		}

		verb := "switched to"
		if created {
			verb = "created and switched to"
		}
		if OutputIsJSON() {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			return enc.Encode(map[string]any{"active": name, "path": path, "created": created})
		}
		fmt.Printf("  %s  %s workspace %s\n", colorGreen("[ok]"), verb, colorCyan(name))
		fmt.Printf("  %s %s\n", colorDim("config:"), path)
		fmt.Printf("  %s pentestswarm --config %s <command>\n", colorDim("or explicitly:"), path)
		return nil
	},
}

func init() {
	workspaceCmd.AddCommand(workspaceListCmd)
	workspaceCmd.AddCommand(workspaceUseCmd)
	workspaceCmd.AddCommand(workspaceCurrentCmd)
	rootCmd.AddCommand(workspaceCmd)

	rootCmd.PersistentPreRunE = resolveActiveWorkspaceConfig
}

// resolveActiveWorkspaceConfig runs before every command's RunE. When no
// explicit --config was given, it points cfgFile at the active
// workspace's config file (if one is set and still exists on disk) so
// every config.Load(cfgFile) call across the CLI transparently picks it
// up. Leaves cfgFile untouched otherwise, so the default/no-workspace
// path is unchanged.
func resolveActiveWorkspaceConfig(cmd *cobra.Command, args []string) error {
	if cfgFile == "" {
		if path, ok := activeWorkspaceConfigPath(); ok {
			cfgFile = path
		}
	}
	return nil
}

// defaultWorkspaceConfig seeds a brand-new workspace when there's no
// existing config to copy from. Mirrors init.go's writeMinimalConfig
// closely enough to be a sane starting point without duplicating its
// keychain-aware API-key handling.
const defaultWorkspaceConfig = `# pentestswarm workspace config
# Created by: pentestswarm workspace use

orchestrator:
  provider: claude
  model: claude-sonnet-4-6
  context_window: 200000
  max_tokens: 8192
  temperature: 0.1

scope:
  enforce_strict: true

logging:
  level: info
  format: console
`

// createWorkspaceFrom writes a new workspace file at destPath, seeded
// from whatever config pentestswarm currently resolves to (--config, an
// already-active workspace, or the default search path), falling back to
// defaultWorkspaceConfig when nothing is found.
func createWorkspaceFrom(destPath string) error {
	if err := os.MkdirAll(filepath.Dir(destPath), 0o755); err != nil {
		return fmt.Errorf("creating workspace dir: %w", err)
	}

	data := []byte(defaultWorkspaceConfig)
	if srcPath, exists := resolveConfigPath(); exists {
		b, err := os.ReadFile(srcPath)
		if err != nil {
			return fmt.Errorf("reading %s: %w", srcPath, err)
		}
		data = b
	}

	return os.WriteFile(destPath, data, 0o644)
}

// validWorkspaceName rejects names that would escape the workspaces
// directory or collide with the active-marker file.
func validWorkspaceName(name string) error {
	if name == "" {
		return fmt.Errorf("workspace name must not be empty")
	}
	if name != filepath.Base(name) || name == "." || name == ".." {
		return fmt.Errorf("invalid workspace name %q: use a simple name (no slashes)", name)
	}
	if strings.HasPrefix(name, ".") {
		return fmt.Errorf("invalid workspace name %q: must not start with '.'", name)
	}
	return nil
}

// pentestswarmConfigDir returns <userConfigDir>/pentestswarm, the base
// directory for workspace state (mirrors the XDG config dir on Linux,
// Application Support on macOS, %AppData% on Windows).
func pentestswarmConfigDir() (string, error) {
	base, err := os.UserConfigDir()
	if err != nil {
		return "", fmt.Errorf("resolving user config dir: %w", err)
	}
	return filepath.Join(base, "pentestswarm"), nil
}

func workspacesDir() (string, error) {
	dir, err := pentestswarmConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "workspaces"), nil
}

func workspaceFilePath(name string) (string, error) {
	dir, err := workspacesDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, name+".yaml"), nil
}

func activeMarkerPath() (string, error) {
	dir, err := workspacesDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "active"), nil
}

// listWorkspaces returns the names of saved workspaces (the .yaml files
// under workspacesDir, minus the extension), sorted alphabetically. A
// missing workspaces directory is not an error — it just means none
// exist yet.
func listWorkspaces() ([]string, error) {
	dir, err := workspacesDir()
	if err != nil {
		return nil, err
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("reading workspaces dir: %w", err)
	}

	var names []string
	for _, e := range entries {
		if e.IsDir() || filepath.Ext(e.Name()) != ".yaml" {
			continue
		}
		names = append(names, strings.TrimSuffix(e.Name(), ".yaml"))
	}
	sort.Strings(names)
	return names, nil
}

// activeWorkspaceName returns the name recorded in the active marker
// file, or "" if none is set. A missing marker file is not an error.
func activeWorkspaceName() (string, error) {
	marker, err := activeMarkerPath()
	if err != nil {
		return "", err
	}
	data, err := os.ReadFile(marker)
	if err != nil {
		if os.IsNotExist(err) {
			return "", nil
		}
		return "", fmt.Errorf("reading active workspace marker: %w", err)
	}
	return strings.TrimSpace(string(data)), nil
}

func setActiveWorkspaceName(name string) error {
	dir, err := workspacesDir()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return fmt.Errorf("creating workspaces dir: %w", err)
	}
	marker, err := activeMarkerPath()
	if err != nil {
		return err
	}
	return os.WriteFile(marker, []byte(name+"\n"), 0o644)
}

// activeWorkspaceConfigPath returns the config file path for the active
// workspace, and whether one is actually set and present on disk. A
// stale marker (workspace deleted after being made active) reports
// false rather than erroring, so callers fall back cleanly to the
// default config resolution.
func activeWorkspaceConfigPath() (string, bool) {
	name, err := activeWorkspaceName()
	if err != nil || name == "" {
		return "", false
	}
	path, err := workspaceFilePath(name)
	if err != nil {
		return "", false
	}
	if _, err := os.Stat(path); err != nil {
		return "", false
	}
	return path, true
}
