"""
Mini solveur elements finis 3D (poutres + barres) ecrit pour le projet COSYN-30.

Contenu
-------
- Element POUTRE 3D Euler-Bernoulli, 12 ddl, avec relachements d'extremite
  (rotules) traites par condensation statique.
- Element BARRE 3D (2 noeuds, 6 ddl) avec precontrainte et option "tension only"
  (indispensable pour les rayons d'une roue a rayons tendus).
- Assemblage creux, conditions limites par penalisation propre (elimination),
  post-traitement des efforts internes en repere local.

Conventions
-----------
Unites SI strictes : m, N, Pa, kg.
DDL par noeud : [ux, uy, uz, rx, ry, rz].
"""

from __future__ import annotations

import numpy as np

DOF_PER_NODE = 6


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------
class Section:
    """Section droite. Tube circulaire, tube rectangulaire ou section pleine."""

    def __init__(self, name, A, Iy, Iz, J, ymax, zmax, rho, mat):
        self.name = name
        self.A = A          # aire [m2]
        self.Iy = Iy        # inertie flexion autour de y local [m4]
        self.Iz = Iz        # inertie flexion autour de z local [m4]
        self.J = J          # inertie de torsion [m4]
        self.ymax = ymax    # distance fibre extreme selon y [m]
        self.zmax = zmax    # distance fibre extreme selon z [m]
        self.rho = rho      # masse volumique [kg/m3]
        self.mat = mat      # dict materiau

    @property
    def mass_per_m(self):
        return self.A * self.rho

    @staticmethod
    def tube(name, od, t, mat):
        """Tube circulaire : od = diametre exterieur, t = epaisseur."""
        ri = od / 2 - t
        ro = od / 2
        A = np.pi * (ro ** 2 - ri ** 2)
        I = np.pi / 4 * (ro ** 4 - ri ** 4)
        J = 2 * I
        return Section(name, A, I, I, J, ro, ro, mat["rho"], mat)

    @staticmethod
    def rect_tube(name, b, h, t, mat):
        """Tube rectangulaire : b = largeur (selon y), h = hauteur (selon z)."""
        A = b * h - (b - 2 * t) * (h - 2 * t)
        Iz = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12      # flexion /z ... depth h
        Iy = (h * b ** 3 - (h - 2 * t) * (b - 2 * t) ** 3) / 12
        # Torsion Bredt (paroi mince, section fermee)
        bm, hm = b - t, h - t
        Am = bm * hm
        peri = 2 * (bm + hm)
        J = 4 * Am ** 2 * t / peri
        return Section(name, A, Iy, Iz, J, b / 2, h / 2, mat["rho"], mat)

    @staticmethod
    def solid_round(name, d, mat):
        A = np.pi * d ** 2 / 4
        I = np.pi * d ** 4 / 64
        return Section(name, A, I, I, 2 * I, d / 2, d / 2, mat["rho"], mat)


# --------------------------------------------------------------------------
# Modele
# --------------------------------------------------------------------------
class Model:
    def __init__(self):
        self.nodes = {}        # name -> np.array(3)
        self.order = []        # ordre d'insertion
        self.beams = []        # dicts
        self.bars = []         # dicts
        self.bcs = {}          # name -> list de ddl bloques (0..5)
        self.loads = {}        # name -> np.array(6)

    # -- construction -------------------------------------------------------
    def node(self, name, x, y, z):
        self.nodes[name] = np.array([x, y, z], float)
        self.order.append(name)
        return name

    def beam(self, n1, n2, sec, releases1=(), releases2=(), vref=None, label=None):
        self.beams.append(dict(n1=n1, n2=n2, sec=sec, r1=tuple(releases1),
                               r2=tuple(releases2), vref=vref,
                               label=label or f"{n1}->{n2}"))
        return self.beams[-1]

    def bar(self, n1, n2, A, E, pretension=0.0, tension_only=False, label=None):
        self.bars.append(dict(n1=n1, n2=n2, A=A, E=E, T0=pretension,
                              tonly=tension_only, active=True,
                              label=label or f"{n1}~{n2}"))
        return self.bars[-1]

    def fix(self, name, dofs=(0, 1, 2, 3, 4, 5)):
        self.bcs.setdefault(name, set()).update(dofs)

    def load(self, name, fx=0, fy=0, fz=0, mx=0, my=0, mz=0):
        v = self.loads.setdefault(name, np.zeros(6))
        v += np.array([fx, fy, fz, mx, my, mz], float)

    # -- utilitaires --------------------------------------------------------
    def _index(self):
        return {n: i for i, n in enumerate(self.order)}

    def _length(self, n1, n2):
        return float(np.linalg.norm(self.nodes[n2] - self.nodes[n1]))

    # -- matrices elementaires ---------------------------------------------
    @staticmethod
    def _rotation(p1, p2, vref=None):
        """Matrice 3x3 des cosinus directeurs (lignes = axes locaux x,y,z)."""
        ex = p2 - p1
        L = np.linalg.norm(ex)
        ex = ex / L
        if vref is None:
            up = np.array([0.0, 0.0, 1.0])
            if abs(np.dot(ex, up)) > 0.99:
                up = np.array([0.0, 1.0, 0.0])
        else:
            up = np.asarray(vref, float)
        ez = np.cross(ex, up)
        nz = np.linalg.norm(ez)
        if nz < 1e-9:
            up = np.array([1.0, 0.0, 0.0])
            ez = np.cross(ex, up)
            nz = np.linalg.norm(ez)
        ez = ez / nz
        ey = np.cross(ez, ex)
        return np.vstack([ex, ey, ez]), L

    @staticmethod
    def _k_beam_local(E, G, sec, L):
        A, Iy, Iz, J = sec.A, sec.Iy, sec.Iz, sec.J
        k = np.zeros((12, 12))
        # axial
        k[0, 0] = k[6, 6] = E * A / L
        k[0, 6] = k[6, 0] = -E * A / L
        # torsion
        k[3, 3] = k[9, 9] = G * J / L
        k[3, 9] = k[9, 3] = -G * J / L
        # flexion plan x-z (utilise Iy), ddl uz(2,8) ry(4,10)
        a = E * Iy
        k[2, 2] = k[8, 8] = 12 * a / L ** 3
        k[2, 8] = k[8, 2] = -12 * a / L ** 3
        k[2, 4] = k[4, 2] = -6 * a / L ** 2
        k[2, 10] = k[10, 2] = -6 * a / L ** 2
        k[8, 4] = k[4, 8] = 6 * a / L ** 2
        k[8, 10] = k[10, 8] = 6 * a / L ** 2
        k[4, 4] = k[10, 10] = 4 * a / L
        k[4, 10] = k[10, 4] = 2 * a / L
        # flexion plan x-y (utilise Iz), ddl uy(1,7) rz(5,11)
        b = E * Iz
        k[1, 1] = k[7, 7] = 12 * b / L ** 3
        k[1, 7] = k[7, 1] = -12 * b / L ** 3
        k[1, 5] = k[5, 1] = 6 * b / L ** 2
        k[1, 11] = k[11, 1] = 6 * b / L ** 2
        k[7, 5] = k[5, 7] = -6 * b / L ** 2
        k[7, 11] = k[11, 7] = -6 * b / L ** 2
        k[5, 5] = k[11, 11] = 4 * b / L
        k[5, 11] = k[11, 5] = 2 * b / L
        return k

    @staticmethod
    def _condense(k, released):
        """Condensation statique des ddl relaches (rotules)."""
        if not released:
            return k
        keep = [i for i in range(12) if i not in released]
        rel = list(released)
        krr = k[np.ix_(rel, rel)]
        kkr = k[np.ix_(keep, rel)]
        kkk = k[np.ix_(keep, keep)]
        kc = kkk - kkr @ np.linalg.solve(krr, kkr.T)
        out = np.zeros((12, 12))
        out[np.ix_(keep, keep)] = kc
        return out

    # -- resolution ---------------------------------------------------------
    def solve(self, max_iter=30, verbose=False):
        idx = self._index()
        n = len(self.order) * DOF_PER_NODE

        for it in range(max_iter):
            K = np.zeros((n, n))
            F = np.zeros(n)

            # poutres
            for e in self.beams:
                p1, p2 = self.nodes[e["n1"]], self.nodes[e["n2"]]
                R, L = self._rotation(p1, p2, e["vref"])
                sec = e["sec"]
                E, G = sec.mat["E"], sec.mat["G"]
                kl = self._k_beam_local(E, G, sec, L)
                rel = set(e["r1"]) | {6 + r for r in e["r2"]}
                kl = self._condense(kl, rel)
                T = np.zeros((12, 12))
                for blk in range(4):
                    T[blk * 3:blk * 3 + 3, blk * 3:blk * 3 + 3] = R
                kg = T.T @ kl @ T
                e["_T"], e["_kl"], e["_L"] = T, kl, L
                d = self._dofs(idx, e["n1"], e["n2"])
                K[np.ix_(d, d)] += kg

            # barres (rayons)
            for b in self.bars:
                if not b["active"]:
                    continue
                p1, p2 = self.nodes[b["n1"]], self.nodes[b["n2"]]
                v = p2 - p1
                L = np.linalg.norm(v)
                c = v / L
                kax = b["A"] * b["E"] / L
                kl = kax * np.outer(np.r_[-c, c], np.r_[-c, c])
                d = self._dofs(idx, b["n1"], b["n2"], trans_only=True)
                K[np.ix_(d, d)] += kl
                b["_c"], b["_L"], b["_k"] = c, L, kax
                # precontrainte : force nodale equivalente
                if b["T0"]:
                    F[d] += b["T0"] * np.r_[c, -c]

            # charges exterieures
            for name, v in self.loads.items():
                d = self._dofs(idx, name)
                F[d] += v

            # conditions limites
            fixed = []
            for name, dofs in self.bcs.items():
                base = idx[name] * DOF_PER_NODE
                fixed += [base + k for k in dofs]
            free = np.setdiff1d(np.arange(n), fixed)

            u = np.zeros(n)
            Kff = K[np.ix_(free, free)]
            u[free] = np.linalg.solve(Kff, F[free])

            # efforts dans les barres, desactivation des rayons detendus
            changed = False
            for b in self.bars:
                d = self._dofs(idx, b["n1"], b["n2"], trans_only=True)
                du = u[d]
                elong = float(np.dot(np.r_[-b["_c"], b["_c"]], du)) if b["active"] else 0.0
                T = b["T0"] + (b["_k"] * elong if b["active"] else 0.0)
                b["T"] = T
                b["elong"] = elong
                if b["tonly"]:
                    if b["active"] and T < 0:
                        b["active"] = False
                        b["T"] = 0.0
                        changed = True
                    elif (not b["active"]) and b["T0"] > 0 and elong > 0:
                        pass
            if not changed:
                break

        self.u = u
        self.K = K
        self.F = F
        self._idx = idx
        self._post_beams()
        return u

    def _post_beams(self):
        for e in self.beams:
            d = self._dofs(self._idx, e["n1"], e["n2"])
            ug = self.u[d]
            ul = e["_T"] @ ug
            fl = e["_kl"] @ ul
            e["f_local"] = fl     # [N1,Vy1,Vz1,T1,My1,Mz1, N2,...]
            sec = e["sec"]
            N = abs(fl[0])
            My = max(abs(fl[4]), abs(fl[10]))
            Mz = max(abs(fl[5]), abs(fl[11]))
            Tq = abs(fl[3])
            s_ax = N / sec.A
            s_by = My * sec.zmax / sec.Iy
            s_bz = Mz * sec.ymax / sec.Iz
            e["sigma"] = s_ax + s_by + s_bz
            e["tau"] = Tq * max(sec.ymax, sec.zmax) / sec.J if sec.J > 0 else 0.0
            e["sigma_vm"] = np.sqrt(e["sigma"] ** 2 + 3 * e["tau"] ** 2)

    @staticmethod
    def _dofs(idx, *names, trans_only=False):
        out = []
        for nm in names:
            base = idx[nm] * DOF_PER_NODE
            rng = range(3) if trans_only else range(6)
            out += [base + k for k in rng]
        return out

    def disp(self, name):
        base = self._idx[name] * DOF_PER_NODE
        return self.u[base:base + 6]

    def mass(self):
        m = 0.0
        for e in self.beams:
            m += e["sec"].mass_per_m * self._length(e["n1"], e["n2"])
        return m

    # -- reactions d'appui ---------------------------------------------------
    def reactions(self):
        """Vecteur des reactions R = K.u - F (non nul aux seuls ddl bloques)."""
        return self.K @ self.u - self.F

    def reaction(self, name):
        R = self.reactions()
        base = self._idx[name] * DOF_PER_NODE
        return R[base:base + 6]
