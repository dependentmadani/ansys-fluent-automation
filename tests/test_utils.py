import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils import speed_of_sound, first_layer_height_from_yplus

def test_speed_of_sound_std_air():
    a = speed_of_sound(288.15)  # ISA sea-level temp
    assert 330 < a < 350  # ~340.3 m/s

def test_first_layer_height_reasonable_range():
    # y+=1, M=0.2 at 288.15 K, 1 atm, L_ref=0.3 m
    from src.utils import u_inf_from_mach
    U = u_inf_from_mach(0.2, 288.15)
    y1, nu, u_tau = first_layer_height_from_yplus(1.0, U, 0.30, 288.15, 101325.0)
    assert 1e-6 < y1 < 1e-4  # ~5e-6 m is typical here
    assert nu > 0
    assert u_tau > 0
