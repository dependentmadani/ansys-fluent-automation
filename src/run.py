from config import MeshingConfig, SolverConfig
from utils import speed_of_sound, u_inf_from_mach, first_layer_height_from_yplus
from pathlib import Path
import argparse

GREEN = '\033[32m'
RESET = '\033[0m'

def parse_aoa_list(s: str):
    """
    Accepts comma list: "0,2,4,6" or a range "start:step:stop" e.g "-4:2:10"
    """
    if ":" in s:
        a,b,c = map(float, s.split(":"))
        out = []
        x = a
        while (b > 0 and x <= c) or (b < 0 and x >= c):
            out.append(x)
            x += b
        return out
    return [float(x.strip()) for x in s.split(",") if x.strip()]

def main():
    p = argparse.ArgumentParser(description="Automate CAD->mesh->solve for a generic wing in Fluent.")
    p.add_argument("--cad", type=str, required=True, help="Path to CAD (.pmdb/.fmd/.step/.iges)")
    p.add_argument("--mach", type=float, default=0.2, help="Mach number")
    p.add_argument("--tinf", type=float, default=288.15, help="Free-stream temperature [K]")
    p.add_argument("--pop", type=float, default=101325.0, help="Free-stream pressure [Pa]")
    p.add_argument("--ref-length", type=float, default=0.30, help="Reference length [m]")
    p.add_argument("--yplus", type=float, default=None, help="Target y+ for boundary layer")
    args = p.parse_args()

    cad_path = Path(args.cad).resolve()
    if not cad_path.exists():
        raise SystemExit(f"CAD file does not exist: {cad_path}")
    
    # Meshing config
    mcfg = MeshingConfig(cad_file=str(cad_path))

    if args.yplus is not None:
        U_inf = u_inf_from_mach(args.mach, args.tinf)
        y1, nu, u_tau = first_layer_height_from_yplus(args.yplus, U_inf, args.ref_length, args.tinf, args.pop)
        mcfg.first_layer_height = y1
        print(f"{GREEN}[info]{RESET} Target y+={args.yplus:.2f} -> FirstLayerHeight≈{y1:.3e} m  (nu={nu:.3e} m^2/s, u_tau={u_tau:.3f} m/s)")

if __name__ == "__main__":
    main()