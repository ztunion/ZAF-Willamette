#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import ipaddress
import logging
import threading

from ip2asn_db import get_instance as get_asn_db
from ip2geo_db import get_instance as get_geo_db
from cms_client_gcloud import GrpcCMSClientGcloud
from cms_client import PolicyResult

log = logging.getLogger(__name__)

_cms_client: GrpcCMSClientGcloud | None = None
_cms_lock = threading.Lock()


def _get_cms_client() -> GrpcCMSClientGcloud:
    global _cms_client
    if _cms_client is None:
        with _cms_lock:
            if _cms_client is None:
                _cms_client = GrpcCMSClientGcloud()
    return _cms_client


class CredentialManagement:
    """Manages credentials based on IP, JA3, JA4, API key, and destination URL."""

    def __init__(self, ip: str, ja3: str, ja4: str, api_key: str, url: str):
        self.ip = ip
        self.ja3 = ja3
        self.ja4 = ja4
        self.api_key = api_key
        self.url = url
        self.asn_info = get_asn_db().lookup(ip)
        self.geo_info = get_geo_db().lookup(ip)

    def get_new_api_key(self) -> str:
        cms_client = _get_cms_client()
        result = cms_client.get_policy(self.api_key)
        if self.validate_policy(result):
            result =cms_client.resolve(self.api_key)
            if result:
                return result.credential

        log.warning("CMS could not resolve key %s — using original", self.api_key)
        return self.api_key

    def validate_policy(self, policy_info: PolicyResult) -> bool:
        """Returns True if the client satisfies all enabled policy checks."""
        if policy_info is None or not policy_info.allowed:
            return False

        policies = policy_info.policies

        if policies.get("ip_validation_enabled"):
            if not self._check_ip(policies.get("allowed_ip_ranges", [])):
                log.warning("Policy denied: IP %s not allowed", self.ip)
                return False

        if policies.get("ja3_validation_enabled"):
            if self.ja3 not in policies.get("allowed_ja3", []):
                log.warning("Policy denied: JA3 %s not allowed", self.ja3)
                return False

        if policies.get("ja4_validation_enabled"):
            if self.ja4 not in policies.get("allowed_ja4", []):
                log.warning("Policy denied: JA4 %s not allowed", self.ja4)
                return False

        if policies.get("country_validation_enabled"):
            if not self._check_country(policies.get("allowed_countries", [])):
                log.warning("Policy denied: country not in allowed list %s",
                            policies.get("allowed_countries"))
                return False

        return True

    def _check_ip(self, allowed_ranges: list[str]) -> bool:
        if not allowed_ranges:
            return True
        try:
            client_ip = ipaddress.ip_address(self.ip)
            return any(
                client_ip in ipaddress.ip_network(r, strict=False)
                for r in allowed_ranges
            )
        except ValueError:
            return False

    def _check_country(self, allowed_countries: list[str]) -> bool:
        asn_country = self.asn_info.get("country") if self.asn_info else None
        geo_country = self.geo_info.get("country") if self.geo_info else None
        if asn_country and geo_country and asn_country != geo_country:
            log.warning("Policy warning: country mismatch asn=%s geo=%s",
                        asn_country, geo_country)
        
        return geo_country in allowed_countries
