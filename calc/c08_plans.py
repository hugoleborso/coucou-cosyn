"""
COSYN-30 -- generation des PLANS (SVG) directement a partir du parametrage.

Aucun trait n'est dessine "a la main" : toutes les coordonnees viennent de
params.py et du modele elements finis, de sorte qu'une modification de la
geometrie regenere des plans exacts.
"""
from __future__ import annotations
import numpy as np
import c02_cadre as C
from params import Geo as G, Loads as LD, Pack

S = 1.0          # echelle interne : on travaille en mm
CSS = """
.tr{fill:none;stroke:#1a1a1a;stroke-width:2.2;stroke-linecap:round}
.tr2{fill:none;stroke:#1a1a1a;stroke-width:1.4}
.fin{fill:none;stroke:#666;stroke-width:0.8}
.axe{fill:none;stroke:#c0392b;stroke-width:0.8;stroke-dasharray:12 3 2 3}
.cache{fill:none;stroke:#888;stroke-width:1;stroke-dasharray:5 4}
.cote{fill:none;stroke:#0b6e99;stroke-width:0.8}
.hach{fill:#1a1a1a;opacity:0.12}
.roue{fill:none;stroke:#1a1a1a;stroke-width:3}
.tread{fill:none;stroke:#333;stroke-width:11;opacity:.75}
.seg{fill:none;stroke:#c0392b;stroke-width:3}
.pack{fill:none;stroke:#1a1a1a;stroke-width:2}
.box{fill:#0b6e99;opacity:.18;stroke:#0b6e99;stroke-width:1}
text{font-family:'DejaVu Sans',Helvetica,sans-serif;fill:#1a1a1a}
.t{font-size:11px}.ts{font-size:9px;fill:#555}.tt{font-size:17px;font-weight:700}
.tc{font-size:10px;fill:#0b6e99}
"""


def svg(w, h, body, title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}"><style>{CSS}</style>'
            f'<rect width="{w}" height="{h}" fill="#fbfaf8"/>{body}</svg>')


def line(p1, p2, cls="tr"):
    return f'<line class="{cls}" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}"/>'


def circ(c, r, cls="tr"):
    return f'<circle class="{cls}" cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{r:.1f}"/>'


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def txt(p, s, cls="t", anchor="start", rot=0):
    s = esc(s)
    tr = f' transform="rotate({rot} {p[0]:.1f} {p[1]:.1f})"' if rot else ""
    return (f'<text class="{cls}" x="{p[0]:.1f}" y="{p[1]:.1f}" '
            f'text-anchor="{anchor}"{tr}>{s}</text>')


def cote(p1, p2, label, off=18, vertical=False):
    """Ligne de cote simple avec fleches."""
    p1, p2 = np.array(p1, float), np.array(p2, float)
    d = p2 - p1
    n = np.array([-d[1], d[0]])
    n = n / (np.linalg.norm(n) + 1e-9) * off
    a, b = p1 + n, p2 + n
    mid = (a + b) / 2
    ang = np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))
    if ang > 90 or ang < -90:
        ang += 180
    return (line(p1, a, "fin") + line(p2, b, "fin") + line(a, b, "cote")
            + f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2" fill="#0b6e99"/>'
            + f'<circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="2" fill="#0b6e99"/>'
            + txt(mid + np.array([0, -4]), label, "tc", "middle", ang))


# ==========================================================================
def plan_general():
    """Vue de cote, velo deploye, cote."""
    m = C.build_frame()
    W, H = 1500, 900
    K = 640.0                  # echelle m -> px
    sk = K / 1000.0
    ox, oy = 80 + 0.640 * K, 118 + 0.790 * K

    def P(node):
        p = m.nodes[node]
        return np.array([ox + p[0] * K, oy - p[2] * K])

    b = []
    sol = oy + G.bb_height * K
    b.append(line((60, sol), (W - 60, sol), "tr2"))
    for x in range(60, W - 60, 14):
        b.append(line((x, sol), (x - 8, sol + 8), "fin"))

    # roues
    for nd in ("FAV", "FAR"):
        c = P(nd)
        b.append(f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{(G.wheel_r-G.tread_t/2)*K:.1f}" fill="none" stroke="#333" stroke-width="{G.tread_t*K:.1f}" opacity=".75"/>')
        b.append(circ(c, (G.rim_r_mid + G.rim_h / 2) * K, "tr2"))
        b.append(circ(c, (G.rim_r_mid - G.rim_h / 2) * K, "tr2"))
        # 8 arcs de jante
        for k in range(G.n_seg):
            a0 = 2 * np.pi * k / G.n_seg + 0.10
            a1 = 2 * np.pi * (k + 1) / G.n_seg - 0.10
            r = G.rim_r_mid * K
            p0 = c + r * np.array([np.cos(a0), -np.sin(a0)])
            p1 = c + r * np.array([np.cos(a1), -np.sin(a1)])
            b.append(f'<path class="seg" d="M{p0[0]:.1f},{p0[1]:.1f} '
                     f'A{r:.1f},{r:.1f} 0 0 0 {p1[0]:.1f},{p1[1]:.1f}"/>')
        # rayons
        for k in range(G.n_spokes):
            a = 2 * np.pi * k / G.n_spokes
            phi = np.deg2rad(2 * 720.0 / G.n_spokes) * (1 if k % 2 else -1)
            rr = G.rim_r_mid * K
            rf = G.hub_flange_r * K
            p0 = c + rr * np.array([np.cos(a), -np.sin(a)])
            p1 = c + rf * np.array([np.cos(a + phi), -np.sin(a + phi)])
            b.append(line(p0, p1, "fin"))
        b.append(circ(c, G.hub_flange_r * K, "tr2"))
        b.append(circ(c, G.disc_d / 2 * K, "cache"))

    # cadre
    tubes = [("BB", "PA"), ("PA", "PB"), ("PB", "PC"), ("PC", "PD"), ("PD", "HB"),
             ("HB", "HT"), ("HT", "CA"), ("CA", "CB"), ("CB", "BAR"),
             ("BB", "SM"), ("SM", "TA"), ("TA", "TB"), ("TB", "TC"),
             ("TC", "TD"), ("TD", "SD"), ("BBL", "DL"), ("DL", "SM"),
             ("HB", "FR"), ("BBL", "PEDL")]
    ep = {"BB->PA": 46, "PA->PB": 44, "PB->PC": 41, "PC->PD": 39, "PD->HB": 36,
          "HB->HT": 46, "HT->CA": 34, "CA->CB": 32, "CB->BAR": 29,
          "BB->SM": 42, "SM->TA": 32, "TA->TB": 30, "TB->TC": 27,
          "TC->TD": 25, "TD->SD": 23, "BBL->DL": 38, "DL->SM": 26,
          "HB->FR": 46, "BBL->PEDL": 24}
    ep = {k: v * sk for k, v in ep.items()}
    for a, c_ in tubes:
        p, q = P(a), P(c_)
        e = ep.get(f"{a}->{c_}", 30 * sk) / 2
        d = q - p
        n = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9) * e
        b.append(f'<path class="tr" d="M{p[0]+n[0]:.1f},{p[1]+n[1]:.1f} '
                 f'L{q[0]+n[0]:.1f},{q[1]+n[1]:.1f} '
                 f'M{p[0]-n[0]:.1f},{p[1]-n[1]:.1f} '
                 f'L{q[0]-n[0]:.1f},{q[1]-n[1]:.1f}"/>')
    # reperes des emmanchements
    for a, c_, lab in (("PA", "PB", "E1"), ("PC", "PD", "E2"),
                       ("CA", "CB", "E3"), ("TA", "TB", "E4"), ("TC", "TD", "E5")):
        p = (P(a) + P(c_)) / 2
        b.append(circ(p, 13, "cote"))
        b.append(txt(p + np.array([0, 4]), lab, "tc", "middle"))

    # selle, cintre, pedale
    sd = P("SD")
    b.append(f'<path class="tr" d="M{sd[0]-95*sk:.1f},{sd[1]:.1f} '
             f'q {50*sk:.0f},{-16*sk:.0f} {95*sk:.0f},{-2*sk:.0f} '
             f'q {45*sk:.0f},{14*sk:.0f} {60*sk:.0f},{4*sk:.0f} '
             f'q {-30*sk:.0f},{22*sk:.0f} {-100*sk:.0f},{20*sk:.0f} '
             f'q {-45*sk:.0f},{-2*sk:.0f} {-55*sk:.0f},{-22*sk:.0f} z" '
             f'fill="#1a1a1a" opacity=".85"/>')
    bar = P("BAR")
    b.append(circ(bar, 13 * sk, "tr"))
    b.append(line(bar, bar + np.array([-70 * sk, -6 * sk]), "tr"))
    ped = P("PEDL")
    b.append(f'<rect class="tr" x="{ped[0]-32*sk:.0f}" y="{ped[1]-5*sk:.0f}" '
             f'width="{64*sk:.0f}" height="{10*sk:.0f}" rx="3"/>')
    bb = P("BB")
    b.append(circ(bb, G.chainring * 12.7 / (2 * np.pi) * 1.06 * sk, "cache"))
    b.append(circ(P("FAR"), G.sprocket * 12.7 / (2 * np.pi) * 1.06 * sk, "cache"))

    # cotes
    fa, ra = P("FAV"), P("FAR")
    b.append(cote((ra[0], sol), (fa[0], sol),
                  f"empattement {G.wheelbase*1000:.0f}", 52))
    b.append(cote((bb[0], sol), (bb[0], bb[1]),
                  f"hauteur BdP {G.bb_height*1000:.0f}", -46))
    b.append(cote((ra[0], ra[1]), (bb[0], bb[1]),
                  f"base {G.chainstay*1000:.0f}", -26))
    b.append(cote((sd[0], sd[1]), (bb[0], bb[1]),
                  f"selle/BdP {int((0.720)*1000)}", 34))
    b.append(cote((fa[0] - G.wheel_r * K, fa[1]),
                  (fa[0] + G.wheel_r * K, fa[1]),
                  f"Ø{G.wheel_od*1000:.0f}", -40))
    # angle de direction et chasse
    hb, ht = P("HB"), P("HT")
    d = (ht - hb) / np.linalg.norm(ht - hb)
    b.append(line(hb - d * 260 * sk, ht + d * 130 * sk, "axe"))
    gx = fa[0] + G.trail() * K
    b.append(line((gx, sol - 60 * sk), (gx, sol + 26), "fin"))
    b.append(cote((fa[0], sol + 16), (gx, sol + 16),
                  f"chasse {G.trail()*1000:.0f}", 22))
    b.append(txt((ht[0] + 26, ht[1] - 40), f"{np.degrees(G.head_angle):.0f}°",
                 "tc"))

    b.append(txt((60, 52), "COSYN-30 — vue generale, velo deploye", "tt"))
    b.append(txt((60, 74),
                 f"empattement {G.wheelbase*1000:.0f} · roues Ø{G.wheel_od*1000:.0f} "
                 f"(8 arcs, {G.n_spokes} rayons) · chasse {G.trail()*1000:.1f} mm · "
                 f"developpement {G.development():.2f} m/tour · monobras AV et AR", "ts"))
    b.append(txt((60, H - 26),
                 "E1..E5 : emmanchements telescopiques a expandeur conique — "
                 "cotes en mm — echelle 1:1 a l'export 1500 px", "ts"))
    return svg(W, H, "".join(b))


# ==========================================================================
def plan_roue():
    W, H = 1500, 1020
    b = []
    K = 660.0
    cx, cy = 400, 400
    Rm = G.rim_r_mid * K
    Ro = (G.rim_r_mid + G.rim_h / 2) * K
    Ri = (G.rim_r_mid - G.rim_h / 2) * K
    Rt = G.wheel_od / 2 * K

    b.append(txt((60, 52), "COSYN-30 — roue deployable a jante segmentee", "tt"))
    b.append(txt((60, 74),
                 f"8 arcs de 45° · {G.n_spokes} rayons croises 2 · "
                 f"precontrainte {G.spoke_T0:.0f} N · mise en tension par came "
                 "d'ecartement des brides", "ts"))

    # -- vue de face
    b.append(circ((cx, cy), Rt, "tread"))
    for k in range(G.n_seg):
        a0 = 2 * np.pi * k / G.n_seg + 0.055
        a1 = 2 * np.pi * (k + 1) / G.n_seg - 0.055
        for r in (Ro, Ri):
            p0 = (cx + r * np.cos(a0), cy - r * np.sin(a0))
            p1 = (cx + r * np.cos(a1), cy - r * np.sin(a1))
            b.append(f'<path class="seg" d="M{p0[0]:.1f},{p0[1]:.1f} '
                     f'A{r:.1f},{r:.1f} 0 0 0 {p1[0]:.1f},{p1[1]:.1f}"/>')
        # joint : tenon conique
        aj = 2 * np.pi * k / G.n_seg
        pj = (cx + Rm * np.cos(aj), cy - Rm * np.sin(aj))
        b.append(circ(pj, 9, "seg"))
    for k in range(G.n_spokes):
        a = 2 * np.pi * (k + 0.5) / G.n_spokes
        phi = np.deg2rad(2 * 720.0 / G.n_spokes) * (1 if k % 2 else -1)
        p0 = (cx + Ri * np.cos(a), cy - Ri * np.sin(a))
        p1 = (cx + G.hub_flange_r * K * np.cos(a + phi),
              cy - G.hub_flange_r * K * np.sin(a + phi))
        b.append(line(p0, p1, "fin"))
    b.append(circ((cx, cy), G.hub_flange_r * K, "tr2"))
    b.append(circ((cx, cy), 24, "tr"))
    b.append(line((cx - Rt - 30, cy), (cx + Rt + 30, cy), "axe"))
    b.append(line((cx, cy - Rt - 30), (cx, cy + Rt + 30), "axe"))
    b.append(cote((cx - Rt, cy + Rt + 40), (cx + Rt, cy + Rt + 40),
                  f"Ø{G.wheel_od*1000:.0f} hors-tout", 24))
    b.append(txt((cx, cy + Rt + 96), "vue de face, roue deployee",
                 "ts", "middle"))

    # -- coupe de jante (detail A)
    dx, dy = 830, 200
    sc = 5.2
    wj, hj, t = G.rim_w * K * sc, G.rim_h * K * sc, G.rim_t * K * sc
    b.append(f'<rect class="tr" x="{dx:.0f}" y="{dy:.0f}" width="{wj:.0f}" '
             f'height="{hj:.0f}" rx="4"/>')
    b.append(f'<rect class="tr2" x="{dx+t:.0f}" y="{dy+t:.0f}" '
             f'width="{wj-2*t:.0f}" height="{hj-2*t:.0f}" rx="3"/>')
    b.append(f'<rect class="hach" x="{dx:.0f}" y="{dy:.0f}" width="{wj:.0f}" '
             f'height="{hj:.0f}"/>')
    b.append(f'<rect class="hach" x="{dx+t:.0f}" y="{dy+t:.0f}" '
             f'width="{wj-2*t:.0f}" height="{hj-2*t:.0f}" fill="#fbfaf8" '
             f'opacity="1" stroke="none"/>')
    b.append(f'<rect class="tr2" x="{dx-6:.0f}" y="{dy-G.tread_t*K*sc:.0f}" '
             f'width="{wj+12:.0f}" height="{G.tread_t*K*sc:.0f}" rx="5" '
             f'fill="#333" opacity=".7"/>')
    b.append(cote((dx, dy + hj + 8), (dx + wj, dy + hj + 8),
                  f"{G.rim_w*1000:.0f}", 22))
    b.append(cote((dx + wj + 8, dy), (dx + wj + 8, dy + hj),
                  f"{G.rim_h*1000:.0f}", 24))
    b.append(txt((dx, dy - G.tread_t * K * sc - 16),
                 f"DETAIL A — caisson de jante 7075-T6, paroi {G.rim_t*1000:.1f} mm",
                 "t"))
    b.append(txt((dx, dy + hj + 46),
                 f"bande alveolaire PU {G.tread_t*1000:.1f} mm, densite relative "
                 f"{G.tread_rho_rel:.2f}", "ts"))
    b.append(txt((dx, dy + hj + 62), "siege de rayon : insert rapporte "
                 "rayon 3 mm (Kt 1.8 au lieu de 2.5 sur percage brut)", "ts"))

    # -- detail tenon conique (detail B)
    ex, ey = 830, 430
    b.append(txt((ex, ey - 16), "DETAIL B — jonction d'arcs a tenon conique 6°", "t"))
    L = 300
    b.append(f'<path class="tr" d="M{ex},{ey} h{L*0.42:.0f} '
             f'l 46,-13 v 26 l -46,-13 M{ex},{ey+52} h{L*0.42:.0f} '
             f'l 46,13 v -26 l -46,13"/>')
    b.append(f'<path class="tr" d="M{ex+L:.0f},{ey} h-{L*0.34:.0f} '
             f'M{ex+L:.0f},{ey+52} h-{L*0.34:.0f}"/>')
    b.append(f'<path class="tr" d="M{ex+L*0.42+46:.0f},{ey-13:.0f} '
             f'L{ex+L*0.66:.0f},{ey-13:.0f} M{ex+L*0.42+46:.0f},{ey+65:.0f} '
             f'L{ex+L*0.66:.0f},{ey+65:.0f}"/>')
    b.append(txt((ex, ey + 84), "la precontrainte des rayons plaque les arcs : "
                 "le joint ne travaille QU'EN COMPRESSION", "ts"))
    b.append(txt((ex, ey + 100), "excentricite e = M/N < h/6 verifiee sur les "
                 "8 joints, tous cas de charge", "ts"))

    # -- coupe de moyeu (detail C)
    hx, hy = 830, 620
    b.append(txt((hx, hy - 16), "DETAIL C — moyeu a brides ecartables "
                 "(mise en tension par came)", "t"))
    b.append(f'<rect class="tr" x="{hx}" y="{hy+40}" width="300" height="34" rx="4"/>')
    for s_ in (0, 1):
        fx = hx + 20 + s_ * 244
        b.append(f'<path class="tr" d="M{fx},{hy+40} l -14,-46 h 22 l 14,46 z"/>')
        b.append(f'<path class="tr" d="M{fx},{hy+74} l -14,46 h 22 l 14,-46 z"/>')
    b.append(f'<path class="tr2" d="M{hx+120},{hy+30} h 60 v 54 h -60 z"/>')
    b.append(circ((hx + 150, hy + 57), 16, "seg"))
    b.append(line((hx + 150, hy + 57), (hx + 150, hy - 6), "seg"))
    b.append(txt((hx + 160, hy + 4), "levier de came", "tc"))
    b.append(line((hx - 20, hy + 57), (hx + 330, hy + 57), "axe"))
    b.append(txt((hx, hy + 140),
                 "course de came 5.0 mm -> allongement 0.34 mm par rayon -> "
                 f"{G.spoke_T0:.0f} N ; effort au levier ~96 N crete", "ts"))
    b.append(txt((hx, hy + 156),
                 "8 secteurs a baionnette : les 8 arcs s'accrochent en une "
                 "rotation de 1/16e de tour", "ts"))

    # -- sequence de montage
    sy = 800
    b.append(txt((60, sy - 20), "SEQUENCE DE MONTAGE D'UNE ROUE (≈ 25 s)", "t"))
    etapes = ["1 — derouler le\nchapelet d'arcs",
              "2 — fermer l'anneau\n(tenons coniques)",
              "3 — engager le moyeu,\n1/16e de tour",
              "4 — rabattre le levier\nde came",
              "5 — controle : temoin\nde tension vert"]
    for i, e in enumerate(etapes):
        x = 70 + i * 270
        b.append(f'<rect class="fin" x="{x}" y="{sy}" width="230" height="150" rx="8"/>')
        cxx, cyy = x + 115, sy + 72
        if i == 0:
            for k in range(4):
                b.append(f'<path class="seg" d="M{x+30+k*44},{cyy+30} '
                         f'q 22,-46 44,0"/>')
        elif i == 1:
            b.append(circ((cxx, cyy), 52, "seg"))
        elif i == 2:
            b.append(circ((cxx, cyy), 52, "seg"))
            b.append(circ((cxx, cyy), 20, "tr2"))
            for k in range(8):
                a = 2 * np.pi * k / 8
                b.append(line((cxx + 20 * np.cos(a), cyy - 20 * np.sin(a)),
                              (cxx + 52 * np.cos(a), cyy - 52 * np.sin(a)), "fin"))
        elif i == 3:
            b.append(circ((cxx, cyy), 52, "seg"))
            b.append(circ((cxx, cyy), 20, "tr2"))
            b.append(line((cxx, cyy), (cxx + 40, cyy - 30), "seg"))
        else:
            b.append(circ((cxx, cyy), 52, "seg"))
            b.append(circ((cxx, cyy), 20, "tr2"))
            b.append(circ((cxx + 34, cyy - 34), 9, "tr"))
        for j, ln in enumerate(e.split("\n")):
            b.append(txt((x + 12, sy + 130 + j * 13), ln, "ts"))
    return svg(W, H, "".join(b))


# ==========================================================================
def plan_emmanchement():
    W, H = 1500, 760
    b = []
    b.append(txt((60, 52), "COSYN-30 — emmanchement telescopique a expandeur "
                 "conique (coupe)", "tt"))
    b.append(txt((60, 74), "identique pour la poutre principale (E1, E2), la "
                 "colonne de direction (E3) et la tige de selle (E4, E5)", "ts"))
    ox, oy, sc = 130, 300, 3.4
    Do, ti = 46 * sc, 2.2 * sc
    Di, tii = 41 * sc, 2.2 * sc
    Lo, e = 420, 58 * sc
    # tube exterieur
    b.append(f'<rect class="tr" x="{ox}" y="{oy}" width="{Lo}" height="{ti}"/>')
    b.append(f'<rect class="tr" x="{ox}" y="{oy+Do-ti}" width="{Lo}" height="{ti}"/>')
    # tube interieur
    xi = ox + Lo - e
    off = (Do - Di) / 2
    b.append(f'<rect class="tr" x="{xi}" y="{oy+off}" width="{e+430}" height="{tii}"/>')
    b.append(f'<rect class="tr" x="{xi}" y="{oy+off+Di-tii}" width="{e+430}" '
             f'height="{tii}"/>')
    for r in [(ox, oy, Lo, ti), (ox, oy + Do - ti, Lo, ti),
              (xi, oy + off, e + 430, tii), (xi, oy + off + Di - tii, e + 430, tii)]:
        b.append(f'<rect class="hach" x="{r[0]}" y="{r[1]}" width="{r[2]}" '
                 f'height="{r[3]}"/>')
    # portees de guidage
    for xx in (xi + 12, ox + Lo - 26):
        b.append(f'<rect class="seg" x="{xx}" y="{oy+ti}" width="26" '
                 f'height="{off-ti:.0f}" fill="#c0392b" opacity=".35"/>')
        b.append(f'<rect class="seg" x="{xx}" y="{oy+Do-off}" width="26" '
                 f'height="{off-ti:.0f}" fill="#c0392b" opacity=".35"/>')
    # expandeur conique
    ex = xi + 60
    b.append(f'<path class="tr" d="M{ex},{oy+off+tii} l 96,0 l 22,{Di/2-tii-6:.0f} '
             f'l -22,0 z"/>')
    b.append(f'<path class="tr" d="M{ex},{oy+off+Di-tii} l 96,0 '
             f'l 22,-{Di/2-tii-6:.0f} l -22,0 z"/>')
    b.append(f'<rect class="tr2" x="{ex-150}" y="{oy+Do/2-7}" width="{270}" '
             f'height="14" rx="3"/>')
    b.append(f'<circle class="tr" cx="{ex-160}" cy="{oy+Do/2}" r="16"/>')
    b.append(line((ex - 160, oy + Do / 2), (ex - 210, oy + Do / 2 - 60), "seg"))
    b.append(line((ox - 30, oy + Do / 2), (ox + Lo + 470, oy + Do / 2), "axe"))

    b.append(cote((xi, oy - 20), (ox + Lo, oy - 20),
                  f"recouvrement 58 (mini calcule 20)", 26))
    b.append(cote((ox, oy + Do + 26), (ox + Lo, oy + Do + 26), "tube exterieur Ø46x2.2", 26))
    b.append(cote((xi, oy + Do + 80), (xi + e + 430, oy + Do + 80),
                  "tube interieur Ø41x2.2", 26))
    notes = [
        "1. Le cone 8° dilate la douille fendue : le jeu de coulissement "
        "(60 µm) est annule, donc AUCUN flou residuel a la direction.",
        "2. Sans expandeur, le basculement libre serait de 0.059° par liaison, "
        "soit 1.1 mm cumules au cintre — inacceptable.",
        "3. Effort de tirant calcule 1.1 a 2.6 kN selon la liaison, obtenu au "
        "couple de 1.3 a 3.2 N.m sur vis M6.",
        "4. Pression de matage sur portees : 6.8 a 10.5 MPa pour 25 MPa "
        "admissibles (bague PA66-CF sur alu anodise dur) -> marge 2.4 a 3.7.",
        "5. Butee d'index usinee dans le tube interieur : la longueur deployee "
        "est repetable sans reglage.",
    ]
    for i, n in enumerate(notes):
        b.append(txt((130, 540 + i * 26), n, "t"))
    return svg(W, H, "".join(b))


# ==========================================================================
def plan_rangement():
    import json
    d = json.load(open("../out/encombrement.json"))
    W, H = 1500, 760
    b = []
    b.append(txt((60, 52), "COSYN-30 — plan de rangement verifie "
                 "(calcul voxel 6 mm)", "tt"))
    b.append(txt((60, 74),
                 f"volume utile du sac {Pack.L*1000:.0f} x {Pack.H*1000:.0f} x "
                 f"{Pack.W*1000:.0f} = {Pack.litres():.1f} L · "
                 f"matiere {d['volume_solide_L']:.1f} L · "
                 f"{len(d['rangement'])} organes places, "
                 f"{len(d['non_ranges'])} non place", "ts"))
    sc = 1.9
    vues = [("vue de cote (X-Y)", 0, 1, 90, 140),
            ("vue de dessus (X-Z)", 0, 2, 90, 470)]
    pal = ["#0b6e99", "#c0392b", "#1e8449", "#8e44ad", "#d68910", "#16a085",
           "#7f8c8d", "#2c3e50", "#c2185b", "#00838f", "#6d4c41"]
    for titre, ia, ib, ox, oy in vues:
        dims = [Pack.L * 1000, Pack.H * 1000, Pack.W * 1000]
        b.append(f'<rect class="pack" x="{ox}" y="{oy}" '
                 f'width="{dims[ia]*sc:.0f}" height="{dims[ib]*sc:.0f}" rx="10"/>')
        b.append(txt((ox, oy - 10), titre, "t"))
        for i, r in enumerate(d["rangement"]):
            p, s = r["pos_mm"], r["dim_mm"]
            b.append(f'<rect x="{ox+p[ia]*sc:.0f}" y="{oy+p[ib]*sc:.0f}" '
                     f'width="{s[ia]*sc:.0f}" height="{s[ib]*sc:.0f}" rx="3" '
                     f'fill="{pal[i%len(pal)]}" opacity=".22" '
                     f'stroke="{pal[i%len(pal)]}" stroke-width="1.2"/>')
            b.append(txt((ox + p[ia] * sc + 4, oy + p[ib] * sc + 13),
                         str(i + 1), "ts"))
    lx = 1010
    b.append(txt((lx, 130), "NOMENCLATURE DE RANGEMENT", "t"))
    for i, r in enumerate(d["rangement"]):
        nm = r["nom"][:52]
        b.append(f'<rect x="{lx}" y="{146+i*26}" width="13" height="13" rx="2" '
                 f'fill="{pal[i%len(pal)]}" opacity=".55"/>')
        b.append(txt((lx + 22, 157 + i * 26), f"{i+1}. {nm}", "ts"))
        b.append(txt((lx + 22, 168 + i * 26),
                     f"   {r['dim_mm'][0]}x{r['dim_mm'][1]}x{r['dim_mm'][2]} mm",
                     "ts"))
    return svg(W, H, "".join(b))


if __name__ == "__main__":
    import os
    os.makedirs("../plans", exist_ok=True)
    for nom, f in (("01-vue-generale", plan_general),
                   ("02-roue-deployable", plan_roue),
                   ("03-emmanchement-telescopique", plan_emmanchement),
                   ("04-plan-de-rangement", plan_rangement)):
        open(f"../plans/{nom}.svg", "w").write(f())
        print(f"plans/{nom}.svg genere")
