/** Lien de téléchargement d'un fichier de static/ : <Telechargement fichier="kits/galerie.tar.gz" /> */
import useBaseUrl from '@docusaurus/useBaseUrl';
import styles from './styles.module.css';

export default function Telechargement({fichier, children}: {fichier: string; children?: React.ReactNode}) {
  const url = useBaseUrl(`/${fichier}`);
  const nom = fichier.split('/').pop();
  return (
    <a className={styles.bouton} href={url} download>
      <span className={styles.fleche}>↓</span>
      <span>{children ?? nom}</span>
    </a>
  );
}
