#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import sys
import hashlib
import logging
from mitmproxy.tls import ClientHelloData
from mitmproxy import http

log = logging.getLogger(__name__)

GREASE = {0x0a0a,0x1a1a,0x2a2a,0x3a3a,0x4a4a,0x5a5a,
          0x6a6a,0x7a7a,0x8a8a,0x9a9a,0xaaaa,0xbaba,
          0xcaca,0xdada,0xeaea,0xfafa}

# TLS extension type codes (RFC 8446 §4.2)
TLS_EXT_SNI                  = 0   # server_name
TLS_EXT_SUPPORTED_GROUPS     = 10  # supported_groups (elliptic curves)
TLS_EXT_EC_POINT_FORMATS     = 11  # ec_point_formats
TLS_EXT_SIGNATURE_ALGORITHMS = 13  # signature_algorithms
TLS_EXT_ALPN                 = 16  # application_layer_protocol_negotiation
TLS_EXT_SUPPORTED_VERSIONS   = 43  # supported_versions

JA4_EXT_EXCLUDE = {TLS_EXT_SNI, TLS_EXT_ALPN}


def _parse_u16_list(data: bytes, prefix: int = 2) -> list[int]:
    byte_len = int.from_bytes(data[:prefix], 'big')
    avail = min(byte_len, len(data) - prefix)
    return [int.from_bytes(data[prefix + i*2 : prefix + i*2 + 2], 'big') for i in range(avail // 2)]


def _parse_u8_list(data: bytes) -> list[int]:
    count = data[0]
    avail = min(count, len(data) - 1)
    return list(data[1 : 1 + avail])


class JAFingerprintAddon:
    def running(self) -> None:
        log.info("[ja_fingerprint] ready")

    def tls_clienthello(self, data: ClientHelloData) -> None:
        h = data.client_hello

        try:
            raw_cs  = h.cipher_suites
            raw_ext = h.extensions if h.extensions else []
            try:
                rb = h.raw_bytes()
            except NotImplementedError:
                return

            ver       = int.from_bytes(rb[9:11], 'big') if len(rb) >= 11 else 0x0303  # rb[9:11] = ClientHello.legacy_version
            ext_types = [e[0] for e in raw_ext if e[0] not in GREASE]

            tls_ver  = _tls_ver(raw_ext, ver)
            sni      = "d" if h.sni else "i"
            cs_clean = sorted(c for c in raw_cs if c not in GREASE)
            ex_hash  = sorted(t for t in ext_types if t not in JA4_EXT_EXCLUDE)

            alpn = "00"
            if h.alpn_protocols:
                name = h.alpn_protocols[0]
                if isinstance(name, bytes):
                    name = name.decode(errors='replace')
                if name:
                    if ord(name[0]) > 127:
                        alpn = "99"
                    elif len(name) > 2:
                        alpn = name[0] + name[-1]
                    elif len(name) == 2:
                        alpn = name
                    else:
                        alpn = name + name

            sig_algs   = []
            curves_list = []
            points_list = []
            for etype, ebody in raw_ext:
                if etype == TLS_EXT_SIGNATURE_ALGORITHMS and len(ebody) >= 2:
                    sig_algs    = _parse_u16_list(ebody, prefix=2)
                elif etype == TLS_EXT_SUPPORTED_GROUPS and len(ebody) >= 2:
                    curves_list = [g for g in _parse_u16_list(ebody, prefix=2) if g not in GREASE]
                elif etype == TLS_EXT_EC_POINT_FORMATS and len(ebody) >= 1:
                    points_list = _parse_u8_list(ebody)

            cs_hash_str = ",".join(f"{c:04x}" for c in cs_clean)
            ex_hash_str = ",".join(f"{e:04x}" for e in ex_hash)
            sa_hash_str = ",".join(f"{s:04x}" for s in sig_algs)

            ch = hashlib.sha256(cs_hash_str.encode()).hexdigest()[:12] if cs_clean else "000000000000"
            if ex_hash:
                if sig_algs:
                    eh = hashlib.sha256(f"{ex_hash_str}_{sa_hash_str}".encode()).hexdigest()[:12]
                else:
                    eh = hashlib.sha256(ex_hash_str.encode()).hexdigest()[:12]
            else:
                eh = "000000000000"

            ja4 = f"t{tls_ver}{sni}{len(cs_clean):02d}{len(ext_types):02d}{alpn}_{ch}_{eh}"

            # JA3
            ext_str    = "-".join(str(t) for t in ext_types)
            cs_str     = "-".join(str(c) for c in raw_cs if c not in GREASE)
            curves_str = "-".join(str(g) for g in curves_list)
            points_str = "-".join(str(p) for p in points_list)

            ja3_raw  = f"{ver},{cs_str},{ext_str},{curves_str},{points_str}"
            ja3_hash = hashlib.md5(ja3_raw.encode()).hexdigest()

            data.context.client.ja3 = ja3_hash
            data.context.client.ja4 = ja4
            data.context.client.sni = h.sni

        except Exception as e:
            sys.stdout.write(f"[ERROR] {e}\n")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()


def _tls_ver(exts, fallback):
    m = {0x0301:"10", 0x0302:"11", 0x0303:"12", 0x0304:"13"}
    for etype, ebody in exts:
        if etype == TLS_EXT_SUPPORTED_VERSIONS and len(ebody) >= 1:
            vs = [v for v in _parse_u16_list(ebody, prefix=1) if v not in GREASE]
            if vs:
                return m.get(max(vs), "00")
    return m.get(fallback, "00")

addons = [JAFingerprintAddon()]
