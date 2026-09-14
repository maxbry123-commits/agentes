/**
 * Version Checker - Validates Node.js version requirements
 */

export interface VersionCheckResult {
  isCompatible: boolean;
  currentVersion: string;
  requiredVersion: string;
  errorMessage?: string;
}

/**
 * Check if the current Node.js version meets the minimum requirement
 * @param minVersion - Minimum required version (e.g., "18.0.0")
 * @returns Version check result
 */
export function checkNodeVersion(minVersion: string = '18.0.0'): VersionCheckResult {
  const currentVersion = process.version.slice(1); // Remove 'v' prefix
  const requiredVersion = minVersion;

  const isCompatible = compareVersions(currentVersion, requiredVersion) >= 0;

  if (!isCompatible) {
    return {
      isCompatible: false,
      currentVersion,
      requiredVersion,
      errorMessage: `AgentGuard requires Node.js ${requiredVersion} or higher. Current version: ${currentVersion}`
    };
  }

  return {
    isCompatible: true,
    currentVersion,
    requiredVersion
  };
}

/**
 * Compare two semantic version strings
 * @param version1 - First version string (e.g., "18.0.0")
 * @param version2 - Second version string (e.g., "18.0.0")
 * @returns -1 if version1 < version2, 0 if equal, 1 if version1 > version2
 */
export function compareVersions(version1: string, version2: string): number {
  const parts1 = version1.split('.').map(Number);
  const parts2 = version2.split('.').map(Number);

  for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
    const part1 = parts1[i] || 0;
    const part2 = parts2[i] || 0;

    if (part1 < part2) return -1;
    if (part1 > part2) return 1;
  }

  return 0;
}

/**
 * Display error message and exit if Node.js version is incompatible
 */
export function enforceNodeVersion(): void {
  const result = checkNodeVersion();
  
  if (!result.isCompatible) {
    console.error(`Error: ${result.errorMessage}`);
    console.error(`Please upgrade Node.js to version ${result.requiredVersion} or higher.`);
    process.exit(1);
  }
}
