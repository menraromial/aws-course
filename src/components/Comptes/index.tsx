/**
 * Onglets « Compte personnel AWS » / « Compte fourni par l'enseignant ».
 *
 * Tous les onglets du site partagent le même groupe : le choix fait sur une
 * page vaut pour toutes les autres, et le navigateur s'en souvient. L'adresse
 * ?compte=personnel ou ?compte=enseignant force le choix.
 *
 *   <Comptes>
 *   <TabItem value="personnel" label="Compte personnel AWS">…</TabItem>
 *   <TabItem value="enseignant" label="Compte fourni par l'enseignant">…</TabItem>
 *   </Comptes>
 */
import type {ReactNode} from 'react';
import Tabs from '@theme/Tabs';

export default function Comptes({children}: {children: ReactNode}) {
  return (
    <Tabs groupId="compte" queryString="compte" defaultValue="personnel">
      {children}
    </Tabs>
  );
}
