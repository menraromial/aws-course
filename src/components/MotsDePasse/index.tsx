/**
 * Liste des mots de passe des TP, pour le guide de l'enseignant.
 *
 * src/verrous.json contient la liste chiffrée en AES-GCM ; la clé dérive du
 * mot de passe « enseignant » (PBKDF2-SHA-256, sel « sel:coffre »). Le
 * déchiffrement se fait dans le navigateur : la liste n'apparaît en clair ni
 * dans le dépôt ni dans les fichiers du site. Voir outils/verrous.py.
 */
import {useState, type FormEvent} from 'react';
import verrous from '@site/src/verrous.json';
import styles from '../Verrou/styles.module.css';

const LIBELLES: Record<string, string> = {
  tp1: 'TP 1',
  tp2: 'TP 2',
  tp3: 'TP 3',
  tp4: 'TP 4',
  tp5: 'TP 5, partie 1',
  'tp5-partie2': 'TP 5, partie 2',
  'tp5-partie3': 'TP 5, partie 3',
  enseignant: 'Enseignant (tous les TP et ce guide)',
};

const octets = (b64: string) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));

async function ouvrir(motDePasse: string): Promise<Record<string, string>> {
  const code = new TextEncoder();
  const base = await crypto.subtle.importKey('raw', code.encode(motDePasse), 'PBKDF2', false, ['deriveKey']);
  const cle = await crypto.subtle.deriveKey(
    {name: 'PBKDF2', hash: 'SHA-256', salt: code.encode(`${verrous.sel}:coffre`), iterations: verrous.iterations},
    base,
    {name: 'AES-GCM', length: 256},
    false,
    ['decrypt'],
  );
  const clair = await crypto.subtle.decrypt(
    {name: 'AES-GCM', iv: octets(verrous.coffre.iv)},
    cle,
    octets(verrous.coffre.donnees),
  );
  return JSON.parse(new TextDecoder().decode(clair));
}

export default function MotsDePasse() {
  const [saisie, setSaisie] = useState('');
  const [liste, setListe] = useState<Record<string, string> | null>(null);
  const [erreur, setErreur] = useState(false);

  async function valider(e: FormEvent) {
    e.preventDefault();
    try {
      setListe(await ouvrir(saisie.trim().toLowerCase()));
    } catch {
      setErreur(true);
    }
  }

  if (liste) {
    return (
      <table>
        <thead>
          <tr><th>Verrou</th><th>Mot de passe</th></tr>
        </thead>
        <tbody>
          {Object.entries(liste).map(([id, mdp]) => (
            <tr key={id}><td>{LIBELLES[id] ?? id}</td><td><code>{mdp}</code></td></tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <form className={styles.verrou} onSubmit={valider}>
      <p>Les mots de passe sont chiffrés. Saisissez le mot de passe de l'enseignant pour les afficher.</p>
      <div className={styles.ligne}>
        <input
          type="password"
          className={styles.champ}
          value={saisie}
          onChange={(e) => {
            setSaisie(e.target.value);
            setErreur(false);
          }}
          aria-label="Mot de passe de l'enseignant"
          autoComplete="off"
        />
        <button type="submit" className="button button--primary">
          Afficher
        </button>
      </div>
      {erreur && <p className={styles.erreur}>Mot de passe incorrect.</p>}
    </form>
  );
}
