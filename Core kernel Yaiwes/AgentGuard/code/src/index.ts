/**
 * AgentGuard - Main entry point
 */

import { CLI } from './cli';
import { enforceNodeVersion } from './version-checker';

export async function main(args: string[]): Promise<number> {
  // Check Node.js version before proceeding
  enforceNodeVersion();
  
  const cli = new CLI();
  return await cli.run(args);
}

// Run if called directly
if (require.main === module) {
  main(process.argv.slice(2))
    .then((exitCode) => {
      process.exit(exitCode);
    })
    .catch((error) => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}

// Export for testing
export * from './types';
export { Validator } from './validator';
export { CLI } from './cli';
export { checkNodeVersion, compareVersions, enforceNodeVersion } from './version-checker';
export { OutputFormatter } from './output-formatter';
export { CommandUnwrapper } from './command-unwrapper';
export { ScriptAnalyzer } from './script-analyzer';
