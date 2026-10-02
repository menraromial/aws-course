/** Chemin de navigation dans la console : <Chemin>IAM › Users › Create user</Chemin> */
import type {ReactNode} from 'react';
import styles from './styles.module.css';

export default function Chemin({children}: {children: string}) {
  const etapes = children.split('›').map((s) => s.trim());
  const rendu: ReactNode[] = [];
  etapes.forEach((e, i) => {
    if (i > 0) rendu.push(<span key={`s${i}`} className={styles.sep}>›</span>);
    rendu.push(<span key={i} className={styles.etape}>{e}</span>);
  });
  return <span className={styles.chemin}>{rendu}</span>;
}
