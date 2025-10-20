from __future__ import annotations
import argparse
from pathlib import Path
from datetime import datetime

from .config import MeshingConfig, SolverConfig
from .utils import first_layer_height_from_yplus, u_inf_from_mach
from .logging_utils import get_logger

log = get_logger()

def parse_aoa_list(s: str):
    """
    Accepts comma list: "0,2,4,6" or a range "start:step:stop" e.g. "-4:2:10".
    """
    if ":" in s:
        a, b, c = map(float, s.split(":"))
        out = []
        x = a
        # inclusive range with the given step
        if b == 0:
            return [a]
        while (b > 0 and x <= c) or (b < 0 and x >= c):
            out.append(round(x, 6))
            x += b
        return out
    return [float(x.strip()) for x in s.split(",") if x.strip()]

def main():
    p = argparse.ArgumentParser(description="Automate CAD→mesh→solve for a generic wing in Fluent.")
    p.add_argument("--cad", type=str, required=True, help="Path to CAD (.pmdb/.fmd/.step/.iges)")
    p.add_argument("--workflow", type=str, default="fault-tolerant",
                   choices=["fault-tolerant", "watertight"], help="Meshing workflow to use")
    p.add_argument("--farfield", type=str, default="farfield", help="Farfield zone name")
    p.add_argument("--wing-zones", type=str, default="wing,wing-tip", help="Comma-separated wing wall zone names")
    p.add_argument("--unit", type=str, default="m", help="Length unit for CAD import (m/mm/in/...)")
    p.add_argument("--surf-min", type=float, default=0.002, help="Surface min size [m]")
    p.add_argument("--surf-max", type=float, default=0.05, help="Surface max size [m]")
    p.add_argument("--hex-max", type=float, default=0.25, help="Hexcore max cell length [m]")
    p.add_argument("--bl-layers", type=int, default=12, help="Number of boundary layers")
    p.add_argument("--bl-growth", type=float, default=1.2, help="Boundary-layer growth rate")
    p.add_argument("--yplus", type=float, default=None, help="Target y+ (optional; computes FirstLayerHeight)")
    p.add_argument("--aoa", type=str, default="0,2,4,6,8,10", help='AoA list "0,2,4" or range "start:step:stop"')
    p.add_argument("--mach", type=float, default=0.20, help="Free-stream Mach")
    p.add_argument("--tinf", type=float, default=288.15, help="Free-stream temperature [K]")
    p.add_argument("--pop", type=float, default=101325.0, help="Operating pressure [Pa]")
    p.add_argument("--ref-area", type=float, default=0.10, help="Reference area [m^2]")
    p.add_argument("--ref-length", type=float, default=0.30, help="Reference length [m]")
    p.add_argument("--iters", type=int, default=250, help="Iterations per AoA")
    p.add_argument("--outdir", type=str, default="runs", help="Directory to store outputs")
    p.add_argument("--save-per-aoa", action="store_true", help="Write case/data after each AoA")
    p.add_argument("--dry-run", action="store_true", help="Do not launch Fluent; just validate and print plan.")
    args = p.parse_args()

    cad_path = Path(args.cad).resolve()
    if not cad_path.exists():
        raise SystemExit(f"CAD file not found: {cad_path}")

    aoa_list = parse_aoa_list(args.aoa)
    run_dir = Path(args.outdir) / datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir/"manifest.txt").write_text(str(vars(args)))

    # Meshing config
    mcfg = MeshingConfig(
        cad_file=str(cad_path),
        length_unit=args.unit,
        workflow=args.workflow,
        create_enclosure=True if args.workflow == "fault-tolerant" else False,
        enclosure_name=args.farfield,
        surf_min=args.surf_min,
        surf_max=args.surf_max,
        bl_n_layers=args.bl_layers,
        bl_growth=args.bl_growth,
        volume_fill="poly-hexcore",
        hex_max_cell_length=args.hex_max,
    )

    # Optional first-layer height from y+
    if args.yplus is not None:
        U_inf = u_inf_from_mach(args.mach, args.tinf)
        y1, nu, u_tau = first_layer_height_from_yplus(args.yplus, U_inf, args.ref_length, args.tinf, args.pop)
        mcfg.first_layer_height = y1
        print(f"[info] Target y+={args.yplus:.2f} → FirstLayerHeight≈{y1:.3e} m  (nu={nu:.3e} m^2/s, u_tau={u_tau:.3f} m/s)")

    # Solver config
    scfg = SolverConfig(
        farfield_name=args.farfield,
        wing_wall_zones=[z.strip() for z in args.wing_zones.split(",") if z.strip()],
        mach=args.mach,
        t_inf=args.tinf,
        p_op=args.pop,
        ref_area=args.ref_area,
        ref_length=args.ref_length,
        aoa_deg=aoa_list,
        n_iters=args.iters,
    )

    if args.dry_run:
        print("[dry-run] Meshing workflow:", mcfg.workflow)
        print("[dry-run] CAD:", mcfg.cad_file)
        print("[dry-run] Surface sizes:", mcfg.surf_min, "→", mcfg.surf_max)
        print("[dry-run] BL layers:", mcfg.bl_n_layers, "growth:", mcfg.bl_growth,
              "first-layer-height:", mcfg.first_layer_height)
        print("[dry-run] Hexcore max cell length:", mcfg.hex_max_cell_length)
        print("[dry-run] Farfield name:", scfg.farfield_name)
        print("[dry-run] Wing walls:", ", ".join(scfg.wing_wall_zones))
        print("[dry-run] AoA list:", aoa_list)
        print("[dry-run] Mach/T∞/Pₒₚ:", scfg.mach, scfg.t_inf, scfg.p_op)
        print("[dry-run] Output directory:", run_dir)
        return

    log.info("Lanching meshing workflow: %s", mcfg.workflow)
    # Import heavy modules only if not dry-run
    from .meshing import build_mesh
    from .solver import solve_from_mesher_and_sweep

    meshing_session = build_mesh(mcfg)
    solve_from_mesher_and_sweep(meshing_session, scfg)

    log.info("Completed meshing workflow: %s", mcfg.workflow)

if __name__ == "__main__":
    main()
