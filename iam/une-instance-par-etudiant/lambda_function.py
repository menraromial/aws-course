"""Une seule instance EC2 en marche par étudiant.

Déclenchée par EventBridge à chaque passage d'une instance à l'état
« running ». Regroupe les instances en marche du même propriétaire (tag
Proprietaire, comparé sans tenir compte de la casse), garde celle qui tourne
depuis le plus longtemps et arrête les autres. Arrêter plutôt que résilier :
l'étudiant ne perd jamais son disque, il peut résilier lui-même l'instance
en trop.
"""

import logging

import boto3

TAG = "Proprietaire"
ETATS_ACTIFS = ["pending", "running"]

journal = logging.getLogger()
journal.setLevel(logging.INFO)

ec2 = boto3.client("ec2")


def proprietaire(instance):
    for tag in instance.get("Tags", []):
        if tag["Key"] == TAG:
            return tag["Value"].strip().lower()
    return None


def instances_actives():
    pages = ec2.get_paginator("describe_instances").paginate(
        Filters=[{"Name": "instance-state-name", "Values": ETATS_ACTIFS}]
    )
    for page in pages:
        for reservation in page["Reservations"]:
            yield from reservation["Instances"]


def lambda_handler(event, context):
    instance_id = event["detail"]["instance-id"]
    reponse = ec2.describe_instances(InstanceIds=[instance_id])
    nouvelle = reponse["Reservations"][0]["Instances"][0]
    nom = proprietaire(nouvelle)
    if nom is None:
        journal.info("%s sans tag %s : ignorée", instance_id, TAG)
        return {"arretees": []}

    siennes = [i for i in instances_actives() if proprietaire(i) == nom]
    if len(siennes) <= 1:
        return {"arretees": []}

    siennes.sort(key=lambda i: (i["LaunchTime"], i["InstanceId"]))
    a_arreter = [i["InstanceId"] for i in siennes[1:]]
    ec2.stop_instances(InstanceIds=a_arreter)
    ec2.create_tags(
        Resources=a_arreter,
        Tags=[{"Key": "ArreteeAutomatiquement", "Value": "une seule instance en marche par etudiant"}],
    )
    journal.info("%s : %s garde %s, arrêt de %s", nom, len(siennes), siennes[0]["InstanceId"], a_arreter)
    return {"arretees": a_arreter}
