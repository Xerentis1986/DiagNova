"""DiagNova Diagnoseprotokolle.

Schichten: Transport (extern) / Protokoll / Adapter-Capabilities / Fahrzeugdefinition.
OBD-II J1979 Basis (Phase 04) + Multiprotokoll-Grundlagen (Phase 05).
Keine herstellerspezifischen Geheimprotokolle, keine erfundenen OEM-Adressen.
"""

from .capability_matrix import adapter_capabilities, capability_matrix
from .dtc import DTC_MODE_STATUS, decode_dtc, format_dtc, parse_dtc_bytes, parse_mode_dtc_response
from .ecu_definition import ecu_overview_static, vehicle_definition_template
from .elm_response import (
    EcuFrame,
    ParsedElmResponse,
    ResponseKind,
    group_frames_by_ecu,
    parse_elm_response,
)
from .freeze_frame import decode_freeze_frame
from .isotp import IsoTpFrameType, parse_isotp_pci, reassemble_isotp
from .layers import ArchitectureLayer, architecture_overview
from .multi_ecu import build_ecu_inventory, discover_ecus_from_frames
from .obd_addresses import (
    FUNCTIONAL_REQUEST_11BIT,
    STANDARD_OBD_SLOTS,
    is_standard_obd_response,
    normalize_ecu_id,
    slot_for_response,
    standard_address_catalog,
)
from .pid_support import merge_supported_pids, parse_pid_bitmap
from .pids import PID_DEFINITIONS, PidDefinition, decode_pid, scale_pid_a_b
from .protocol_catalog import list_protocols, protocol_by_id, protocol_summary
from .readiness import ReadinessStatus, decode_readiness, readiness_as_simple_bool_map
from .uds import decode_nrc, is_service_enabled, parse_negative_response, uds_catalog
from .vin import decode_vin_bytes, decode_vin_from_mode09_frames

__all__ = [
    "ArchitectureLayer",
    "DTC_MODE_STATUS",
    "EcuFrame",
    "FUNCTIONAL_REQUEST_11BIT",
    "IsoTpFrameType",
    "PID_DEFINITIONS",
    "ParsedElmResponse",
    "PidDefinition",
    "ReadinessStatus",
    "ResponseKind",
    "STANDARD_OBD_SLOTS",
    "adapter_capabilities",
    "architecture_overview",
    "build_ecu_inventory",
    "capability_matrix",
    "decode_dtc",
    "decode_freeze_frame",
    "decode_nrc",
    "decode_pid",
    "decode_readiness",
    "decode_vin_bytes",
    "decode_vin_from_mode09_frames",
    "discover_ecus_from_frames",
    "ecu_overview_static",
    "format_dtc",
    "group_frames_by_ecu",
    "is_service_enabled",
    "is_standard_obd_response",
    "list_protocols",
    "merge_supported_pids",
    "normalize_ecu_id",
    "parse_dtc_bytes",
    "parse_elm_response",
    "parse_isotp_pci",
    "parse_mode_dtc_response",
    "parse_negative_response",
    "parse_pid_bitmap",
    "protocol_by_id",
    "protocol_summary",
    "readiness_as_simple_bool_map",
    "reassemble_isotp",
    "scale_pid_a_b",
    "slot_for_response",
    "standard_address_catalog",
    "uds_catalog",
    "vehicle_definition_template",
]
