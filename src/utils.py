from math import sqrt
from typing import Tuple

R_AIR = 287.04
GAMMA = 1.4

def speed_of_sound(T: float, gamma: float = GAMMA, R: float = R_AIR) -> float:
    return sqrt(gamma * R * T)

def u_inf_from_mach(M: float, T: float) -> float:
    return M * speed_of_sound(T)

def sutherland_mu(T: float, mu_ref=1.716e-5, T_ref=273.11, S=110.56) -> float:
    """
    Sutherland three-coefficient law (SI)
    """
    return mu_ref * ((T / T_ref ) ** 1.5) * (T_ref + S)/(T + S)

def rho_from_pT(p: float, T: float, R: float = R_AIR) -> float:
    return p / (R * T)

def flat_plate_cf_turbulent(Re_L: float) -> float:
    """
    Simple empirical Cf for turbulent flat plate, zero pressure gradient
    Prandtl=SChilichting: Cf = 0.026 / Re^(1/7) (calid over a broad range)
    """
    if Re_L <= 0:
        return 0.003
    return 0.026 / (Re_L ** (1.0 / 7.0))

def first_layer_height_from_yplus(
    y_plus: float, U_inf: float, L_ref: float, T:float, p:float
) -> Tuple[float, float, float]:
    """
    Estimate first_layer height (m) from target y+ using Cf-based skin friction velocity.
    Returns (y1_m, nu, u_tau).
    """
    mu = sutherland_mu(T)
    rho = rho_from_pT(p, T)
    nu = mu / rho
    Re_L = rho * U_inf * L_ref / mu
    Cf = flat_plate_cf_turbulent(Re_L)
    u_tau = sqrt(0.5 * Cf) * U_inf
    if u_tau < 1e-12:
        raise ValueError("u_tau computed ~0; check inputs.")
    y1 = y_plus * nu / u_tau
    return y1, nu, u_tau