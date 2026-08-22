"""
COSYN-30 -- TENUE EN FATIGUE sur spectre de service.

Le velo n'est pas sollicite par un cas unique mais par un spectre : pedalage
regulier, petits chocs de chaussee, gros chocs (trottoirs), plus les cycles de
DEPLOYEMENT (chaque montage-demontage est un cycle de contrainte pour les
emmanchements, les tenons de jante et le mecanisme de tension).

Methode : comptage par blocs + cumul lineaire de Miner sur la droite de Basquin
du materiau, corrigee de l'effet d'entaille, de l'etat de surface et de la
contrainte moyenne (Goodman).
"""
from __future__ import annotations
import json
import numpy as np

import c02_cadre as C
import c03_roue as R
from params import Geo as G, Loads as LD, MAT, CS, sigma_allow

AL = MAT["AL7075T6"]
DUREE_KM = 8000.0          # objectif de duree de vie
MONTAGES = 3000.0          # nombre de cycles montage/demontage vises


def spectre_roulage():
    """Blocs de service ramenes a DUREE_KM km.

    part      : fraction du kilometrage
    facteur   : multiple de la charge statique roue vue par la structure
    n_par_km  : nombre de cycles de ce type par kilometre
    """
    tours_par_km = 1000.0 / (np.pi * G.wheel_od)
    pedalees_par_km = 1000.0 / G.development()
    return [
        dict(nom="pedalage regulier (assis)", n_par_km=pedalees_par_km,
             facteur=1.00, source="pedalier"),
        dict(nom="pedalage en cote / demarrage", n_par_km=0.08 * pedalees_par_km,
             facteur=2.10, source="pedalier"),
        dict(nom="rotation de roue, chaussee lisse", n_par_km=tours_par_km,
             facteur=1.00, source="roue"),
        dict(nom="chaussee degradee (30 % du parcours)",
             n_par_km=0.30 * tours_par_km, facteur=1.60, source="roue"),
        dict(nom="joints de chaussee, pave", n_par_km=8.0, facteur=2.20,
             source="roue"),
        dict(nom="trottoir monte/descendu", n_par_km=0.6, facteur=3.20,
             source="roue"),
        dict(nom="nid de poule franc", n_par_km=0.05, facteur=4.20,
             source="roue"),
    ]


def miner(blocs, sigma_ref, kf, R_rapport=0.0, km=DUREE_KM):
    """Cumul de Miner. sigma_ref = contrainte pour facteur = 1."""
    D = 0.0
    lignes = []
    for b in blocs:
        sa = sigma_ref * b["facteur"]
        n = b["n_par_km"] * km
        # amplitude admissible a n cycles : on inverse la droite de Basquin
        Nf = _cycles_a_rupture(sa, kf, R_rapport)
        D += n / Nf
        lignes.append(dict(bloc=b["nom"], sigma_MPa=sa / 1e6, n=n, Nf=Nf,
                           dommage=n / Nf))
    return D, lignes


def _cycles_a_rupture(sa, kf, R_rapport):
    s1e3 = 0.9 * AL["Rm"]
    b = np.log(AL["sN"] / s1e3) / np.log(1e7 / 1e3)
    # correction entaille / surface / echelle / contrainte moyenne
    corr = 0.9 * 0.9 / kf
    if R_rapport > -1.0:
        sm_over_sa = (1 + R_rapport) / (1 - R_rapport)
        sa_eq = sa / max(1 - sm_over_sa * sa / AL["Rm"], 1e-3)
    else:
        sa_eq = sa
    sa_adm_1e3 = s1e3 * corr
    if sa_eq >= sa_adm_1e3:
        return 1e3
    N = 1e3 * (sa_eq / sa_adm_1e3) ** (1 / b)
    return min(N, 1e9)


def main():
    print("=" * 100)
    print(f"FATIGUE SUR SPECTRE -- objectif {DUREE_KM:.0f} km et "
          f"{MONTAGES:.0f} montages")
    print("=" * 100)

    # --- 1. cadre : contrainte de reference sous chargement statique unitaire
    cases = C.load_cases()
    m_stat, rows_stat = C.run_case(cases[0])          # F1 statique assis
    sigma_cadre = rows_stat[0]["sigma"]
    el_cadre = rows_stat[0]["el"]
    print(f"\nCADRE -- element le plus sollicite en service : {el_cadre}")
    print(f"  contrainte de reference (assis, 1 g) : {sigma_cadre/1e6:.0f} MPa")
    blocs_p = [b for b in spectre_roulage() if b["source"] == "pedalier"]
    D_cadre, lg = miner(blocs_p, sigma_cadre, kf=C.KF_JONCTION, R_rapport=0.0)
    print(f"{'bloc':<36}{'sigma_a':>10}{'cycles':>13}{'N rupture':>13}{'dommage':>11}")
    for l in lg:
        print(f"{l['bloc']:<36}{l['sigma_MPa']:9.0f}M{l['n']:13.3g}"
              f"{l['Nf']:13.3g}{l['dommage']:11.4f}")
    print(f"{'CUMUL DE MINER':<36}{'':10}{'':13}{'':13}{D_cadre:11.4f}")
    print(f"  -> duree de vie estimee : {DUREE_KM/max(D_cadre,1e-9):,.0f} km "
          f"(coefficient {1/max(D_cadre,1e-9):.1f} sur l'objectif)")

    # --- 2. jante : contrainte de reference roue arriere chargee
    W = LD.m_total() * LD.g
    xf, xr = G.front_axle()[0], G.rear_axle()[0]
    fr = (LD.cg_x - xf) / (xr - xf)
    Pr = W * fr
    ref, _ = R.envelope_over_phase("ref", n_phase=8, joint_eta_I=1.0, P_rad=Pr)
    sigma_jante = ref["sigma_locale_MPa"] * 1e6
    print(f"\nJANTE -- contrainte locale de reference (roue AR, 1 g) : "
          f"{sigma_jante/1e6:.0f} MPa")
    blocs_r = [b for b in spectre_roulage() if b["source"] == "roue"]
    D_jante, lg = miner(blocs_r, sigma_jante, kf=1.0, R_rapport=-0.6)
    print(f"{'bloc':<36}{'sigma_a':>10}{'cycles':>13}{'N rupture':>13}{'dommage':>11}")
    for l in lg:
        print(f"{l['bloc']:<36}{l['sigma_MPa']:9.0f}M{l['n']:13.3g}"
              f"{l['Nf']:13.3g}{l['dommage']:11.4f}")
    print(f"{'CUMUL DE MINER':<36}{'':10}{'':13}{'':13}{D_jante:11.4f}")
    print(f"  -> duree de vie estimee : {DUREE_KM/max(D_jante,1e-9):,.0f} km")

    # --- 3. rayons : variation de tension par tour de roue
    cas = R.solve_case("roulage AR", P_rad=Pr)
    cas.pop("model")
    A_sp = np.pi * G.spoke_d_mid ** 2 / 4
    s_max = cas["T_max"] / A_sp
    s_min = cas["T_min"] / A_sp
    sa = (s_max - s_min) / 2
    sm = (s_max + s_min) / 2
    Rr = s_min / s_max
    inox = MAT["INOX_RAYON"]
    s1e3 = 0.9 * inox["Rm"]
    b = np.log(inox["sN"] / s1e3) / np.log(1e7 / 1e3)
    kf_rayon = 2.2       # coude / filetage lamine
    sa_adm = s1e3 * 0.85 * 0.9 / kf_rayon
    sa_eq = sa / max(1 - (sm / inox["Rm"]), 1e-3)
    N_rayon = 1e3 * (sa_eq / sa_adm) ** (1 / b)
    tours = 1000.0 / (np.pi * G.wheel_od) * DUREE_KM
    print(f"\nRAYONS -- tension {cas['T_min']:.0f} a {cas['T_max']:.0f} N "
          f"par tour de roue (R = {Rr:.2f})")
    print(f"  amplitude {sa/1e6:.0f} MPa, moyenne {sm/1e6:.0f} MPa, "
          f"Kf = {kf_rayon}")
    print(f"  N a rupture = {N_rayon:.3g} cycles ; besoin {tours:.3g} cycles "
          f"-> coefficient {N_rayon/tours:.1f}")

    # --- 4. cycles de montage/demontage
    print(f"\nCYCLES DE MONTAGE ({MONTAGES:.0f} deploiements = "
          f"~2 par jour pendant 4 ans)")
    montage = [
        ("Tenon conique de jante", "matage Al/Al anodise dur", 25e6, 1.0,
         "usure d'emmanchement : jeu <0.05 mm apres 3000 cycles (essai a mener)"),
        ("Expandeur conique de poutre", "traction du tirant M6", 2.6e3, 1.0,
         "acier 42CrMo4, sigma_a = 92 MPa -> illimite"),
        ("Came de tension de moyeu", "contact hertzien came/poussoir", 1.1e9, 1.0,
         "acier cemente 58 HRC, p_max = 1100 MPa -> 1e6 cycles admissibles"),
        ("Cordon captif aramide", "flexion alternee r = 25 mm", 1.0, 1.0,
         "remplacement preventif tous les 2000 cycles (piece d'usure declaree)"),
    ]
    for nom, mode, val, _, note in montage:
        print(f"   {nom:<30}{mode:<34}{note}")

    out = dict(duree_km=DUREE_KM, dommage_cadre=D_cadre, dommage_jante=D_jante,
               vie_cadre_km=DUREE_KM / max(D_cadre, 1e-9),
               vie_jante_km=DUREE_KM / max(D_jante, 1e-9),
               rayon_N=N_rayon, rayon_besoin=tours,
               sigma_cadre_MPa=sigma_cadre / 1e6,
               sigma_jante_MPa=sigma_jante / 1e6)
    with open("../out/fatigue.json", "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
