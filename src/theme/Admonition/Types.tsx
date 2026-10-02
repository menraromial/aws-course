/**
 * Encadrés du cours. Syntaxe Markdown habituelle (:::tip, :::warning...),
 * plus :::cout pour les remarques de facturation.
 */
import type {ComponentProps, ReactNode} from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const LIBELLES: Record<string, [string, string]> = {
  note: ['Remarque', 'gris'],
  info: ['Bon à savoir', 'bleu'],
  tip: ['Astuce', 'vert'],
  warning: ['Attention', 'orange'],
  caution: ['Attention', 'orange'],
  danger: ['Piège', 'rouge'],
  cout: ['Côté facture', 'violet'],
};

type Props = {type?: string; title?: ReactNode; className?: string; children: ReactNode};

function Encadre({type = 'note', title, className, children}: Props) {
  const [libelle, ton] = LIBELLES[type] ?? LIBELLES.note;
  const titre = title && title !== type ? title : null;
  return (
    <aside className={clsx(styles.encadre, styles[ton], className)}>
      <div className={styles.tete}>
        <span className={styles.puce}>{libelle}</span>
        {titre && <span className={styles.titre}>{titre}</span>}
      </div>
      <div className={styles.corps}>{children}</div>
    </aside>
  );
}

const fabrique = (t: string) => (p: ComponentProps<typeof Encadre>) => <Encadre {...p} type={t} />;
export default Object.fromEntries(Object.keys(LIBELLES).map((k) => [k, fabrique(k)]));
