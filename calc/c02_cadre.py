"""
COSYN-30 -- Etude structurelle du CADRE (modele poutres 3D complet).

Le cadre est un monopoutre telescopique 3 etages entre le boitier de pedalier
et le tube de direction, complete par :
  * un triangle arriere rigide (bases + haubans) qui n'est JAMAIS demonte :
    il porte le pedalier, la transmission et le disque arriere, donc la boucle
    de chaine reste fermee en permanence ;
  * une tige de selle telescopique 3 etages ;
  * une colonne de direction telescopique 3 etages.

Les emmanchements telescopiques sont modelises par des troncons courts de
rigidite EI reduite (module joints.py) : c'est la ou se joue le "flou" ressenti
au guidon, principal risque percu sur un velo pliant tres compact.
"""

from __future__ import annotations
import json
import numpy as np

from fem import Model, Section
from params import Geo as G, Loads as LD, MAT, CS, sigma_allow
from joints import Telescope, tube_props, ETA_JOINT

AL = MAT["AL7075T6"]
TI = MAT["TI3AL25V"]

# --------------------------------------------------------------------------
# Sections tubulaires (od, epaisseur, materiau)
# --------------------------------------------------------------------------
TUBES = dict(
    poutre1=(0.0460, 0.0022, AL),      # poutre principale, etage BdP
    poutre2=(0.0410, 0.0022, AL),
    poutre3=(0.0360, 0.0020, AL),
    base=(0.0380, 0.0026, AL),         # bras arriere monobranche
    hauban=(0.0260, 0.0020, AL),       # hauban arriere monobranche
    mat_selle=(0.0420, 0.0026, AL),    # mat de selle fixe
    tds1=(0.0318, 0.0018, AL),         # tige de selle etage 1
    tds2=(0.0272, 0.0018, AL),
    tds3=(0.0226, 0.0016, AL),
    tube_dir=(0.0460, 0.0025, AL),     # tube de direction
    col1=(0.0340, 0.0024, AL),         # colonne de direction : tube fixe (pivot)
    col2=(0.0290, 0.0024, AL),         # colonne de direction : tube coulissant
    fourreau=(0.0460, 0.0032, AL),     # fourche monobras
    cintre=(0.0254, 0.0020, AL),       # cintre (repliable en 2 demi-cintres)
    manivelle=(0.0240, 0.0035, AL),
    axe=(0.0150, 0.0060, MAT["ACIER_42CD4"]),
)
SEC = {k: Section.tube(k, *v) for k, v in TUBES.items()}

# joints telescopiques : longueur de recouvrement retenue
OVERLAP = dict(poutre=0.058, tds=0.052, col=0.058)


def joint_section(name, outer_key, inner_key, eta=ETA_JOINT):
    """Section fictive donnant EI = eta*(EI_ext + EI_int) sur le recouvrement."""
    o, i = SEC[outer_key], SEC[inner_key]
    EI = eta * (AL["E"] * o.Iy + AL["E"] * i.Iy)
    GJ = eta * (AL["G"] * o.J + AL["G"] * i.J)
    s = Section(name, o.A + i.A, EI / AL["E"], EI / AL["E"], GJ / AL["G"],
                o.ymax, o.zmax, AL["rho"], AL)
    # La section fictive ne sert qu'a la RIGIDITE. Pour la CONTRAINTE reelle,
    # le moment se repartit entre les deux tubes au prorata de leur inertie :
    # sigma_ext = M * r_ext / (I_ext + I_int).  On memorise le module reel.
    s.Z_real = (o.Iy + i.Iy) / o.zmax
    s.J_real = o.J + i.J
    return s


SEC["j_poutre12"] = joint_section("j_poutre12", "poutre1", "poutre2")
SEC["j_poutre23"] = joint_section("j_poutre23", "poutre2", "poutre3")
SEC["j_tds12"] = joint_section("j_tds12", "tds1", "tds2")
SEC["j_tds23"] = joint_section("j_tds23", "tds2", "tds3")
SEC["j_col12"] = joint_section("j_col12", "col1", "col2")
SEC["rigide"] = Section.tube("rigide", 0.060, 0.010, MAT["ACIER_42CD4"])


def lerp(a, b, t):
    return a + (b - a) * t


def build_frame(eta=ETA_JOINT, saddle_h=None, release=(), extra_fix=()):
    saddle_h = saddle_h or 0.720
    m = Model()
    HB, HT = G.head_bottom(), G.head_top()
    FA, RA = G.front_axle(), G.rear_axle()
    n = m.node

    # --- pedalier et triangle arriere ---------------------------------
    n("BB", 0, 0, 0)
    n("BBL", 0, 0.036, 0)
    n("DL", RA[0], 0.062, RA[2])
    n("FAR", RA[0], 0, RA[2])
    sm = G.seat_mast_len * np.array([-np.cos(G.seat_angle), 0, np.sin(G.seat_angle)])
    n("SM", *sm)
    # bras arriere MONOBRANCHE (cote gauche) : la roue se monte sur un
    # tourillon central, un seul ecrou, aucun axe traversant a enfiler.
    m.beam("BB", "BBL", SEC["rigide"])
    m.beam("BBL", "DL", SEC["base"])
    m.beam("DL", "SM", SEC["hauban"])
    m.beam("DL", "FAR", SEC["rigide"])          # tourillon de roue AR
    m.beam("BB", "SM", SEC["mat_selle"])

    # --- poutre principale telescopique BdP -> tube de direction -------
    P0, P3 = np.zeros(3), HB
    L = np.linalg.norm(P3 - P0)
    ov = OVERLAP["poutre"]
    # 3 etages separes par 2 troncons de joint
    lseg = (L - 2 * ov) / 3
    s = [0.0, lseg, lseg + ov, 2 * lseg + ov, 2 * lseg + 2 * ov, L]
    names = ["BB", "PA", "PB", "PC", "PD", "HB"]
    for nm, ss in zip(names[1:], s[1:]):
        p = lerp(P0, P3, ss / L)
        n(nm, *p)
    secs = ["poutre1", "j_poutre12", "poutre2", "j_poutre23", "poutre3"]
    for a, b, k in zip(names[:-1], names[1:], secs):
        sec = joint_section("j", *(("poutre1", "poutre2") if k == "j_poutre12"
                                   else ("poutre2", "poutre3")), eta=eta) \
            if k.startswith("j_") else SEC[k]
        e = m.beam(a, b, sec, label=k)
        e["kind"] = k

    # --- tube de direction, colonne, cintre ----------------------------
    n("HT", *HT)
    m.beam("HB", "HT", SEC["tube_dir"])
    d = G.steer_dir()
    t_bar = (G.bar_h - HT[2]) / d[2]
    ovc = OVERLAP["col"]
    lc = (t_bar - ovc) / 2
    sc = [0, lc, lc + ovc, t_bar]
    cn = ["HT", "CA", "CB", "BAR"]
    for nm, ss in zip(cn[1:], sc[1:]):
        n(nm, *(HT + d * ss))
    csec = ["col1", "j_col12", "col2"]
    for a, b, k in zip(cn[:-1], cn[1:], csec):
        sec = joint_section("j", "col1", "col2", eta=eta) \
            if k.startswith("j_") else SEC[k]
        e = m.beam(a, b, sec, label=k); e["kind"] = k
    BARp = m.nodes["BAR"]
    n("BL", BARp[0] - 0.060, 0.220, BARp[2])
    n("BR", BARp[0] - 0.060, -0.220, BARp[2])
    m.beam("BAR", "BL", SEC["cintre"]); m.beam("BAR", "BR", SEC["cintre"])

    # --- fourche --------------------------------------------------------
    # fourche MONOBRAS (cote droit, oppose au bras arriere pour equilibrer)
    n("FR", FA[0], -0.052, FA[2]); n("FAV", *FA)
    m.beam("HB", "FR", SEC["fourreau"])
    m.beam("FR", "FAV", SEC["rigide"])          # tourillon de roue AV

    # --- tige de selle telescopique -------------------------------------
    dsa = np.array([-np.cos(G.seat_angle), 0, np.sin(G.seat_angle)])
    t_sd = (saddle_h - sm[2]) / dsa[2]
    ovs = OVERLAP["tds"]
    ls = (t_sd - 2 * ovs) / 3
    ss_ = [0, ls, ls + ovs, 2 * ls + ovs, 2 * ls + 2 * ovs, t_sd]
    sn = ["SM", "TA", "TB", "TC", "TD", "SD"]
    for nm, v in zip(sn[1:], ss_[1:]):
        n(nm, *(sm + dsa * v))
    tsec = ["tds1", "j_tds12", "tds2", "j_tds23", "tds3"]
    for a, b, k in zip(sn[:-1], sn[1:], tsec):
        sec = joint_section("j", *(("tds1", "tds2") if k == "j_tds12"
                                   else ("tds2", "tds3")), eta=eta) \
            if k.startswith("j_") else SEC[k]
        e = m.beam(a, b, sec, label=k); e["kind"] = k

    # --- manivelles ------------------------------------------------------
    n("BBR", 0, -0.036, 0)
    m.beam("BB", "BBR", SEC["rigide"])
    n("PEDL", G.crank_len, 0.075, 0); n("PEDR", -G.crank_len, -0.075, 0)
    m.beam("BBL", "PEDL", SEC["manivelle"]); m.beam("BBR", "PEDR", SEC["manivelle"])

    # --- appuis (isostatiques) -------------------------------------------
    # appuis : contacts au sol. Le roulis est bloque par les roues elles-memes,
    # represente ici par le blocage de la rotation rx en patte arriere.
    m.fix("DL", (0, 1, 2, 3)); m.fix("FAV", (1, 2))
    for nd, dofs in release:
        for d in dofs:
            m.bcs[nd].discard(d)
    for nd, dofs in extra_fix:
        m.fix(nd, dofs)
    return m


# --------------------------------------------------------------------------
# Cas de charge
# --------------------------------------------------------------------------
def load_cases():
    W = LD.m_total() * LD.g
    xf, xr = G.front_axle()[0], G.rear_axle()[0]
    fr = (LD.cg_x - xf) / (xr - xf)
    Wr, Wf = W * fr, W * (1 - fr)
    Wc = LD.m_rider * LD.g + LD.m_payload * LD.g
    F_imp = 1050.0          # cf. c03 : choc 50 mm filtre par l'elastomere 30 mm
    a_pitch = 9.81 * (xf - LD.cg_x) / (LD.cg_z + G.bb_height)

    return [
        dict(nom="F1 statique assis", crit="Re", cs=CS["statique_elastique"],
             loads={"SD": dict(fz=-LD.frac_saddle * Wc),
                    "BL": dict(fz=-LD.frac_bar * Wc / 2),
                    "BR": dict(fz=-LD.frac_bar * Wc / 2),
                    "PEDL": dict(fz=-LD.frac_pedals * Wc)}),
        # Choc frontal : on applique l'inertie du cycliste a ses trois points
        # d'appui, calee (methode d'inertie-relief, cf. run_case) pour que la
        # REACTION verticale a l'axe avant vaille exactement F_imp.
        dict(nom="F2 choc trottoir AV", crit="Re", cs=CS["choc"],
             cible=("FAV", 2, F_imp),
             loads={"SD": dict(fz=-0.55), "BL": dict(fz=-0.15),
                    "BR": dict(fz=-0.15), "PEDL": dict(fz=-0.15),
                    "FAV": dict(fx=-0.6 * F_imp / 1000.0)}),
        dict(nom="F3 choc trottoir AR", crit="Re", cs=CS["choc"],
             loads={"SD": dict(fz=-1.9 * Wc),
                    "BL": dict(fz=-0.2 * Wc), "BR": dict(fz=-0.2 * Wc)}),
        dict(nom="F4 pedalage danseuse (ISO 4210-6)", crit="Re",
             cs=CS["statique_elastique"],
             loads={"PEDL": dict(fz=-LD.F_pedal_iso),
                    "BL": dict(fz=0.35 * LD.F_pedal_iso, fy=LD.F_bar_lat_iso),
                    "BR": dict(fz=0.15 * LD.F_pedal_iso)}),
        dict(nom="F5 freinage AV limite basculement", crit="Re",
             cs=CS["statique_elastique"],
             loads={"FAV": dict(fx=-W * a_pitch / 9.81 * 1.0,
                                my=-W * a_pitch / 9.81 * G.wheel_r),
                    "BL": dict(fz=-0.45 * Wc, fx=0.25 * Wc),
                    "BR": dict(fz=-0.45 * Wc, fx=0.25 * Wc)}),
        dict(nom="F6 cintre 600 N (ISO 4210-5 stat.)", crit="Re",
             cs=CS["statique_elastique"],
             loads={"BL": dict(fz=-LD.F_bar_lat_iso)}),
        dict(nom="F6b cintre +/-270 N (ISO 4210-5, 1e5 cy.)", crit="sN", N=1e5,
             cs=CS["fatigue"],
             loads={"BL": dict(fz=-270.0), "BR": dict(fz=270.0)}),
        dict(nom="F7 fatigue pedalage (1e6 cy. = 5000 km)", crit="sN", N=1e6,
             cs=CS["fatigue"],
             loads={"PEDL": dict(fz=-0.5 * LD.F_pedal_iso),
                    "PEDR": dict(fz=-0.5 * LD.F_pedal_iso),
                    "SD": dict(fz=-0.5 * Wc)}),
    ]


KF_JONCTION = 1.25      # effet d'entaille aux raccords colles-goupilles (fatigue)


def run_case(case, eta=ETA_JOINT):
    def _assemble(scale=1.0):
        mm = build_frame(eta=eta, release=case.get("release", ()),
                         extra_fix=case.get("extra_fix", ()))
        for nd, kw in case["loads"].items():
            if kw:
                mm.load(nd, **{k: v * scale for k, v in kw.items()})
        mm.solve()
        return mm

    if "cible" in case:
        # inertie-relief : on cale l'amplitude du chargement pour obtenir la
        # reaction d'appui visee (le systeme est lineaire -> une seule iteration)
        nd, dof, val = case["cible"]
        m0 = _assemble(1000.0)
        r0 = m0.reaction(nd)[dof]
        m = _assemble(1000.0 * val / r0) if abs(r0) > 1e-6 else m0
    else:
        m = _assemble(1.0)
    rows = []
    for e in m.beams:
        if e["sec"].name == "rigide":
            continue
        sec = e["sec"]
        if hasattr(sec, "Z_real"):
            f = e["f_local"]
            M = max(np.hypot(f[4], f[5]), np.hypot(f[10], f[11]))
            sg = abs(f[0]) / sec.A + M / sec.Z_real
            tau = abs(f[3]) * sec.zmax / sec.J_real
            e["sigma_vm"] = np.sqrt(sg ** 2 + 3 * tau ** 2)
        mat = e["sec"].mat
        if case["crit"] == "sN":
            lim = sigma_allow(mat, case.get("N", 1e7), kf=KF_JONCTION)
            kf = 1.0
        else:
            lim = mat[case["crit"]]
            kf = 1.0
        e["sigma_vm"] *= kf
        rows.append(dict(el=e["label"], sigma=e["sigma_vm"], cs=lim / e["sigma_vm"],
                         mat=mat["name"]))
    rows.sort(key=lambda r: r["cs"])
    return m, rows


def stiffness():
    """Raideurs caracteristiques : BdP lateral, direction en torsion, flou."""
    out = {}
    m = build_frame()
    m.load("BB", fy=1000.0); m.solve()
    out["k_BdP_lateral_N_mm"] = 1000.0 / abs(m.disp("BB")[1]) / 1e3

    m = build_frame()
    m.load("BL", fz=-500); m.load("BR", fz=500); m.solve()
    dz = m.disp("BL")[2] - m.disp("BR")[2]
    theta = abs(dz) / 0.480
    out["k_torsion_direction_Nm_deg"] = (500 * 0.480) / np.rad2deg(theta)

    m = build_frame()
    m.load("BAR", fx=200.0); m.solve()
    out["deplacement_cintre_200N_mm"] = abs(m.disp("BAR")[0]) * 1e3

    m = build_frame()
    m.load("SD", fz=-800); m.solve()
    out["fleche_selle_800N_mm"] = abs(m.disp("SD")[2]) * 1e3
    return out


def main():
    cases = load_cases()
    print("=" * 104)
    print("CADRE COSYN-30 -- verification par elements finis (poutres 3D, "
          f"eta_joint = {ETA_JOINT})")
    print("=" * 104)
    print(f"{'cas de charge':<38}{'element critique':<16}{'sigma_VM':>10}"
          f"{'limite':>9}{'CS obt.':>9}{'CS exige':>10}{'verdict':>9}")
    print("-" * 104)
    summary = []
    for c in cases:
        m, rows = run_case(c)
        w = rows[0]
        lim = (sigma_allow(MAT["AL7075T6"], c.get("N", 1e7), kf=KF_JONCTION)
               if c["crit"] == "sN" else MAT["AL7075T6"][c["crit"]]) / 1e6
        ok = w["cs"] >= c["cs"]
        print(f"{c['nom']:<38}{w['el']:<16}{w['sigma']/1e6:10.0f}{lim:9.0f}"
              f"{w['cs']:9.2f}{c['cs']:10.2f}{'  OK' if ok else '  NON':>9}")
        summary.append(dict(cas=c["nom"], element=w["el"],
                            sigma_MPa=w["sigma"] / 1e6, cs=w["cs"],
                            cs_exige=c["cs"], ok=bool(ok),
                            top5=[dict(el=r["el"], s=r["sigma"] / 1e6, cs=r["cs"])
                                  for r in rows[:5]]))
    print("-" * 104)
    print("\nRaideurs caracteristiques")
    st = stiffness()
    ref = dict(k_BdP_lateral_N_mm="velo de ville acier : 60-90 N/mm",
               k_torsion_direction_Nm_deg="VTT alu : 60-110 N.m/deg",
               deplacement_cintre_200N_mm="",
               fleche_selle_800N_mm="")
    for k, v in st.items():
        print(f"  {k:<34}{v:9.1f}   {ref.get(k,'')}")

    print("\nSensibilite au rendement des emmanchements telescopiques")
    print(f"{'eta':>6}{'k_BdP':>10}{'k_torsion':>12}{'sigma max F4':>14}")
    sens = []
    for eta in (0.35, 0.50, 0.60, 0.75, 1.00):
        m = build_frame(eta=eta); m.load("BB", fy=1000); m.solve()
        kb = 1000 / abs(m.disp("BB")[1]) / 1e3
        m2 = build_frame(eta=eta); m2.load("BL", fz=-500); m2.load("BR", fz=500)
        m2.solve()
        th = abs(m2.disp("BL")[2] - m2.disp("BR")[2]) / 0.480
        kt = (500 * 0.480) / np.rad2deg(th)
        _, rows = run_case(cases[3], eta=eta)
        print(f"{eta:6.2f}{kb:10.1f}{kt:12.1f}{rows[0]['sigma']/1e6:14.0f}")
        sens.append(dict(eta=eta, k_bb=kb, k_tors=kt, s=rows[0]["sigma"] / 1e6))

    m = build_frame()
    m_real = sum(e["sec"].mass_per_m * np.linalg.norm(m.nodes[e["n2"]] - m.nodes[e["n1"]])
                 for e in m.beams if e["sec"].name != "rigide")
    print(f"\nMasse des tubes modelises : {m_real*1e3:.0f} g "
          "(hors raccords, roulements, accastillage)")
    print("\nFlou residuel des emmanchements (jeu de coulissement non rattrape)")
    from joints import Telescope
    tj = [("poutre 1-2", "poutre1", "poutre2", OVERLAP["poutre"], 0.520),
          ("poutre 2-3", "poutre2", "poutre3", OVERLAP["poutre"], 0.350),
          ("colonne 1-2", "col1", "col2", OVERLAP["col"], 0.215)]
    print(f"{'liaison':<14}{'recouvr.':>10}{'jeu diam.':>11}{'basculement':>13}"
          f"{'flou au cintre':>16}")
    flou = 0.0
    for nm, ko, ki, ov, lev in tj:
        t = Telescope(nm, tube_props(*TUBES[ko][:2], TUBES[ko][2]),
                      tube_props(*TUBES[ki][:2], TUBES[ki][2]), ov, clearance=60e-6)
        f_mm = t.slop_tip(lev) * 1e3
        flou += f_mm if "colonne" in nm or "poutre" in nm else 0
        print(f"{nm:<14}{ov*1e3:9.0f}mm{60:10.0f}um"
              f"{np.rad2deg(t.slop_angle()):12.3f}d{f_mm:15.2f}mm")
    print(f"{'CUMUL':<14}{'':10}{'':11}{'':13}{flou:15.2f}mm"
          f"   -> a annuler par expandeur conique")

    with open("../out/cadre.json", "w") as f:
        json.dump(dict(cas=summary, raideurs=st, sensibilite=sens,
                       masse_tubes_g=m_real * 1e3), f, indent=1, default=float)


if __name__ == "__main__":
    main()
