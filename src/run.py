from config import MeshingConfig, SolverConfig
import argparse

def main():
    p = argparse.ArgumentParser(description="Automate CAD->mesh->solve for a generic wing in Fluent.")
    p.add_argument("--cad", type=str, required=True, help="Path to CAD (.pmdb/.fmd/.step/.iges)")

    cad_path = Path(args.cad).resolve()
    if not cad_path.exists():
        raise SystemExit(f"CAD file does not exist: {cad_path}")
    
    # Meshing config
    mcfg = MeshingConfig(cad_file=str(cad_path))

if __name__ == "__main__":
    main()