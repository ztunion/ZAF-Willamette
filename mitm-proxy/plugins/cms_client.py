#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import grpc

import cms_pb2
import cms_pb2_grpc

log = logging.getLogger(__name__)

_GRPC_ENDPOINT = os.getenv(
    "CMS_GRPC_ENDPOINT",
    "willamette-cms-grpc-842442707510.northamerica-northeast1.run.app:443",
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

@dataclass
class CredentialResult:
    credential: str
    handle: str
    vendor: str
    from_cache: bool = False


@dataclass
class PolicyResult:
    allowed: bool
    reason: str
    policies: dict = field(default_factory=dict)
    from_cache: bool = False


# ---------------------------------------------------------------------------
# TTL cache
# ---------------------------------------------------------------------------

class _TTLCache:
    def __init__(self, ttl: float) -> None:
        self.ttl = ttl
        self._store: dict[str, tuple[object, float]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry:
            if time.monotonic() - entry[1] < self.ttl:
                return entry[0]
            del self._store[key]
        return None

    def set(self, key: str, value) -> None:
        self._store[key] = (value, time.monotonic())

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Base client
# ---------------------------------------------------------------------------

class GrpcCMSClient:

    def __init__(
        self,
        endpoint: str,
        channel_credentials: grpc.ChannelCredentials,
        credential_ttl: float = 60.0,
        policy_ttl: float     = 600.0,
        timeout: float        = 5.0,
    ) -> None:
        self._timeout = timeout
        self._channel = grpc.secure_channel(endpoint, channel_credentials)
        self._stub    = cms_pb2_grpc.CmsServiceStub(self._channel)

        self._cred_cache   = _TTLCache(credential_ttl)
        self._policy_cache = _TTLCache(policy_ttl)

    def resolve(self, virtual_key: str) -> Optional[CredentialResult]:
        """Resolve a virtual API key to its real key. Result is cached."""
        cached = self._cred_cache.get(virtual_key)
        if cached:
            return CredentialResult(credential=cached, handle=virtual_key, vendor="", from_cache=True)
        try:
            resp = self._stub.ResolveApiKey(
                cms_pb2.ResolveApiKeyRequest(virtual_api_key=virtual_key),
                timeout=self._timeout,
            )
            if not resp.found:
                return None
            self._cred_cache.set(virtual_key, resp.real_api_key)
            return CredentialResult(credential=resp.real_api_key, handle=virtual_key, vendor="")
        except grpc.RpcError as e:
            log.error("ResolveApiKey failed: %s %s", e.code(), e.details())
            return None

    def get_policy(self, virtual_key: str) -> Optional[PolicyResult]:
        """Fetch the policy for a virtual key. Result is cached."""
        cached = self._policy_cache.get(virtual_key)
        if cached is not None:
            return PolicyResult(allowed=True, reason="cached", policies=cached, from_cache=True)
        try:
            resp = self._stub.GetKeyPolicy(
                cms_pb2.GetKeyPolicyRequest(virtual_api_key=virtual_key),
                timeout=self._timeout,
            )
            if not resp.found:
                return PolicyResult(allowed=False, reason="Key not found")
            policies = _policy_to_dict(resp.policy)
            self._policy_cache.set(virtual_key, policies)
            return PolicyResult(allowed=True, reason="ok", policies=policies)
        except grpc.RpcError as e:
            log.error("GetKeyPolicy failed: %s %s", e.code(), e.details())
            return None

    def invalidate(self, virtual_key: str) -> None:
        """Evict credential and policy cache entries for a virtual key."""
        self._cred_cache.delete(virtual_key)
        self._policy_cache.delete(virtual_key)

    def close(self) -> None:
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ---------------------------------------------------------------------------
# Proto helpers
# ---------------------------------------------------------------------------

def _policy_to_dict(p: cms_pb2.Policy) -> dict:
    return {
        "ip_validation_enabled":      p.ip_validation_enabled,
        "allowed_ip_ranges":          list(p.allowed_ip_ranges),
        "ja3_validation_enabled":     p.ja3_validation_enabled,
        "allowed_ja3":                list(p.allowed_ja3),
        "ja4_validation_enabled":     p.ja4_validation_enabled,
        "allowed_ja4":                list(p.allowed_ja4),
        "country_validation_enabled": p.country_validation_enabled,
        "allowed_countries":          list(p.allowed_countries),
    }
