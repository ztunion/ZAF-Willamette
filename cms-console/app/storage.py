#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import os

from google.cloud import firestore


PROJECT_ID = os.getenv("GCP_PROJECT", "santiam")
COLLECTION_NAME = "api_keys"

db = firestore.Client(project=PROJECT_ID)


def save_api_key_record(
    virtual_api_key: str,
    record: dict,
) -> None:
    db.collection(COLLECTION_NAME).document(virtual_api_key).set(record)


def get_api_key_record(
    virtual_api_key: str,
) -> dict | None:
    doc = db.collection(COLLECTION_NAME).document(virtual_api_key).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def list_api_key_records() -> list[dict]:
    docs = db.collection(COLLECTION_NAME).stream()

    records = []

    for doc in docs:
        data = doc.to_dict()
        records.append(data)

    return records


def delete_api_key_record(
    virtual_api_key: str,
) -> None:
    db.collection(COLLECTION_NAME).document(virtual_api_key).delete()