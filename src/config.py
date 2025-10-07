from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class MeshingConfig:
    cad_file: str = "./wing.pmdb"      # .pmdb/.fmd/.step/.iges
    length_unit: str = "m"             # "m", "mm", "in", etc.

    # Workflow selection
    workflow: str = "fault-tolerant"   # "fault-tolerant" or "watertight"
    create_enclosure: bool = True
    enclosure_name: str = "farfield"

    # Enclosure ratios (for bounding box about geometry extents)
    bbox_ratio: Dict[str, float] = field(default_factory=lambda: dict(
        x_minus=10.0, x_plus=20.0, y_minus=10.0, y_plus=10.0, z_minus=10.0, z_plus=10.0
    ))

    # Surface mesh sizing
    surf_min: float = 0.002  # m
    surf_max: float = 0.05   # m

    # Boundary layers
    bl_n_layers: int = 12
    bl_growth: float = 1.2
    first_layer_height: Optional[float] = None  # set if you compute from target y+

    # Volume mesh (poly-hexcore recommended for external aero)
    volume_fill: str = "poly-hexcore"
    hex_max_cell_length: float = 0.25  # m

    # Fluent launch
    precision: str = "double"
    processors: int = 4


@dataclass
class SolverConfig:
    # Zones
    farfield_name: str = "farfield"
    wing_wall_zones: List[str] = field(default_factory=lambda: ["wing", "wing-tip"])

    # Free-stream / gas model
    mach: float = 0.20
    t_inf: float = 288.15          # K
    p_op: float = 101325.0         # Pa (operating pressure)

    # Reference values for coefficients
    ref_area: float = 0.10         # m^2
    ref_length: float = 0.30       # m

    # Sweep and iterations
    aoa_deg: List[float] = field(default_factory=lambda: [0, 2, 4, 6, 8, 10])
    n_iters: int = 250

    # Fluent launch
    precision: str = "double"
    processors: int = 4
