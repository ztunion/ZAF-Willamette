#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import os
import grpc

import cms_pb2
import cms_pb2_grpc


HOST = "willamette-cms-grpc-842442707510.northamerica-northeast1.run.app:443"


def main():
    token = os.getenv("TOKEN")

    if not token:
        raise RuntimeError("TOKEN environment variable is not set")

    credentials = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel(HOST, credentials)

    stub = cms_pb2_grpc.CmsServiceStub(channel)

    metadata = [
        ("authorization", f"Bearer {token}")
    ]

    print("=== ListPolicies ===")
    response = stub.ListPolicies(
        cms_pb2.ListPoliciesRequest(),
        metadata=metadata,
    )
    print(response)

    print("\n=== GetKeyPolicy ===")
    response = stub.GetKeyPolicy(
        cms_pb2.GetKeyPolicyRequest(
            virtual_api_key="sk-willamette-test-virtual-001"
        ),
        metadata=metadata,
    )
    print(response)

    print("\n=== ResolveApiKey ===")
    response = stub.ResolveApiKey(
        cms_pb2.ResolveApiKeyRequest(
            virtual_api_key="sk-willamette-test-virtual-001"
        ),
        metadata=metadata,
    )
    print(response)


if __name__ == "__main__":
    main()