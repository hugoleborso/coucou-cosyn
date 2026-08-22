"""
COSYN-30 -- VERIFICATION D'ENCOMBREMENT dans un sac a dos 30 L compact.

Methode : chaque organe replie est decrit par une union de primitives
(boites et cylindres) dans son repere propre, voxelise au pas de 5 mm, puis
place dans le volume utile du sac par un algorithme glouton "premier creux"
teste sur les 24 orientations axiales. On obtient :
  - la faisabilite reelle du rangement (et non une simple somme de volumes),
  - le taux de remplissage,
  - une coupe de rangement exploitable pour dessiner la mousse de calage.
"""
from __future__ import annotations
import json
import numpy as np

from params import Geo as G, Pack

VOX = 0.006          # pas de voxelisation [m]


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------
def box(c, dims):
    return ("box", np.array(c, float), np.array(dims, float))


def cyl(p1, p2, d):
    return ("cyl", np.array(p1, float), np.array(p2, float), d)


def _rot(p, ang, axis=2):
    c, s = np.cos(ang), np.sin(ang)
    R = np.eye(3)
    i, j = [(1, 2), (2, 0), (0, 1)][axis]
    R[i, i] = c; R[i, j] = -s; R[j, i] = s; R[j, j] = c
    if p[0] == "box":
        # une boite tournee est re-encadree par sa boite englobante (conservatif)
        d = p[2].copy()
        di = abs(c) * d[i] + abs(s) * d[j]
        dj = abs(s) * d[i] + abs(c) * d[j]
        d[i], d[j] = di, dj
        return ("box", R @ p[1], d)
    return ("cyl", R @ p[1], R @ p[2], p[3])


class Part:
    def __init__(self, name, prims, essential=True):
        self.name = name
        self.prims = prims
        self.essential = essential
        self.grid = self._voxelise()

    def rotated(self, deg, axis=2):
        a = np.deg2rad(deg)
        return Part(f"{self.name} [oblique {deg:+.0f} deg/ax{axis}]",
                    [_rot(p, a, axis) for p in self.prims], self.essential)

    def _bounds(self):
        pts = []
        for p in self.prims:
            if p[0] == "box":
                pts += [p[1] - p[2] / 2, p[1] + p[2] / 2]
            else:
                r = p[3] / 2
                ax = p[2] - p[1]
                nax = np.linalg.norm(ax)
                ext = r * np.sqrt(np.maximum(1 - (ax / nax) ** 2, 0))
                pts += [p[1] - ext, p[1] + ext, p[2] - ext, p[2] + ext]
        pts = np.array(pts)
        return pts.min(axis=0), pts.max(axis=0)

    def _voxelise(self):
        lo, hi = self._bounds()
        n = np.maximum(np.ceil((hi - lo) / VOX).astype(int), 1)
        g = np.zeros(n, bool)
        ix, iy, iz = np.indices(n)
        pts = lo + (np.stack([ix, iy, iz], -1) + 0.5) * VOX
        for p in self.prims:
            if p[0] == "box":
                d = np.abs(pts - p[1]) - p[2] / 2
                g |= np.all(d <= 0, axis=-1)
            else:
                a, b, r = p[1], p[2], p[3] / 2
                ab = b - a
                L2 = float(ab @ ab)
                t = ((pts - a) @ ab) / L2
                proj = a + np.clip(t, 0, 1)[..., None] * ab
                g |= (np.linalg.norm(pts - proj, axis=-1) <= r) & (t >= 0) & (t <= 1)
        return g

    @property
    def volume(self):
        return self.grid.sum() * VOX ** 3

    @property
    def bbox_mm(self):
        return np.array(self.grid.shape) * VOX * 1e3


# --------------------------------------------------------------------------
# Definition des organes replies
# --------------------------------------------------------------------------
def parts():
    P = []
    Rout = G.rim_r_mid + G.rim_h / 2 + G.tread_t
    a = np.pi / G.n_seg
    h_arc = Rout * (1 - np.cos(a)) + G.rim_h + G.tread_t
    pas = G.tread_w + 0.002
    larg = G.n_seg * pas

    # --- fagots de jante : 6 arcs cote a cote, enfiles sur le cordon captif
    # les 8 arcs se rangent en DEUX rangees de 4 : le fagot devient carre,
    # ce qui pave nettement mieux la section du sac qu'une rangee de 8.
    # Le cordon captif autorise a plier les 8 arcs en DEUX demi-fagots de 4 :
    # deux paquets plats se rangent bien mieux qu'un seul bloc.
    n_rang = 1
    n_col = 4
    for cote in ("AV-a", "AV-b", "AR-a", "AR-b"):
        prims = []
        for k in range(4):
            col, rang = k % n_col, k // n_col
            y = -(n_col * pas) / 2 + (col + 0.5) * pas
            dz_rang = (rang - (n_rang - 1) / 2) * (G.rim_h + G.tread_t + 0.002)
            for i in range(9):
                th = -a + 2 * a * (i + 0.5) / 9
                x = Rout * np.sin(th)
                z = (Rout * (np.cos(th) - np.cos(a)) - h_arc / 2
                     + (G.rim_h + G.tread_t) / 2 + dz_rang)
                prims.append(box((x, y, z),
                                 (2 * Rout * np.sin(a / 9) * 1.2, G.tread_w,
                                  G.rim_h + G.tread_t)))
        # secteurs de moyeu + rayons rabattus au creux du fagot
        prims.append(box((0, 0, -h_arc / 2 + 0.040),
                         (0.110, n_col * pas * 0.85, 0.020)))
        P.append(Part(f"Demi-fagot de jante {cote} (4 arcs + rayons captifs)",
                      prims))

    # --- moyeux (le disque reste solidaire)
    for cote in ("AV", "AR"):
        P.append(Part(f"Moyeu a secteurs + disque {cote}",
                      [cyl((0, 0, 0.000), (0, 0, 0.058), 0.070),
                       cyl((0, 0, 0.058), (0, 0, 0.062), 0.140),
                       cyl((0, 0, 0.062), (0, 0, 0.098), 0.048)]))

    # --- module arriere : mat ET manivelles rabattus VERS L'ARRIERE
    cs = G.chainstay
    # module arriere MONOBRANCHE : un seul bras (gauche), mat rabattu vers l'arriere
    P.append(Part("Module arriere (BdP, bras monobranche, mat rabattu, pedalier)", [
        cyl((0, -0.045, 0), (0, 0.045, 0), 0.042),
        cyl((0, 0.058, 0), (-cs, 0.058, 0.004), 0.038),
        cyl((-0.02, 0.052, 0.036), (-cs + 0.01, 0.052, 0.024), 0.026),
        cyl((-0.015, 0, 0.040), (-0.300, 0, 0.040), 0.042),
        cyl((0, -0.047, 0), (0, -0.052, 0), 0.147),
        cyl((-cs, 0.040, 0.004), (-cs, 0.085, 0.004), 0.048),
    ]))

    # Manivelles DEMONTABLES (vis auto-extractibles) : sans elles la section
    # du module arriere passe de 174 x 156 a 120 x 147 mm, ce qui debloque
    # le pavage de la section du sac (cf. commentaire d'etude).
    P.append(Part("Manivelles + pedales pliantes (demontees)", [
        cyl((0, 0.030, 0), (0.152, 0.030, 0), 0.024),
        cyl((0, -0.030, 0), (0.152, -0.030, 0), 0.024),
        box((0.150, 0.030, 0), (0.060, 0.035, 0.030)),
        box((0.150, -0.030, 0), (0.060, 0.035, 0.030)),
    ]))

    # --- module avant : fourche + tube de direction (colonne retiree)
    d = G.steer_dir()
    # module avant MONOBRAS : une seule jambe (droite) + tube de direction
    P.append(Part("Module avant (fourche monobras + tube de direction)", [
        cyl((0, -0.050, 0), (0.141, -0.050, -0.280), 0.046),
        cyl((0, 0, -0.010), (d[0] * (G.head_tube_len + 0.02), 0,
                             d[2] * (G.head_tube_len + 0.02)), 0.046),
        cyl((0.141, -0.072, -0.280), (0.141, -0.028, -0.280), 0.048),
    ]))

    # --- ensemble cintre : colonne + 2 demi-cintres replies + leviers
    P.append(Part("Ensemble cintre (colonne + demi-cintres + leviers)", [
        cyl((0, 0, 0), (0.285, 0, 0), 0.034),
        cyl((0.255, 0.018, 0.028), (0.045, 0.060, 0.028), 0.026),
        cyl((0.255, -0.018, 0.028), (0.045, -0.060, 0.028), 0.026),
        box((0.060, 0.055, 0.028), (0.070, 0.040, 0.045)),
        box((0.060, -0.055, 0.028), (0.070, 0.040, 0.045)),
    ]))

    P.append(Part("Poutre principale retractee",
                  [cyl((0, 0, 0), (0.233, 0, 0), 0.048)]))
    P.append(Part("Tige de selle retractee + selle rabattue",
                  [cyl((0, 0, 0), (0.206, 0, 0), 0.042),
                   box((0.120, 0, 0.045), (0.250, 0.140, 0.045))]))
    P.append(Part("Trousse (outils, pompe, sangles)",
                  [box((0, 0, 0), (0.190, 0.075, 0.045))], essential=False))
    return P


ORIENTATIONS = []
for axes in [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]:
    for fl in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]:
        ORIENTATIONS.append((axes, fl))


def oriented(grid, o):
    axes, fl = o
    g = np.transpose(grid, axes)
    for i, f in enumerate(fl):
        if f:
            g = np.flip(g, i)
    return g


OBLIQUES = [(d, ax) for ax in (2, 1, 0) for d in (20, -20, 30, -30, 40, -40)]


def _first_fit(occ, g, n, stride=2):
    s = np.array(g.shape)
    if np.any(s > n):
        return None
    lim = n - s + 1
    for k in range(0, lim[2], stride):
        for j in range(0, lim[1], stride):
            for i in range(0, lim[0], stride):
                if not np.any(occ[i:i + s[0], j:j + s[1], k:k + s[2]] & g):
                    return (i, j, k), s
    return None


def _dedupe(grids):
    out, seen = [], set()
    for key, g in grids:
        h = (g.shape, g.tobytes())
        if h in seen:
            continue
        seen.add(h)
        out.append((key, g))
    return out


def _densite(q):
    return q.volume / (np.prod(q.bbox_mm) / 1e9)


ORDRES = {
    "encombrant d'abord": lambda q: -float(np.prod(q.bbox_mm)),
    "le plus long d'abord": lambda q: -float(max(q.bbox_mm)),
    "compact d'abord": lambda q: (0 if _densite(q) >= 0.40 else 1,
                                  -float(np.prod(q.bbox_mm))),
    "long puis compact": lambda q: (0 if max(q.bbox_mm) > 400 else 1,
                                    -float(np.prod(q.bbox_mm))),
}


def pack_multi(parts_list, container_mm):
    """Multi-depart : on essaie plusieurs ordres de rangement et on garde le
    premier qui range tout (a defaut, celui qui laisse le moins d'organes)."""
    best = None
    for nom, cle in ORDRES.items():
        r = pack(sorted(parts_list, key=cle), container_mm)
        if not r[2]:
            return r + (nom,)
        if best is None or len(r[2]) < len(best[2]):
            best, bnom = r, nom
    return best + (bnom,)


def pack(parts_list, container_mm):
    """Rangement par 'meilleur ajustement' : pour chaque organe on essaie toutes
    les orientations axiales (24) plus, si necessaire, des poses obliques, et on
    retient celle qui minimise la hauteur de pile occupee (puis le volume de la
    boite englobante). Les organes les plus encombrants sont places en premier."""
    n = np.ceil(np.array(container_mm) / 1e3 / VOX).astype(int)
    occ = np.zeros(n, bool)
    placed, failed = [], []
    ordre = list(parts_list)
    for p in ordre:
        best = None
        for essai in (0, 1):
            variantes = [((0, 0), p)] if essai == 0 else \
                [((d, ax), p.rotated(d, ax)) for d, ax in OBLIQUES]
            cands = _dedupe([((ang, o), oriented(pv.grid, o))
                             for ang, pv in variantes for o in ORIENTATIONS])
            for (ang, o), g in cands:
                r = _first_fit(occ, g, n)
                if r is None:
                    continue
                pos, s = r
                score = (pos[2] + s[2], pos[1] + s[1], pos[0] + s[0])
                if best is None or score < best[0]:
                    best = (score, pos, s, g, o, ang,
                            p.name if ang == (0, 0) else
                            f"{p.name} [oblique {ang[0]:+.0f} deg]")
            if best is not None:
                break
        if best is None:
            failed.append(p.name)
            continue
        _, pos, s, g, o, ang, nm = best
        i, j, k = pos
        occ[i:i + s[0], j:j + s[1], k:k + s[2]] |= g
        placed.append((nm, pos, s, o))
    return occ, placed, failed


def main():
    P = parts()
    print("=" * 96)
    print("ENCOMBREMENT -- organes replies")
    print("=" * 96)
    print(f"{'organe':<48}{'encombrement (mm)':>26}{'volume solide':>14}"
          f"{'remplissage':>13}")
    Vtot = 0.0
    for p in P:
        b = p.bbox_mm
        Vtot += p.volume
        print(f"{p.name:<48}{b[0]:8.0f} x{b[1]:6.0f} x{b[2]:6.0f}"
              f"{p.volume*1e3:12.2f} L{100*p.volume/(np.prod(b)/1e9):11.0f} %")
    print("-" * 96)
    print(f"{'VOLUME SOLIDE CUMULE':<48}{'':26}{Vtot*1e3:12.2f} L")

    for name, dims in (("sac 30 L compact (volume utile)",
                        (Pack.L * 1e3, Pack.H * 1e3, Pack.W * 1e3)),):
        occ, placed, failed, ordre_nom = pack_multi(P, dims)
        Vc = np.prod(dims) / 1e9
        print(f"\nStrategie de rangement retenue : {ordre_nom}")
        print(f"Rangement dans {name} : "
              f"{dims[0]:.0f} x {dims[1]:.0f} x {dims[2]:.0f} mm = {Vc*1e3:.1f} L")
        print(f"  taux de remplissage solide : {100*Vtot/Vc:.0f} %")
        if failed:
            print(f"  NON RANGES : {failed}")
        else:
            print("  tous les organes sont ranges")
        occ_frac = occ.sum() / occ.size
        print(f"  voxels occupes             : {100*occ_frac:.0f} %")
        # hauteur reellement utilisee
        used = np.argwhere(occ)
        ext = (used.max(axis=0) + 1) * VOX * 1e3
        print(f"  volume reellement occupe   : {ext[0]:.0f} x {ext[1]:.0f} "
              f"x {ext[2]:.0f} mm = {np.prod(ext)/1e6:.1f} L")

    print("\nPlan de rangement (coin bas-avant du sac, cotes en mm)")
    print(f"{'organe':<48}{'x':>7}{'y':>7}{'z':>7}{'dx':>7}{'dy':>7}{'dz':>7}")
    for nm, pos, s, o in placed:
        print(f"{nm:<48}{pos[0]*5:7.0f}{pos[1]*5:7.0f}{pos[2]*5:7.0f}"
              f"{s[0]*5:7.0f}{s[1]*5:7.0f}{s[2]*5:7.0f}")

    with open("../out/encombrement.json", "w") as f:
        json.dump(dict(organes=[dict(nom=p.name, bbox_mm=list(p.bbox_mm),
                                     volume_L=p.volume * 1e3) for p in P],
                       volume_solide_L=Vtot * 1e3,
                       sac_L=Pack.litres(),
                       rangement=[dict(nom=nm, pos_mm=[int(x) * 5 for x in pos],
                                       dim_mm=[int(x) * 5 for x in s])
                                  for nm, pos, s, o in placed],
                       non_ranges=failed), f, indent=1, default=float)


if __name__ == "__main__":
    main()
