from __future__ import annotations
import os
import csv
from math import radians, sin, cos
from typing import List
from .config import SolverConfig
from .utils import u_inf_from_mach, rho_from_pT

def _setup_physics(solver, cfg: SolverConfig):
    visc = solver.setup.models.viscous
    visc.model = "k-omega"
    visc.k_omega_model = "sst"

    energy = solver.setup.models.energy
    energy.enabled = True

    air = solver.setup.materials.fluid["air"]
    air.density.option = "ideal-gas"
    air.viscosity.option = "sutherland"
    air.viscosity.sutherland.option = "three-coefficient-method"
    air.viscosity.sutherland.reference_viscosity = 1.716e-5
    air.viscosity.sutherland.reference_temperature = 273.11
    air.viscosity.sutherland.effective_temperature = 110.56

    solver.setup.general.operating_conditions.operating_pressure = cfg.p_op

def _setup_farfield(solver, cfg: SolverConfig):
    pff = solver.setup.boundary_conditions.pressure_far_field[cfg.farfield_name]
    pff.momentum.gauge_pressure = 0.0
    pff.thermal.temperature = cfg.t_inf
    pff.momentum.mach_number = cfg.mach
    return pff

def _set_reference_values(solver, cfg: SolverConfig, U_inf: float):
    ref = solver.setup.reference_values
    ref.area = cfg.ref_area
    ref.length = cfg.ref_length
    ref.velocity = U_inf

def _force_on_walls(solver, walls: List[str]):
    # Lazy import only when needed
    from ansys.fluent.core.solver.function import reduction

    valid = [z for z in walls if z in solver.setup.boundary_conditions.wall.get_object_names()]
    if not valid:
        raise RuntimeError("No valid wing wall zones found in the case.")
    wall_objs = [solver.setup.boundary_conditions.wall[z] for z in valid]
    Fx, Fy, Fz = reduction.force(locations=wall_objs, ctxt=solver)
    return Fx, Fy, Fz

def solve_from_mesher_and_sweep(meshing_session, cfg: SolverConfig, csv_name: str = "wing_aoa_results.csv"):
    solver = meshing_session.switch_to_solver()
    solver.mesh.check()

    _setup_physics(solver, cfg)
    pff = _setup_farfield(solver, cfg)

    U_inf = u_inf_from_mach(cfg.mach, cfg.t_inf)
    rho_inf = rho_from_pT(cfg.p_op, cfg.t_inf)
    q_inf = 0.5 * rho_inf * U_inf ** 2

    _set_reference_values(solver, cfg, U_inf)

    out_path = os.path.abspath(csv_name)
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["AoA_deg", "Fx_N", "Fy_N", "Fz_N", "Lift_N", "Drag_N", "CL", "CD"])

        for aoa_deg in cfg.aoa_deg:
            a = radians(aoa_deg)
            pff.momentum.flow_direction[0] = cos(a)  # x
            pff.momentum.flow_direction[2] = sin(a)  # z

            solver.solution.initialization.hybrid_initialize()
            solver.solution.run_calculation.iterate(number_of_iterations=cfg.n_iters)

            Fx, Fy, Fz = _force_on_walls(solver, cfg.wing_wall_zones)

            Drag = -Fx
            Lift = Fz
            CL = Lift / (q_inf * cfg.ref_area)
            CD = Drag / (q_inf * cfg.ref_area)

            writer.writerow([aoa_deg, Fx, Fy, Fz, Lift, Drag, CL, CD])

    solver.file.write_case_data(file_name="wing_external.cas.h5")
    return out_path
