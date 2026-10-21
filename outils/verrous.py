#!/usr/bin/env python3
"""Mots de passe des TP verrouillés (composant src/components/Verrou).

    python3 outils/verrous.py              nouveaux mots de passe pour tous les verrous
    python3 outils/verrous.py tp3 tp4      nouveaux mots de passe pour ces verrous seulement
    python3 outils/verrous.py --choisir tp3   saisir soi-même le mot de passe de tp3

Le script affiche les mots de passe une seule fois et n'écrit dans
src/verrous.json que leurs empreintes PBKDF2-SHA-256. Notez-les : on ne peut
pas les retrouver à partir du fichier. Le mot de passe « enseignant » ouvre
tous les verrous, y compris le guide de l'enseignant, qui n'a pas le sien.
Après une modification : npm run build, puis commit et push.
"""
import getpass
import hashlib
import json
import secrets
import sys
from pathlib import Path

FICHIER = Path(__file__).resolve().parent.parent / "src" / "verrous.json"
VERROUS = ["tp1", "tp2", "tp3", "tp4", "tp5", "tp5-partie2", "tp5-partie3", "enseignant"]
SEL = "aws-course"
ITERATIONS = 200_000
MOTS = """abeille acier aigle albatros ananas ancre arbre ardoise argile automne avion
baleine bambou banane barque basalte bison bleuet boussole brique brume cactus
camion canard canyon caramel cascade castor cerise chameau chene citron colline
comete corail coton crabe cristal cygne dauphin desert diamant dune ecorce
ecureuil etoile falaise faucon fenouil feuille figue flamant foret fougere fraise
galet gazelle geyser girafe glacier granit grenade griffon hamac hibou horizon
iceberg igloo jaguar jasmin jungle kayak koala lagune lavande lezard lichen
loutre lynx mangue marmotte meteore mimosa montagne mouette navire nuage oasis
olive orage orchidee ours panda papaye pelican phare pingouin pirogue platane
poivre pommier prairie quartz radeau renard requin riviere rocher safran sapin
saule sequoia sirocco soleil tamaris tigre tonnerre torrent toucan tournesol
tulipe vallee vanille volcan zebre""".split()


def empreinte(id_: str, mot_de_passe: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), f"{SEL}:{id_}".encode(), ITERATIONS).hex()


def nouveau_mot_de_passe() -> str:
    return "-".join(secrets.choice(MOTS) for _ in range(3)) + f"-{secrets.randbelow(90) + 10}"


def main() -> int:
    args = sys.argv[1:]
    choisir = "--choisir" in args
    ids = [a for a in args if a != "--choisir"] or VERROUS
    inconnus = [i for i in ids if i not in VERROUS]
    if inconnus:
        sys.exit(f"Verrous inconnus : {', '.join(inconnus)}. Verrous possibles : {', '.join(VERROUS)}")
    donnees = json.loads(FICHIER.read_text()) if FICHIER.exists() else {}
    empreintes = donnees.get("empreintes", {})
    print(f"{'verrou':<14} mot de passe")
    for id_ in ids:
        mdp = getpass.getpass(f"Mot de passe pour {id_} : ") if choisir else nouveau_mot_de_passe()
        empreintes[id_] = empreinte(id_, mdp)
        print(f"{id_:<14} {'(saisi)' if choisir else mdp}")
    FICHIER.write_text(json.dumps({"sel": SEL, "iterations": ITERATIONS, "empreintes": empreintes}, indent=2) + "\n")
    print(f"\nEmpreintes écrites dans {FICHIER.relative_to(FICHIER.parent.parent)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
