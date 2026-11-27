"""ELM327/OBD-II Textantwort-Parser (SAE J1979 über ELM327 ASCII).

Behandelt Mehrzeilen-/Mehr-ECU-Antworten, NO DATA, SEARCHING, BUS ERROR,
CAN ERROR, STOPPED, UNABLE TO CONNECT, negative Antworten und Timeouts.
Unbekannte Werte werden NICHT als null interpretiert – Status bleibt explizit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class ResponseKind(str, Enum):
    OK = "ok"
    NO_DATA = "no_data"
    TIMEOUT = "timeout"
    SEARCHING = "searching"
    BUS_ERROR = "bus_error"
    CAN_ERROR = "can_error"
    STOPPED = "stopped"
    UNABLE_TO_CONNECT = "unable_to_connect"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"
    EMPTY = "empty"
    FRAGMENTED = "fragmented"
    MALFORMED = "malformed"


# ELM-Fehlertexte (Großschreibung nach Normalisierung)
_ELM_ERROR_MAP: list[tuple[str, ResponseKind]] = [
    ("NO DATA", ResponseKind.NO_DATA),
    ("STOPPED", ResponseKind.STOPPED),
    ("UNABLE TO CONNECT", ResponseKind.UNABLE_TO_CONNECT),
    ("BUS ERROR", ResponseKind.BUS_ERROR),
    ("CAN ERROR", ResponseKind.CAN_ERROR),
    ("BUS INIT", ResponseKind.SEARCHING),
    ("SEARCHING", ResponseKind.SEARCHING),
    ("ERROR", ResponseKind.UNKNOWN),
    ("?", ResponseKind.MALFORMED),
]


@dataclass(frozen=True)
class EcuFrame:
    """Eine Antwortzeile eines Steuergeräts (optional mit CAN-Header)."""

    ecu_id: str | None
    service: int | None
    pid_or_info: int | None
    data: tuple[int, ...]
    raw_hex: str
    negative_code: int | None = None

    @property
    def is_negative(self) -> bool:
        return self.service == 0x7F or self.negative_code is not None


@dataclass
class ParsedElmResponse:
    kind: ResponseKind
    raw: str
    frames: list[EcuFrame] = field(default_factory=list)
    message_de: str = ""
    timed_out: bool = False
    aborted: bool = False

    @property
    def multi_ecu(self) -> bool:
        ecu_ids = {f.ecu_id for f in self.frames if f.ecu_id}
        return len(ecu_ids) > 1 or (len(self.frames) > 1 and not ecu_ids)


_HEX_TOKEN = re.compile(r"^[0-9A-Fa-f]{2}$")
_HEX_RUN = re.compile(r"[0-9A-Fa-f]{2}")


def _normalize_lines(raw: str) -> list[str]:
    text = raw.replace("\r", "\n")
    lines: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s == ">":
            continue
        # Echo / Prompt-Reste entfernen
        if s.endswith(">"):
            s = s[:-1].strip()
        if s:
            lines.append(s)
    return lines


def _bytes_from_hex_line(line: str) -> list[int] | None:
    """Extrahiert Hex-Bytes; akzeptiert '7E8 41 0C 1F 40', '41 0C 1F 40' oder kompakt."""
    cleaned = line.replace(":", " ").replace(",", " ")
    tokens = cleaned.split()
    if not tokens:
        return None

    out: list[int] = []
    start = 0
    # ELM ATH1: 11-bit CAN-ID als 3 Nibbles (7E8–7EF)
    if len(tokens[0]) == 3 and re.fullmatch(r"[0-9A-Fa-f]{3}", tokens[0]):
        can_id = int(tokens[0], 16)
        if 0x700 <= can_id <= 0x7FF:
            out.append((can_id >> 8) & 0xFF)
            out.append(can_id & 0xFF)
            start = 1

    rest = tokens[start:]
    if rest and all(_HEX_TOKEN.match(t) or (len(t) == 1 and re.fullmatch(r"[0-9A-Fa-f]", t)) for t in rest):
        for t in rest:
            out.append(int(t, 16))
        return out if out else None

    if tokens and all(_HEX_TOKEN.match(t) for t in tokens):
        return [int(t, 16) for t in tokens]

    compact = re.sub(r"[^0-9A-Fa-f]", "", line)
    if len(compact) >= 2 and len(compact) % 2 == 0 and re.fullmatch(r"[0-9A-Fa-f]+", compact):
        return [int(compact[i : i + 2], 16) for i in range(0, len(compact), 2)]
    return None


def _parse_frame_bytes(data: list[int]) -> EcuFrame | None:
    if not data:
        return None

    ecu_id: str | None = None
    payload = data

    # CAN 11-bit Header oft als 3 Hex-Nibbles / 2 Bytes vor dem Service (z. B. 7E8)
    # ELM mit ATH1: "7E8 41 0C 1F 40"
    if len(data) >= 3 and data[0] in (0x7E8, 0x7E9, 0x7EA, 0x7EB, 0x7EC, 0x7ED, 0x7EE, 0x7EF):
        # Wenn als volles Byte 0x7E8 gespeichert – selten; eher zwei Bytes 07 E8
        pass

    # Zwei-Byte-Header 07 Ex (häufig bei ATH1)
    if len(data) >= 4 and data[0] == 0x07 and 0xE8 <= data[1] <= 0xEF:
        ecu_id = f"{data[0]:02X}{data[1]:02X}"
        payload = data[2:]
    elif len(data) >= 3 and 0x7E8 <= data[0] <= 0x7EF:
        ecu_id = f"{data[0]:03X}"
        payload = data[1:]

    if not payload:
        return None

    # Negativantwort ISO 14229 / SAE J1979: 7F <sid> <nrc>
    if payload[0] == 0x7F:
        sid = payload[1] if len(payload) > 1 else None
        nrc = payload[2] if len(payload) > 2 else None
        return EcuFrame(
            ecu_id=ecu_id,
            service=0x7F,
            pid_or_info=sid,
            data=tuple(payload[3:]) if len(payload) > 3 else (),
            raw_hex=" ".join(f"{b:02X}" for b in data),
            negative_code=nrc,
        )

    service = payload[0]
    # Positive Response = request + 0x40
    pid: int | None = None
    body: tuple[int, ...]
    if len(payload) >= 2 and service in (0x41, 0x42, 0x43, 0x47, 0x4A, 0x49):
        pid = payload[1]
        body = tuple(payload[2:])
    else:
        body = tuple(payload[1:])

    return EcuFrame(
        ecu_id=ecu_id,
        service=service,
        pid_or_info=pid,
        data=body,
        raw_hex=" ".join(f"{b:02X}" for b in data),
    )


def parse_elm_response(
    raw: str | None,
    *,
    timed_out: bool = False,
    aborted: bool = False,
) -> ParsedElmResponse:
    """Parst eine ELM327-Rohantwort. Unbekannt ≠ null."""
    if aborted:
        return ParsedElmResponse(
            kind=ResponseKind.STOPPED,
            raw=raw or "",
            message_de="Abbruch durch Benutzer oder Cancel.",
            aborted=True,
        )
    if timed_out:
        return ParsedElmResponse(
            kind=ResponseKind.TIMEOUT,
            raw=raw or "",
            message_de="Timeout – keine vollständige Antwort vom Adapter.",
            timed_out=True,
        )
    if raw is None or not str(raw).strip():
        return ParsedElmResponse(
            kind=ResponseKind.EMPTY,
            raw=raw or "",
            message_de="Leere Antwort – Status unbekannt (nicht als null gewertet).",
        )

    text = str(raw)
    upper = text.upper()
    lines = _normalize_lines(text)

    for needle, kind in _ELM_ERROR_MAP:
        if needle in upper and kind != ResponseKind.MALFORMED:
            # "?" nur wenn keine Hex-Payload
            if kind == ResponseKind.SEARCHING and "STOPPED" in upper:
                continue
            # Wenn Hex-Frames und zusätzlich SEARCHING-Zwischenstand: Frames bevorzugen
            has_hex = any(_bytes_from_hex_line(l) for l in lines)
            if kind == ResponseKind.SEARCHING and has_hex:
                break
            if kind in (
                ResponseKind.NO_DATA,
                ResponseKind.STOPPED,
                ResponseKind.UNABLE_TO_CONNECT,
                ResponseKind.BUS_ERROR,
                ResponseKind.CAN_ERROR,
            ):
                return ParsedElmResponse(
                    kind=kind,
                    raw=text,
                    message_de=_message_de(kind),
                )

    if "?" in upper and not any(_bytes_from_hex_line(l) for l in lines):
        return ParsedElmResponse(
            kind=ResponseKind.MALFORMED,
            raw=text,
            message_de="Adapter meldet unverständlichen Befehl (?).",
        )

    frames: list[EcuFrame] = []
    for line in lines:
        lu = line.upper()
        if any(n in lu for n, _ in _ELM_ERROR_MAP if n not in ("?", "SEARCHING", "BUS INIT")):
            continue
        if lu.startswith("AT") or lu == "OK" or "ELM" in lu:
            continue
        # ISO-TP Multiframe-Indikator (erste Nibble 1x): z. B. "10 14 49 02 01 …"
        data = _bytes_from_hex_line(line)
        if data is None:
            continue
        # PCI-Byte entfernen wenn Multiframe-First (0x10) oder Consecutive (0x2x)
        if data and (data[0] & 0xF0) == 0x10 and len(data) >= 2:
            # First frame: PCI + length nibble – Rest ist Payload
            data = data[1:]  # drop PCI; length ignored for MVP assemble
        elif data and (data[0] & 0xF0) == 0x20:
            data = data[1:]
        elif data and data[0] == 0x00 and len(data) >= 2:
            # Single-frame length prefix mancher ELM-Modi
            length = data[1] if data[0] == 0x00 else data[0] & 0x0F
            # Alternative: 00 XX als Padding – behalten wenn Service erkennbar
            if len(data) > 2 and data[2] in (0x41, 0x42, 0x43, 0x47, 0x49, 0x4A, 0x7F):
                data = data[2:]
            elif length and len(data) >= length + 1:
                data = data[1 : 1 + length]

        frame = _parse_frame_bytes(data)
        if frame:
            frames.append(frame)

    if not frames:
        if "SEARCHING" in upper:
            return ParsedElmResponse(
                kind=ResponseKind.SEARCHING,
                raw=text,
                message_de=_message_de(ResponseKind.SEARCHING),
            )
        return ParsedElmResponse(
            kind=ResponseKind.UNKNOWN,
            raw=text,
            message_de="Antwort nicht als OBD-Frame erkennbar – Status unbekannt.",
        )

    if any(f.is_negative for f in frames):
        return ParsedElmResponse(
            kind=ResponseKind.NEGATIVE,
            raw=text,
            frames=frames,
            message_de="Negative Antwort (7F) von ECU.",
        )

    return ParsedElmResponse(
        kind=ResponseKind.OK,
        raw=text,
        frames=frames,
        message_de="Antwort geparst." + (" Mehrere ECU-Antworten." if len({f.ecu_id for f in frames}) > 1 else ""),
    )


def group_frames_by_ecu(frames: Iterable[EcuFrame]) -> dict[str, list[EcuFrame]]:
    """Gruppiert Frames nach ECU; fehlende ID → 'unknown' (nicht null)."""
    out: dict[str, list[EcuFrame]] = {}
    for f in frames:
        key = f.ecu_id if f.ecu_id is not None else "unknown"
        out.setdefault(key, []).append(f)
    return out


def _message_de(kind: ResponseKind) -> str:
    return {
        ResponseKind.NO_DATA: "NO DATA – ECU hat keine Daten geliefert.",
        ResponseKind.TIMEOUT: "Timeout.",
        ResponseKind.SEARCHING: "Protokollsuche läuft (SEARCHING…).",
        ResponseKind.BUS_ERROR: "Bus-Fehler.",
        ResponseKind.CAN_ERROR: "CAN-Fehler.",
        ResponseKind.STOPPED: "Übertragung gestoppt.",
        ResponseKind.UNABLE_TO_CONNECT: "Keine Verbindung zum Fahrzeugprotokoll.",
        ResponseKind.NEGATIVE: "Negative ECU-Antwort.",
        ResponseKind.EMPTY: "Leere Antwort.",
        ResponseKind.MALFORMED: "Ungültige/fehlerhafte Antwort.",
        ResponseKind.UNKNOWN: "Unbekannter Antwortstatus.",
        ResponseKind.FRAGMENTED: "Fragmentierte Antwort unvollständig.",
        ResponseKind.OK: "OK",
    }.get(kind, "Unbekannt")
