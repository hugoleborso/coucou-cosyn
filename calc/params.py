"""
COSYN-30 : parametrage central du velo pliant sac-a-dos.

Toutes les valeurs sont en unites SI (m, N, Pa, kg, s).
Toute etude aval (cadre, roue, emmanchements, masses, encombrement, fatigue)
importe ce fichier : il n'y a qu'une seule source de verite geometrique.

Repere global (velo deploye) :
    origine  = axe du boitier de pedalier (BdP)
    x        = vers l'avant
    y        = vers la gauche du cycliste
    z        = vers le haut
"""

from __future__ import annotations
import numpy as np

# ==========================================================================
# 1. MATERIAUX
#    Re  : limite elastique      Rm : resistance a rupture
#    sN  : amplitude admissible a 1e7 cycles (R = -1, eprouvette lisse)
# ==========================================================================
MAT = {
    "AL7075T6": dict(name="Aluminium 7075-T6", E=71.7e9, G=26.9e9, rho=2810,
                     Re=503e6, Rm=572e6, sN=159e6, kt_weld=None),
    "AL6082T6": dict(name="Aluminium 6082-T6", E=70.0e9, G=26.3e9, rho=2700,
                     Re=260e6, Rm=310e6, sN=95e6, kt_weld=0.45),
    "AL7020T6": dict(name="Aluminium 7020-T6 (soudable)", E=70.0e9, G=26.5e9,
                     rho=2780, Re=290e6, Rm=350e6, sN=105e6, kt_weld=0.62),
    "TI3AL25V": dict(name="Titane 3Al-2.5V recuit", E=100e9, G=39e9, rho=4480,
                     Re=500e6, Rm=620e6, sN=280e6, kt_weld=0.80),
    "CFRP": dict(name="Carbone HM tisse/UD (stratifie quasi-iso)", E=90e9,
                 G=25e9, rho=1550, Re=600e6, Rm=700e6, sN=300e6, kt_weld=None),
    "INOX_RAYON": dict(name="Fil inox 18/8 trefile (rayon)", E=200e9, G=77e9,
                       rho=7900, Re=1000e6, Rm=1350e6, sN=420e6, kt_weld=None),
    "PU85A": dict(name="Polyurethane 85 ShA (bande de roulement)", E=32e6,
                  G=11e6, rho=1150, Re=8e6, Rm=35e6, sN=3e6, kt_weld=None),
    "ACIER_42CD4": dict(name="42CrMo4 trempe revenu (axes, cames)", E=210e9,
                        G=81e9, rho=7850, Re=750e6, Rm=1000e6, sN=380e6,
                        kt_weld=None),
}

# Coefficients de securite retenus (cf. docs/02-etude-structurelle.md)
CS = dict(
    statique_elastique=1.5,     # vs Re, cas de charge nominal
    choc=1.25,                  # vs Re, cas de charge extreme (choc trottoir)
    rupture=2.5,                # vs Rm, pieces de securite (fourche, direction)
    fatigue=1.4,                # vs limite d'endurance corrigee
    flambement=3.0,             # vs charge critique d'Euler / anneau
    contact=1.6,                # vs pression admissible dans les emmanchements
)

# ==========================================================================
# 2. GEOMETRIE CYCLE (velo deploye)
# ==========================================================================
class Geo:
    # --- roues
    wheel_od        = 0.500     # diametre exterieur hors-tout roue deployee [m]
    wheel_r         = wheel_od / 2
    rim_r_mid       = 0.2275    # rayon fibre neutre de la jante [m]
    rim_w           = 0.024     # largeur (axiale) du caisson de jante [m]
    rim_h           = 0.022     # hauteur (radiale) du caisson de jante [m]
    rim_t           = 0.0014    # epaisseur de paroi [m]
    n_seg           = 8         # nombre d'arcs de jante (etudie en c06)
    n_spokes        = 32        # nombre de rayons par roue (4 par arc)
    spoke_d         = 0.0018    # diametre nominal du rayon [m]
    spoke_d_mid     = 0.0016    # diametre en partie courante (rayon double-butted)
    spoke_T0        = 700.0     # precontrainte cible par rayon [N]
    hub_flange_r    = 0.030     # rayon des brides de moyeu [m]
    hub_bracing     = 0.030     # demi-ecartement des brides (+/- y) [m]
    tread_t         = 0.0115    # epaisseur bande de roulement alveolaire [m]
    tread_w         = 0.028     # largeur bande de roulement [m]
    tread_rho_rel   = 0.32      # densite relative de la structure alveolaire
    susp_travel     = 0.030     # debattement elastomere AV et AR [m]
    susp_k          = 40e3      # raideur a la roue de l element elastomere [N/m]

    # --- implantation cycle
    bb_height       = 0.265     # hauteur du boitier de pedalier / sol [m]
    chainstay       = 0.375     # BdP -> axe roue arriere [m]
    wheelbase       = 0.980     # empattement [m]
    head_angle      = np.deg2rad(71.0)
    fork_offset     = 0.042     # chasse geometrique de fourche [m]
    head_tube_len   = 0.150     # longueur du tube de direction [m]
    head_z_bottom   = 0.265     # cote z du bas du tube de direction [m]
    seat_angle      = np.deg2rad(73.0)
    seat_mast_len   = 0.300     # partie fixe du mat de selle [m]
    crank_len       = 0.152     # longueur de manivelle [m]
    chainring       = 34        # dents plateau (Ø ext. 147 mm)
    sprocket        = 12        # dents pignon
    saddle_h_min    = 0.680     # hauteur selle / BdP mini [m]
    saddle_h_max    = 0.790     # hauteur selle / BdP maxi [m]
    bar_h           = 0.640     # hauteur guidon / BdP [m]
    bar_width       = 0.480     # largeur guidon deploye [m]
    disc_d          = 0.140     # diametre disque de frein [m]

    # --- sections principales (mm -> m dans les modules d'analyse)
    beam_od         = 0.046     # poutre principale, tube exterieur [m]
    beam_t          = 0.0022
    beam_od2        = 0.0396    # poutre principale, tube interieur [m]
    beam_t2         = 0.0022
    post_od         = 0.0318    # tige de selle etage 1
    post_t          = 0.0018
    steerer_od      = 0.0286    # colonne de direction etage 1
    steerer_t       = 0.0020

    # --- cinematique de pliage
    beam_stages     = 3         # nombre d'etages de la poutre principale
    post_stages     = 3
    steerer_stages  = 3
    overlap_ratio   = 0.28      # recouvrement mini / longueur deployee d'etage

    @classmethod
    def rear_axle(cls):
        return np.array([-cls.chainstay, 0.0, cls.wheel_r - cls.bb_height])

    @classmethod
    def front_axle(cls):
        x = cls.wheelbase - cls.chainstay
        return np.array([x, 0.0, cls.wheel_r - cls.bb_height])

    @classmethod
    def trail(cls):
        """Chasse au sol [m]."""
        return (cls.wheel_r * np.cos(cls.head_angle) - cls.fork_offset) \
            / np.sin(cls.head_angle)

    @classmethod
    def steer_axis_ground_x(cls):
        return cls.front_axle()[0] + cls.trail()

    @classmethod
    def steer_dir(cls):
        """Vecteur unitaire de l'axe de direction, oriente vers le haut."""
        return np.array([-np.cos(cls.head_angle), 0.0, np.sin(cls.head_angle)])

    @classmethod
    def point_on_steer_axis(cls, z_global):
        """Point de l'axe de direction a la cote z demandee."""
        x0 = cls.steer_axis_ground_x()
        z0 = -cls.bb_height
        d = cls.steer_dir()
        t = (z_global - z0) / d[2]
        return np.array([x0 + d[0] * t, 0.0, z_global])

    @classmethod
    def head_bottom(cls):
        return cls.point_on_steer_axis(cls.head_z_bottom)

    @classmethod
    def head_top(cls):
        return cls.point_on_steer_axis(cls.head_z_bottom
                                      + cls.head_tube_len * np.sin(cls.head_angle))

    @classmethod
    def development(cls):
        """Developpement [m/tour de pedalier]."""
        return np.pi * cls.wheel_od * cls.chainring / cls.sprocket


# ==========================================================================
# 3. MASSES ET CAS DE CHARGE
# ==========================================================================
class Loads:
    m_rider       = 85.0        # cycliste de dimensionnement [kg]
    m_bike_target = 8.0         # objectif masse velo [kg]
    m_payload     = 5.0         # sac / charge portee
    g             = 9.81

    # repartition statique assis (fraction du poids cycliste)
    frac_saddle   = 0.60
    frac_bar      = 0.15
    frac_pedals   = 0.25

    # facteurs dynamiques
    k_bump        = 2.5         # passage de trottoir / nid de poule
    k_kerb_drop   = 3.2         # descente de trottoir 150 mm, sans suspension
    F_pedal_iso   = 1100.0      # ISO 4210-6, effort de pedalage
    F_bar_lat_iso = 600.0       # ISO 4210-2, effort horizontal au guidon
    mu_tyre       = 0.75        # adherence pneu/chaussee seche
    a_brake_des   = 0.45 * 9.81 # deceleration de dimensionnement [m/s2]

    # centre de gravite du systeme (velo + cycliste), repere global
    cg_x          = -0.050      # position du CdG systeme / BdP [m]
    cg_z          = 0.750       # hauteur du CdG systeme / BdP [m]

    @classmethod
    def m_total(cls):
        return cls.m_rider + cls.m_bike_target + cls.m_payload

    @classmethod
    def W_total(cls):
        return cls.m_total() * cls.g


# ==========================================================================
# 4. ENCOMBREMENT CIBLE (sac a dos 30 L "compact")
# ==========================================================================
class Pack:
    # volume utile interieur retenu pour un sac 30 L a dos rigide
    # sac 30 L "compact" a dos rigide : ext. ~530 x 310 x 220 mm
    L = 0.490
    H = 0.280
    W = 0.195

    @classmethod
    def volume(cls):
        return cls.L * cls.H * cls.W      # m3

    @classmethod
    def litres(cls):
        return cls.volume() * 1000.0


if __name__ == "__main__":
    g = Geo
    print(f"Empattement            : {g.wheelbase*1000:.0f} mm")
    print(f"Roue OD                : {g.wheel_od*1000:.0f} mm")
    print(f"Chasse (trail)         : {g.trail()*1000:.1f} mm")
    print(f"Axe AV                 : {np.round(g.front_axle()*1000,1)}")
    print(f"Axe AR                 : {np.round(g.rear_axle()*1000,1)}")
    print(f"Base tube direction    : {np.round(g.head_bottom()*1000,1)}")
    print(f"Haut tube direction    : {np.round(g.head_top()*1000,1)}")
    print(f"Developpement          : {g.development():.2f} m/tour "
          f"({g.development()*80*60/1000:.1f} km/h a 80 tr/min)")
    print(f"Volume sac utile       : {Pack.litres():.1f} L")


# ==========================================================================
# 5. COURBE DE WOHLER (Basquin) -- amplitude admissible a N cycles
# ==========================================================================
def sigma_allow(mat, N, R=-1.0, kf=1.0, surface=0.9, taille=0.9):
    """Amplitude de contrainte admissible a N cycles.

    Droite de Basquin calee sur deux points : 0.9*Rm a 1e3 cycles et la valeur
    'sN' du materiau (amplitude a 1e7 cycles, eprouvette lisse polie).
    Corrigee par l'effet d'entaille kf, l'etat de surface et l'effet d'echelle.
    Correction de contrainte moyenne par la droite de Goodman.
    """
    import numpy as _np
    s1e3 = 0.9 * mat["Rm"]
    b = _np.log(mat["sN"] / s1e3) / _np.log(1e7 / 1e3)
    sa = s1e3 * (N / 1e3) ** b
    sa *= surface * taille / kf
    if R > -1.0:                       # contrainte moyenne non nulle
        sm_over_sa = (1 + R) / (1 - R)
        sa = sa / (1 + sm_over_sa * sa / mat["Rm"])
    return sa
