#!/usr/bin/env python3
"""
exp_rpt_stack-php-large-v4 -> v5 patcher.

Observed v4 failure mode (QC 2026-05-18, 200-trial sample from
``laion/exp_rpt_stack-php-large-v4/traces/``):

  v4 attempted to bypass PHPUnit 10's strict-basename
  ``Runner\\TestSuiteLoader::loadSuiteClassFile`` rule by declaring
  ``<directory suffix="TestSolution.php">/tests</directory>`` in phpunit.xml.
  The hypothesis was that ``<directory>`` discovery would route through
  the Reflection-based scan loader instead of the strict-basename loader.

  **This hypothesis was wrong.** PHPUnit 10.5's ``XmlConfiguration\\
  TestSuiteMapper`` still routes through
  ``TestSuite->addTestFile($path) -> TestSuiteLoader->load($path) ->
  loadSuiteClassFile($path)``. That loader does:

    1. ``require_once($path)`` (catches any "Class X not found",
       "Trait Y not found", "Failed to open stream" errors at parent-
       class load time).
    2. Then scans the file's basename, derives "TestSolution", and
       searches the just-loaded symbols for a class whose name matches.
       0 / 500 sampled tasks declare a class literally named
       ``TestSolution``, so this fails on every well-formed task.

  Sample-wide distribution of 200 v4 verifier outputs:

       88  Class TestSolution cannot be found in /tests/TestSolution.php  (44.0%)
       42  must be compatible with PHPUnit::setUp(): void                 (21.0%)
       37  Class "<framework-base>" not found                              (18.5%)
       23  Trait "<...>" not found                                          (11.5%)
        6  require_once Failed to open stream                              (3.0%)
        4  other (override-final / undefined-method / "App did not exist!") (2.0%)
        0  OK / Tests:N Failures:0 Errors:0                                (0.0%)

  v4 also bundled a bootstrap shim that class_alias'd
  PHPUnit_Framework_TestCase -> PHPUnit\\Framework\\TestCase and stubbed
  Tests\\TestCase. That bootstrap *runs*, but it does nothing for the
  44% strict-basename failure (loadSuiteClassFile completes its require
  before checking class name), and it doesn't help the 18.5% +
  framework-base or 11.5% trait-not-found failures since the bootstrap
  only stubs two specific names.

Fix (v5): stop letting PHPUnit's TestSuiteLoader anywhere near the
file. Build the suite ourselves in PHP and hand a constructed
``TestSuite`` object directly to ``PHPUnit\\TextUI\\Application`` (or
equivalently, run via the ``Framework\\TestRunner`` API).

  Concretely, v5 replaces ``tests/test.sh`` with a script that:

    1. Opportunistic composer dump-autoload (unchanged from v4).
    2. Writes ``/app/run_tests.php``, a PHP harness that:
         a. Sets up composer autoload (if present) and the
            Dockerfile-baked PSR-4 fallback at /app/autoload.php.
         b. Registers a *catch-all* spl_autoload_register that stubs
            any not-yet-defined ``*TestCase`` / ``*TestCase\\<x>`` /
            ``Tests\\<...>\\TestCase`` class as an empty subclass of
            PHPUnit\\Framework\\TestCase, any not-yet-defined trait
            with a name suggesting test infrastructure as an empty
            trait, and any other not-yet-defined class as a trivial
            empty stub. This unblocks the "Class X not found" /
            "Trait Y not found" parent-load failures (~30% of v4
            sample) at the cost of letting tests run against shimmed
            base classes -- many will fail at runtime, but they
            FAIL CLEANLY (failures>0) instead of CRASHING the loader
            (runner_rc!=0, tests_run=0).
         c. class_alias(PHPUnit\\Framework\\TestCase ->
            PHPUnit_Framework_TestCase) BEFORE require'ing
            TestSolution.php (so the un-namespaced legacy parent
            resolves).
         d. eval-defines a stub ``Tests\\TestCase`` extending
            PHPUnit\\Framework\\TestCase BEFORE require.
         e. ``require_once '/tests/TestSolution.php'`` directly. This
            is the load step PHPUnit's TestSuiteLoader would have
            done -- we do it ourselves, so no "Class TestSolution
            cannot be found" basename check happens.
         f. Scans declared classes for any TestCase subclass and
            adds it to a manually-built TestSuite.
         g. Runs the suite via PHPUnit\\TextUI\\Application with a
            minimal in-memory config (no XML), capturing Failures/
            Errors/Tests counts and printing the same summary line
            shape v4 was already parsing.
    3. Invokes ``php /app/run_tests.php`` and captures rc/output.
    4. Parses test output for "OK (...)" / "Tests: N, ..." lines.
    5. Reward=1 iff rc==0 AND tests_run>=1 AND failures==0 AND errors==0.

  Unfixable from a test.sh rewrite:
    - The 21% "setUp() must be compatible ... :void" fatal errors are
      PHPUnit 3/4-era tests that predate PHPUnit 8's mandatory ``: void``
      return on setUp/tearDown/setUpBeforeClass/tearDownAfterClass.
      PHP itself raises a fatal at class compile (before any
      try/catch fires). Workaround would require AST-rewriting the
      TestSolution.php to add ``: void`` -- out of scope. These will
      still register 0% solve rate in v5.
    - The 2% misc fatals (override-final, undefined-method,
      "App did not exist!") are also compile-time fatals.
    - Net expected solve rate ceiling for v5: ~77% of tasks
      *loadable*, of which an unknown fraction will pass with shim
      parents; realistic >0% solve rate target.

Idempotency marker:
  ``# --- laion exp_rpt_stack-php-large-v5 patch: php_runner_no_phpunit_loader ---``

  Distinct from v4's
    ``# --- laion exp_rpt_stack-php-large-v4 patch: phpunit_xml + shim_bootstrap ---``
  v3's
    ``# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---``
  and earlier markers, so grep on any test.sh tells you which
  generation it came from.

Usage:
  python data/patchers/patch_exp_rpt_stack_php_large_v5_tasks.py \\
      --root <dir> [--dry-run] [--limit N]

Constraints:
  - Only ``tests/test.sh`` is touched. ``instruction.md``,
    ``tests/TestSolution.php``, ``environment/Dockerfile``,
    ``task.toml``, etc. are preserved verbatim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PATCH_MARKER = (
    "# --- laion exp_rpt_stack-php-large-v5 patch: php_runner_no_phpunit_loader ---"
)

PRIOR_MARKERS = (
    "# --- laion exp_rpt_stack-php-large-v4 patch: phpunit_xml + shim_bootstrap ---",
    "# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---",
    "# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---",
    "# --- laion v3 patch: tests_found gate ---",
)

# The v5 test.sh writes a PHP harness, runs it via the system php (NOT
# the phpunit phar's CLI), and parses the harness's output. PHPUnit is
# used purely as a library (TestCase / TestSuite / TestRunner) -- never
# as the TestSuiteLoader-driven CLI entrypoint.
NEW_TEST_SH = """#!/bin/bash
# --- laion exp_rpt_stack-php-large-v5 patch: php_runner_no_phpunit_loader ---
# Verifier: gate reward on (a) clean exit AND (b) at least one test run
# AND (c) zero failures/errors.
#
# History:
#   v2 (upstream): scored on phpunit exit code only; rubber-stamped
#       "No tests executed!" as reward=1.
#   v3: tried --fail-on-no-tests (does not exist), then
#       --fail-on-empty-test-suite + positional test file. Hit PHPUnit's
#       strict-basename loadSuiteClassFile rule on 67/200 trials and
#       parent-class-not-found on 133/200.
#   v4: tried <directory suffix="TestSolution.php"> in phpunit.xml,
#       hoping it would route through PHPUnit's Reflection-based scan
#       loader. It does NOT -- TestSuiteMapper still calls addTestFile
#       which still calls loadSuiteClassFile which still does the
#       basename check. 88/200 trials hit "Class TestSolution cannot
#       be found"; 0/200 successful runs.
#   v5 (this file): stop using PHPUnit's TestSuiteLoader entirely.
#       Build the suite ourselves: require_once the test file directly
#       (bypassing the basename rule), reflect to find TestCase
#       subclasses, and run them via PHPUnit-as-library.

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

# Step 0: opportunistic composer dump-autoload so the agent's namespaced
# solution classes resolve when laid out as PSR-4. Cheap if composer.json
# absent or composer not installed.
if [ -f /app/composer.json ] && command -v composer >/dev/null 2>&1; then
    composer dump-autoload --no-dev --classmap-authoritative >/dev/null 2>&1 || true
fi

# Step 1: extract the PHPUnit phar into a directory PHP can include from.
# The /usr/local/bin/phpunit shipped by the Dockerfile is a phar, and
# phar:// includes work natively in PHP, BUT a number of PHPUnit
# internals reference autoload paths that resolve correctly only when
# the phar is "running" as a script. We work around this by `require`ing
# the phar at the top of our runner -- PHP supports `require '/path/to/file.phar'`
# and PHPUnit's phar stub registers its autoloader on require.

# Step 2: emit /app/run_tests.php. Self-contained: stubs unresolvable
# parent classes/traits with catch-all autoload, requires the test
# file directly, then runs whatever TestCase subclasses got declared.
cat > /app/run_tests.php <<'PHPEOF'
<?php
declare(strict_types=1);

// Load PHPUnit as a library. The phpunit phar is self-extracting on
// require: it registers PHPUnit\\Framework\\TestCase etc. into the
// global classloader.
require '/usr/local/bin/phpunit';

// 1. Composer autoload (if the agent set it up).
if (is_file('/app/vendor/autoload.php')) {
    require_once '/app/vendor/autoload.php';
}
// 2. Dockerfile-baked PSR-4 fallback.
if (is_file('/app/autoload.php')) {
    require_once '/app/autoload.php';
}

// 3. Legacy PHPUnit_Framework_TestCase alias. Must happen BEFORE
//    require'ing TestSolution.php, since 26%+ of test files extend
//    this name.
if (class_exists('PHPUnit\\Framework\\TestCase')
        && !class_exists('PHPUnit_Framework_TestCase', false)) {
    class_alias('PHPUnit\\Framework\\TestCase', 'PHPUnit_Framework_TestCase');
}
// PHPUnit_TestCase is another less-common legacy spelling.
if (class_exists('PHPUnit\\Framework\\TestCase')
        && !class_exists('PHPUnit_TestCase', false)) {
    class_alias('PHPUnit\\Framework\\TestCase', 'PHPUnit_TestCase');
}

// 4. Tests\\TestCase stub (Laravel etc., ~6% of tasks). Must exist
//    before TestSolution.php is loaded.
if (!class_exists('Tests\\TestCase', false)) {
    eval('namespace Tests; class TestCase extends \\PHPUnit\\Framework\\TestCase {}');
}

// 5. CATCH-ALL autoloader. Registered LAST so it only fires for symbols
//    nothing else could resolve. Stubs each unresolved name with a
//    sensible default so the require_once below doesn't fatal.
//
//    Heuristic:
//      - if name ends in "TestCase" or "TestCaseTrait" or "Trait" with
//        "Test" in it -> declare as an empty subclass of TestCase OR
//        an empty trait.
//      - if name contains "Interface" suffix -> declare empty interface.
//      - if name starts with "Trait" or ends in "Trait" -> declare
//        empty trait.
//      - otherwise -> declare as an empty class.
//
//    Stubs are namespace-aware via eval'd code.
spl_autoload_register(function (string $name): void {
    // Don't shim PHPUnit's own classes or PHP built-ins.
    if (strncmp($name, 'PHPUnit\\\\', 8) === 0) { return; }
    if (strncmp($name, 'SebastianBergmann\\\\', 19) === 0) { return; }

    // Parse namespace + short name.
    $pos = strrpos($name, '\\\\');
    if ($pos === false) {
        $ns = '';
        $short = $name;
        $fqExt = '\\\\PHPUnit\\\\Framework\\\\TestCase';
    } else {
        $ns = substr($name, 0, $pos);
        $short = substr($name, $pos + 1);
        $fqExt = '\\\\PHPUnit\\\\Framework\\\\TestCase';
    }

    $isInterface = (substr($short, -9) === 'Interface');
    $isTrait     = (substr($short, -5) === 'Trait')
                    || (strpos($short, 'Trait') !== false && stripos($short, 'Test') !== false);
    $isTestBase  = (substr($short, -8) === 'TestCase')
                    || (substr($short, -4) === 'Test' && strpos($short, 'TestCase') !== false);

    if ($isInterface) {
        $code = $ns === ''
            ? "interface {$short} {}"
            : "namespace {$ns}; interface {$short} {}";
    } elseif ($isTrait) {
        $code = $ns === ''
            ? "trait {$short} {}"
            : "namespace {$ns}; trait {$short} {}";
    } elseif ($isTestBase) {
        $code = $ns === ''
            ? "class {$short} extends {$fqExt} {}"
            : "namespace {$ns}; class {$short} extends {$fqExt} {}";
    } else {
        // Generic class stub. Most "Class \"X\" not found" cases where X is
        // a project-specific Controller/Service/etc. land here. Tests
        // referencing them at runtime will fail (failures>0) but at
        // least the file will LOAD.
        $code = $ns === ''
            ? "class {$short} {}"
            : "namespace {$ns}; class {$short} {}";
    }
    @eval($code);
});

// 6. Snapshot already-declared classes so we can identify which ones
//    were defined by TestSolution.php itself.
$pre = get_declared_classes();
$preSet = array_flip($pre);

// 7. Require the test file directly. THIS is the load PHPUnit's
//    TestSuiteLoader would have done -- we do it here ourselves,
//    bypassing the strict-basename rule.
$err = null;
try {
    require_once '/tests/TestSolution.php';
} catch (\\Throwable $t) {
    $err = $t;
}

if ($err !== null) {
    fwrite(STDERR, "TestSolution.php load failed: " . $err->getMessage() . "\\n");
    fwrite(STDERR, $err->getTraceAsString() . "\\n");
    echo "v5 harness: Tests: 0, Assertions: 0, Failures: 0, Errors: 1\\n";
    exit(2);
}

// 8. Find any newly-declared TestCase subclass.
$post = get_declared_classes();
$newClasses = array_diff($post, $pre);
$testClasses = [];
foreach ($newClasses as $cls) {
    try {
        $rc = new \\ReflectionClass($cls);
        if ($rc->isAbstract()) { continue; }
        if ($rc->isSubclassOf('PHPUnit\\Framework\\TestCase')) {
            $testClasses[] = $cls;
        }
    } catch (\\Throwable $t) { /* ignore broken reflections */ }
}

if (empty($testClasses)) {
    fwrite(STDERR, "No TestCase subclasses found after loading /tests/TestSolution.php\\n");
    echo "v5 harness: Tests: 0, Assertions: 0, Failures: 0, Errors: 1\\n";
    exit(3);
}

// 9. Run tests via PHPUnit-as-library WITHOUT going through
//    TestSuite::fromClassReflector / addTestSuite. That path requires
//    PHPUnit\\TextUI\\Configuration\\Registry to be initialized
//    (which only happens when phpunit is run as a CLI Application).
//    We don't want the Application because it brings back the
//    TestSuiteLoader basename rule we're trying to escape.
//
//    Instead: walk each TestCase reflection class, find its public
//    test methods (methods starting with "test" OR having a @test
//    docblock), instantiate the TestCase with the method name in its
//    constructor, and call ->runBare() on each instance. This is the
//    minimal public-API pattern that works on PHPUnit 9/10 without
//    Registry initialization.
$tests       = 0;
$assertions  = 0;
$failures    = 0;
$errors      = 0;
$skipped     = 0;
$failureMsgs = [];

foreach ($testClasses as $cls) {
    try {
        $refl = new \\ReflectionClass($cls);
    } catch (\\Throwable $t) {
        $errors++;
        $failureMsgs[] = "ERROR reflecting {$cls}: " . $t->getMessage();
        continue;
    }
    if ($refl->isAbstract()) { continue; }

    $methods = [];
    foreach ($refl->getMethods(\\ReflectionMethod::IS_PUBLIC) as $m) {
        if ($m->isStatic() || $m->isConstructor() || $m->isDestructor()) { continue; }
        $declaringName = $m->getDeclaringClass()->getName();
        if ($declaringName === 'PHPUnit\\Framework\\TestCase') { continue; }
        if (strncmp($declaringName, 'PHPUnit\\\\', 8) === 0) { continue; }
        $name = $m->getName();
        if (strncmp($name, 'test', 4) === 0) { $methods[] = $name; continue; }
        $doc = $m->getDocComment();
        if (is_string($doc) && strpos($doc, '@test') !== false) { $methods[] = $name; }
    }

    foreach ($methods as $methodName) {
        try {
            $test = new $cls($methodName);
        } catch (\\Throwable $t) {
            $errors++;
            $failureMsgs[] = "ERROR instantiating {$cls}::{$methodName}: " . $t->getMessage();
            continue;
        }
        $tests++;
        try {
            $test->runBare();
            $assertions += $test->numberOfAssertionsPerformed();
        } catch (\\PHPUnit\\Framework\\SkippedTest $e) {
            $skipped++;
            $assertions += $test->numberOfAssertionsPerformed();
        } catch (\\PHPUnit\\Framework\\IncompleteTest $e) {
            $skipped++;
            $assertions += $test->numberOfAssertionsPerformed();
        } catch (\\PHPUnit\\Framework\\AssertionFailedError $e) {
            $failures++;
            $assertions += $test->numberOfAssertionsPerformed();
            $failureMsgs[] = sprintf("FAILURE in %s::%s : %s",
                $cls, $methodName, $e->getMessage());
        } catch (\\Throwable $e) {
            $errors++;
            $assertions += $test->numberOfAssertionsPerformed();
            $failureMsgs[] = sprintf("ERROR in %s::%s : %s (%s)",
                $cls, $methodName, $e->getMessage(), get_class($e));
        }
    }
}

// 10. Print summary in a shape the bash gate below can parse. We emit
//     BOTH PHPUnit-10-style "Tests: X, Assertions: Y, Failures: Z,
//     Errors: W" AND, if everything passed, the "OK (N tests, M assertions)"
//     line.
if ($failures === 0 && $errors === 0 && $tests > 0) {
    printf("OK (%d tests, %d assertions)\\n", $tests, $assertions);
}
printf("Tests: %d, Assertions: %d, Failures: %d, Errors: %d, Skipped: %d\\n",
    $tests, $assertions, $failures, $errors, $skipped);

foreach ($failureMsgs as $msg) {
    echo "  - $msg\\n";
}

if ($failures > 0 || $errors > 0) {
    exit(1);
}
exit(0);
PHPEOF

echo "Running PHPUnit tests (v5 harness)..."
php /app/run_tests.php 2>&1 | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# Parse output. v5 harness prints both PHPUnit-style lines.
ok_line=$(grep -oE 'OK \\([0-9]+ tests?, [0-9]+ assertions?\\)' \\
    /logs/verifier/test_output.txt | tail -1)
detail_line=$(grep -oE 'Tests: [0-9]+(, Assertions: [0-9]+)?(, Failures: [0-9]+)?(, Errors: [0-9]+)?' \\
    /logs/verifier/test_output.txt | tail -1)

tests_run=0
failures=0
errors=0
if [ -n "$ok_line" ]; then
    tests_run=$(echo "$ok_line" | grep -oE '[0-9]+' | head -1)
elif [ -n "$detail_line" ]; then
    tests_run=$(echo "$detail_line" | grep -oE 'Tests: [0-9]+' | grep -oE '[0-9]+' | head -1)
    failures=$(echo "$detail_line" | grep -oE 'Failures: [0-9]+' | grep -oE '[0-9]+' | head -1)
    errors=$(echo "$detail_line"   | grep -oE 'Errors: [0-9]+'   | grep -oE '[0-9]+' | head -1)
fi
tests_run=${tests_run:-0}
failures=${failures:-0}
errors=${errors:-0}

echo "exp_rpt_stack-php-large-v5 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

if [ "$runner_rc" -eq 0 ] \\
        && [ "$tests_run" -ge 1 ] \\
        && [ "$failures" -eq 0 ] \\
        && [ "$errors" -eq 0 ]; then
    echo "1" > /logs/verifier/reward.txt
    exit 0
else
    echo "0" > /logs/verifier/reward.txt
    if [ "$runner_rc" -ne 0 ]; then exit "$runner_rc"; fi
    exit 1
fi
"""


def patch_one(test_sh: Path, dry_run: bool) -> str:
    """Patch a single tests/test.sh file. Returns one of:
    'patched_from_v4', 'patched_from_v3', 'patched_from_v2',
    'patched_unusual', 'already', 'missing', 'skipped_no_phpunit',
    'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if PATCH_MARKER in existing:
        return "already"

    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    if PRIOR_MARKERS[0] in existing:
        source = "patched_from_v4"
    elif PRIOR_MARKERS[1] in existing:
        source = "patched_from_v3"
    elif PRIOR_MARKERS[2] in existing or "--fail-on-no-tests" in existing:
        source = "patched_from_v2"
    elif PRIOR_MARKERS[3] in existing:
        source = "patched_from_v2"
    else:
        source = "patched_unusual"

    if not dry_run:
        test_sh.write_text(NEW_TEST_SH, encoding="utf-8")
    return source


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="Path to extracted tasks root")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    task_dirs = sorted(d for d in root.iterdir() if d.is_dir())
    if args.limit:
        task_dirs = task_dirs[: args.limit]

    n_total = len(task_dirs)
    counts = {
        "patched_from_v4": 0,
        "patched_from_v3": 0,
        "patched_from_v2": 0,
        "patched_unusual": 0,
        "already": 0,
        "missing": 0,
        "skipped_no_phpunit": 0,
        "unparseable": 0,
    }

    for i, td in enumerate(task_dirs, 1):
        test_sh = td / "tests" / "test.sh"
        result = patch_one(test_sh, dry_run=args.dry_run)
        counts[result] = counts.get(result, 0) + 1

        if i % 1000 == 0 or i == n_total:
            print(
                f"[{i}/{n_total}] "
                f"from_v4={counts['patched_from_v4']} "
                f"from_v3={counts['patched_from_v3']} "
                f"from_v2={counts['patched_from_v2']} "
                f"unusual={counts['patched_unusual']} "
                f"already={counts['already']} "
                f"missing={counts['missing']} "
                f"skipped_no_phpunit={counts['skipped_no_phpunit']} "
                f"unparseable={counts['unparseable']}",
                flush=True,
            )

    print(
        f"\nDone. total={n_total} "
        f"patched_from_v4={counts['patched_from_v4']} "
        f"patched_from_v3={counts['patched_from_v3']} "
        f"patched_from_v2={counts['patched_from_v2']} "
        f"patched_unusual={counts['patched_unusual']} "
        f"already_patched={counts['already']} "
        f"missing={counts['missing']} "
        f"skipped_no_phpunit={counts['skipped_no_phpunit']} "
        f"unparseable={counts['unparseable']} "
        f"(dry_run={args.dry_run})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
