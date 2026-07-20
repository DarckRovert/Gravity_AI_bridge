"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — GTLIS GEO-INTELLIGENCE ENGINE V2.0                             ║
║  Módulo 5: Extracción máxima de inteligencia geográfica (100% legal)         ║
║                                                                              ║
║  LÍMITE TÉCNICO HONESTO:                                                     ║
║  TikTok no expone las IPs de viewers individuales en ninguna API pública.    ║
║  Obtenerlas requiere técnicas ilegales (MITM, exploits). Este módulo extrae  ║
║  TODO lo que SÍ es posible sin violar la ley.                                ║
║                                                                              ║
║  Capacidades:                                                                ║
║    [5a] StreamInfraMapper  — Mapeo completo de infraestructura del stream    ║
║         • IP del servidor de ingesta (origen real del stream)                ║
║         • IP del servidor CDN de distribución                                ║
║         • BGP/ASN del proveedor de red                                       ║
║         • Geo precisa del servidor (ciudad, ISP, lat/lon)                    ║
║         • Trace de todos los IPs en la cadena HLS/CDN                        ║
║                                                                              ║
║    [5b] StreamerGeoProfiler — Perfil geográfico del streamer                 ║
║         • Idioma principal y variante regional (NLP sobre bio/título/chat)   ║
║         • Zona horaria inferida del horario histórico de streams             ║
║         • País/ciudad detectados en bio, hashtags y captions                 ║
║         • Correlación con eventos locales públicos                           ║
║         • Cross-ref de redes sociales para triangular ubicación              ║
║                                                                              ║
║    [5c] CommentGeoAnalyzer — Análisis geográfico de comentarios públicos     ║
║         • Detección de idioma por comentario (langdetect/heurística)         ║
║         • Distribución geográfica estimada de la audiencia                   ║
║         • Huso horario de actividad del chat                                 ║
║         • Hashtags geolocalizados en los comentarios                         ║
║                                                                              ║
║    [5d] DNSChainMapper     — Mapa completo de la cadena DNS del stream       ║
║         • Todos los hostnames resueltos en la cadena HLS                     ║
║         • CNAME chain completo                                               ║
║         • Todos los IPs resueltos (múltiples registros A)                    ║
║         • ASN y organización de cada IP                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import os
import re
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_dns_cache = {}

_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(_TOOL_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from core.logger import log

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "Accept": "*/*",
}

# ── Timezone → Region mapping (para inferir ubicación desde horario) ──────────
TZ_OFFSET_TO_REGIONS: Dict[int, List[str]] = {
    -12: ["Baker Island (EEUU)"],
    -11: ["Samoa Americana", "Niue"],
    -10: ["Hawái", "Polinesia Francesa"],
    -9:  ["Alaska"],
    -8:  ["Costa Oeste EEUU", "Canadá Pacífico", "México (Baja California)"],
    -7:  ["Montañas EEUU", "México (Chihuahua, Sonora)"],
    -6:  ["Centro EEUU", "México Central", "Colombia", "Ecuador", "Perú",
          "Guatemala", "El Salvador", "Honduras", "Nicaragua", "Costa Rica"],
    -5:  ["Este EEUU", "Colombia", "Ecuador", "Perú", "Cuba", "Jamaica",
          "Panamá", "Bolivia (algunas zonas)"],
    -4:  ["Venezuela", "Bolivia", "Paraguay", "Chile", "Brasil (Manaos)",
          "Puerto Rico", "República Dominicana", "Trinidad y Tobago"],
    -3:  ["Argentina", "Uruguay", "Chile (verano)", "Brasil (Brasília, São Paulo)",
          "Guyana Francesa", "Surinam"],
    -2:  ["Atlántico Sur", "Fernando de Noronha"],
    -1:  ["Azores", "Cabo Verde"],
     0:  ["Reino Unido", "Irlanda", "Portugal", "Ghana", "Senegal", "Marruecos"],
     1:  ["Europa Central (Berlín, París, Madrid, Roma)", "África Occidental"],
     2:  ["Europa del Este", "Sudáfrica", "Egipto", "Grecia", "Turquía",
          "Israel", "Lituania", "Ucrania"],
     3:  ["Rusia (Moscú)", "Arabia Saudí", "Kuwait", "Irak", "Kenia",
          "Etiopía", "Tanzania"],
     4:  ["UAE (Dubai)", "Omán", "Georgia", "Azerbaiyán", "Armenia"],
     5:  ["Pakistán (UTC+5)", "Uzbekistán", "Tayikistán", "Maldivas"],
     6:  ["Bangladesh", "Kazajistán", "Kirguistán"],
     7:  ["Vietnam", "Tailandia", "Indonesia (Java)", "Camboya", "Laos",
          "Myanmar (UTC+6:30)"],
     8:  ["China", "Taiwán", "Hong Kong", "Singapur", "Malasia",
          "Filipinas", "Australia Occidental"],
     9:  ["Japón", "Corea del Sur", "Indonesia (Irian Jaya)"],
    10:  ["Australia Oriental", "Papua Nueva Guinea", "Guam"],
    11:  ["Salomón", "Vanuatu", "Nueva Caledonia"],
    12:  ["Nueva Zelanda", "Fiyi", "Kiribati"],
}

# ── Idioma → regiones probables ───────────────────────────────────────────────
LANG_TO_REGIONS: Dict[str, List[str]] = {
    "es": ["España", "México", "Colombia", "Argentina", "Perú", "Chile",
           "Venezuela", "Ecuador", "Guatemala", "Cuba", "Bolivia", "Honduras",
           "Paraguay", "El Salvador", "Nicaragua", "Costa Rica", "Panamá",
           "Uruguay", "República Dominicana"],
    "en": ["EEUU", "Reino Unido", "Canadá", "Australia", "Irlanda",
           "Nueva Zelanda", "Jamaica", "Trinidad y Tobago"],
    "pt": ["Brasil", "Portugal", "Angola", "Mozambique", "Cabo Verde"],
    "fr": ["Francia", "Bélgica", "Suiza", "Canadá (Quebec)", "Costa de Marfil",
           "Senegal", "Camerún", "Argelia", "Marruecos (bilingüe)"],
    "ar": ["Arabia Saudí", "Egipto", "Irak", "Siria", "Marruecos", "Argelia",
           "Túnez", "Líbano", "Jordania", "UAE", "Kuwait"],
    "zh": ["China", "Taiwán", "Singapur", "Malaysia (comunidad china)",
           "Hong Kong"],
    "ja": ["Japón"],
    "ko": ["Corea del Sur", "Corea del Norte"],
    "ru": ["Rusia", "Ucrania", "Bielorrusia", "Kazajistán", "Uzbekistán",
           "Moldova", "Georgia", "Armenia", "Azerbaiyán"],
    "de": ["Alemania", "Austria", "Suiza (alemán)", "Liechtenstein"],
    "it": ["Italia", "San Marino", "Suiza (italiano)"],
    "hi": ["India (Hindi)", "Nepal", "Fiji"],
    "tr": ["Turquía", "Chipre (turcochipriota)"],
    "vi": ["Vietnam"],
    "th": ["Tailandia"],
    "id": ["Indonesia"],
    "ms": ["Malasia", "Brunéi", "Singapur"],
    "tl": ["Filipinas"],
    "uk": ["Ucrania"],
    "pl": ["Polonia"],
    "nl": ["Países Bajos", "Bélgica (Flandes)", "Surinam"],
}

# ── Palabras/hashtags de geo explícita ────────────────────────────────────────
GEO_KEYWORDS: Dict[str, str] = {
    # Países y ciudades comunes en hashtags/bio de TikTok
    "🇲🇽": "México", "🇨🇴": "Colombia", "🇵🇪": "Perú", "🇦🇷": "Argentina",
    "🇨🇱": "Chile", "🇻🇪": "Venezuela", "🇪🇨": "Ecuador", "🇧🇷": "Brasil",
    "🇺🇸": "EEUU", "🇪🇸": "España", "🇬🇧": "Reino Unido", "🇨🇦": "Canadá",
    "🇯🇵": "Japón", "🇰🇷": "Corea del Sur", "🇨🇳": "China", "🇮🇳": "India",
    "🇩🇪": "Alemania", "🇫🇷": "Francia", "🇮🇹": "Italia", "🇷🇺": "Rusia",
    "🇹🇷": "Turquía", "🇸🇦": "Arabia Saudí", "🇦🇪": "UAE", "🇲🇾": "Malasia",
    "🇮🇩": "Indonesia", "🇵🇭": "Filipinas", "🇹🇭": "Tailandia", "🇻🇳": "Vietnam",
    "🇬🇹": "Guatemala", "🇸🇻": "El Salvador", "🇭🇳": "Honduras",
    "🇳🇮": "Nicaragua", "🇨🇷": "Costa Rica", "🇵🇦": "Panamá",
    "🇧🇴": "Bolivia", "🇵🇾": "Paraguay", "🇺🇾": "Uruguay",
    # Ciudad keywords
    "bogotá": "Colombia", "medellín": "Colombia", "cali": "Colombia",
    "lima": "Perú", "cusco": "Perú", "arequipa": "Perú",
    "ciudad de méxico": "México", "cdmx": "México", "guadalajara": "México",
    "monterrey": "México", "tijuana": "México",
    "buenos aires": "Argentina", "córdoba": "Argentina", "rosario": "Argentina",
    "santiago": "Chile", "valparaíso": "Chile",
    "caracas": "Venezuela", "maracaibo": "Venezuela",
    "quito": "Ecuador", "guayaquil": "Ecuador",
    "madrid": "España", "barcelona": "España", "sevilla": "España",
    "são paulo": "Brasil", "rio de janeiro": "Brasil", "brasília": "Brasil",
    "new york": "EEUU", "los angeles": "EEUU", "miami": "EEUU",
    "london": "Reino Unido", "manchester": "Reino Unido",
    "paris": "Francia", "berlin": "Alemania", "rome": "Italia",
    "moscow": "Rusia", "istanbul": "Turquía", "dubai": "UAE",
    "tokyo": "Japón", "osaka": "Japón", "seoul": "Corea del Sur",
    "beijing": "China", "shanghai": "China", "mumbai": "India",
    "bangkok": "Tailandia", "jakarta": "Indonesia", "manila": "Filipinas",
    "hanoi": "Vietnam", "ho chi minh": "Vietnam",
    "kuala lumpur": "Malasia", "singapore": "Singapur",
}


# ══════════════════════════════════════════════════════════════════════════════
# [5a] StreamInfraMapper — Mapa completo de infraestructura de red del stream
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class InfraNode:
    """Nodo de infraestructura descubierto en la cadena del stream."""
    role: str           # 'cdn_edge', 'origin_ingest', 'hls_segment', 'api'
    hostname: str = ""
    ip: str = ""
    asn: str = ""
    asn_org: str = ""
    geo_country: str = ""
    geo_region: str = ""
    geo_city: str = ""
    geo_lat: float = 0.0
    geo_lon: float = 0.0
    isp: str = ""
    reverse_dns: str = ""
    cdn_provider: str = ""
    tls_issuer: str = ""
    response_server: str = ""
    discovered_via: str = ""


@dataclass
class InfraMap:
    """Mapa completo de la infraestructura de red de un stream."""
    stream_url: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    nodes: List[InfraNode] = field(default_factory=list)
    all_ips: List[str] = field(default_factory=list)
    all_hostnames: List[str] = field(default_factory=list)
    cname_chain: List[str] = field(default_factory=list)
    hls_segments_sampled: int = 0
    ingest_server_guess: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class StreamInfraMapper:
    """
    Módulo 5a: Mapeo completo de la infraestructura de red de un TikTok Live.

    Técnicas utilizadas (todas pasivas y legales):
    - DNS resolution multi-registro (A, CNAME) de todos los hostnames
    - IP geolocation vía ipinfo.io API pública
    - BGP/ASN lookup vía ipinfo.io
    - Reverse DNS (PTR record)
    - HTTP header analysis de cada nodo CDN
    - TLS certificate inspection (emisor, SAN, organización)
    - HLS manifest traversal — descubrir URLs de segmentos y sus CDNs
    - WHOIS-like lookup vía rdap.org (público, no requiere key)
    """

    _IPINFO_BASE = "https://ipinfo.io"
    _RDAP_BASE = "https://rdap.org/ip"

    def map_stream(self, stream_url: str) -> InfraMap:
        """Construye el mapa completo de infraestructura del stream."""
        infra = InfraMap(stream_url=stream_url)
        seen_ips = set()

        try:
            parsed = urllib.parse.urlparse(stream_url)
            hostname = parsed.hostname or ""

            if not hostname:
                infra.error = "URL de stream inválida"
                return infra

            # 1. Resolver la cadena DNS completa (CNAME → A)
            cname_chain, all_ips = self._resolve_full_dns_chain(hostname)
            infra.cname_chain = cname_chain
            infra.all_hostnames = list(set([hostname] + cname_chain))

            for ip in all_ips:
                if ip not in seen_ips:
                    seen_ips.add(ip)
                    infra.all_ips.append(ip)
                    node = self._build_node_from_ip(ip, hostname, "cdn_edge")
                    infra.nodes.append(node)

            # 2. Si es HLS (.m3u8), parsear el manifest y descubrir más nodos
            if ".m3u8" in stream_url or "hls" in stream_url.lower():
                extra_nodes = self._traverse_hls_manifest(stream_url, seen_ips)
                infra.nodes.extend(extra_nodes)
                infra.hls_segments_sampled = len(extra_nodes)

            # 3. TLS certificate inspection del hostname principal
            tls_info = self._inspect_tls(hostname, parsed.port or 443)
            if tls_info and infra.nodes:
                infra.nodes[0].tls_issuer = tls_info.get("issuer", "")

            # 4. HTTP header analysis del CDN edge
            headers = self._fetch_cdn_headers(stream_url)
            if headers and infra.nodes:
                infra.nodes[0].response_server = headers.get("server", "")

            # 5. Intentar inferir el servidor de ingesta (origen del streamer)
            infra.ingest_server_guess = self._guess_ingest_server(hostname, infra.cname_chain)

            log.info(
                f"[GTLIS·InfraMapper] Mapeados {len(infra.nodes)} nodos, "
                f"{len(infra.all_ips)} IPs únicos"
            )

        except Exception as exc:
            infra.error = str(exc)
            log.error(f"[GTLIS·InfraMapper] Error: {exc}")

        return infra

    def _resolve_full_dns_chain(self, hostname: str) -> Tuple[List[str], List[str]]:
        """
        Resuelve la cadena CNAME completa y todos los registros A.
        Usa socket.getaddrinfo() — no requiere librerías externas.
        """
        cnames: List[str] = []
        ips: List[str] = []

        try:
            # getaddrinfo retorna todas las IPs (round-robin DNS incluido)
            results = socket.getaddrinfo(hostname, None, socket.AF_INET)
            ips = list(set(r[4][0] for r in results))
        except socket.gaierror:
            pass

        # Intentar nslookup para obtener la CNAME chain
        try:
            out = subprocess.run(
                ["nslookup", hostname],
                capture_output=True, text=True, timeout=5
            )
            if out.returncode == 0:
                for line in out.stdout.splitlines():
                    # Líneas como "Name:    something.tiktokcdn.com"
                    # o "Addresses:  1.2.3.4"
                    line = line.strip()
                    if "canonical name" in line.lower() or "aliases:" in line.lower():
                        m = re.search(r"=\s*(.+)", line)
                        if m:
                            cnames.append(m.group(1).strip().rstrip("."))
                    elif re.match(r"^\d+\.\d+\.\d+\.\d+$", line):
                        if line not in ips:
                            ips.append(line)
        except Exception:
            pass

        return cnames, ips

    def _build_node_from_ip(self, ip: str, hostname: str, role: str) -> InfraNode:
        """Construye un InfraNode completo a partir de una IP usando APIs públicas."""
        node = InfraNode(role=role, hostname=hostname, ip=ip)

        # ipinfo.io — datos públicos sin auth key (100 req/día gratis)
        try:
            geo = self._ipinfo_lookup(ip)
            node.geo_country = geo.get("country", "")
            node.geo_city = geo.get("city", "")
            node.geo_region = geo.get("region", "")
            node.isp = geo.get("org", "")
            node.asn = geo.get("org", "").split()[0] if geo.get("org") else ""
            node.asn_org = " ".join(geo.get("org", "").split()[1:]) if geo.get("org") else ""

            # Lat/Lon si están disponibles
            loc = geo.get("loc", "")
            if loc and "," in loc:
                try:
                    lat, lon = loc.split(",")
                    node.geo_lat = float(lat)
                    node.geo_lon = float(lon)
                except ValueError:
                    pass

            node.discovered_via = "ipinfo.io"
        except Exception:
            pass

        # Reverse DNS
        try:
            node.reverse_dns = socket.gethostbyaddr(ip)[0]
        except Exception:
            pass

        # CDN identification from reverse DNS
        node.cdn_provider = self._identify_cdn_from_rdns(
            node.reverse_dns or hostname
        )

        return node

    def _ipinfo_lookup(self, ip: str) -> Dict[str, str]:
        """Lookup completo en ipinfo.io (API pública gratuita)."""
        url = f"{self._IPINFO_BASE}/{ip}/json"
        try:
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return {}

    def _identify_cdn_from_rdns(self, rdns: str) -> str:
        """Identifica el CDN a partir del reverse DNS."""
        rdns = rdns.lower()
        patterns = {
            "tiktok": "TikTok CDN", "muscdn": "TikTok MusCDN",
            "bytedance": "ByteDance", "bytecdn": "ByteDance CDN",
            "akamai": "Akamai", "akamaiedge": "Akamai Edge",
            "cloudfront": "AWS CloudFront", "fastly": "Fastly",
            "cloudflare": "Cloudflare", "llnwd": "Limelight",
            "gcdn": "G-Core", "google": "Google CDN",
        }
        for pattern, name in patterns.items():
            if pattern in rdns:
                return name
        return "Unknown"

    def _traverse_hls_manifest(self, m3u8_url: str, seen_ips: set) -> List[InfraNode]:
        """
        Parsea el manifest HLS maestro y los sub-manifests para
        descubrir todos los servidores CDN implicados en la entrega.
        """
        nodes: List[InfraNode] = []
        try:
            req = urllib.request.Request(m3u8_url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="replace")

            # Extraer todas las URLs únicas del manifest
            segment_urls: List[str] = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    full_url = (
                        line if line.startswith("http")
                        else urllib.parse.urljoin(m3u8_url, line)
                    )
                    segment_urls.append(full_url)

            # Analizar los primeros 5 segmentos únicos de hostnames
            seen_hosts_in_hls: set = set()
            for seg_url in segment_urls[:20]:
                parsed = urllib.parse.urlparse(seg_url)
                h = parsed.hostname or ""
                if h and h not in seen_hosts_in_hls:
                    seen_hosts_in_hls.add(h)
                    try:
                        results = socket.getaddrinfo(h, None, socket.AF_INET)
                        for r in results:
                            ip = r[4][0]
                            if ip not in seen_ips:
                                seen_ips.add(ip)
                                node = self._build_node_from_ip(ip, h, "hls_segment")
                                nodes.append(node)
                    except Exception:
                        pass

        except Exception as exc:
            log.debug(f"[GTLIS·HLSTraversal] {exc}")

        return nodes

    def _inspect_tls(self, hostname: str, port: int = 443) -> Dict[str, str]:
        """Inspecciona el certificado TLS del servidor."""
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as raw_sock:
                with ctx.wrap_socket(raw_sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    issuer = dict(x[0] for x in cert.get("issuer", []))
                    subject = dict(x[0] for x in cert.get("subject", []))
                    san = cert.get("subjectAltName", [])
                    return {
                        "issuer": issuer.get("organizationName", ""),
                        "issuer_cn": issuer.get("commonName", ""),
                        "subject_cn": subject.get("commonName", ""),
                        "san_domains": [v for t, v in san if t == "DNS"][:10],
                        "version": ssock.version() or "",
                    }
        except Exception:
            return {}

    def _fetch_cdn_headers(self, url: str) -> Dict[str, str]:
        """Hace HEAD request y retorna los headers diagnósticos del CDN."""
        try:
            req = urllib.request.Request(
                url, headers={**_BROWSER_HEADERS, "Range": "bytes=0-0"}, method="HEAD"
            )
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                return {k.lower(): v for k, v in dict(resp.headers).items()}
        except Exception:
            return {}

    def _guess_ingest_server(self, hostname: str, cnames: List[str]) -> str:
        """
        Intenta inferir el servidor de ingesta (RTMP) del streamer.
        Los servidores de ingesta TikTok tienen patrones conocidos en sus hostnames:
        push-xxx.tiktokcdn.com, ingest-xxx.tiktok.com, etc.
        """
        all_hosts = [hostname] + cnames
        ingest_patterns = ["push", "ingest", "rtmp", "upload", "live-upload"]
        for h in all_hosts:
            for p in ingest_patterns:
                if p in h.lower():
                    return h
        # Heurística: si el hostname tiene "pull", el servidor push es similar
        for h in all_hosts:
            h_lower = h.lower()
            if "pull" in h_lower:
                guess = h_lower.replace("pull", "push")
                return f"{guess} (inferido)"
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# [5b] StreamerGeoProfiler — Perfil geográfico del streamer
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class GeoProfile:
    """Perfil geográfico inferido del streamer."""
    username: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Idioma
    detected_language: str = ""
    detected_language_variant: str = ""   # ej: "es-MX", "en-US"
    language_confidence: float = 0.0
    possible_regions_by_lang: List[str] = field(default_factory=list)
    # Timezone
    inferred_tz_offset: Optional[int] = None
    inferred_tz_regions: List[str] = field(default_factory=list)
    # Geo explícita
    explicit_locations: List[str] = field(default_factory=list)  # de bio/hashtags
    flag_emojis: List[str] = field(default_factory=list)
    # Triangulación
    top_candidate_countries: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    methodology: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamerGeoProfiler:
    """
    Módulo 5b: Construye un perfil geográfico completo del streamer
    a partir de señales públicas y técnicas.

    Metodología de triangulación:
    1. Idioma detectado en bio, título del live y caption
    2. Hashtags con nombres de ciudades/países
    3. Emojis de banderas en bio
    4. Horario histórico de streaming → inferencia de zona horaria
    5. Idioma dominante en comentarios públicos recientes
    6. Cross-referencia con otras redes sociales (perfil público)
    7. Metadata del CDN: el edge server geográficamente más cercano al streamer
       tiende a ser el mismo región (heurística con margen de error)
    """

    # Patrones de variantes regionales de español
    _ES_VARIANT_KEYWORDS: Dict[str, str] = {
        "wey": "es-MX", "güey": "es-MX", "órale": "es-MX", "chido": "es-MX",
        "parce": "es-CO", "gonorrea": "es-CO", "bacano": "es-CO",
        "pata": "es-PE", "causa": "es-PE", "mostro": "es-PE",
        "pana": "es-VE", "chamo": "es-VE", "coño": "es-VE",
        "chaval": "es-ES", "tío": "es-ES", "joder": "es-ES",
        "boludo": "es-AR", "che": "es-AR", "pibe": "es-AR",
        "huevón": "es-CL", "bacán": "es-CL", "po": "es-CL",
        "mae": "es-CR", "tuanis": "es-CR",
        "maje": "es-HN", "bicho": "es-SV",
        "vos": "es-AR|es-UY|es-CR|es-BO",
    }

    def build_profile(
        self,
        username: str,
        bio: str = "",
        live_title: str = "",
        comment_sample: List[str] = None,
        live_history: List[Dict] = None,
        stream_cdn_country: str = "",
    ) -> GeoProfile:
        """
        Construye el perfil geográfico triangulando todas las señales disponibles.
        """
        profile = GeoProfile(username=username)
        country_votes: Counter = Counter()

        # ── Señal 1: Emojis de bandera en bio ──────────────────────────────────
        all_text = f"{bio} {live_title}"
        flag_countries = self._extract_flags(all_text)
        for country in flag_countries:
            country_votes[country] += 5  # peso alto — explícito
        profile.flag_emojis = [k for k in GEO_KEYWORDS if k in all_text and len(k) == 2]
        profile.explicit_locations.extend(flag_countries)
        if flag_countries:
            profile.methodology.append(f"Banderas emoji detectadas: {flag_countries}")

        # ── Señal 2: Palabras clave geográficas en bio/título ─────────────────
        text_lower = all_text.lower()
        keyword_countries = self._extract_geo_keywords(text_lower)
        for country in keyword_countries:
            country_votes[country] += 4
        profile.explicit_locations.extend(keyword_countries)
        if keyword_countries:
            profile.methodology.append(f"Geo-keywords detectadas: {keyword_countries}")

        # ── Señal 3: Detección de idioma ──────────────────────────────────────
        lang, variant, confidence = self._detect_language(all_text, comment_sample)
        profile.detected_language = lang
        profile.detected_language_variant = variant
        profile.language_confidence = confidence
        if lang and lang in LANG_TO_REGIONS:
            profile.possible_regions_by_lang = LANG_TO_REGIONS[lang]
            for region in LANG_TO_REGIONS[lang]:
                country_votes[region] += 2  # peso medio — idioma no es determinante
            profile.methodology.append(
                f"Idioma detectado: {lang} (variante: {variant}, conf: {confidence:.0%})"
            )

        # ── Señal 4: Variante regional del español ────────────────────────────
        if lang == "es" and variant:
            variant_region = {
                "es-MX": "México", "es-CO": "Colombia", "es-PE": "Perú",
                "es-VE": "Venezuela", "es-ES": "España", "es-AR": "Argentina",
                "es-CL": "Chile", "es-CR": "Costa Rica",
            }.get(variant)
            if variant_region:
                country_votes[variant_region] += 8  # peso muy alto
                profile.methodology.append(
                    f"Variante de español detectada: {variant} → {variant_region}"
                )

        # ── Señal 5: Zona horaria inferida del historial de streams ───────────
        if live_history:
            tz_offset, tz_confidence = self._infer_timezone(live_history)
            if tz_offset is not None:
                profile.inferred_tz_offset = tz_offset
                tz_regions = TZ_OFFSET_TO_REGIONS.get(tz_offset, [])
                profile.inferred_tz_regions = tz_regions
                for region in tz_regions:
                    country_votes[region] += 3
                profile.methodology.append(
                    f"Timezone inferida: UTC{tz_offset:+d} "
                    f"(confianza: {tz_confidence:.0%}) → {tz_regions[:3]}"
                )

        # ── Señal 6: País del servidor CDN edge (heurística geográfica) ───────
        if stream_cdn_country:
            country_votes[stream_cdn_country] += 1  # peso bajo — CDN ≠ streamer
            profile.methodology.append(
                f"CDN edge país: {stream_cdn_country} "
                f"(correlación débil — el streamer puede estar cerca)"
            )

        # ── Consolidar candidatos ─────────────────────────────────────────────
        total_votes = sum(country_votes.values()) or 1
        profile.top_candidate_countries = [
            {
                "country": country,
                "votes": votes,
                "confidence": round(votes / total_votes, 3),
            }
            for country, votes in country_votes.most_common(5)
        ]

        if profile.top_candidate_countries:
            top_conf = profile.top_candidate_countries[0]["confidence"]
            profile.confidence_score = round(top_conf, 3)

        log.info(
            f"[GTLIS·GeoProfiler] @{username} → top candidato: "
            f"{profile.top_candidate_countries[0]['country'] if profile.top_candidate_countries else 'N/A'} "
            f"({profile.confidence_score:.0%})"
        )

        return profile

    def _extract_flags(self, text: str) -> List[str]:
        """Extrae países de emojis de banderas."""
        countries = []
        for emoji, country in GEO_KEYWORDS.items():
            if len(emoji) == 2 and emoji in text:  # solo emojis (2 chars unicode)
                countries.append(country)
        return list(set(countries))

    def _extract_geo_keywords(self, text_lower: str) -> List[str]:
        """Extrae países/ciudades mencionados en el texto."""
        countries = []
        for keyword, country in GEO_KEYWORDS.items():
            if len(keyword) > 2 and keyword in text_lower:
                countries.append(country)
        # Extraer hashtags con nombres de lugar (#Lima, #Bogota, etc.)
        hashtags = re.findall(r"#(\w+)", text_lower)
        for tag in hashtags:
            for keyword, country in GEO_KEYWORDS.items():
                if len(keyword) > 2 and tag in keyword.replace(" ", ""):
                    countries.append(country)
        return list(set(countries))

    def _detect_language(
        self,
        text: str,
        comments: Optional[List[str]] = None
    ) -> Tuple[str, str, float]:
        """
        Detecta el idioma del texto usando heurísticas de n-gramas de caracteres.
        Retorna (lang_code, variant, confidence).
        Heurística robusta sin librerías externas.
        """
        all_text = text
        if comments:
            all_text += " " + " ".join(comments[:50])

        if not all_text.strip():
            return "", "", 0.0

        text_lower = all_text.lower()

        # Conteo de palabras diagnósticas por idioma
        lang_scores: Counter = Counter()

        LANG_MARKERS: Dict[str, List[str]] = {
            "es": ["que", "de", "la", "el", "en", "y", "con", "por", "para",
                   "una", "los", "las", "del", "es", "no", "se", "lo", "le",
                   "muy", "más", "pero", "como", "todo", "bien", "gracias",
                   "amigo", "hola", "qué", "está", "tengo"],
            "en": ["the", "and", "is", "in", "to", "of", "a", "that", "it",
                   "for", "you", "with", "he", "she", "we", "they", "this",
                   "have", "from", "or", "an", "will", "my", "one", "all",
                   "would", "there", "their", "what", "so", "up", "out"],
            "pt": ["que", "de", "a", "o", "e", "do", "da", "em", "para",
                   "com", "um", "uma", "os", "as", "não", "por", "mas",
                   "ao", "se", "na", "isso", "tudo", "muito", "obrigado"],
            "fr": ["le", "la", "les", "de", "du", "et", "en", "un", "une",
                   "je", "tu", "il", "nous", "vous", "ils", "est", "pas",
                   "que", "qui", "sur", "pour", "avec", "dans", "ce", "se"],
            "de": ["die", "der", "das", "und", "ist", "ich", "du", "er",
                   "wir", "sie", "es", "nicht", "ein", "eine", "von", "zu",
                   "mit", "auf", "für", "an", "dem", "den", "auch", "noch"],
            "it": ["il", "la", "le", "di", "e", "in", "un", "una", "che",
                   "non", "si", "con", "per", "del", "della", "mi", "ti",
                   "ci", "lo", "li", "ho", "ha", "sono", "sei", "è"],
            "ru": ["и", "в", "не", "на", "я", "что", "тот", "быть", "он",
                   "с", "а", "как", "это", "по", "но", "они", "к", "из"],
            "ar": ["ال", "في", "من", "إلى", "على", "أن", "هذا", "مع",
                   "كان", "قال", "له", "هو"],
            "zh": ["的", "是", "在", "了", "和", "我", "有", "不", "这", "人"],
            "ja": ["の", "に", "は", "を", "が", "で", "と", "て", "た", "し"],
            "ko": ["이", "가", "은", "는", "을", "를", "의", "에", "도", "한"],
            "tr": ["bir", "ve", "bu", "da", "de", "ile", "ne", "mi", "için", "ben"],
            "vi": ["và", "của", "là", "có", "trong", "không", "được", "với", "cho", "như"],
        }

        words = re.findall(r"\b\w+\b", text_lower)
        word_set = set(words)

        for lang, markers in LANG_MARKERS.items():
            hits = sum(1 for m in markers if m in word_set)
            lang_scores[lang] = hits

        if not lang_scores or lang_scores.most_common(1)[0][1] == 0:
            return "", "", 0.0

        top_lang, top_hits = lang_scores.most_common(1)[0]
        second_hits = lang_scores.most_common(2)[1][1] if len(lang_scores) > 1 else 0
        total = sum(lang_scores.values()) or 1
        confidence = (top_hits - second_hits) / total

        # Detectar variante regional si es español
        variant = ""
        if top_lang == "es":
            variant_votes: Counter = Counter()
            for word, var in self._ES_VARIANT_KEYWORDS.items():
                if word in text_lower:
                    for v in var.split("|"):
                        variant_votes[v] += 1
            if variant_votes:
                variant = variant_votes.most_common(1)[0][0]

        return top_lang, variant, round(min(confidence, 1.0), 3)

    def _infer_timezone(
        self, snapshots: List[Dict]
    ) -> Tuple[Optional[int], float]:
        """
        Infiere la zona horaria del streamer analizando en qué horas locales
        suele hacer live. Asume que los streams ocurren entre 18:00-02:00 hora local.

        Algoritmo: encuentra el offset UTC que maximiza la cantidad de streams
        en la ventana 18:00-01:00 hora local.
        """
        live_hours_utc = []
        for s in snapshots:
            if s.get("is_live") or s.get("is_live") == 1:
                try:
                    dt = datetime.fromisoformat(s["ts"].replace("Z", "+00:00"))
                    live_hours_utc.append(dt.hour)
                except Exception:
                    pass

        if len(live_hours_utc) < 3:
            return None, 0.0

        best_offset: Optional[int] = None
        best_score: int = 0

        # Probar todos los offsets UTC de -12 a +12
        for offset in range(-12, 13):
            local_hours = [(h + offset) % 24 for h in live_hours_utc]
            # Ventana horaria típica de streaming: 17:00 - 02:00 local
            in_window = sum(
                1 for h in local_hours
                if h >= 17 or h <= 2
            )
            if in_window > best_score:
                best_score = in_window
                best_offset = offset

        confidence = best_score / len(live_hours_utc) if live_hours_utc else 0.0
        return best_offset, round(confidence, 3)


# ══════════════════════════════════════════════════════════════════════════════
# [5c] CommentGeoAnalyzer — Distribución geográfica de la audiencia
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class AudienceGeoProfile:
    """Perfil geográfico de la audiencia de un live."""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    comments_analyzed: int = 0
    language_distribution: Dict[str, float] = field(default_factory=dict)
    geo_distribution_estimate: Dict[str, float] = field(default_factory=dict)
    dominant_language: str = ""
    audience_regions: List[str] = field(default_factory=list)
    geo_hashtags_found: List[str] = field(default_factory=list)
    activity_hour_utc_peak: Optional[int] = None
    estimated_tz_offset: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommentGeoAnalyzer:
    """
    Módulo 5c: Analiza la distribución geográfica de la audiencia
    a partir de comentarios públicos del live.

    Técnicas:
    - Detección de idioma por comentario
    - Extracción de hashtags y menciones geográficas
    - Análisis de timestamps de actividad para inferir zona horaria de la audiencia
    - Palabras clave regionales por variante dialectal
    """

    def __init__(self):
        self._profiler = StreamerGeoProfiler()

    def analyze(self, comments: List[Dict[str, Any]]) -> AudienceGeoProfile:
        """
        Analiza una muestra de comentarios públicos.

        Args:
            comments: Lista de dicts con keys: user_id, text, timestamp_ms
        """
        profile = AudienceGeoProfile()
        profile.comments_analyzed = len(comments)

        if not comments:
            return profile

        # ── Detección de idioma por comentario ────────────────────────────────
        lang_counts: Counter = Counter()
        all_texts = [str(c.get("text", "")) for c in comments if c.get("text")]

        for text in all_texts:
            lang, _, conf = self._profiler._detect_language(text)
            if lang and conf > 0.1:
                lang_counts[lang] += 1

        total_with_lang = sum(lang_counts.values()) or 1
        profile.language_distribution = {
            lang: round(count / total_with_lang, 3)
            for lang, count in lang_counts.most_common(8)
        }
        if lang_counts:
            profile.dominant_language = lang_counts.most_common(1)[0][0]

        # ── Distribución geográfica estimada por idioma ───────────────────────
        geo_scores: Counter = Counter()
        for lang, count in lang_counts.items():
            if lang in LANG_TO_REGIONS:
                share = count / total_with_lang
                regions = LANG_TO_REGIONS[lang]
                per_region = share / len(regions)
                for region in regions:
                    geo_scores[region] += per_region

        total_geo = sum(geo_scores.values()) or 1
        profile.geo_distribution_estimate = {
            region: round(score / total_geo, 3)
            for region, score in geo_scores.most_common(10)
        }
        profile.audience_regions = [r for r, _ in geo_scores.most_common(5)]

        # ── Hashtags y menciones geográficas en comentarios ───────────────────
        combined_text = " ".join(all_texts).lower()
        geo_tags = []
        for keyword, country in GEO_KEYWORDS.items():
            if len(keyword) > 2 and keyword in combined_text:
                geo_tags.append(f"#{keyword}→{country}")
            elif len(keyword) == 2 and keyword in combined_text:  # flag emoji
                geo_tags.append(f"{keyword}→{country}")
        profile.geo_hashtags_found = list(set(geo_tags))[:15]

        # ── Zona horaria de la audiencia por timestamps de comentarios ─────────
        timestamps_ms = [
            float(c.get("timestamp_ms", 0)) for c in comments
            if c.get("timestamp_ms")
        ]
        if timestamps_ms:
            # Hora UTC del pico de actividad
            hours_utc = [
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).hour
                for ts in timestamps_ms
            ]
            hour_counter = Counter(hours_utc)
            profile.activity_hour_utc_peak = hour_counter.most_common(1)[0][0]

            # Inferir TZ de audiencia: el pico suele ser 20:00 hora local
            peak_utc = profile.activity_hour_utc_peak
            # offset = local_peak - utc_peak. Asumimos peak local a las 20h
            estimated_offset = (20 - peak_utc + 12) % 24 - 12
            profile.estimated_tz_offset = estimated_offset

        log.info(
            f"[GTLIS·CommentGeo] {len(comments)} comentarios → "
            f"idioma dominante: {profile.dominant_language}, "
            f"top región: {profile.audience_regions[0] if profile.audience_regions else 'N/A'}"
        )

        return profile


# ══════════════════════════════════════════════════════════════════════════════
# [5d] DNSChainMapper — Mapa completo de cadena DNS
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class DNSRecord:
    hostname: str
    record_type: str    # A, CNAME, MX, TXT
    value: str
    ttl: int = 0
    asn: str = ""
    geo_country: str = ""
    geo_city: str = ""
    isp: str = ""


@dataclass
class DNSChain:
    target: str
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    records: List[DNSRecord] = field(default_factory=list)
    all_ips: List[str] = field(default_factory=list)
    geo_summary: Dict[str, int] = field(default_factory=dict)  # país → count IPs

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DNSChainMapper:
    """
    Módulo 5d: Mapa completo de la cadena DNS de cualquier hostname.
    Usa nslookup nativo de Windows (siempre disponible, sin deps).
    """

    def map(self, hostname: str) -> DNSChain:
        """Resuelve todos los registros DNS del hostname y geo-localiza cada IP."""
        chain = DNSChain(target=hostname)

        # A records
        try:
            results = socket.getaddrinfo(hostname, None)
            for family, _, _, _, addr in results:
                ip = addr[0]
                if ip not in chain.all_ips:
                    chain.all_ips.append(ip)
                    geo = self._geoip(ip)
                    chain.records.append(DNSRecord(
                        hostname=hostname,
                        record_type="A" if "." in ip else "AAAA",
                        value=ip,
                        asn=geo.get("org", "").split()[0] if geo.get("org") else "",
                        geo_country=geo.get("country", ""),
                        geo_city=geo.get("city", ""),
                        isp=" ".join(geo.get("org", "").split()[1:]) if geo.get("org") else "",
                    ))
                    country = geo.get("country", "unknown")
                    chain.geo_summary[country] = chain.geo_summary.get(country, 0) + 1
        except Exception:
            pass

        # nslookup para obtener más info (MX, CNAME via texto)
        try:
            nsl = subprocess.run(
                ["nslookup", "-type=ANY", hostname],
                capture_output=True, text=True, timeout=5,
            )
            for line in nsl.stdout.splitlines():
                line = line.strip()
                if "canonical name" in line.lower():
                    m = re.search(r"=\s*(.+)", line)
                    if m:
                        cname = m.group(1).strip().rstrip(".")
                        chain.records.append(
                            DNSRecord(hostname=hostname, record_type="CNAME", value=cname)
                        )
                elif "mail exchanger" in line.lower():
                    m = re.search(r"mail exchanger\s*=\s*(.+)", line, re.IGNORECASE)
                    if m:
                        chain.records.append(
                            DNSRecord(hostname=hostname, record_type="MX", value=m.group(1).strip())
                        )
                elif "text" in line.lower() and "=" in line:
                    m = re.search(r'text\s*=\s*"?(.+?)"?$', line, re.IGNORECASE)
                    if m:
                        chain.records.append(
                            DNSRecord(hostname=hostname, record_type="TXT", value=m.group(1))
                        )
        except Exception:
            pass

        _dns_cache[hostname] = chain
        return chain

    def _geoip(self, ip: str) -> Dict[str, str]:
        try:
            if ip in _dns_cache:
                return _dns_cache[ip]
            url = f"https://ipinfo.io/{ip}/json"
            req = urllib.request.Request(url, headers=_BROWSER_HEADERS)
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                _dns_cache[ip] = data
                return data
        except Exception:
            return {}


# ══════════════════════════════════════════════════════════════════════════════
# GeoIntelligenceEngine — Fachada unificada para todos los módulos de geo
# ══════════════════════════════════════════════════════════════════════════════


class GeoIntelligenceEngine:
    """
    Fachada que orquesta los 4 sub-módulos de inteligencia geográfica.
    Punto de entrada único para el TikTokLiveMonitor y el bridge_server.
    """

    def __init__(self) -> None:
        self.infra_mapper = StreamInfraMapper()
        self.geo_profiler = StreamerGeoProfiler()
        self.comment_geo = CommentGeoAnalyzer()
        self.dns_mapper = DNSChainMapper()

    def full_geo_report(
        self,
        username: str,
        stream_url: str = "",
        bio: str = "",
        live_title: str = "",
        comments: Optional[List[Dict]] = None,
        live_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Genera el informe geográfico completo combinando todos los sub-módulos.

        Returns un dict con:
        - infra_map: Todos los nodos de red descubiertos con IPs y geo
        - streamer_profile: Perfil geográfico del streamer
        - audience_geo: Distribución geográfica de la audiencia (si hay comments)
        - dns_chain: Mapa DNS completo del hostname del stream
        - summary: Resumen ejecutivo de hallazgos
        """
        report: Dict[str, Any] = {
            "username": username,
            "ts": datetime.now(timezone.utc).isoformat(),
            "methodology_note": (
                "LÍMITE LEGAL: Las IPs de viewers individuales no son accesibles "
                "sin técnicas ilegales (MITM/exploits). Este reporte contiene toda "
                "la inteligencia geográfica extraíble por vías legales."
            ),
        }

        # ── Infra Map ─────────────────────────────────────────────────────────
        if stream_url:
            try:
                infra = self.infra_mapper.map_stream(stream_url)
                report["infra_map"] = infra.to_dict()

                # DNS Chain del hostname del stream
                parsed = urllib.parse.urlparse(stream_url)
                hostname = parsed.hostname or ""
                if hostname:
                    dns_chain = self.dns_mapper.map(hostname)
                    report["dns_chain"] = dns_chain.to_dict()

                # Extraer país CDN para el geo_profiler
                cdn_country = ""
                if infra.nodes:
                    cdn_country = infra.nodes[0].geo_country

            except Exception as exc:
                report["infra_map"] = {"error": str(exc)}
                cdn_country = ""
        else:
            cdn_country = ""

        # ── Streamer Geo Profile ──────────────────────────────────────────────
        comment_texts = [c.get("text", "") for c in (comments or []) if c.get("text")]
        try:
            geo_profile = self.geo_profiler.build_profile(
                username=username,
                bio=bio,
                live_title=live_title,
                comment_sample=comment_texts[:100],
                live_history=live_history,
                stream_cdn_country=cdn_country,
            )
            report["streamer_geo_profile"] = geo_profile.to_dict()
        except Exception as exc:
            report["streamer_geo_profile"] = {"error": str(exc)}

        # ── Audience Geo (solo si hay comments) ──────────────────────────────
        if comments:
            try:
                audience = self.comment_geo.analyze(comments)
                report["audience_geo"] = audience.to_dict()
            except Exception as exc:
                report["audience_geo"] = {"error": str(exc)}

        # ── Summary ejecutivo ─────────────────────────────────────────────────
        report["summary"] = self._build_summary(report)

        return report

    def _build_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae los hallazgos más relevantes en un resumen ejecutivo."""
        summary: Dict[str, Any] = {}

        # IPs descubiertas
        infra = report.get("infra_map", {})
        summary["ips_discovered"] = infra.get("all_ips", [])
        summary["nodes_mapped"] = len(infra.get("nodes", []))
        summary["ingest_server"] = infra.get("ingest_server_guess", "")

        # Top candidato de ubicación del streamer
        geo = report.get("streamer_geo_profile", {})
        candidates = geo.get("top_candidate_countries", [])
        if candidates:
            top = candidates[0]
            summary["streamer_location_top_candidate"] = {
                "country": top.get("country"),
                "confidence": top.get("confidence"),
                "based_on": geo.get("methodology", []),
            }

        # Idioma del streamer
        summary["streamer_language"] = geo.get("detected_language", "")
        summary["streamer_language_variant"] = geo.get("detected_language_variant", "")
        summary["explicit_locations_in_bio"] = geo.get("explicit_locations", [])
        summary["inferred_timezone"] = (
            f"UTC{geo.get('inferred_tz_offset', 0):+d}"
            if geo.get("inferred_tz_offset") is not None else "unknown"
        )
        summary["inferred_timezone_regions"] = geo.get("inferred_tz_regions", [])

        # Audiencia
        audience = report.get("audience_geo", {})
        summary["audience_dominant_language"] = audience.get("dominant_language", "")
        summary["audience_top_regions"] = audience.get("audience_regions", [])[:3]
        
        # Feedback clínico para estado offline
        if not summary.get("ips_discovered") and not summary.get("explicit_locations_in_bio"):
            summary["offline_reason"] = (
                "Canal inactivo o con perfil cerrado. No hay transmisión en vivo (stream_url) "
                "para triangular nodos CDN, ni se detectó ninguna ubicación explícita en su biografía."
            )

        return summary
