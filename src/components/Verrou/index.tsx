/**
 * Verrou de TP : le contenu ne s'affiche qu'après saisie du mot de passe.
 *
 *   <Verrou id="tp3">
 *
 *   …contenu du TP en Markdown…
 *
 *   </Verrou>
 *
 * Le site ne contient que l'empreinte PBKDF2-SHA-256 du mot de passe, salée
 * par « sel:id » (src/verrous.json, produit par outils/verrous.py), jamais le
 * mot de passe lui-même.
 * Le mot de passe de l'enseignant ouvre tous les verrous. Une fois ouvert, un
 * verrou le reste dans ce navigateur. Protection légère : le texte du TP reste
 * dans le dépôt public et dans les fichiers JavaScript du site.
 */
import {useEffect, useState, type FormEvent, type ReactNode} from 'react';
import verrous from '@site/src/verrous.json';
import styles from './styles.module.css';

const CLE = (id: string) => `verrou-${id}`;

async function empreinte(id: string, motDePasse: string): Promise<string> {
  const code = new TextEncoder();
  const cle = await crypto.subtle.importKey('raw', code.encode(motDePasse), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    {name: 'PBKDF2', hash: 'SHA-256', salt: code.encode(`${verrous.sel}:${id}`), iterations: verrous.iterations},
    cle,
    256,
  );
  return Array.from(new Uint8Array(bits), (o) => o.toString(16).padStart(2, '0')).join('');
}

function attendue(id: string): string | undefined {
  return (verrous.empreintes as Record<string, string>)[id];
}

export default function Verrou({id, children}: {id: string; children: ReactNode}) {
  const [ouvert, setOuvert] = useState(false);
  const [saisie, setSaisie] = useState('');
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    try {
      const garde = localStorage.getItem(CLE(id));
      if (garde && (garde === attendue(id) || garde === attendue('enseignant'))) setOuvert(true);
    } catch {
      /* stockage indisponible : il faudra saisir le mot de passe */
    }
  }, [id]);

  async function valider(e: FormEvent) {
    e.preventDefault();
    const candidats = [
      [id, attendue(id)],
      ['enseignant', attendue('enseignant')],
    ] as const;
    for (const [nom, attendu] of candidats) {
      if (attendu && (await empreinte(nom, saisie.trim())) === attendu) {
        try {
          localStorage.setItem(CLE(id), attendu);
        } catch {
          /* tant pis : ouvert pour cette visite seulement */
        }
        setOuvert(true);
        return;
      }
    }
    setErreur(true);
  }

  if (ouvert) return <>{children}</>;

  return (
    <form className={styles.verrou} onSubmit={valider}>
      {/* les notes de bas de page du TP restent cachées tant qu'il est verrouillé */}
      <style>{'section.footnotes{display:none}'}</style>
      <p className={styles.titre}>Ce TP est verrouillé</p>
      <p>Saisissez le mot de passe donné par votre enseignant au début de la séance.</p>
      <div className={styles.ligne}>
        <input
          type="password"
          className={styles.champ}
          value={saisie}
          onChange={(e) => {
            setSaisie(e.target.value);
            setErreur(false);
          }}
          aria-label="Mot de passe du TP"
          autoComplete="off"
        />
        <button type="submit" className="button button--primary">
          Ouvrir
        </button>
      </div>
      {erreur && <p className={styles.erreur}>Mot de passe incorrect.</p>}
    </form>
  );
}
