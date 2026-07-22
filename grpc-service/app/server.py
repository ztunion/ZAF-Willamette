#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import os
import secrets
import string
from concurrent import futures

import grpc

import cms_pb2
import cms_pb2_grpc

from secret_store import (
    create_or_update_secret,
    access_secret,
)

from storage import (
    save_api_key_record,
    get_api_key_record,
    list_api_key_records,
)


TEST_OPENAI_KEY = "sk-willamette-test-virtual-001"
TEST_HF_KEY = "hf_willamette_test_virtual_001"
TEST_ANTHROPIC_KEY = "sk-ant-willamette-test-virtual-001"


def generate_virtual_key(provider: str) -> str:
    chars = string.ascii_letters + string.digits
    normalized = (provider or "other").lower()

    if normalized == "huggingface":
        return "hf_" + "".join(secrets.choice(chars) for _ in range(34))

    if normalized == "anthropic":
        return "sk-ant-" + "".join(secrets.choice(chars) for _ in range(32))

    if normalized == "openai":
        return "sk-" + "".join(secrets.choice(chars) for _ in range(48))

    return "vk-" + "".join(secrets.choice(chars) for _ in range(32))


def policy_to_dict(policy) -> dict:
    return {
        "ip_validation_enabled": policy.ip_validation_enabled,
        "allowed_ip_ranges": list(policy.allowed_ip_ranges),
        "ja3_validation_enabled": policy.ja3_validation_enabled,
        "allowed_ja3": list(policy.allowed_ja3),
        "ja4_validation_enabled": policy.ja4_validation_enabled,
        "allowed_ja4": list(policy.allowed_ja4),
        "country_validation_enabled": policy.country_validation_enabled,
        "allowed_countries": list(policy.allowed_countries),
    }


def dict_to_policy(policy_dict: dict):
    return cms_pb2.Policy(
        ip_validation_enabled=policy_dict.get("ip_validation_enabled", False),
        allowed_ip_ranges=policy_dict.get("allowed_ip_ranges", []),
        ja3_validation_enabled=policy_dict.get("ja3_validation_enabled", False),
        allowed_ja3=policy_dict.get("allowed_ja3", []),
        ja4_validation_enabled=policy_dict.get("ja4_validation_enabled", False),
        allowed_ja4=policy_dict.get("allowed_ja4", []),
        country_validation_enabled=policy_dict.get("country_validation_enabled", False),
        allowed_countries=policy_dict.get("allowed_countries", []),
    )


def default_policy():
    return cms_pb2.Policy(
        ip_validation_enabled=True,
        allowed_ip_ranges=["99.233.12.0/24"],
        ja3_validation_enabled=True,
        allowed_ja3=["test-ja3-001"],
        ja4_validation_enabled=True,
        allowed_ja4=["test-ja4-001"],
        country_validation_enabled=True,
        allowed_countries=["AE", "US", "CA"],
    )


def seed_record(virtual_key: str, provider: str, real_key: str, secret_id: str):
    if get_api_key_record(virtual_key):
        return

    secret_version = create_or_update_secret(
        secret_id=secret_id,
        secret_value=real_key,
    )

    record = {
        "virtual_api_key": virtual_key,
        "provider": provider,
        "secret_version": secret_version,
        "status": "active",
        "owner": "test-user",
        "policy": policy_to_dict(default_policy()),
    }

    save_api_key_record(virtual_key, record)


def seed_test_data_if_missing():
    seed_record(
        TEST_OPENAI_KEY,
        "openai",
        "sk-real-test-key-for-bruce",
        "api-key-test-bruce-openai",
    )

    seed_record(
        TEST_HF_KEY,
        "huggingface",
        "hf_real_test_key_for_bruce",
        "api-key-test-bruce-huggingface",
    )

    seed_record(
        TEST_ANTHROPIC_KEY,
        "anthropic",
        "sk-ant-real-test-key-for-bruce",
        "api-key-test-bruce-anthropic",
    )


class CmsService(cms_pb2_grpc.CmsServiceServicer):

    def CreateApiKey(self, request, context):
        provider = (request.provider or "other").lower()
        virtual_key = generate_virtual_key(provider)

        secret_id = virtual_key.replace("sk-", "api-key-", 1)
        secret_id = secret_id.replace("hf_", "api-key-hf-", 1)
        secret_id = secret_id.replace("vk-", "api-key-vk-", 1)

        secret_version = create_or_update_secret(
            secret_id=secret_id,
            secret_value=request.real_api_key,
        )

        record = {
            "virtual_api_key": virtual_key,
            "provider": provider,
            "secret_version": secret_version,
            "status": "active",
            "owner": "grpc-user",
            "policy": policy_to_dict(request.policy),
        }

        save_api_key_record(virtual_key, record)

        return cms_pb2.CreateApiKeyResponse(
            virtual_api_key=virtual_key,
            provider=provider,
        )

    def GetKeyPolicy(self, request, context):
        record = get_api_key_record(request.virtual_api_key)

        if not record:
            return cms_pb2.GetKeyPolicyResponse(
                found=False,
                virtual_api_key=request.virtual_api_key,
            )

        real_api_key = access_secret(record["secret_version"])

        return cms_pb2.GetKeyPolicyResponse(
            found=True,
            virtual_api_key=record["virtual_api_key"],
            real_api_key=real_api_key,
            provider=record.get("provider", "unknown"),
            policy=dict_to_policy(record["policy"]),
        )

    def ResolveApiKey(self, request, context):
        record = get_api_key_record(request.virtual_api_key)

        if not record:
            return cms_pb2.ResolveApiKeyResponse(
                found=False,
                virtual_api_key=request.virtual_api_key,
            )

        real_api_key = access_secret(record["secret_version"])

        return cms_pb2.ResolveApiKeyResponse(
            found=True,
            virtual_api_key=record["virtual_api_key"],
            real_api_key=real_api_key,
            provider=record.get("provider", "unknown"),
            policy=dict_to_policy(record["policy"]),
        )

    def ListPolicies(self, request, context):
        items = []

        for record in list_api_key_records():
            real_api_key = access_secret(record["secret_version"])

            items.append(
                cms_pb2.GetKeyPolicyResponse(
                    found=True,
                    virtual_api_key=record["virtual_api_key"],
                    real_api_key=real_api_key,
                    provider=record.get("provider", "unknown"),
                    policy=dict_to_policy(record["policy"]),
                )
            )

        return cms_pb2.ListPoliciesResponse(items=items)


def serve():
    seed_test_data_if_missing()

    port = os.getenv("PORT", "8080")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    cms_pb2_grpc.add_CmsServiceServicer_to_server(
        CmsService(),
        server,
    )

    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print(f"Willamette CMS gRPC service listening on port {port}")

    server.wait_for_termination()


if __name__ == "__main__":
    serve()