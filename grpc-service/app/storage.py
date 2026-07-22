#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from google.cloud import firestore


db = firestore.Client()

COLLECTION_NAME = "api_keys"


def save_api_key_record(
    virtual_api_key: str,
    record: dict,
) -> None:
    db.collection(COLLECTION_NAME).document(
        virtual_api_key
    ).set(record)


def get_api_key_record(
    virtual_api_key: str,
) -> dict | None:
    doc = db.collection(COLLECTION_NAME).document(
        virtual_api_key
    ).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def list_api_key_records() -> list[dict]:
    docs = db.collection(COLLECTION_NAME).stream()

    return [
        doc.to_dict()
        for doc in docs
    ]