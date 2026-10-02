import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  cours: [
    'index',
    {
      type: 'category',
      label: '1. Introduction à AWS',
      collapsed: false,
      items: ['module-1/cours', 'module-1/tp'],
    },
    {
      type: 'category',
      label: '2. Sécurité et accès',
      collapsed: false,
      items: ['module-2/cours', 'module-2/tp'],
    },
    {
      type: 'category',
      label: '3. Calcul : EC2',
      collapsed: false,
      items: ['module-3/cours', 'module-3/tp'],
    },
    {
      type: 'category',
      label: '4. Stockage, bases, messages',
      collapsed: false,
      items: ['module-4/cours', 'module-4/tp'],
    },
    {
      type: 'category',
      label: '5. Projet final',
      collapsed: false,
      items: ['module-5/projet', 'module-5/tp'],
    },
  ],
};

export default sidebars;
