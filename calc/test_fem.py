"""Validation du solveur fem.py sur des cas a solution analytique."""
import numpy as np
from fem import Model, Section

STEEL = dict(E=210e9, G=81e9, rho=7850, Re=350e6, Rm=500e6, name="acier")
TOL = 1e-6
results = []


def check(name, num, ana):
    err = abs(num - ana) / max(abs(ana), 1e-30)
    results.append((name, num, ana, err))
    assert err < 1e-6, f"{name}: {num} vs {ana} (err {err:.2e})"


def t_cantilever_bending():
    s = Section.tube("t", 0.030, 0.002, STEEL)
    m = Model(); m.node("A", 0, 0, 0); m.node("B", 1.0, 0, 0)
    m.beam("A", "B", s); m.fix("A"); m.load("B", fz=-100)
    m.solve()
    check("console flexion w", m.disp("B")[2], -100 * 1.0 ** 3 / (3 * STEEL["E"] * s.Iy))


def t_cantilever_torsion():
    s = Section.tube("t", 0.030, 0.002, STEEL)
    m = Model(); m.node("A", 0, 0, 0); m.node("B", 0.8, 0, 0)
    m.beam("A", "B", s); m.fix("A"); m.load("B", mx=50)
    m.solve()
    check("console torsion", m.disp("B")[3], 50 * 0.8 / (STEEL["G"] * s.J))


def t_axial():
    s = Section.tube("t", 0.030, 0.002, STEEL)
    m = Model(); m.node("A", 0, 0, 0); m.node("B", 2.0, 0, 0)
    m.beam("A", "B", s); m.fix("A"); m.load("B", fx=5000)
    m.solve()
    check("traction", m.disp("B")[0], 5000 * 2.0 / (STEEL["E"] * s.A))


def t_hinge():
    """Poutre bi-appuyee obtenue par relachement des rotations : w = PL^3/48EI."""
    s = Section.tube("t", 0.030, 0.002, STEEL)
    m = Model()
    m.node("A", 0, 0, 0); m.node("C", 0.5, 0, 0); m.node("B", 1.0, 0, 0)
    m.beam("A", "C", s, releases1=(4,))
    m.beam("C", "B", s, releases2=(4,))
    m.fix("A", (0, 1, 2, 3, 5)); m.fix("B", (1, 2, 3, 5))
    m.load("C", fz=-1000)
    m.solve()
    check("bi-appuyee", m.disp("C")[2], -1000 * 1.0 ** 3 / (48 * STEEL["E"] * s.Iy))


def t_truss():
    """Treillis a 2 barres symetrique, charge verticale au sommet."""
    A, E, ang = 100e-6, 210e9, np.deg2rad(60)
    m = Model()
    m.node("L", -1.0, 0, 0); m.node("R", 1.0, 0, 0)
    m.node("T", 0.0, 0, 1.0 * np.tan(ang))
    m.bar("L", "T", A, E); m.bar("R", "T", A, E)
    m.fix("L"); m.fix("R"); m.fix("T", (1, 3, 4, 5))
    P = 10000.0
    m.load("T", fz=-P)
    m.solve()
    ana = -P / (2 * np.sin(ang))          # compression dans chaque barre
    check("treillis effort", m.bars[0]["T"], ana)
    L = np.linalg.norm(m.nodes["T"] - m.nodes["L"])
    check("treillis fleche", m.disp("T")[2], ana * L / (A * E) / np.sin(ang))


def t_tension_only():
    """Barre 'tension only' comprimee -> desactivee."""
    m = Model()
    m.node("A", 0, 0, 0); m.node("B", 0, 0, 1.0); m.node("C", 1.0, 0, 1.0)
    s = Section.tube("t", 0.040, 0.003, STEEL)
    m.beam("A", "B", s)
    m.bar("B", "C", 2e-6, 200e9, tension_only=True)
    m.fix("A"); m.fix("C")
    m.load("B", fx=500)            # pousse B vers C : le hauban passe en compression
    m.solve()
    assert m.bars[0]["T"] == 0.0, "le rayon aurait du etre desactive"
    results.append(("tension-only desactivation", 0.0, 0.0, 0.0))


def main():
    for f in (t_cantilever_bending, t_cantilever_torsion, t_axial,
              t_hinge, t_truss, t_tension_only):
        f()
    w = max(len(r[0]) for r in results)
    print(f"{'cas':<{w}}  {'FEM':>14}  {'analytique':>14}  {'ecart rel':>10}")
    for nm, num, ana, err in results:
        print(f"{nm:<{w}}  {num:14.6e}  {ana:14.6e}  {err:10.2e}")
    print(f"\n{len(results)}/{len(results)} cas de validation OK")


if __name__ == "__main__":
    main()
