#!/bin/bash
# Crée les comptes des étudiants : utilisateur IAM, mot de passe provisoire à
# changer à la première connexion, groupe « etudiants », limite de
# permissions aws-cours-etudiant.
#
#   ./creer-etudiants.sh reponses.csv   comptes lus dans le CSV téléchargé
#                                       depuis la feuille du formulaire
#                                       (colonnes username et password)
#   ./creer-etudiants.sh 100            comptes student1 ... student100, mots
#                                       de passe tirés au hasard et écrits
#                                       dans etudiants.csv
#
# À lancer dans CloudShell avec un compte administrateur, après avoir créé
# les trois stratégies aws-cours-*. Relançable : les comptes existants sont
# laissés tels quels.
set -euo pipefail

SOURCE=${1:?"usage : $0 reponses.csv | nombre"}
GROUPE=etudiants
COMPTE=$(aws sts get-caller-identity --query Account --output text)
STRATEGIE=arn:aws:iam::$COMPTE:policy/aws-cours-etudiant

aws iam get-policy --policy-arn "$STRATEGIE" >/dev/null \
  || { echo "Créez d'abord la stratégie aws-cours-etudiant"; exit 1; }

if ! aws iam get-group --group-name $GROUPE >/dev/null 2>&1; then
  aws iam create-group --group-name $GROUPE >/dev/null
fi
aws iam attach-group-policy --group-name $GROUPE --policy-arn "$STRATEGIE"

# Liste « utilisateur<TAB>mot de passe », une ligne par compte
comptes() {
  if [[ $SOURCE =~ ^[0-9]+$ ]]; then
    [ -f etudiants.csv ] || echo "username,password" > etudiants.csv
    for i in $(seq 1 "$SOURCE"); do
      printf 'student%s\tAws-%s-%sZ\n' "$i" "$(openssl rand -hex 5)" "$((RANDOM % 90 + 10))"
    done
  else
    python3 - "$SOURCE" <<'PY'
import csv, sys
with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
    lecteur = csv.DictReader(f)
    if not {"username", "password"} <= set(lecteur.fieldnames or []):
        sys.exit("Le fichier doit contenir les colonnes username et password")
    for ligne in lecteur:
        u, p = ligne["username"].strip(), ligne["password"].strip()
        if u and p:
            print(f"{u}\t{p}")
PY
  fi
}

ATTENTION=0
while IFS=$'\t' read -r U MDP <&3; do
  if [[ ! $U =~ ^[a-z0-9]+$ ]]; then
    echo "!! $U ignoré : un nom d'utilisateur ne doit contenir que des minuscules et des chiffres"
    ATTENTION=1; continue
  fi
  if aws iam get-user --user-name "$U" >/dev/null 2>&1; then
    echo "!! $U existe déjà dans le compte : vérifiez qu'il s'agit bien de cet étudiant"
    ATTENTION=1; continue
  fi
  aws iam create-user --user-name "$U" --permissions-boundary "$STRATEGIE" >/dev/null
  aws iam create-login-profile --user-name "$U" --password "$MDP" --password-reset-required >/dev/null
  aws iam add-user-to-group --user-name "$U" --group-name $GROUPE
  [[ $SOURCE =~ ^[0-9]+$ ]] && echo "$U,$MDP" >> etudiants.csv
  echo "$U créé"
done 3< <(comptes)

echo
echo "Adresse de connexion : https://$COMPTE.signin.aws.amazon.com/console"
[[ $SOURCE =~ ^[0-9]+$ ]] && echo "Identifiants : $(pwd)/etudiants.csv (Actions › Download file)"
[ $ATTENTION -eq 0 ] || echo "Certaines lignes ont été ignorées, voir les messages « !! » ci-dessus."
echo "Pensez à effacer de CloudShell le fichier qui contient les mots de passe."
