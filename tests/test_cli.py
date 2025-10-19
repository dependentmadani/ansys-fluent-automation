import sys
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.run import parse_aoa_list

def test_parse_aoa_list_variants():
    assert parse_aoa_list("0,2,4,6") == [0.0, 2.0, 4.0, 6.0]
    assert parse_aoa_list("-4:2:2") == [-4.0, -2.0, 0.0, 2.0]
    assert parse_aoa_list("5:0:9") == [5.0]  # step = 0 -> single value

def test_dry_run_cli(tmp_path: Path):
    dummy_cad = tmp_path / "dummy.step"
    dummy_cad.write_text("solid-dummy")
    cmd = [
        sys.executable, "-m", "src.run",
        "--cad", str(dummy_cad),
        "--workflow", "fault-tolerant",
        "--dry-run",
        "--yplus", "1.0",
        "--mach", "0.2",
        "--tinf", "288.15",
        "--pop", "101325",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "[dry-run]" in proc.stdout
    assert "Target y+" in proc.stdout
