"""
COSYN-30 -- Dimensionnement des EMMANCHEMENTS TELESCOPIQUES.

Trois organes coulissants : poutre principale (3 etages), tige de selle
(3 etages), colonne de direction (2 etages). Chaque liaison doit assurer :
  1. la transmission du moment flechissant sans matage des portees,
  2. la reprise de l'effort axial et du couple par adherence (expandeur),
  3. un jeu residuel nul en position deployee (sinon "flou" au guidon),
  4. le verrouillage en longueur, repetable et indexe.

Les moments sollicitants sont extraits du modele elements finis du cadre
(c02_cadre.py), enveloppe de tous les cas de charge.
"""

from __future__ import annotations
import json
import numpy as np

import c02_cadre as C
from joints import Telescope, tube_props, P_ADM_BEARING
from params import Geo as G, Loads as LD, MAT, CS

AL = MAT["AL7075T6"]

# liaisons : (nom, tube ext, tube int, recouvrement, element FEM porteur, bras de levier)
LIAISONS = [
    ("Poutre 1-2", "poutre1", "poutre2", C.OVERLAP["poutre"], "j_poutre12", 0.520),
    ("Poutre 2-3", "poutre2", "poutre3", C.OVERLAP["poutre"], "j_poutre23", 0.350),
    ("Selle 1-2", "tds1", "tds2", C.OVERLAP["tds"], "j_tds12", 0.300),
    ("Selle 2-3", "tds2", "tds3", C.OVERLAP["tds"], "j_tds23", 0.160),
    ("Direction 1-2", "col1", "col2", C.OVERLAP["col"], "j_col12", 0.215),
]


def envelope_efforts():
    """Enveloppe (M, V, N, T) dans chaque troncon de joint, tous cas confondus."""
    env = {}
    for case in C.load_cases():
        m, _ = C.run_case(case)
        for e in m.beams:
            if not e["label"].startswith("j_"):
                continue
            f = e["f_local"]
            M = max(np.hypot(f[4], f[5]), np.hypot(f[10], f[11]))
            V = np.hypot(f[1], f[2])
            N = abs(f[0])
            T = abs(f[3])
            cur = env.setdefault(e["label"], dict(M=0, V=0, N=0, T=0, cas=""))
            if M > cur["M"]:
                env[e["label"]] = dict(M=M, V=V, N=N, T=T, cas=case["nom"])
    return env


def retracted_lengths():
    """Longueurs deployee / repliee de chaque organe telescopique."""
    HB, HT = G.head_bottom(), G.head_top()
    out = {}
    L = np.linalg.norm(HB)
    out["poutre principale"] = dict(n=3, L=L, e=C.OVERLAP["poutre"])
    sm = G.seat_mast_len
    t_sd = (0.720 - sm * np.sin(G.seat_angle)) / np.sin(G.seat_angle)
    out["tige de selle"] = dict(n=3, L=t_sd, e=C.OVERLAP["tds"])
    t_bar = (G.bar_h - HT[2]) / G.steer_dir()[2]
    out["colonne direction"] = dict(n=2, L=t_bar, e=C.OVERLAP["col"])
    for k, v in out.items():
        n, L, e = v["n"], v["L"], v["e"]
        ell = (L + (n - 1) * e) / n          # longueur physique d'un etage
        v["etage_mm"] = ell * 1e3
        v["deploye_mm"] = L * 1e3
        v["replie_mm"] = ell * 1e3
        v["ratio"] = L / ell
    return out


def main():
    env = envelope_efforts()
    print("=" * 112)
    print("EMMANCHEMENTS TELESCOPIQUES -- verification")
    print("=" * 112)
    print(f"{'liaison':<14}{'M env.':>8}{'V env.':>8}{'recouv.':>9}{'e mini':>8}"
          f"{'p matage':>10}{'CS mat.':>9}{'jeu ->flou':>11}{'F expand.':>10}"
          f"{'C vis':>8}{'p exp.':>8}")
    print(f"{'':14}{'[N.m]':>8}{'[N]':>8}{'[mm]':>9}{'[mm]':>8}{'[MPa]':>10}"
          f"{'':9}{'[mm]':>11}{'[N]':>10}{'[N.m]':>8}{'[MPa]':>8}")
    print("-" * 112)
    rows = []
    for nom, ko, ki, ov, lab, lever in LIAISONS:
        eff = env.get(lab, dict(M=0, V=0, N=0, T=0))
        t = Telescope(nom, tube_props(*C.TUBES[ko][:2], C.TUBES[ko][2]),
                      tube_props(*C.TUBES[ki][:2], C.TUBES[ki][2]),
                      ov, clearance=60e-6, bearing_len=0.012)
        # effort axial a transmettre : effort normal enveloppe + marge de securite
        F_ax = max(eff["N"], 1500.0)
        T_tq = max(eff["T"], 25.0)
        r = t.report(eff["M"], eff["V"], F_ax, T_tq, lever, cone_deg=8.0)
        ok = r["marge_matage"] >= CS["contact"]
        print(f"{nom:<14}{eff['M']:8.1f}{eff['V']:8.0f}{ov*1e3:9.0f}"
              f"{r['e_min_mm']:8.0f}{r['p_matage_MPa']:10.1f}{r['marge_matage']:9.2f}"
              f"{r['flou_mm']:11.2f}{r['F_tirant_N']:10.0f}{r['C_vis_Nm']:8.1f}"
              f"{r['p_expandeur_MPa']:8.1f}{'' if ok else '   <-- NON'}")
        r.update(M=eff["M"], V=eff["V"], cas=eff.get("cas", ""))
        rows.append(r)
    print("-" * 112)
    print(f"pression de matage admissible retenue : {P_ADM_BEARING/1e6:.0f} MPa "
          "(Al 7075 anodise dur 50 um sur bague PA66-CF, marge exigee "
          f"{CS['contact']})")

    print("\nCourses telescopiques")
    print(f"{'organe':<20}{'etages':>8}{'deploye':>10}{'replie':>9}{'ratio':>8}")
    rl = retracted_lengths()
    for k, v in rl.items():
        print(f"{k:<20}{v['n']:8d}{v['deploye_mm']:9.0f}mm{v['replie_mm']:8.0f}mm"
              f"{v['ratio']:8.2f}")

    print("\nSequence de verrouillage (1 geste par liaison)")
    seq = [
        ("1", "Deployer la poutre jusqu'a l'index de butee (gorge usinee)"),
        ("2", "Rabattre le levier d'expandeur : le cone 8 deg dilate la douille "
              "fendue et annule le jeu"),
        ("3", "Idem colonne de direction, puis tige de selle"),
        ("4", "Le temoin rouge disparait quand le levier est en position sur-centree"),
    ]
    for a, b in seq:
        print(f"   {a}. {b}")

    with open("../out/telescopes.json", "w") as f:
        json.dump(dict(liaisons=rows, courses=rl), f, indent=1, default=float)


if __name__ == "__main__":
    main()
