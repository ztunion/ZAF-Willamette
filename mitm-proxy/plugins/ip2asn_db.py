#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional, Dict, Any

from ip2asn import IP2ASN

_DEFAULT_TSV = Path(__file__).parent / "ip2asn" / "database.tsv"

_instance: Optional["IP2ASNDatabase"] = None
_instance_lock = threading.Lock()


def get_instance(tsv_path: Path = _DEFAULT_TSV) -> "IP2ASNDatabase":
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:  # double-checked locking
                _instance = IP2ASNDatabase(tsv_path)
    return _instance


def _extract(r: dict) -> Dict[str, Any]:
    return {
        "asn":     r["ASN"],
        "country": r["country"],
        "isp":     r["owner"],
    }


class IP2ASNDatabase:

    def __init__(self, tsv_path: Path = _DEFAULT_TSV):
        self._ip2asn = IP2ASN(ip2asn_file=tsv_path)
        self._query = self._ip2asn.lookup_address

    def lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        try:
            r = self._query(ip)
            return _extract(r) if r else None
        except Exception:
            return None

    def close(self):
        pass