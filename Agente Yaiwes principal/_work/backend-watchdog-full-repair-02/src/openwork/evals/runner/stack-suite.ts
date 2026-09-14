const TEST_FILE = /\.test\.[cm]?[jt]sx?$/;
const GLOB_MARKER = /[*?{}[\]]/;

function explicitTestFiles(argv: readonly string[]): string[] {
  return argv.filter((argument) => TEST_FILE.test(argument) && !GLOB_MARKER.test(argument));
}

export function shouldPrepareSuite(argv: readonly string[]): boolean {
  const testArguments = argv.filter((argument) => argument.includes(".test.") || GLOB_MARKER.test(argument));
  return testArguments.length !== 1 || explicitTestFiles(testArguments).length !== 1;
}

function configuredWorkerCount(env: NodeJS.ProcessEnv): number {
  const configured = Number.parseInt(env.OPENWORK_EVAL_MAX_WORKERS?.trim() ?? "", 10);
  if (Number.isInteger(configured) && configured > 0) return configured;
  return env.OPENWORK_EVAL_DAYTONA?.trim() === "1" ? 2 : 3;
}

export function suiteWorkerCount(argv: readonly string[], env: NodeJS.ProcessEnv): number {
  const fileCount = explicitTestFiles(argv).length;
  const workers = configuredWorkerCount(env);
  return fileCount > 0 ? Math.min(fileCount, workers) : workers;
}

export function workerSlot(workerId: string | undefined, slotCount: number): number {
  if (!Number.isInteger(slotCount) || slotCount < 1) throw new Error("Stack preparation requires at least one worker slot.");
  const parsed = Number.parseInt(workerId ?? "", 10);
  const worker = Number.isInteger(parsed) && parsed > 0 ? parsed : 1;
  return (worker - 1) % slotCount;
}
