#!/usr/bin/env python3
"""Shared helpers for stack-php* test.sh patchers.

Both ``laion/exp_rpt_stack-php-v2`` and ``laion/exp_rpt_stack-php-large``
share the same Harbor mount layout (`tests/` at `/tests/`, `app/` at `/app/`)
and the same Dockerfile-baked PHPUnit 10.5 / composer toolchain. Their v4
generations both failed at 0% solve rate with the SAME family of bugs at
test-class load time:

1. **PHPUnit's strict file-basename rule**
   ``Runner\\TestSuiteLoader::load($path)`` requires the file basename
   ("TestSolution") to match a declared class inside the file. The actual
   class declared in ``/tests/TestSolution.php`` is named after the upstream
   codebase (``EditorTest``, ``AuthTest``, etc.). v4 of both datasets tried
   to bypass this — large-v4 via ``<directory suffix>`` (still uses
   `loadSuiteClassFile` -> still fails), v2-v4 via positional file arg
   (also uses `loadSuiteClassFile` -> also fails). Result: ~30-65% of
   trials fail at this gate with ``Class TestSolution cannot be found``.

2. **Missing legacy / framework parent test base classes**
   PHPUnit 4-6 era code extends ``PHPUnit_Framework_TestCase``;
   Laravel-style tests extend ``Tests\\TestCase``; CakePHP/Yii/Orchestra/
   Zend variants have their own bases. The container only ships PHPUnit
   10.5 with the namespaced ``PHPUnit\\Framework\\TestCase``; the upstream
   framework is not installed. ~25-45% of trials fail with
   ``Class "X" not found`` for X in this list.

3. **PHP method-signature drift across PHPUnit major versions**
   ``setUp()`` and ``tearDown()`` changed from ``public function`` (no
   return type) in PHPUnit 6 to ``protected function ...(): void`` in
   PHPUnit 9+. Test classes carrying the older signature get a PHP
   fatal "Declaration of X::setUp() must be compatible with Y::setUp(): void"
   at class load. ~10-25% of trials hit this. Not fixable without rewriting
   TestSolution.php (which we are forbidden from touching).

v5 strategy (the body returned by ``new_test_sh``):

  Step 0: ``composer dump-autoload`` if /app/composer.json exists, so PSR-4
          namespaced solution classes the agent wrote can resolve.

  Step 1: Write a /app/phpunit_bootstrap.php that does FIVE things, in
          order:
            a. Eagerly autoloads ``PHPUnit\\Framework\\TestCase`` so the
               aliases below find a real target.
            b. ``class_alias`` for the un-namespaced
               ``PHPUnit_Framework_TestCase`` (PHPUnit 4/5/6 legacy name).
            c. Defines a trivial ``Tests\\TestCase`` stub extending the
               namespaced one (Laravel/Lumen-style).
            d. require_once's /app/vendor/autoload.php (composer) and
               /app/autoload.php (Dockerfile baked) so the test file's
               ``use Foo\\Bar;`` lines resolve.
            e. **The critical step**: pre-include /tests/TestSolution.php
               itself, then walk ``get_declared_classes()`` to find the
               first class that extends ``PHPUnit\\Framework\\TestCase``,
               then ``class_alias`` that class as ``TestSolution`` so
               PHPUnit's basename rule is satisfied. The TestSolution.php
               require_once may emit fatal errors (signature drift, missing
               parents); we wrap with ``try/catch \\Throwable`` so the rest
               of the bootstrap still runs.

  Step 2: Write /app/phpunit.xml with bootstrap=phpunit_bootstrap.php AND
          ``<file>/tests/TestSolution.php</file>`` as the test target.
          Since our bootstrap pre-loaded everything and created the
          TestSolution alias, when PHPUnit later does its require_once +
          basename lookup, the require_once is a no-op (file already
          loaded) and the basename lookup finds our alias.

  Step 3: Invoke ``phpunit --configuration /app/phpunit.xml`` and parse
          the standard "OK (N tests, M assertions)" / "Tests: N, ..."
          summary lines. Reward = 1 iff runner_rc==0 AND tests_run >= 1
          AND failures == 0 AND errors == 0.

Idempotency: the caller passes ``dataset_tag`` (e.g. ``stack-php-v2-v5``)
which gets embedded into the marker comment and the verifier log line so
``grep`` on a test.sh tells you which generation+dataset it came from.
"""

from __future__ import annotations


def new_test_sh(dataset_tag: str) -> str:
    """Return the v5 test.sh body for a given dataset tag.

    Args:
        dataset_tag: e.g. ``"stack-php-v2-v5"`` or ``"stack-php-large-v5"``.
            Embedded in the patch marker comment + verifier log line.
    """
    marker = patch_marker(dataset_tag)
    # We use a triple-quoted f-string so the marker / dataset_tag are
    # interpolated, but every ``$variable`` and ``${variable}`` reference
    # in the shell body must use double braces ``{{`` ``}}`` to escape the
    # f-string. We also escape ``\\`` -> ``\\\\`` in PHP namespace strings
    # because Python str literal eats one layer.
    return f"""#!/bin/bash
{marker}
# Verifier for {dataset_tag}: gate reward on (a) clean PHPUnit exit AND
# (b) PHPUnit reporting at least one test actually executed (and zero
# failures/errors). Uses bootstrap-side class_alias to bypass PHPUnit 10's
# strict file-basename rule, plus class_alias shims for the two most
# common legacy parent test-case classes (PHPUnit_Framework_TestCase,
# Tests\\TestCase).
#
# See data/patchers/_stack_php_common.py for the full design discussion
# and the failure-mode distribution that motivated each step.

set +e
mkdir -p /logs/verifier
echo "0" > /logs/verifier/reward.txt
cd /app

# --- Step 0: opportunistic composer dump-autoload ---
# Cheap if composer.json absent or composer not installed.
if [ -f /app/composer.json ] && command -v composer >/dev/null 2>&1; then
    composer dump-autoload --no-dev --classmap-authoritative >/dev/null 2>&1 || true
fi

# --- Step 1: write the bootstrap shim ---
# Five responsibilities, see the module-level docstring of
# _stack_php_common.py.
cat > /app/phpunit_bootstrap.php <<'BOOTSTRAP_EOF'
<?php
// Generated by laion {dataset_tag} patcher. Do not edit in-place.

// (a) Eagerly autoload the namespaced PHPUnit TestCase so the
//     class_alias below can resolve.
if (!class_exists('PHPUnit\\\\Framework\\\\TestCase', true)) {{
    @class_exists('PHPUnit\\\\Framework\\\\TestCase');
}}

// (b) class_alias for PHPUnit 4/5/6 era un-namespaced base class.
if (class_exists('PHPUnit\\\\Framework\\\\TestCase')
        && !class_exists('PHPUnit_Framework_TestCase', false)) {{
    class_alias('PHPUnit\\\\Framework\\\\TestCase', 'PHPUnit_Framework_TestCase');
}}

// (c) Laravel/Lumen-style Tests\\TestCase stub. Bare-minimum: just
//     extends PHPUnit core. Any Laravel-specific helpers the test
//     relies on will fail at runtime, but at least the class loads.
if (class_exists('PHPUnit\\\\Framework\\\\TestCase')
        && !class_exists('Tests\\\\TestCase', false)) {{
    eval('namespace Tests; class TestCase extends \\\\PHPUnit\\\\Framework\\\\TestCase {{}}');
}}

// (d) Project-baked autoload chain. Both files may be absent.
if (is_file('/app/vendor/autoload.php')) {{
    @require_once '/app/vendor/autoload.php';
}}
if (is_file('/app/autoload.php')) {{
    @require_once '/app/autoload.php';
}} else if (!is_file('/app/vendor/autoload.php')) {{
    // Last-resort spl_autoload: /app/Foo/Bar.php for class Foo\\Bar
    spl_autoload_register(function($class) {{
        $file = '/app/' . str_replace('\\\\', '/', $class) . '.php';
        if (file_exists($file)) {{ require_once $file; }}
    }});
}}

// (e) Pre-include TestSolution.php and alias its declared test class
//     as TestSolution so PHPUnit's basename rule passes. Wrapped in
//     try/catch so a fatal-on-include (signature drift, missing parent)
//     doesn't kill the bootstrap entirely — PHPUnit will then report
//     a clean error rather than a phar-trace.
$pre = get_declared_classes();
try {{
    @require_once '/tests/TestSolution.php';
}} catch (\\Throwable $e) {{
    // fall through; if the class load failed there's nothing to alias.
}}
if (!class_exists('TestSolution', false)) {{
    $candidate = null;
    foreach (get_declared_classes() as $c) {{
        if (in_array($c, $pre, true)) {{ continue; }}
        // Only consider classes defined IN /tests/TestSolution.php.
        try {{
            $rc = new \\ReflectionClass($c);
            if ($rc->getFileName() !== '/tests/TestSolution.php') {{ continue; }}
            if (!$rc->isSubclassOf('PHPUnit\\\\Framework\\\\TestCase')) {{ continue; }}
            $candidate = $c;
            break;
        }} catch (\\Throwable $e) {{
            continue;
        }}
    }}
    if ($candidate !== null) {{
        class_alias($candidate, 'TestSolution');
    }}
}}
BOOTSTRAP_EOF

# --- Step 2: write phpunit.xml ---
# Uses <file> form (not <directory suffix>) so we point at the exact
# file. Both forms ultimately invoke loadSuiteClassFile, but with our
# bootstrap-side class_alias above the basename lookup succeeds.
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
            <file>/tests/TestSolution.php</file>
        </testsuite>
    </testsuites>
</phpunit>
XMLEOF

# --- Step 3: run phpunit + parse summary ---
echo "Running PHPUnit tests..."
phpunit --configuration /app/phpunit.xml --fail-on-skipped 2>&1 \\
    | tee /logs/verifier/test_output.txt
runner_rc=${{PIPESTATUS[0]}}

# PHPUnit 10 summary line shapes (most common first):
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
tests_run=${{tests_run:-0}}
failures=${{failures:-0}}
errors=${{errors:-0}}

echo "{dataset_tag} verifier: runner_rc=$runner_rc tests_run=$tests_run failures=$failures errors=$errors"

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


def patch_marker(dataset_tag: str) -> str:
    """Idempotency marker line (also appears in the generated test.sh)."""
    return f"# --- laion {dataset_tag} patch: alias_TestSolution + shim_bootstrap ---"
