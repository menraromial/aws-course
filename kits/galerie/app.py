"""Galerie : une petite application web qui range ses fichiers dans Amazon S3.

Elle ne contient aucun identifiant AWS. Sur une instance EC2 munie d'un rôle IAM,
boto3 obtient tout seul des identifiants temporaires auprès du service de
métadonnées de l'instance.

Configuration par variables d'environnement :
  GALERIE_BUCKET   nom du bucket (obligatoire)
  GALERIE_REGION   région du bucket (défaut : eu-west-3)
  GALERIE_PREFIXE  préfixe des fichiers déposés (défaut : uploads/)
"""
from __future__ import annotations

import os
import urllib.request
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

BUCKET = os.environ.get("GALERIE_BUCKET", "")
REGION = os.environ.get("GALERIE_REGION", "eu-west-3")
PREFIXE = os.environ.get("GALERIE_PREFIXE", "uploads/")
TAILLE_MAX = 10 * 1024 * 1024          # 10 Mo par fichier
DUREE_LIEN = 300                       # durée de validité des liens présignés, en secondes
IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = TAILLE_MAX

# Signature v4 et adresses « virtual-hosted » : les liens présignés pointent
# vers https://<bucket>.s3.<region>.amazonaws.com/...
s3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)


def metadonnee(chemin: str) -> str:
    """Lit une métadonnée de l'instance (IMDSv2). Renvoie « ? » hors d'EC2."""
    base = "http://169.254.169.254/latest"
    try:
        req = urllib.request.Request(
            f"{base}/api/token", method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        jeton = urllib.request.urlopen(req, timeout=0.5).read().decode()
        req = urllib.request.Request(
            f"{base}/meta-data/{chemin}",
            headers={"X-aws-ec2-metadata-token": jeton},
        )
        return urllib.request.urlopen(req, timeout=0.5).read().decode()
    except OSError:
        return "?"


INSTANCE = {"id": metadonnee("instance-id"), "zone": metadonnee("placement/availability-zone")}


def taille_lisible(octets: int) -> str:
    for unite in ("o", "Ko", "Mo", "Go"):
        if octets < 1024 or unite == "Go":
            return f"{octets:.0f} {unite}" if unite == "o" else f"{octets:.1f} {unite}"
        octets /= 1024
    return f"{octets} o"


def lien_presigne(cle: str) -> str:
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": cle}, ExpiresIn=DUREE_LIEN
    )


def lister_fichiers() -> list[dict]:
    fichiers = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIXE):
        for objet in page.get("Contents", []):
            cle = objet["Key"]
            if cle.endswith("/"):
                continue
            nom = cle[len(PREFIXE):]
            fichiers.append({
                "cle": cle,
                "nom": nom,
                "taille": taille_lisible(objet["Size"]),
                "date": objet["LastModified"],
                "image": os.path.splitext(nom)[1].lower() in IMAGES,
                "lien": lien_presigne(cle),
            })
    return sorted(fichiers, key=lambda f: f["date"], reverse=True)


def expliquer(erreur: Exception) -> str:
    """Traduit les erreurs AWS les plus fréquentes en conseils compréhensibles."""
    if isinstance(erreur, NoCredentialsError):
        return ("Aucun identifiant AWS disponible. L'instance a-t-elle un rôle IAM "
                "(Actions › Security › Modify IAM role) ?")
    if isinstance(erreur, ClientError):
        code = erreur.response.get("Error", {}).get("Code", "")
        if code in ("AccessDenied", "403"):
            return (f"Accès refusé par S3 ({code}). La stratégie du rôle autorise-t-elle "
                    f"cette action sur le bucket {BUCKET} ?")
        if code in ("NoSuchBucket", "404"):
            return f"Le bucket {BUCKET} n'existe pas (ou pas dans la région {REGION})."
        return f"Erreur S3 : {code}"
    return f"Erreur inattendue : {erreur}"


@app.get("/")
def accueil():
    erreur, fichiers = None, []
    try:
        fichiers = lister_fichiers()
    except (BotoCoreError, ClientError) as e:
        erreur = expliquer(e)
    return render_template(
        "index.html", fichiers=fichiers, erreur=erreur, bucket=BUCKET,
        instance=INSTANCE, depose=request.args.get("depose"), duree=DUREE_LIEN // 60,
    )


@app.post("/deposer")
def deposer():
    fichier = request.files.get("fichier")
    if not fichier or not fichier.filename:
        return redirect(url_for("accueil"))
    nom = secure_filename(fichier.filename) or "fichier"
    horodatage = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    cle = f"{PREFIXE}{horodatage}-{nom}"
    try:
        s3.upload_fileobj(
            fichier.stream, BUCKET, cle,
            ExtraArgs={"ContentType": fichier.mimetype or "application/octet-stream"},
        )
    except (BotoCoreError, ClientError) as e:
        return render_template("index.html", fichiers=[], erreur=expliquer(e), bucket=BUCKET,
                               instance=INSTANCE, depose=None, duree=DUREE_LIEN // 60), 502
    return redirect(url_for("accueil", depose=nom))


@app.errorhandler(413)
def trop_gros(_):
    return render_template("index.html", fichiers=[], bucket=BUCKET, instance=INSTANCE,
                           depose=None, duree=DUREE_LIEN // 60,
                           erreur=f"Fichier trop volumineux (maximum {TAILLE_MAX // 2**20} Mo)."), 413


@app.get("/sante")
def sante():
    """Point de contrôle : l'application répond-elle, et atteint-elle son bucket ?"""
    try:
        s3.head_bucket(Bucket=BUCKET)
        return jsonify(statut="ok", bucket=BUCKET, instance=INSTANCE)
    except (BotoCoreError, ClientError) as e:
        return jsonify(statut="erreur", bucket=BUCKET, detail=expliquer(e)), 503


if not BUCKET:
    raise SystemExit("La variable d'environnement GALERIE_BUCKET n'est pas définie.")
