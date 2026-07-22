#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from __future__ import annotations

import logging
import subprocess
import threading
import time
import shutil
import grpc

from cms_client import GrpcCMSClient, _GRPC_ENDPOINT

log = logging.getLogger(__name__)

_TOKEN_LIFETIME = 3600.0  # gcloud identity tokens live ~1 hour
_REFRESH_MARGIN = 120.0   # refresh this many seconds before expiry
_RETRY_INTERVAL = 60.0    # retry delay after a failed refresh


class _GcloudTokenPlugin:

    def __init__(self) -> None:
        self._token: str = ""
        self._lock = threading.Lock()

        self._do_refresh()  # fail fast at startup if gcloud is unavailable

        t = threading.Thread(target=self._refresh_loop, daemon=True,
                             name="gcloud-token-refresh")
        t.start()

    def __call__(self, context, callback) -> None:
        with self._lock:
            token = self._token
        callback([("authorization", f"Bearer {token}")], None)

    def _refresh_loop(self) -> None:
        while True:
            time.sleep(_TOKEN_LIFETIME - _REFRESH_MARGIN)
            try:
                self._do_refresh()
                log.info("gcloud identity token refreshed")
            except Exception as e:
                log.error("gcloud token refresh failed: %s — retrying in %ds",
                          e, int(_RETRY_INTERVAL))
                time.sleep(_RETRY_INTERVAL)

    def _do_refresh(self) -> None:
        result = subprocess.run(
            [
                shutil.which("gcloud.cmd") or shutil.which("gcloud") or "gcloud",
                "auth",
                "print-identity-token",
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"gcloud auth print-identity-token failed: {result.stderr.strip()}"
            )
        with self._lock:
            self._token = result.stdout.strip()


def _build_channel_credentials() -> grpc.ChannelCredentials:
    return grpc.composite_channel_credentials(
        grpc.ssl_channel_credentials(),
        grpc.metadata_call_credentials(_GcloudTokenPlugin()),
    )


class GrpcCMSClientGcloud(GrpcCMSClient):
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
