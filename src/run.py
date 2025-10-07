from config import MeshingConfig, SolverConfig
from pathlib import Path
import argparse

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
    args = p.parse_args()

    cad_path = Path(args.cad).resolve()
    if not cad_path.exists():
        raise SystemExit(f"CAD file does not exist: {cad_path}")
    
    # Meshing config
    mcfg = MeshingConfig(cad_file=str(cad_path))

if __name__ == "__main__":
    main()