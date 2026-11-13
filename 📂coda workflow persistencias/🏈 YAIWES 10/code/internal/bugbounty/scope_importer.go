package bugbounty

import (
	"fmt"
	"strings"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// ImportScope converts a bug bounty program's scope into a ScopeDefinition.
func ImportScope(program *BugBountyProgram) (*pipeline.ScopeDefinition, error) {
	scope := &pipeline.ScopeDefinition{}

	for _, asset := range program.InScope {
		switch strings.ToLower(asset.AssetType) {
		case "url", "domain", "wildcard":
			identifier := asset.Identifier
			// Strip protocol prefixes
			identifier = strings.TrimPrefix(identifier, "https://")
			identifier = strings.TrimPrefix(identifier, "http://")
			identifier = strings.TrimSuffix(identifier, "/")

			scope.AllowedDomains = append(scope.AllowedDomains, identifier)

		case "cidr", "ip_address":
			scope.AllowedCIDRs = append(scope.AllowedCIDRs, asset.Identifier)
		}
	}

	// Add out-of-scope as exclusions
	for _, asset := range program.OutOfScope {
		if strings.ToLower(asset.AssetType) == "cidr" {
			scope.ExcludedCIDRs = append(scope.ExcludedCIDRs, asset.Identifier)
		}
	}

	if len(scope.AllowedCIDRs) == 0 && len(scope.AllowedDomains) == 0 {
		return nil, fmt.Errorf("program %s has no importable scope assets", program.Handle)
	}

	return scope, nil
}
