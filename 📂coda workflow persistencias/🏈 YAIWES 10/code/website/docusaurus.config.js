// @ts-check
// Docusaurus 3.x config for the Pentest Swarm AI documentation site.
// Docs run this file in Node CJS, so keep it CommonJS.

const { themes: prismThemes } = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Pentest Swarm AI',
  tagline: 'The open-source XBOW alternative — built on a real swarm.',
  favicon: 'img/logo.svg',

  // Deployed to GitHub Pages under the project repo path.
  url: 'https://armur-ai.github.io',
  baseUrl: '/Pentest-Swarm-AI/',

  organizationName: 'Armur-Ai',
  projectName: 'Pentest-Swarm-AI',
  trailingSlash: false,

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          // Docs-only mode: serve docs from the site root.
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl:
            'https://github.com/Armur-Ai/Pentest-Swarm-AI/tree/main/website/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: 'dark',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Pentest Swarm AI',
        logo: {
          alt: 'Pentest Swarm AI',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'doc',
            docId: 'quickstart',
            position: 'left',
            label: 'Quick Start',
          },
          {
            type: 'doc',
            docId: 'cli',
            position: 'left',
            label: 'CLI',
          },
          {
            href: 'https://github.com/Armur-Ai/Pentest-Swarm-AI',
            label: 'GitHub',
            position: 'right',
          },
          {
            href: 'https://discord.gg/6qtkhpW8tk',
            label: 'Discord',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              { label: 'Quick Start', to: '/quickstart' },
              { label: 'CLI Reference', to: '/cli' },
              { label: 'Providers', to: '/providers' },
            ],
          },
          {
            title: 'Community',
            items: [
              { label: 'Discord', href: 'https://discord.gg/6qtkhpW8tk' },
              {
                label: 'GitHub Discussions',
                href: 'https://github.com/Armur-Ai/Pentest-Swarm-AI/discussions',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/Armur-Ai/Pentest-Swarm-AI',
              },
              {
                label: 'Roadmap',
                href: 'https://github.com/orgs/Armur-Ai/projects/1',
              },
              { label: 'Armur AI', href: 'https://github.com/Armur-Ai' },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Armur-Ai. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
        additionalLanguages: ['bash', 'go', 'json', 'yaml'],
      },
    }),
};

module.exports = config;
