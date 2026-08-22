"""
COSYN-30 -- Etude de la ROUE DEPLOYABLE a jante segmentee et rayons tendus.

Architecture analysee
---------------------
* jante en N arcs d'aluminium extrude, assembles par tenons coniques ;
  la precontrainte des rayons plaque les arcs les uns contre les autres et
  cree un anneau continu comprime -> les joints ne travaillent qu'en
  COMPRESSION + cisaillement, jamais en traction.
* rayons acier inox, croises k=2, montes sur deux brides de moyeu ;
  ils sont *souples* : detendus, ils laissent les arcs se rabattre en
  eventail (aucune piece n'est desolidarisee).
* tension globale obtenue en ecartant axialement les deux brides du moyeu
  (vis differentielle / came a levier) : un seul geste tend les N x 4 rayons.

Le modele elements finis traite la jante en poutres 3D (avec troncons de
joint a rigidite reduite), les rayons en barres precontraintes "tension only"
(un rayon qui se detend sort automatiquement du modele).
"""

from __future__ import annotations
import json
import numpy as np

from fem import Model, Section
from params import Geo as G, Loads as LD, MAT, CS

RIM_MAT = MAT["AL7075T6"]
SPOKE_MAT = MAT["INOX_RAYON"]

KT_SPOKE = 1.8          # concentration au siege de rayon (insert rapporte rayon 3 mm)
ETA_JOINT_I = 0.45      # rendement de flexion du joint a tenon conique
ETA_JOINT_J = 0.50      # rendement de torsion
JOINT_ARC_DEG = 2.0     # etendue angulaire modelisee du joint


def rim_section(scale_I=1.0, scale_J=1.0, name="jante"):
    """Caisson de jante : b = largeur axiale, h = hauteur radiale."""
    s = Section.rect_tube(name, G.rim_w, G.rim_h, G.rim_t, RIM_MAT)
    # repere local de la poutre de jante : x = tangentiel, y = axial, z = radial
    s.Iy *= scale_I     # flexion dans le plan de la roue (depth = h radial)
    s.Iz *= scale_I     # flexion hors-plan
    s.J *= scale_J
    return s


def build_wheel(n_spokes=None, n_seg=None, T0=None, lacing_cross=2,
                joint_eta_I=ETA_JOINT_I, phase=0.0):
    n_spokes = n_spokes or G.n_spokes
    n_seg = n_seg or G.n_seg
    T0 = G.spoke_T0 if T0 is None else T0
    R = G.rim_r_mid
    rf = G.hub_flange_r
    b = G.hub_bracing

    m = Model()
    sec_rim = rim_section()
    sec_joint = rim_section(joint_eta_I, ETA_JOINT_J, "joint")

    # --- stations angulaires ------------------------------------------
    spokes_per_seg = n_spokes // n_seg
    dth_seg = 2 * np.pi / n_seg
    stations = []        # (theta, type) type in {'spoke','joint-','joint+'}
    for s in range(n_seg):
        th0 = s * dth_seg + phase
        stations.append((th0 + np.deg2rad(JOINT_ARC_DEG) / 2, "jend"))
        for k in range(spokes_per_seg):
            stations.append((th0 + dth_seg * (k + 0.5) / spokes_per_seg, "spoke"))
        stations.append((th0 + dth_seg - np.deg2rad(JOINT_ARC_DEG) / 2, "jstart"))
    stations.sort()

    rim_nodes = []
    for i, (th, kind) in enumerate(stations):
        nm = f"R{i}"
        m.node(nm, R * np.cos(th), 0.0, R * np.sin(th))
        rim_nodes.append((nm, th, kind))

    # --- elements de jante --------------------------------------------
    nn = len(rim_nodes)
    for i in range(nn):
        a, tha, ka = rim_nodes[i]
        c, thc, kc = rim_nodes[(i + 1) % nn]
        # troncon de joint = celui qui relie un 'jstart' a un 'jend'
        is_joint = (ka == "jstart" and kc == "jend")
        sec = sec_joint if is_joint else sec_rim
        vref = np.array([0.0, 1.0, 0.0])      # y local = axe de roue
        e = m.beam(a, c, sec, vref=vref, label="joint" if is_joint else "jante")
        e["theta"] = float(np.angle(np.exp(1j * tha) + np.exp(1j * thc)))
        e["is_joint"] = is_joint

    # --- moyeu + rayons -----------------------------------------------
    phi = np.deg2rad(lacing_cross * 720.0 / n_spokes)
    A_sp = np.pi * G.spoke_d_mid ** 2 / 4
    idx = 0
    for nm, th, kind in rim_nodes:
        if kind != "spoke":
            continue
        side = 1 if idx % 2 == 0 else -1          # bride gauche / droite
        lead = 1 if (idx // 1) % 2 == 0 else -1
        lead = 1 if (idx % 4) < 2 else -1         # alternance tirant / poussant
        thh = th - lead * phi
        hn = f"H{idx}"
        m.node(hn, rf * np.cos(thh), side * G.hub_bracing, rf * np.sin(thh))
        m.fix(hn)                                  # moyeu suppose indeformable
        sp = m.bar(hn, nm, A_sp, SPOKE_MAT["E"], pretension=T0,
                   tension_only=True, label=f"rayon{idx}")
        sp["theta"] = th
        sp["side"] = side
        sp["lead"] = lead
        idx += 1
    return m, rim_nodes


def contact_nodes(rim_nodes, n=3):
    """Noeuds de jante les plus proches du point de contact au sol (theta=-90)."""
    tgt = -np.pi / 2
    d = [(abs(np.angle(np.exp(1j * (th - tgt)))), nm) for nm, th, k in rim_nodes]
    d.sort()
    return [nm for _, nm in d[:n]]


def apply_ground(m, rim_nodes, P_rad=0.0, P_lat=0.0, T_brake=0.0):
    """Charge au contact : radiale (vers le haut), laterale, couple de freinage."""
    cn = contact_nodes(rim_nodes, 3)
    w = [0.5, 0.25, 0.25]
    Ft = T_brake / G.wheel_r
    for nm, wi in zip(cn, w):
        m.load(nm, fz=wi * P_rad, fy=wi * P_lat, fx=wi * Ft)


def equalise(m, T_target, n_iter=6):
    """Reproduit le devoilage : on ajuste la longueur libre de chaque rayon
    (donc sa precontrainte de montage) jusqu'a ce que TOUTES les tensions
    montees a vide valent la cible. Sans cela, la raideur variable de la
    jante au droit des joints cree une dispersion artificielle."""
    for _ in range(n_iter):
        m.solve()
        err = 0.0
        for b in m.bars:
            d = T_target - b["T"]
            b["T0"] += d
            err = max(err, abs(d))
        if err < 0.5:
            break
    return err


def solve_case(name, P_rad, P_lat=0.0, T_brake=0.0, T0=None, **kw):
    T0v = G.spoke_T0 if T0 is None else T0
    m, rn = build_wheel(T0=T0v, **kw)
    equalise(m, T0v)
    for b in m.bars:
        b["active"] = True
    apply_ground(m, rn, P_rad, P_lat, T_brake)
    m.solve()

    tens = np.array([b["T"] for b in m.bars])
    slack = int(np.sum(tens <= 1.0))
    cn = contact_nodes(rn, 1)[0]
    u = m.disp(cn)
    defl_rad = u[2]
    defl_lat = u[1]

    # efforts internes de jante
    hoop, Mip, Mop, joints = [], [], [], []
    for e in m.beams:
        f = e["f_local"]
        hoop.append(f[0])
        Mip.append(max(abs(f[4]), abs(f[10])))     # flexion plan de roue
        Mop.append(max(abs(f[5]), abs(f[11])))     # flexion hors plan
        if e["is_joint"]:
            N = f[0]                                # >0 = compression
            M = max(abs(f[4]), abs(f[10]))
            V = np.hypot(f[1], f[2])
            joints.append(dict(N=N, M=M, V=V, theta=float(e["theta"])))
    sig = max(e["sigma_vm"] for e in m.beams)

    return dict(cas=name, P_rad=P_rad, P_lat=P_lat, T_brake=T_brake,
                T0=T0v, T_max=float(tens.max()), T_min=float(tens.min()),
                n_slack=slack,
                defl_rad_mm=float(defl_rad * 1e3),
                defl_lat_mm=float(defl_lat * 1e3),
                k_rad_N_mm=float(abs(P_rad / defl_rad) / 1e3) if P_rad else None,
                k_lat_N_mm=float(abs(P_lat / defl_lat) / 1e3) if P_lat else None,
                N_hoop_max=float(min(hoop)), M_ip_max=float(max(Mip)),
                M_op_max=float(max(Mop)),
                sigma_vm_MPa=float(sig / 1e6),
                sigma_locale_MPa=float(sig * KT_SPOKE / 1e6),
                joints=joints, model=m)


# ----------------------------------------------------------------------
# Verifications analytiques complementaires
# ----------------------------------------------------------------------
def ring_buckling(T0=None, n_spokes=None, eta=ETA_JOINT_I):
    """Flambement de l'anneau de jante sous la pression radiale des rayons.

    Charge critique d'un anneau sous pression radiale uniforme : q_cr = 3EI/R^3.
    L'inertie est penalisee par le rendement des joints (borne basse).
    """
    T0 = G.spoke_T0 if T0 is None else T0
    n_spokes = n_spokes or G.n_spokes
    s = rim_section()
    R = G.rim_r_mid
    # composante radiale d'un rayon (angle de bracage)
    phi = np.deg2rad(2 * 720.0 / n_spokes)
    Lsp, comp = spoke_geom(phi)
    q = n_spokes * T0 * comp["radial"] / (2 * np.pi * R)
    EI = RIM_MAT["E"] * s.Iy
    q_cr_ideal = 3 * EI / R ** 3
    q_cr = eta * q_cr_ideal
    return dict(q_N_m=q, q_cr_N_m=q_cr, marge=q_cr / q,
                N_hoop_N=n_spokes * T0 * comp["radial"] / (2 * np.pi))


def spoke_geom(phi=None, n_spokes=None):
    n_spokes = n_spokes or G.n_spokes
    phi = np.deg2rad(2 * 720.0 / n_spokes) if phi is None else phi
    R, rf, b = G.rim_r_mid, G.hub_flange_r, G.hub_bracing
    inplane = np.sqrt(R ** 2 + rf ** 2 - 2 * R * rf * np.cos(phi))
    L = np.sqrt(inplane ** 2 + b ** 2)
    # composantes unitaires du rayon vues de la jante
    radial = (R - rf * np.cos(phi)) / L
    tangential = rf * np.sin(phi) / L
    axial = b / L
    return L, dict(radial=radial, tangential=tangential, axial=axial)


def tensioning_mechanism(T0=None, n_spokes=None, lever=0.090, mu_cam=0.10,
                         cam_travel=None, cam_sweep_deg=170.0):
    """Mise en tension par ecartement des brides via une came a levier.

    Le mecanisme retenu est une came excentree type blocage rapide, logee dans
    l'axe creux : un levier de 60 mm ecarte les deux brides de la course
    calculee ci-dessous et tend simultanement les 24 rayons. Un ecrou de
    reglage fin a l'autre extremite fixe la tension nominale une fois pour
    toutes (comme un blocage rapide de roue classique).
    """
    T0 = G.spoke_T0 if T0 is None else T0
    n_spokes = n_spokes or G.n_spokes
    A = np.pi * G.spoke_d_mid ** 2 / 4
    L, comp = spoke_geom(n_spokes=n_spokes)
    k_sp = SPOKE_MAT["E"] * A / L
    db = 1e-6
    b0 = G.hub_bracing
    G.hub_bracing = b0 + db
    L2, _ = spoke_geom(n_spokes=n_spokes)
    G.hub_bracing = b0
    dLdb = (L2 - L) / db

    dL_needed = T0 / k_sp                       # allongement elastique du rayon
    db_needed = dL_needed / dLdb                # ecartement d'UNE bride
    course = cam_travel or 2 * db_needed        # course totale de la came
    F_axial = (n_spokes / 2) * T0 * comp["axial"]

    # came : montee lineaire equivalente sur le balayage du levier
    sweep = np.deg2rad(cam_sweep_deg)
    drdth = course / sweep
    r_cam = 0.009
    F_hand = F_axial * (drdth + mu_cam * r_cam) / lever
    # pic reel en fin de course d'une came sur-centree : facteur 2.2
    return dict(k_spoke_N_m=k_sp, L_spoke_mm=L * 1e3,
                allongement_rayon_mm=dL_needed * 1e3,
                ecartement_bride_mm=db_needed * 1e3,
                course_came_mm=course * 1e3,
                F_axial_bride_N=F_axial,
                effort_main_moyen_N=F_hand,
                effort_main_pic_N=2.2 * F_hand,
                sensibilite_N_par_0p1mm=k_sp * dLdb * 1e-4)


def joint_check(joints):
    """Verifie que chaque joint reste ferme et que la pression de contact du
    tenon conique reste admissible.

    Le noyau central d'une section CREUSE n'est pas h/6 (valeur valable pour un
    rectangle plein) mais Z/A = (I / (h/2)) / A : pour le caisson de jante il
    vaut pres du double, ce qui change la conclusion.
    """
    h = G.rim_h
    b = G.rim_w
    t = G.rim_t
    A_contact = 2 * (b + h) * t - 4 * t ** 2      # section du caisson
    I_rim = rim_section().Iy
    kern = (I_rim / (h / 2)) / A_contact
    out = []
    for j in joints:
        N, M, V = j["N"], j["M"], j["V"]
        e = M / N if N > 1 else np.inf
        sig_max = N / A_contact + M * (h / 2) / I_rim if N > 0 else 0
        sig_min = N / A_contact - M * (h / 2) / I_rim if N > 0 else 0
        out.append(dict(theta_deg=np.rad2deg(j["theta"]) % 360,
                        N=N, M=M, V=V, e_mm=e * 1e3, kern_mm=kern * 1e3,
                        ferme=bool(e <= kern),
                        p_contact_MPa=sig_max / 1e6,
                        sigma_mini_MPa=sig_min / 1e6,
                        tau_MPa=V / A_contact / 1e6))
    return out


# ----------------------------------------------------------------------
def envelope_over_phase(name, n_phase=12, joint_eta_I=ETA_JOINT_I, **case):
    """Enveloppe sur un pas de segment : la roue tourne, donc chaque joint
    finit par se presenter au point de contact. C'est ce balayage, et non une
    position figee, qui donne le cas dimensionnant."""
    pitch = 2 * np.pi / G.n_seg
    worst = None
    hist = []
    for i in range(n_phase):
        ph = pitch * i / n_phase
        r = solve_case(name, phase=ph, joint_eta_I=joint_eta_I, **case)
        r.pop("model")
        r["phase_deg"] = np.rad2deg(ph)
        hist.append(r)
        if worst is None or r["sigma_locale_MPa"] > worst["sigma_locale_MPa"]:
            worst = r
    return worst, hist


def wheel_radial_stiffness():
    r = solve_case("unitaire", P_rad=500.0)
    return r["k_rad_N_mm"] * 1e3      # N/m


def main():
    W = LD.m_total() * LD.g
    xf, xr = G.front_axle()[0], G.rear_axle()[0]
    fr_rear = (LD.cg_x - xf) / (xr - xf)
    P_stat_r = W * fr_rear
    P_stat_f = W * (1 - fr_rear)

    cases = [
        dict(name="W1 statique roue AR", P_rad=P_stat_r),
        dict(name="W2 choc vertical AV (k=3.2)", P_rad=P_stat_f * LD.k_kerb_drop),
        dict(name="W3 choc vertical AR (k=2.5)", P_rad=P_stat_r * LD.k_bump),
        dict(name="W4 virage appuye AR", P_rad=P_stat_r * 1.6,
             P_lat=P_stat_r * 0.6),
        dict(name="W5 freinage AV 0.45 g", P_rad=P_stat_f * 1.8,
             T_brake=LD.m_total() * LD.a_brake_des * G.wheel_r),
        dict(name="W6 nid de poule oblique AV", P_rad=P_stat_f * 2.6,
             P_lat=P_stat_f * 1.2),
    ]
    res = []
    for c in cases:
        r = solve_case(c.pop("name"), **c)
        r.pop("model")
        res.append(r)

    buck = ring_buckling()
    mech = tensioning_mechanism()

    print("=" * 100)
    print("ROUE DEPLOYABLE -- resultats elements finis "
          f"({G.n_seg} arcs, {G.n_spokes} rayons, T0={G.spoke_T0:.0f} N)")
    print("=" * 100)
    hdr = (f"{'cas':<28}{'P[N]':>7}{'Tmax':>7}{'Tmin':>7}{'det.':>5}"
           f"{'f_rad':>8}{'f_lat':>8}{'k_rad':>9}{'sVM':>8}")
    print(hdr)
    print(f"{'':28}{'':7}{'[N]':>7}{'[N]':>7}{'':5}{'[mm]':>8}{'[mm]':>8}"
          f"{'[N/mm]':>9}{'[MPa]':>8}")
    print("-" * 100)
    for r in res:
        print(f"{r['cas']:<28}{r['P_rad']:7.0f}{r['T_max']:7.0f}{r['T_min']:7.0f}"
              f"{r['n_slack']:5d}{r['defl_rad_mm']:8.2f}{r['defl_lat_mm']:8.2f}"
              f"{(r['k_rad_N_mm'] or 0):9.0f}{r['sigma_locale_MPa']:8.0f}")
    print("-" * 100)
    smax = max(r['sigma_locale_MPa'] for r in res)
    print(f"sVM = contrainte locale au siege de rayon (Kt = {KT_SPOKE})")
    print(f"Limite elastique jante 7075-T6 : {RIM_MAT['Re']/1e6:.0f} MPa "
          f"-> CS statique = {RIM_MAT['Re']/1e6/smax:.2f}")
    s_serv = res[0]["sigma_locale_MPa"]
    print(f"  cas EXTREME  : {smax:.0f} MPa vs Re = {RIM_MAT['Re']/1e6:.0f} MPa")
    print(f"  cas COURANT  : {s_serv:.0f} MPa (W1) vs limite d'endurance "
          f"{RIM_MAT['sN']/1e6:.0f} MPa -> CS = {RIM_MAT['sN']/1e6/s_serv:.2f}")
    print("  (le cumul de dommage reel sur spectre est traite en c07_fatigue.py)")
    print()
    print("Flambement de l'anneau de jante sous precontrainte")
    print(f"  charge radiale repartie      q = {buck['q_N_m']:.0f} N/m")
    print(f"  charge critique (joints -55%) q_cr = {buck['q_cr_N_m']:.0f} N/m")
    print(f"  marge au flambement          = {buck['marge']:.1f}")
    print(f"  compression circonferentielle = {buck['N_hoop_N']:.0f} N")
    print()
    print("Mecanisme de mise en tension (ecartement des brides)")
    for k, v in mech.items():
        print(f"  {k:<24} {v:10.3f}")
    print()
    worst = max(res, key=lambda r: r["sigma_locale_MPa"])
    jc = joint_check(worst["joints"])
    print(f"Joints de jante -- cas dimensionnant : {worst['cas']}")
    print(f"{'theta':>8}{'N[N]':>9}{'M[N.m]':>9}{'V[N]':>8}{'e[mm]':>8}"
          f"{'noyau':>8}{'ferme':>7}{'p max':>8}{'p mini':>8}")
    for j in jc:
        print(f"{j['theta_deg']:8.0f}{j['N']:9.0f}{j['M']:9.2f}{j['V']:8.0f}"
              f"{min(j['e_mm'],999):8.2f}{j['kern_mm']:8.2f}"
              f"{str(j['ferme']):>7}{j['p_contact_MPa']:8.1f}"
              f"{j['sigma_mini_MPa']:8.1f}")
    print("  p mini > 0 sur tous les joints => la portee reste integralement "
          "en compression,")
    print("  le tenon conique ne travaille jamais en traction.")

    print()
    print("Sensibilite a la precontrainte des rayons T0")
    print(f"{'T0 [N]':>8}{'Tmin W6':>10}{'Tmax W6':>10}{'det.':>6}"
          f"{'sVM [MPa]':>11}{'sig.loc':>9}{'marge flamb.':>14}{'effort main':>12}")
    sweep = []
    for T0 in (500, 560, 620, 680, 740, 800, 880):
        rr = solve_case("sweep", P_rad=P_stat_f * 2.6, P_lat=P_stat_f * 1.2, T0=T0)
        bb = ring_buckling(T0=T0)
        mm = tensioning_mechanism(T0=T0)
        sweep.append(dict(T0=T0, Tmin=rr["T_min"], Tmax=rr["T_max"],
                          slack=rr["n_slack"], svm=rr["sigma_vm_MPa"],
                          sloc=rr["sigma_locale_MPa"], marge=bb["marge"],
                          main=mm["effort_main_pic_N"]))
        print(f"{T0:8.0f}{rr['T_min']:10.0f}{rr['T_max']:10.0f}{rr['n_slack']:6d}"
              f"{rr['sigma_vm_MPa']:11.0f}{rr['sigma_locale_MPa']:9.0f}"
              f"{bb['marge']:14.1f}{mm['effort_main_pic_N']:12.0f}")

    print()
    print("Sensibilite au nombre d'arcs de jante (a 24 rayons)")
    print(f"{'N arcs':>8}{'Tmin':>8}{'sVM':>8}{'sig.loc':>9}{'marge flamb.':>14}")
    seg = []
    for ns in (4, 6, 8, 12):
        if G.n_spokes % ns:
            continue
        rr = solve_case("seg", P_rad=P_stat_f * 2.6, P_lat=P_stat_f * 1.2, n_seg=ns)
        bb = ring_buckling()
        seg.append(dict(n_seg=ns, Tmin=rr["T_min"], svm=rr["sigma_vm_MPa"],
                        sloc=rr["sigma_locale_MPa"]))
        print(f"{ns:8d}{rr['T_min']:8.0f}{rr['sigma_vm_MPa']:8.0f}"
              f"{rr['sigma_locale_MPa']:9.0f}{bb['marge']:14.1f}")

    out = dict(cas=res, flambement=buck, mise_en_tension=mech,
               balayage_T0=sweep, balayage_arcs=seg,
               joints=jc, cas_dim=worst["cas"],
               k_rad_N_m=wheel_radial_stiffness())
    with open("../out/roue.json", "w") as f:
        json.dump(out, f, indent=1, default=float)
    return out


if __name__ == "__main__":
    main()
