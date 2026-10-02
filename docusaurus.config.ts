import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// Encadré propre au cours, en plus de note/tip/info/warning/danger
const encadres = ['cout'];

const config: Config = {
  title: 'Introduction à AWS',
  tagline: 'Mettre une application en ligne sur AWS, en comprenant chacune de ses pièces.',
  favicon: 'img/favicon.svg',
  future: {v4: true},
  url: 'https://menraromial.com',
  baseUrl: '/aws-course/',
  trailingSlash: false,
  onBrokenLinks: 'throw',
  i18n: {defaultLocale: 'fr', locales: ['fr']},
  markdown: {hooks: {onBrokenMarkdownLinks: 'throw'}},

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: 'cours',
          sidebarPath: './sidebars.ts',
          admonitions: {keywords: encadres, extendDefaults: true},
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {customCss: ['./src/css/custom.css', './src/css/figures.css']},
        svgr: {svgrConfig: {svgo: false}},
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {respectPrefersColorScheme: false, defaultMode: 'light'},
    docs: {sidebar: {hideable: true, autoCollapseCategories: false}},
    tableOfContents: {minHeadingLevel: 2, maxHeadingLevel: 3},
    navbar: {
      title: 'Introduction à AWS',
      logo: {alt: 'Monogramme du cours', src: 'img/logo.svg'},
      items: [
        {type: 'docSidebar', sidebarId: 'cours', position: 'left', label: 'Le cours'},
        {to: '/cours/module-5/projet', label: 'Projet final', position: 'left'},
      ],
    },
    footer: {
      style: 'light',
      links: [
        {
          title: 'Le cours',
          items: [
            {label: 'Organisation', to: '/cours'},
            {label: 'Module 1 : introduction à AWS', to: '/cours/module-1/cours'},
            {label: 'Module 2 : sécurité et accès', to: '/cours/module-2/cours'},
            {label: 'Module 3 : Amazon EC2', to: '/cours/module-3/cours'},
            {label: 'Module 4 : stockage et messages', to: '/cours/module-4/cours'},
            {label: 'Module 5 : projet final', to: '/cours/module-5/projet'},
          ],
        },
      ],
      copyright:
        `© ${new Date().getFullYear()} Romial Menra · Contenu sous licence ` +
        `<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr" rel="license noopener" target="_blank">CC BY-NC-SA 4.0</a>`,
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
      additionalLanguages: ['bash', 'nginx', 'ini', 'json', 'python', 'powershell'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
