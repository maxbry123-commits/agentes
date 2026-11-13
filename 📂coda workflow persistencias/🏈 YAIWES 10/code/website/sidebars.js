// @ts-check

/**
 * A single hand-authored sidebar for the Pentest Swarm AI docs.
 * Order mirrors the docs' `sidebar_position` frontmatter.
 *
 * @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  docs: [
    'intro',
    'quickstart',
    'providers',
    'modes',
    'cli',
    'cost-and-safety',
    'dashboard',
    'playbooks',
    'configuration',
    'troubleshooting',
    'security',
  ],
};

module.exports = sidebars;
