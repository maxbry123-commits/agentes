/**
 * Property-Based Tests for Version Checking
 * 
 * **Feature: agentguard, Property 0: Node.js version requirement**
 * **Validates: Requirements 19.2**
 */

import { describe, test, expect } from 'vitest';
import * as fc from 'fast-check';
import { checkNodeVersion, compareVersions } from '../../src/version-checker';

describe('Property 0: Node.js version requirement', () => {
  /**
   * Property: For any Node.js version string, when checking against the minimum
   * required version (18.0.0), the system should correctly identify whether the
   * version is compatible and provide an appropriate error message if not.
   */
  test('**Feature: agentguard, Property 0: Node.js version requirement**', () => {
    // Generator for semantic version strings
    const versionGenerator = fc.tuple(
      fc.integer({ min: 0, max: 30 }), // major
      fc.integer({ min: 0, max: 50 }), // minor
      fc.integer({ min: 0, max: 100 }) // patch
    ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`);

    fc.assert(
      fc.property(versionGenerator, (version) => {
        // Mock process.version for testing
        const originalVersion = process.version;
        Object.defineProperty(process, 'version', {
          value: `v${version}`,
          writable: true,
          configurable: true
        });

        try {
          const result = checkNodeVersion('18.0.0');

          // Parse version to determine expected compatibility
          const [major] = version.split('.').map(Number);
          const expectedCompatible = major >= 18;

          // Verify compatibility check is correct
          expect(result.isCompatible).toBe(expectedCompatible);
          expect(result.currentVersion).toBe(version);
          expect(result.requiredVersion).toBe('18.0.0');

          // If incompatible, should have error message
          if (!expectedCompatible) {
            expect(result.errorMessage).toBeDefined();
            expect(result.errorMessage).toContain('AgentGuard requires Node.js');
            expect(result.errorMessage).toContain('18.0.0');
            expect(result.errorMessage).toContain(version);
          } else {
            // If compatible, should not have error message
            expect(result.errorMessage).toBeUndefined();
          }
        } finally {
          // Restore original version
          Object.defineProperty(process, 'version', {
            value: originalVersion,
            writable: true,
            configurable: true
          });
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Version comparison should be transitive and consistent
   * For any three versions a, b, c: if a < b and b < c, then a < c
   */
  test('version comparison is transitive', () => {
    const versionGenerator = fc.tuple(
      fc.integer({ min: 0, max: 30 }),
      fc.integer({ min: 0, max: 50 }),
      fc.integer({ min: 0, max: 100 })
    ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`);

    fc.assert(
      fc.property(
        versionGenerator,
        versionGenerator,
        versionGenerator,
        (v1, v2, v3) => {
          const cmp12 = compareVersions(v1, v2);
          const cmp23 = compareVersions(v2, v3);
          const cmp13 = compareVersions(v1, v3);

          // If v1 < v2 and v2 < v3, then v1 < v3
          if (cmp12 < 0 && cmp23 < 0) {
            expect(cmp13).toBeLessThan(0);
          }

          // If v1 > v2 and v2 > v3, then v1 > v3
          if (cmp12 > 0 && cmp23 > 0) {
            expect(cmp13).toBeGreaterThan(0);
          }

          // If v1 == v2 and v2 == v3, then v1 == v3
          if (cmp12 === 0 && cmp23 === 0) {
            expect(cmp13).toBe(0);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Version comparison should be reflexive
   * For any version v: v == v
   */
  test('version comparison is reflexive', () => {
    const versionGenerator = fc.tuple(
      fc.integer({ min: 0, max: 30 }),
      fc.integer({ min: 0, max: 50 }),
      fc.integer({ min: 0, max: 100 })
    ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`);

    fc.assert(
      fc.property(versionGenerator, (version) => {
        const result = compareVersions(version, version);
        expect(result).toBe(0);
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Version comparison should be symmetric
   * For any versions a, b: if a < b then b > a
   */
  test('version comparison is symmetric', () => {
    const versionGenerator = fc.tuple(
      fc.integer({ min: 0, max: 30 }),
      fc.integer({ min: 0, max: 50 }),
      fc.integer({ min: 0, max: 100 })
    ).map(([major, minor, patch]) => `${major}.${minor}.${patch}`);

    fc.assert(
      fc.property(versionGenerator, versionGenerator, (v1, v2) => {
        const cmp12 = compareVersions(v1, v2);
        const cmp21 = compareVersions(v2, v1);

        // If v1 < v2, then v2 > v1
        if (cmp12 < 0) {
          expect(cmp21).toBeGreaterThan(0);
        }

        // If v1 > v2, then v2 < v1
        if (cmp12 > 0) {
          expect(cmp21).toBeLessThan(0);
        }

        // If v1 == v2, then v2 == v1
        if (cmp12 === 0) {
          expect(cmp21).toBe(0);
        }
      }),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Versions with higher major numbers should always be greater
   * For any versions with major1 > major2, version1 > version2
   */
  test('higher major version is always greater', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 30 }),
        fc.integer({ min: 0, max: 30 }),
        fc.integer({ min: 0, max: 50 }),
        fc.integer({ min: 0, max: 50 }),
        fc.integer({ min: 0, max: 100 }),
        fc.integer({ min: 0, max: 100 }),
        (major1, major2, minor1, minor2, patch1, patch2) => {
          const v1 = `${major1}.${minor1}.${patch1}`;
          const v2 = `${major2}.${minor2}.${patch2}`;
          const result = compareVersions(v1, v2);

          if (major1 > major2) {
            expect(result).toBeGreaterThan(0);
          } else if (major1 < major2) {
            expect(result).toBeLessThan(0);
          }
          // If major1 === major2, result depends on minor and patch
        }
      ),
      { numRuns: 100 }
    );
  });
});
