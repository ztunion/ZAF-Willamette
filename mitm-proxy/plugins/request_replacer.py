#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import logging
from mitmproxy import http
from credential_management import CredentialManagement
from ip2geo_db import get_instance as get_geo_db
from ip2asn_db import get_instance as get_asn_db

log = logging.getLogger(__name__)


def replace_application_bearer(request: http.Request, api_key: str) -> None:
    """Replace Authorization Bearer token with a configured API key."""
    auth_value = request.headers.get("Authorization")
    if not auth_value:
        return

    if auth_value.startswith("Bearer "):
        request.headers["Authorization"] = f"Bearer {api_key}"


class HttpRequestReplacer:
    def running(self) -> None:
        get_geo_db()
        get_asn_db()
        log.info("[Htpp Request Replacer] ready — geo/asn DB loaded")

    def request(self, flow: http.HTTPFlow) -> None:
        ja3 = getattr(flow.client_conn, 'ja3', None)
        ja4 = getattr(flow.client_conn, 'ja4', None)
        sni = getattr(flow.client_conn, 'sni', None)
        
        if not ja3 or not ja4:
            return

        auth_header = flow.request.headers.get("Authorization")
        if not auth_header:
            return

        if not auth_header.startswith("Bearer "):
            return

        current_api_key = auth_header[7:]
        ip  = flow.client_conn.address[0]
        url = flow.request.url

        if current_api_key:
            cm = CredentialManagement(ip, ja3, ja4, current_api_key, url)
            new_api_key = cm.get_new_api_key()
            replace_application_bearer(flow.request, new_api_key)


addons = [HttpRequestReplacer()]