#!/usr/bin/env python3
"""
exp_rpt_stack-php-large-v3 -> v4 patcher.

Observed v3 failure mode (QC 2026-05-16, 200-trial sample from
``laion/exp_rpt_stack-php-large-v3/traces/``):

  v3 successfully removed the bogus ``--fail-on-no-tests`` option-parse
  crash, but **still produced 0/200 reward=1 trials**. Every trial failed
  at *test class loading*. Two distinct (and overlapping) loader bugs:

    1. **PHPUnit's strict "file basename must match class name" rule**.
       v3 invoked phpunit with the test file as a positional arg
       (``phpunit ... /tests/TestSolution.php``). PHPUnit 10's
       ``Runner\\TestSuiteLoader::load($path)`` requires the file to
       define a class whose name matches the file's basename
       (``TestSolution``). Every task in this dataset has TestSolution.php
       containing a class named after the upstream codebase
       (``EditorTest``, ``ContainerAwareRequestExecutorTest``,
       ``AuthTest``, ``SwitchUserListenerTest``, etc.) — NOT ``TestSolution``.
       Result: ``Class TestSolution cannot be found in /tests/TestSolution.php``
       on 67 / 200 sampled trials.

    2. **Missing legacy / framework parent test base classes.** Even when
       the basename rule didn't fire (because the class extended e.g.
       ``\\PHPUnit_Framework_TestCase`` whose autoload triggers earlier),
       the file's parent class couldn't be resolved. 133 / 200 trials in
       v3 sample failed with ``Class "X" not found`` errors where X is
       one of: ``PHPUnit_Framework_TestCase`` (46), ``Tests\\TestCase``
       (12), ``Cake\\TestSuite\\TestCase``, ``Orchestra\\Testbench\\TestCase``,
       and a long tail of project-specific bases.

  Sample-wide distribution of the 200 v3 verifier outputs:

      67  Class TestSolution cannot be found
      46  Class "PHPUnit_Framework_TestCase" not found
      13  must be compatible with PHPUnit (signature drift)
      12  Class "Tests\\TestCase" not found
      10  require_once Failed to open stream
       0  OK (...) or Tests: ... line  (zero successful runs)

  Categorising the full 500-task sample of TestSolution.php class
  declarations:
      207  extends PHPUnit\\Framework\\TestCase     (41.4%, immediately
                                                    fixable via fix #1)
      150  extends [\\]PHPUnit_Framework_TestCase    (30.0%, fixable with
                                                    class_alias shim)
       35  extends Tests\\TestCase (Laravel-style)   (7.0%, fixable with
                                                    shim)
      ~108 other framework bases (Cake, Orchestra,  (~21.6%, mostly
                                  Yii, custom)      unfixable without
                                                    full upstream
                                                    composer install)

  So a verifier-only fix can realistically rescue 70-80% of tasks
  (the simple-extends-PHPUnit and PHPUnit-4/5-alias cases). The
  long-tail framework-specific tasks would need per-task composer
  installs and are out of scope for a test.sh rewrite.

Fix (v4):

  1. **Replace positional-file invocation with phpunit.xml directory
     scan**. PHPUnit 10's ``<directory suffix="...">`` test discovery
     uses ``Reflection::loadClassFromFile`` (which scans for ANY
     ``TestCase``-extending class in the file) instead of the
     strict-basename ``loadSuiteClassFile``. This bypasses the
     "Class TestSolution cannot be found" bug entirely.

  2. **Bootstrap with a legacy-shims file** that pre-defines
     ``PHPUnit_Framework_TestCase`` as a ``class_alias`` for
     ``PHPUnit\\Framework\\TestCase``, defines a trivial ``Tests\\TestCase``
     extending the same, and registers a generous spl_autoload
     fallback. Falls through to ``/app/vendor/autoload.php`` if the
     agent ran composer, then to ``/app/autoload.php`` (baked into
     the Dockerfile).

  3. **Opportunistic ``composer dump-autoload``** if /app/composer.json
     exists, so the agent's namespaced solution classes resolve when
     they're put in non-trivial directory layouts.

  4. **Keep the v3 tests_found gate**. Reward=1 iff runner_rc==0 AND
     tests_run >= 1 AND failures == 0 AND errors == 0.

Idempotency marker:
  ``# --- laion exp_rpt_stack-php-large-v4 patch: phpunit_xml + shim_bootstrap ---``

Distinct from v3's
  ``# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---``
so a grep on any test.sh tells you which generation it came from.

Cross-flag: the sibling dataset ``laion/exp_rpt_stack-php-v2-v3`` has a
DIFFERENT bug at the moment (200 / 200 trials die with ``Test file
"/app/tests/TestSolution.php" not found`` — that patcher's phpunit.xml
hardcoded /app/tests instead of /tests as the upload target). Once
that path bug is fixed it will surface this same family of issues
(strict basename + missing-parent) and should reuse this file's
NEW_TEST_SH template (just adjust the marker comment).

Usage:
  python data/patchers/patch_exp_rpt_stack_php_large_v4_tasks.py \\
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

# Idempotency marker -- distinct from v3 / earlier markers.
PATCH_MARKER = (
    "# --- laion exp_rpt_stack-php-large-v4 patch: phpunit_xml + shim_bootstrap ---"
)

# Markers from earlier patch generations -- we want to overwrite any of these.
PRIOR_MARKERS = (
    "# --- laion exp_rpt_stack-php-large-v3 patch: tests_found gate ---",
    "# --- laion exp_rpt_stack-php-v2 patch: tests_found gate ---",
    "# --- laion v3 patch: tests_found gate ---",
)

# Replacement test.sh body. Two big changes vs. v3:
#   (a) emit phpunit.xml with <directory suffix="TestSolution.php"> so
#       PHPUnit uses its scan-based class loader (Reflection-based) instead
#       of the strict-basename ``loadSuiteClassFile`` path that requires
#       the file's basename to match the contained class name. Roughly half
#       the v3 trial failures (67/200) were the basename mismatch.
#   (b) write a /app/phpunit_bootstrap.php that:
#         - registers an spl_autoload fallback for /app classes,
#         - class_aliases PHPUnit_Framework_TestCase -> PHPUnit\Framework\TestCase
#           (PHPUnit 4/5/6 legacy classname; another ~30% of v3 trial
#           failures),
#         - defines a trivial Tests\TestCase that extends
#           PHPUnit\Framework\TestCase (Laravel-style; another ~7%),
#         - falls through to vendor/autoload.php if composer was run.
#       Then phpunit.xml's ``bootstrap=`` attribute loads this file.
#   (c) ``composer dump-autoload --no-dev --classmap-authoritative`` is
#       run opportunistically if /app/composer.json exists, so agent
#       solution classes in namespaced subdirs resolve.
NEW_TEST_SH = """#!/bin/bash
# --- laion exp_rpt_stack-php-large-v4 patch: phpunit_xml + shim_bootstrap ---
# Verifier: gate reward on (a) clean PHPUnit exit AND (b) PHPUnit
# reporting at least one test actually executed (and zero failures/errors).
#
# History:
#   v2 (upstream): scored on phpunit exit code only; rubber-stamped
#       "No tests executed!" runs as reward=1.
#   v3 (broken via --fail-on-no-tests): every trial died at PHPUnit
#       option parse before any test ran.
#   v3 (current laion/exp_rpt_stack-php-large-v3): fixed option parse
#       (used --fail-on-empty-test-suite + named test file positionally)
#       but every trial died at *class load* because (1) PHPUnit's
#       strict basename rule requires the file TestSolution.php to
#       define a class named TestSolution, and (2) parent classes like
#       PHPUnit_Framework_TestCase / Tests\\TestCase couldn't autoload.
#       0 / 200 trials produced "Tests: N" or "OK (N tests)" lines.
#   v4 (this file): switch to phpunit.xml <directory> scan-based loader
#       (bypasses the basename rule), bootstrap with class_alias shims
#       for the two most common legacy bases (PHPUnit_Framework_TestCase
#       + Tests\\TestCase, covering an additional ~37% of tasks beyond
#       the 41% of "extends PHPUnit\\Framework\\TestCase" tasks that v3
#       already in-principle supported).

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

# Step 0: opportunistic composer dump-autoload so the agent's namespaced
# solution classes resolve when laid out as PSR-4. Cheap if composer.json
# absent or composer not installed -- redirected to /dev/null in either
# case. The Dockerfile installs composer at /usr/local/bin/composer.
if [ -f /app/composer.json ] && command -v composer >/dev/null 2>&1; then
    composer dump-autoload --no-dev --classmap-authoritative >/dev/null 2>&1 || true
fi

# Step 1: write the bootstrap shim. This runs BEFORE phpunit loads any
# tests. We define common legacy parent classes here so the test class
# autoloader doesn't choke on `class FooTest extends PHPUnit_Framework_TestCase`.
cat > /app/phpunit_bootstrap.php <<'BOOTSTRAP_EOF'
<?php
// Generated by laion exp_rpt_stack-php-large-v4 patcher.
// Two responsibilities:
//   1. Make common legacy PHPUnit base classes resolvable so test class
//      load doesn't fail before any test method runs.
//   2. Fall through to /app/vendor/autoload.php (composer) if present,
//      else /app/autoload.php (Dockerfile-baked spl_autoload).

// Pull in PHPUnit's namespaced TestCase. The phpunit.phar autoloads this
// when phpunit itself starts, but we reference it eagerly so the
// class_alias below can find it.
if (!class_exists('PHPUnit\\Framework\\TestCase', false)) {
    // Trigger autoload via a harmless reference.
    @class_exists('PHPUnit\\Framework\\TestCase');
}

// PHPUnit 4/5/6 used the un-namespaced PHPUnit_Framework_TestCase name.
// 30% of TestSolution.php files in this dataset still extend that.
// class_alias is the canonical fix.
if (class_exists('PHPUnit\\Framework\\TestCase') && !class_exists('PHPUnit_Framework_TestCase', false)) {
    class_alias('PHPUnit\\Framework\\TestCase', 'PHPUnit_Framework_TestCase');
}

// Laravel-style Tests\\TestCase: 7% of tasks. We give it the bare-minimum
// stub (just extends PHPUnit core). Any Laravel-specific helpers the
// test relies on will fail at runtime, but at least the class loads.
if (class_exists('PHPUnit\\Framework\\TestCase') && !class_exists('Tests\\TestCase', false)) {
    eval('namespace Tests; class TestCase extends \\PHPUnit\\Framework\\TestCase {}');
}

// Project-baked composer autoload (if the agent ran `composer install`
// or `composer dump-autoload`).
if (is_file('/app/vendor/autoload.php')) {
    require_once '/app/vendor/autoload.php';
}

// Dockerfile-baked PSR-4-ish fallback: /app/Foo/Bar.php for class Foo\\Bar
if (is_file('/app/autoload.php')) {
    require_once '/app/autoload.php';
} else {
    // Emit one inline if even the Dockerfile-baked file is missing.
    spl_autoload_register(function($class) {
        $file = '/app/' . str_replace('\\\\', '/', $class) . '.php';
        if (file_exists($file)) { require_once $file; }
    });
}
BOOTSTRAP_EOF

# Step 2: write phpunit.xml.
#   <directory suffix="TestSolution.php">/tests</directory>
#     -> PHPUnit walks /tests, picks files ending in TestSolution.php
#        (one such file: /tests/TestSolution.php), and uses the
#        ``Reflection``-based class loader that DOES NOT require the
#        file basename to match the contained class name. This was the
#        principal v3 -> v4 fix.
#   bootstrap="/app/phpunit_bootstrap.php"
#     -> loads our shim file above before tests run.
#   failOnEmptyTestSuite="true"
#     -> exit non-zero if zero tests collected (replaces the
#        non-existent --fail-on-no-tests CLI flag).
#   beStrictAboutOutputDuringTests="false"
#     -> stray echoes from autoloaders don't get escalated to failures.
cat > /app/phpunit.xml <<'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/10.5/phpunit.xsd"
    bootstrap="/app/phpunit_bootstrap.php"
    cacheDirectory=".phpunit.cache"
    executionOrder="default"
    beStrictAboutOutputDuringTests="false"
    failOnEmptyTestSuite="true"
    colors="false">
    <testsuites>
        <testsuite name="solution">
            <directory suffix="TestSolution.php">/tests</directory>
        </testsuite>
    </testsuites>
</phpunit>
XMLEOF

echo "Running PHPUnit tests..."
# --fail-on-skipped is a real PHPUnit 10.5 flag (belt-and-suspenders;
# the no-tests-collected case is handled by failOnEmptyTestSuite in
# the XML).
phpunit --configuration /app/phpunit.xml --fail-on-skipped 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${PIPESTATUS[0]}

# PHPUnit 10 summary line shapes:
#   "OK (3 tests, 5 assertions)"
#   "Tests: 3, Assertions: 5, Failures: 0, Errors: 0"
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

echo "exp_rpt_stack-php-large-v4 verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

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
    'patched_from_v3', 'patched_from_v2', 'patched_unusual',
    'already', 'missing', 'skipped_no_phpunit', 'unparseable'.
    """
    if not test_sh.is_file():
        return "missing"
    try:
        existing = test_sh.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unparseable"
    if PATCH_MARKER in existing:
        return "already"

    # Skip tasks whose test.sh doesn't actually invoke phpunit -- they're
    # not PHPUnit tasks (or use some other harness) and we'd corrupt them
    # by replacing the file with our PHPUnit-specific gate.
    if "phpunit" not in existing.lower():
        return "skipped_no_phpunit"

    # Classify what we're overwriting (forensic; result is the same body).
    if PRIOR_MARKERS[0] in existing:
        source = "patched_from_v3"
    elif PRIOR_MARKERS[1] in existing or "--fail-on-no-tests" in existing:
        source = "patched_from_v2"
    elif PRIOR_MARKERS[2] in existing:
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
