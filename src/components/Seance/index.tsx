/** Bandeau sous le titre : repères de la séance (numéro, durées). */
import styles from './styles.module.css';

export default function Seance({items}: {items: string[]}) {
  return (
    <div className={styles.bandeau}>
      {items.map((t, i) => (
        <span key={t} className={i === 0 ? styles.premier : styles.item}>{t}</span>
      ))}
    </div>
  );
}
