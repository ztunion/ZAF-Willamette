#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from __future__ import annotations

import grpc

from cms_client import GrpcCMSClient, _GRPC_ENDPOINT


def _build_channel_credentials() -> grpc.ChannelCredentials:
    import google.auth
    import google.auth.transport.grpc
    import google.auth.transport.requests

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_plugin = google.auth.transport.grpc.AuthMetadataPlugin(
        credentials, google.auth.transport.requests.Request()
    )
    return grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(auth_plugin),
    )


class GrpcCMSClientADC(GrpcCMSClient):
    def __init__(
        self,
        endpoint: str         = _GRPC_ENDPOINT,
        credential_ttl: float = 60.0,
        policy_ttl: float     = 600.0,
        timeout: float        = 5.0,
    ) -> None:
        super().__init__(
            endpoint=endpoint,
            channel_credentials=_build_channel_credentials(),
            credential_ttl=credential_ttl,
            policy_ttl=policy_ttl,
            timeout=timeout,
        )
