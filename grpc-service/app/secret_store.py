#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import os

from google.cloud import secretmanager


PROJECT_ID = os.getenv("GCP_PROJECT", "santiam")

client = secretmanager.SecretManagerServiceClient()


def create_or_update_secret(
    secret_id: str,
    secret_value: str,
) -> str:
    parent = f"projects/{PROJECT_ID}"
    secret_name = f"{parent}/secrets/{secret_id}"

    try:
        client.get_secret(
            request={"name": secret_name}
        )
    except Exception:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {
                    "replication": {
                        "automatic": {}
                    }
                },
            }
        )

    version = client.add_secret_version(
        request={
            "parent": secret_name,
            "payload": {
                "data": secret_value.encode("utf-8")
            },
        }
    )

    return version.name


def access_secret(secret_version_name: str) -> str:
    response = client.access_secret_version(
        request={"name": secret_version_name}
    )

    return response.payload.data.decode("utf-8")