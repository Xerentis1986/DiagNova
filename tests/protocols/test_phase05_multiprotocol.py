"""Phase-05 Protokoll-/ISO-TP-/UDS-/ECU-Testvektoren – Simulator/Specs only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "diagnostic-protocols" / "src"))

from diagnova_protocols import (
    IsoTpFrameType,
    architecture_overview,
    build_ecu_inventory,
    capability_matrix,
    decode_nrc,
    ecu_overview_static,
    is_service_enabled,
    is_standard_obd_response,
    parse_elm_response,
    parse_isotp_pci,
    parse_negative_response,
    protocol_summary,
    reassemble_isotp,
    uds_catalog,
)
from diagnova_protocols.isotp import TEST_VECTORS, FlowStatus


def test_architecture_layers_separated():
    overview = architecture_overview()
    ids = {layer["id"] for layer in overview["layers"]}
    assert ids == {"transport", "protocol", "adapter", "vehicle_definition"}


def test_protocol_catalog_statuses():
    summary = protocol_summary()
    assert summary["count"] >= 10
    ids = {p["id"] for p in summary["protocols"]}
    assert "sae_j1979_obd" in ids
    assert "iso_14229_uds" in ids
    assert "iso_13400_doip" in ids
    assert "sae_j2534" in ids
    assert "sae_j1939" in ids
    doip = next(p for p in summary["protocols"] if p["id"] == "iso_13400_doip")
    assert doip["status"] == "documented_prep"
    j1939 = next(p for p in summary["protocols"] if p["id"] == "sae_j1939")
    assert j1939["status"] == "documented_prep"
    assert j1939["phase"] == 19
    rp1210 = next(p for p in summary["protocols"] if p["id"] == "rp1210")
    assert rp1210["status"] == "documented_prep"


def test_capability_matrix_elm_not_doip():
    matrix = capability_matrix()
    elm = next(a for a in matrix["adapters"] if a["adapter_id"] == "elm327-obd")
    assert elm["protocols"]["iso_13400_doip"] == "not_supported"
    assert elm["protocols"]["can_fd"] == "not_supported"
    assert elm["hardware_tested"] is False
    sim = next(a for a in matrix["adapters"] if a["adapter_id"] == "simulator")
    assert sim["protocols"]["sae_j1979_obd"] == "supported_simulated"


def test_isotp_test_vectors():
    for vec in TEST_VECTORS:
        frame = parse_isotp_pci(vec["bytes"])
        assert frame.frame_type == vec["expect_type"]
        if "expect_length" in vec:
            assert frame.total_length == vec["expect_length"]
        if "expect_flow" in vec:
            assert frame.flow_status == vec["expect_flow"]


def test_isotp_reassembly():
    ff = parse_isotp_pci([0x10, 0x0A, 0x49, 0x02, 0x01, 0x41, 0x42, 0x43])
    cf1 = parse_isotp_pci([0x21, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A])
    payload, status = reassemble_isotp([ff, cf1])
    assert status == "ok"
    assert payload is not None
    assert len(payload) == 10
    assert payload[:3] == bytes([0x49, 0x02, 0x01])


def test_uds_nrc_and_disabled_write():
    assert decode_nrc(0x11) == "serviceNotSupported"
    neg = parse_negative_response([0x7F, 0x22, 0x31])
    assert neg is not None
    assert neg.nrc_name == "requestOutOfRange"
    assert is_service_enabled(0x22) is True
    assert is_service_enabled(0x2E) is False
    assert is_service_enabled(0x27) is False
    catalog = uds_catalog()
    assert catalog["active_write_paths"] is False
    assert catalog["security_access_enabled"] is False


def test_standard_obd_addresses_only():
    assert is_standard_obd_response("7E8")
    assert is_standard_obd_response(0x7E9)
    assert not is_standard_obd_response(0x713)  # typische OEM – nicht als Standard akzeptieren
    overview = ecu_overview_static()
    assert overview["blind_scan_allowed"] is False
    abs_cat = next(c for c in overview["categories"] if c["id"] == "abs")
    assert abs_cat["availability"] == "unavailable_no_definition"


def test_multi_ecu_discovery_from_observed_frames_no_blind_scan():
    raw = "7E8 41 00 BE 1F A8 13\r\n7E9 41 00 88 18 80 00\r\n>"
    parsed = parse_elm_response(raw)
    inventory = build_ecu_inventory(parsed.frames, data_source="simulated", protocol_name="ISO 15765-4")
    assert inventory["blind_scan_used"] is False
    assert inventory["count"] == 2
    ids = {e["ecu_id"] for e in inventory["discovered_obd_ecus"]}
    assert "7E8" in ids
    assert "7E9" in ids
    assert any(u["id"] == "abs" for u in inventory["unavailable_categories"])
