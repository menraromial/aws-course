"""Tests de la galerie contre un faux S3 (moto) : aucun appel réel à AWS."""
import io
import os

import boto3
import pytest
from moto import mock_aws

BUCKET = "galerie-test-0000"
os.environ.update(GALERIE_BUCKET=BUCKET, GALERIE_REGION="eu-west-3",
                  AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
                  AWS_EC2_METADATA_DISABLED="true")


@pytest.fixture
def client():
    with mock_aws():
        boto3.client("s3", region_name="eu-west-3").create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "eu-west-3"})
        import importlib
        import app as module
        importlib.reload(module)          # le client S3 doit être créé sous le mock
        module.app.config["TESTING"] = True
        yield module.app.test_client()


def test_page_vide(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Aucun fichier" in r.get_data(as_text=True)


def test_depot_puis_liste(client):
    r = client.post("/deposer", data={"fichier": (io.BytesIO(b"\x89PNG..."), "Mon chat.png")},
                    content_type="multipart/form-data")
    assert r.status_code == 302 and "depose=Mon_chat.png" in r.headers["Location"]
    objets = boto3.client("s3", region_name="eu-west-3").list_objects_v2(Bucket=BUCKET)["Contents"]
    assert len(objets) == 1
    cle = objets[0]["Key"]
    assert cle.startswith("uploads/") and cle.endswith("-Mon_chat.png")
    tete = boto3.client("s3", region_name="eu-west-3").head_object(Bucket=BUCKET, Key=cle)
    assert tete["ContentType"] == "image/png"
    page = client.get("/").get_data(as_text=True)
    assert "Mon_chat.png" in page
    assert f"https://{BUCKET}.s3.eu-west-3.amazonaws.com/uploads/" in page
    assert "X-Amz-Signature=" in page and "X-Amz-Expires=300" in page


def test_fichier_trop_gros(client):
    gros = io.BytesIO(b"0" * (11 * 1024 * 1024))
    r = client.post("/deposer", data={"fichier": (gros, "gros.bin")},
                    content_type="multipart/form-data")
    assert r.status_code == 413
    assert "trop volumineux" in r.get_data(as_text=True)


def test_sante(client):
    r = client.get("/sante")
    assert r.status_code == 200 and r.get_json()["statut"] == "ok"


def test_bucket_absent(client):
    boto3.client("s3", region_name="eu-west-3").delete_bucket(Bucket=BUCKET)
    r = client.get("/")
    assert "existe pas" in r.get_data(as_text=True)
    assert client.get("/sante").status_code == 503
