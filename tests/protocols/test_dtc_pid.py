import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "diagnostic-protocols" / "src"))

from diagnova_protocols import decode_dtc, decode_pid, parse_dtc_bytes, scale_pid_a_b


def test_decode_dtc_p0301():
    # P0301 classic encoding: 0x03 0x01
    assert decode_dtc(0x03, 0x01) == "P0301"


def test_parse_dtc_bytes_skips_empty():
    codes = parse_dtc_bytes([0x03, 0x01, 0x00, 0x00, 0x01, 0x71])
    assert codes == ["P0301", "P0171"]


def test_rpm_scaling():
    # 0x0C: ((A*256)+B)/4 → 2000 rpm => A=0x1F B=0x40
    assert scale_pid_a_b(0x1F, 0x40, pid=0x0C) == 2000.0


def test_coolant_scaling():
    assert scale_pid_a_b(0x64, pid=0x05) == 60.0  # 100-40


def test_decode_pid_structure():
    result = decode_pid(0x0D, [50])
    assert result["name"] == "speed"
    assert result["value"] == 50
    assert result["unit"] == "km/h"
