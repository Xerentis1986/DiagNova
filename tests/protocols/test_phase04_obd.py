"""Phase-04 Parser-Testvektoren – keine Hardware, keine erfundenen Live-Ergebnisse."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "diagnostic-protocols" / "src"))

from diagnova_protocols import (
    ResponseKind,
    decode_freeze_frame,
    decode_pid,
    decode_readiness,
    decode_vin_from_mode09_frames,
    group_frames_by_ecu,
    parse_elm_response,
    parse_mode_dtc_response,
    parse_pid_bitmap,
)


def test_multi_ecu_pid_bitmap():
    raw = "7E8 41 00 BE 1F A8 13\r\n7E9 41 00 88 18 80 00\r\n>"
    parsed = parse_elm_response(raw)
    assert parsed.kind == ResponseKind.OK
    assert parsed.multi_ecu
    by = group_frames_by_ecu(parsed.frames)
    assert "07E8" in by or "7E8" in by or any(k != "unknown" for k in by)
    frame = parsed.frames[0]
    assert frame.service == 0x41
    assert frame.pid_or_info == 0x00
    pids = parse_pid_bitmap(0x00, list(frame.data))
    assert 0x0C in pids
    assert 0x20 in pids


def test_no_data_timeout_negative():
    assert parse_elm_response("NO DATA\r>").kind == ResponseKind.NO_DATA
    assert parse_elm_response(None, timed_out=True).kind == ResponseKind.TIMEOUT
    neg = parse_elm_response("7E8 7F 01 11\r>")
    assert neg.kind == ResponseKind.NEGATIVE
    assert neg.frames[0].is_negative


def test_empty_not_invented_null():
    empty = parse_elm_response("   ")
    assert empty.kind == ResponseKind.EMPTY
    assert "unbekannt" in empty.message_de.lower() or "Leere" in empty.message_de


def test_dtc_modes_permanent_not_clearable():
    stored = parse_mode_dtc_response(0x43, [0x02, 0x03, 0x01, 0x01, 0x71], ecu_id="07E8")
    assert {d["code"] for d in stored} == {"P0301", "P0171"}
    assert all(d["clearable"] for d in stored)

    permanent = parse_mode_dtc_response(0x4A, [0x01, 0x04, 0x20], ecu_id="07E8")
    assert permanent[0]["code"] == "P0420"
    assert permanent[0]["status"] == "permanent"
    assert permanent[0]["clearable"] is False


def test_readiness_and_live_pid():
    rdy = decode_readiness([0x81, 0x07, 0x65, 0x04])
    assert rdy.mil_on is True
    assert rdy.dtc_count == 1
    assert "misfire" in rdy.monitors
    assert rdy.monitors["misfire"]["available"] is True

    rpm = decode_pid(0x0C, [0x1F, 0x40])
    assert rpm["value"] == 2000.0


def test_freeze_frame_and_vin():
    ff = decode_freeze_frame([0x0C, 0x1F, 0x40, 0x0D, 0x32], dtc_high=0x03, dtc_low=0x01)
    assert ff["dtc"] == "P0301"
    assert any(r["name"] == "rpm" for r in ff["readings"])

    vin_bytes = [0x01] + [ord(c) for c in "WVWZZZ1JZXW000001"]
    vin = decode_vin_from_mode09_frames([vin_bytes])
    assert vin["status"] == "ok"
    assert vin["vin"] == "WVWZZZ1JZXW000001"

    missing = decode_vin_from_mode09_frames([[0x00, 0x00]])
    assert missing["status"] == "unavailable"
    assert missing["vin"] is None
