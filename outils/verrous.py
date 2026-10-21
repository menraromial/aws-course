#!/usr/bin/env python3
"""Mots de passe des TP verrouillés (composant src/components/Verrou).

    python3 outils/verrous.py                       nouveaux mots de passe pour tous les verrous
    python3 outils/verrous.py tp3 tp4               nouveaux mots de passe pour ces verrous
    python3 outils/verrous.py --choisir tp3         saisir soi-même le mot de passe de tp3
    python3 outils/verrous.py --definir tp1=<mot>   fixer les mots de passe

src/verrous.json reçoit :
  - l'empreinte PBKDF2-SHA-256 de chaque mot de passe, que le site compare à
    la saisie ;
  - un coffre : la liste de tous les mots de passe, chiffrée en AES-GCM avec
    une clé dérivée du mot de passe « enseignant ». Le guide de l'enseignant
    l'affiche à qui connaît ce mot de passe (composant MotsDePasse).
Aucun mot de passe n'est écrit en clair. Le script demande le mot de passe
« enseignant » quand il en a besoin pour ouvrir ou refaire le coffre.

Les mots de passe sont mis en minuscules : le site ignore les majuscules et
les espaces autour du mot de passe saisi. Le mot de passe « enseignant » ouvre
tous les verrous, y compris le guide de l'enseignant, qui n'a pas le sien.
Après une modification : npm run build, puis commit et push, avec un message
qui ne cite aucun mot de passe.
"""
import base64
import getpass
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

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


def cle_du_coffre(mot_de_passe_enseignant: str) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", mot_de_passe_enseignant.encode(), f"{SEL}:coffre".encode(), ITERATIONS)


def ouvrir_coffre(coffre: dict, mot_de_passe_enseignant: str) -> dict:
    iv = base64.b64decode(coffre["iv"])
    donnees = base64.b64decode(coffre["donnees"])
    return json.loads(AESGCM(cle_du_coffre(mot_de_passe_enseignant)).decrypt(iv, donnees, None))


def fermer_coffre(contenu: dict, mot_de_passe_enseignant: str) -> dict:
    iv = os.urandom(12)
    donnees = AESGCM(cle_du_coffre(mot_de_passe_enseignant)).encrypt(iv, json.dumps(contenu).encode(), None)
    return {"iv": base64.b64encode(iv).decode(), "donnees": base64.b64encode(donnees).decode()}


def nouveau_mot_de_passe() -> str:
    return "-".join(secrets.choice(MOTS) for _ in range(3)) + f"-{secrets.randbelow(90) + 10}"


def main() -> int:
    args = sys.argv[1:]
    choisir = "--choisir" in args
    definis = {}
    if "--definir" in args:
        for a in args:
            if "=" in a:
                cle, _, valeur = a.partition("=")
                definis[cle] = valeur.strip().lower()
        args = list(definis)
    ids = [a for a in args if a != "--choisir"] or VERROUS
    inconnus = [i for i in ids if i not in VERROUS]
    if inconnus:
        sys.exit(f"Verrous inconnus : {', '.join(inconnus)}. Verrous possibles : {', '.join(VERROUS)}")

    donnees = json.loads(FICHIER.read_text()) if FICHIER.exists() else {}
    empreintes = donnees.get("empreintes", {})

    # Contenu actuel du coffre, s'il existe : il faut le mot de passe enseignant actuel.
    # On essaie d'abord celui passé par --definir, qui est le bon s'il ne change pas.
    contenu = {}
    if "coffre" in donnees:
        essai = definis.get("enseignant")
        while True:
            if essai is None:
                essai = getpass.getpass("Mot de passe enseignant actuel (pour ouvrir le coffre) : ").strip().lower()
            try:
                contenu = ouvrir_coffre(donnees["coffre"], essai)
                break
            except InvalidTag:
                if essai != definis.get("enseignant"):
                    print("Ce n'est pas le mot de passe enseignant actuel.")
                essai = None

    print(f"{'verrou':<14} mot de passe")
    for id_ in ids:
        if id_ in definis:
            mdp = definis[id_]
        elif choisir:
            mdp = getpass.getpass(f"Mot de passe pour {id_} : ").strip().lower()
        else:
            mdp = nouveau_mot_de_passe()
        empreintes[id_] = empreinte(id_, mdp)
        contenu[id_] = mdp
        print(f"{id_:<14} {'(saisi)' if choisir else mdp}")

    if "enseignant" not in contenu:
        sys.exit("Le coffre n'a pas encore de mot de passe enseignant : relancez avec le verrou « enseignant ».")
    manquants = [i for i in VERROUS if i not in contenu]
    if manquants:
        print(f"Attention, le coffre ne contient pas encore : {', '.join(manquants)}.")
    coffre = fermer_coffre({i: contenu[i] for i in VERROUS if i in contenu}, contenu["enseignant"])
    FICHIER.write_text(json.dumps({"sel": SEL, "iterations": ITERATIONS, "empreintes": empreintes,
                                   "coffre": coffre}, indent=2) + "\n")
    print(f"\nEmpreintes et coffre écrits dans {FICHIER.relative_to(FICHIER.parent.parent)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
