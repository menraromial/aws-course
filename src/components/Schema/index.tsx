/**
 * Schéma numéroté. Le SVG (figures/src/<nom>.tex -> src/figures/<nom>.svg)
 * est inséré dans la page et non en <img> : ses couleurs sont des variables
 * CSS (src/css/figures.css), il suit donc le thème clair ou sombre.
 *   import regions from '@site/src/figures/region-az.svg';
 *   <Schema svg={regions} num="1.3" alt="...">légende</Schema>
 */
import type {ComponentType, ReactNode, SVGProps} from 'react';
import styles from './styles.module.css';

type Props = {
  svg: ComponentType<SVGProps<SVGSVGElement> & {title?: string}>;
  num?: string;
  alt: string;
  largeur?: string;
  children?: ReactNode;
};

export default function Schema({svg: Svg, num, alt, largeur, children}: Props): ReactNode {
  return (
    <figure className={styles.schema} id={num ? `schema-${num}` : undefined}>
      <Svg role="img" aria-label={alt} style={largeur ? {maxWidth: largeur} : undefined} />
      {children && (
        <figcaption>
          {num && <strong>Schéma {num}. </strong>}
          {children}
        </figcaption>
      )}
    </figure>
  );
}
