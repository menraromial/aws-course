"""Tests de la fonction, avec un faux EC2 (moto) : pytest test_lambda.py"""

import os
import time

import boto3
import pytest
from moto import mock_aws

os.environ.setdefault("AWS_DEFAULT_REGION", "eu-west-3")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")


@pytest.fixture
def env():
    with mock_aws():
        import importlib

        import lambda_function

        importlib.reload(lambda_function)
        client = boto3.client("ec2")
        ami = client.describe_images(Owners=["amazon"])["Images"][0]["ImageId"]

        def lancer(proprietaire):
            tags = [{"Key": "Proprietaire", "Value": proprietaire}] if proprietaire else []
            spec = [{"ResourceType": "instance", "Tags": tags}] if tags else []
            r = client.run_instances(ImageId=ami, InstanceType="t3.micro", MinCount=1, MaxCount=1,
                                     TagSpecifications=spec)
            time.sleep(1.1)  # LaunchTime à la seconde près : ordre déterministe
            return r["Instances"][0]["InstanceId"]

        def evenement(instance_id):
            return lambda_function.lambda_handler({"detail": {"instance-id": instance_id, "state": "running"}}, None)

        def etat(instance_id):
            r = client.describe_instances(InstanceIds=[instance_id])
            return r["Reservations"][0]["Instances"][0]["State"]["Name"]

        yield lancer, evenement, etat


def test_une_seule_instance_reste_en_marche(env):
    lancer, evenement, etat = env
    a = lancer("student1")
    assert evenement(a) == {"arretees": []}
    b = lancer("student1")
    assert evenement(b) == {"arretees": [b]}
    assert etat(a) == "running"
    assert etat(b) == "stopped"


def test_les_etudiants_ne_se_genent_pas(env):
    lancer, evenement, etat = env
    a = lancer("student1")
    b = lancer("student12")
    assert evenement(b) == {"arretees": []}
    assert etat(a) == etat(b) == "running"


def test_casse_ignoree(env):
    lancer, evenement, etat = env
    a = lancer("student3")
    b = lancer("Student3")
    assert evenement(b) == {"arretees": [b]}
    assert etat(a) == "running"


def test_instance_sans_tag_ignoree(env):
    lancer, evenement, etat = env
    a = lancer(None)
    b = lancer(None)
    assert evenement(b) == {"arretees": []}
    assert etat(a) == etat(b) == "running"


def test_trois_instances_lancees_ensemble(env):
    lancer, evenement, etat = env
    ids = [lancer("student4") for _ in range(3)]
    assert evenement(ids[2]) == {"arretees": ids[1:]}
    assert [etat(i) for i in ids] == ["running", "stopped", "stopped"]
