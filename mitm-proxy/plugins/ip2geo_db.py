#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import maxminddb
import threading
from pathlib import Path
from typing import Optional, Dict, Any

_DEFAULT_DB_PATH = Path(__file__).parent / "ip2asn" / "ip66.mmdb"

_instance: Optional["IP2GeoDatabase"] = None
_instance_lock = threading.Lock()


def get_instance(db_path=_DEFAULT_DB_PATH) -> "IP2GeoDatabase":
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:  # double-checked locking
                _instance = IP2GeoDatabase(db_path)
    return _instance


def _extract(r: dict) -> Dict[str, Any]:
    country = r.get("country") or {}
    return {
        "asn":     r.get("autonomous_system_number"),
        "country": country.get("iso_code"),
        "isp":     r.get("autonomous_system_organization"),
    }


class IP2GeoDatabase:

    def __init__(self, db_path=_DEFAULT_DB_PATH):
        self._reader = maxminddb.open_database(db_path)
        self._query  = self._reader.get

    def lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        try:
            r = self._query(ip)
            return _extract(r) if r else None
        except Exception:
            return None

    def close(self):
        self._reader.close()
