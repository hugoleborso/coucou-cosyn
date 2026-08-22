"""
Modele des emmanchements telescopiques (poutre principale, tige de selle,
colonne de direction) du COSYN-30.

Principe retenu
---------------
Chaque etage est un tube coulissant dans le precedent. En position deployee
l'assemblage est *serre* par un expandeur conique interne (type expandeur de
potence) double d'un collier exterieur : le jeu radial de coulissement est
annule, et le raccord travaille comme une poutre composite sur la longueur de
recouvrement, avec un rendement d'assemblage eta < 1 qui traduit le glissement
residuel et la deformation locale de coque.

Verifications produites
-----------------------
1. pression de matage sur les portees de contact       -> longueur mini
2. jeu angulaire residuel si l'expandeur n'agit pas    -> flou de direction
3. couple de serrage / effort d'expandeur necessaire   -> non-glissement
4. rigidite de flexion equivalente du recouvrement     -> injectee dans le FEM
"""

from __future__ import annotations
import numpy as np
from params import MAT, CS

P_ADM_BEARING = 25e6      # pression de matage admissible Al anodise dur / Al [Pa]
MU_CONE = 0.12            # frottement acier/alu graisse sur cone d'expandeur
MU_CLAMP = 0.35           # frottement alu/alu sec, portees sablees
ETA_JOINT = 0.60          # rendement de composition en flexion du recouvrement


def tube_props(od, t, mat):
    ri, ro = od / 2 - t, od / 2
    A = np.pi * (ro ** 2 - ri ** 2)
    I = np.pi / 4 * (ro ** 4 - ri ** 4)
    return dict(A=A, I=I, EI=mat["E"] * I, ro=ro, ri=ri, t=t, od=od, mat=mat)


class Telescope:
    """Un etage telescopique : tube interieur 'inner' dans tube exterieur 'outer'."""

    def __init__(self, name, outer, inner, overlap, clearance=60e-6,
                 bearing_len=0.012):
        self.name = name
        self.o = outer
        self.i = inner
        self.e = overlap            # longueur de recouvrement [m]
        self.c = clearance          # jeu diametral de coulissement [m]
        self.b = bearing_len        # longueur axiale des deux portees [m]

    # -- 1. matage -------------------------------------------------------
    def bearing_pressure(self, M, V=0.0):
        """Pression de matage sous moment M [N.m] et effort tranchant V [N].

        Le moment est repris par un couple de deux reactions radiales
        F = M/e distantes de e ; l'effort tranchant s'y ajoute.
        """
        F = M / self.e + abs(V) / 2
        # projection sur la portee : diametre x longueur de portee
        Aproj = self.i["od"] * self.b
        return F / Aproj, F

    def overlap_required(self, M, V=0.0, p_adm=P_ADM_BEARING):
        """Recouvrement minimal pour rester sous la pression admissible."""
        Aproj = self.i["od"] * self.b
        # F = M/e + V/2 <= p_adm*Aproj  ->  e >= M/(p_adm*Aproj - V/2)
        cap = p_adm * Aproj - abs(V) / 2
        return np.inf if cap <= 0 else M / cap

    # -- 2. jeu angulaire ------------------------------------------------
    def slop_angle(self):
        """Basculement libre du tube interieur si l'expandeur est inactif [rad]."""
        return self.c / self.e

    def slop_tip(self, lever):
        return self.slop_angle() * lever

    # -- 3. expandeur ----------------------------------------------------
    def expander(self, cone_angle_deg, F_axial_req, T_torque_req, r_contact=None):
        """Effort de tirant et couple de vis pour garantir le non-glissement.

        cone_angle_deg : demi-angle du cone de l'expandeur
        F_axial_req    : effort axial a transmettre par adherence [N]
        T_torque_req   : couple a transmettre par adherence [N.m]
        """
        r = r_contact or self.i["ri"]
        a = np.deg2rad(cone_angle_deg)
        # effort radial necessaire (normal total sur la portee)
        N_axial = F_axial_req / MU_CLAMP
        N_torque = T_torque_req / (MU_CLAMP * r)
        N = max(N_axial, N_torque)
        # amplification du cone : N = F_tirant / (tan(a) + mu)
        F_bolt = N * (np.tan(a) + MU_CONE)
        # couple de vis M6 pas 1 (k = 0.20)
        C_vis = 0.20 * 0.006 * F_bolt
        return dict(N_radial=N, F_bolt=F_bolt, C_vis=C_vis,
                    p_contact=N / (np.pi * self.i["od"] * self.b))

    # -- 4. rigidite equivalente ----------------------------------------
    def EI_joint(self, eta=ETA_JOINT):
        """Rigidite de flexion equivalente du troncon de recouvrement."""
        return eta * (self.o["EI"] + self.i["EI"])

    def report(self, M, V, F_ax, T_tq, lever, cone_deg=8.0):
        p, F = self.bearing_pressure(M, V)
        exp = self.expander(cone_deg, F_ax, T_tq)
        return dict(
            nom=self.name,
            e_mm=self.e * 1e3,
            F_contact_N=F,
            p_matage_MPa=p / 1e6,
            marge_matage=P_ADM_BEARING / p,
            e_min_mm=self.overlap_required(M, V) * 1e3,
            jeu_deg=np.rad2deg(self.slop_angle()),
            flou_mm=self.slop_tip(lever) * 1e3,
            F_tirant_N=exp["F_bolt"],
            C_vis_Nm=exp["C_vis"],
            p_expandeur_MPa=exp["p_contact"] / 1e6,
            EI_joint=self.EI_joint(),
            EI_tube_ext=self.o["EI"],
        )
