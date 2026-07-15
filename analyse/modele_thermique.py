"""
Transfert thermique corps humain <-> eau / air
================================================

Question d'Étienne :
    « À effort physique égal, à partir de quelle température du fluide
      (eau ou air) a-t-on plus chaud dans l'eau que dans l'air ? »

Deux faits physiques structurent le problème :

  Fait 1 — Le coefficient d'échange conducto-convectif est BEAUCOUP plus
           élevé dans l'eau que dans l'air (h_eau / h_air ~ 15 à 40).
           À température de fluide identique, on évacue donc bien plus de
           chaleur dans l'eau : l'eau froide refroidit plus que l'air froid.

  Fait 2 — Dans l'air, au-delà d'un certain effort/température, le corps
           TRANSPIRE : il évacue de la chaleur par évaporation (chaleur
           latente), un mécanisme qui NE dépend PAS de l'écart de
           température mais de l'écart de pression de vapeur (humidité).
           Dans l'eau, l'évaporation est impossible.

Modèle : bilan thermique en régime permanent (modèle « lumped » 1 nœud).
Le corps doit dissiper une puissance métabolique M (l'effort). On calcule,
pour chaque fluide, la température de peau d'équilibre nécessaire et la
puissance maximale évacuable.

Unités SI. Températures en °C. Pressions de vapeur en kPa.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

# --------------------------------------------------------------------------
# Palette daltonisme-safe (Okabe-Ito) — validée par le validateur dataviz
# --------------------------------------------------------------------------
C_EAU   = "#0072B2"   # bleu  -> eau
C_AIR   = "#D55E00"   # orange -> air
C_EVAP  = "#E8A33D"   # ambre clair -> part évaporative (dérivé de l'air)
C_DANGER = "#B03030"  # rouge sobre -> seuils / hyperthermie
C_INK   = "#222222"
C_MUTED = "#6E6E6E"
C_GRID  = "#DDDDDD"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 11,
    "font.family": "DejaVu Sans",
    "axes.edgecolor": C_MUTED,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": C_GRID,
    "grid.linewidth": 0.7,
    "axes.axisbelow": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

# --------------------------------------------------------------------------
# Paramètres physiques (valeurs de référence, ordres de grandeur usuels)
# --------------------------------------------------------------------------
A        = 1.8     # m^2   surface corporelle (formule de DuBois)
T_CORE   = 37.0    # °C    température centrale ~ plafond de la température de peau
T_SET    = 35.0    # °C    consigne de peau "confortable" que la sudation cherche à tenir

# Coefficients d'échange conducto-convectif (sensible)
H_EAU    = 200.0   # W/m^2/K  corps immergé, eau calme (gamme 100-500 ; agité -> plus)
H_AIR    = 12.0    # W/m^2/K  air : convection (~7-8) + rayonnement (~4-5) combinés

# Échange évaporatif (uniquement dans l'air)
# Relation de Lewis : h_e ≈ 16.5 * h_conv  [W/m^2/kPa], avec h_conv ~ 8 W/m^2/K
H_EVAP   = 16.5 * 8.0            # ≈ 132 W/m^2/kPa
LAT_HEAT = 2430.0               # kJ/kg  chaleur latente de vaporisation de la sueur
SWEAT_MAX_LPH = 1.3             # L/h    débit de sueur soutenable (adulte entraîné ~1-1.5)
E_CAP    = SWEAT_MAX_LPH * LAT_HEAT / 3.6   # W  plafond physiologique de l'évaporation

# Niveaux d'effort (puissance métabolique à dissiper, W)
EFFORTS = {
    "repos":   100.0,
    "modéré":  450.0,
    "intense": 700.0,
}
M_REF = EFFORTS["modéré"]       # effort de référence des figures principales
RH_REF = 0.50                   # humidité relative de référence


def p_sat(T):
    """Pression de vapeur saturante (kPa) — formule de Magnus, T en °C."""
    return 0.61094 * np.exp(17.625 * T / (T + 243.04))


# --------------------------------------------------------------------------
# EAU : pas d'évaporation. Le corps ne dispose que du flux convectif.
#   M = h_eau * A * (T_peau - T_fluide)  ->  T_peau = T_fluide + M/(h_eau*A)
# --------------------------------------------------------------------------
def skin_temp_water(T_fluid, M, h_eau=H_EAU):
    return T_fluid + M / (h_eau * A)


def q_max_water(T_fluid, h_eau=H_EAU, T_skin_max=T_SET):
    """Puissance max évacuable dans l'eau à température de peau max donnée."""
    return h_eau * A * (T_skin_max - T_fluid)


# --------------------------------------------------------------------------
# AIR : convection (sensible) + évaporation (latente, plafonnée).
# --------------------------------------------------------------------------
def e_air_capacity(T_skin, T_air, RH):
    """Capacité évaporative de l'air (W) : moteur = écart de pression de vapeur,
    plafonnée par le débit de sueur physiologique."""
    e_env = H_EVAP * A * (p_sat(T_skin) - RH * p_sat(T_air))
    return np.clip(min(e_env, E_CAP), 0.0, None)


def skin_temp_air(T_air, M, RH, h_air=H_AIR):
    """Température de peau d'équilibre dans l'air (régulation par sudation)."""
    # Branche froide : convection seule suffit, pas de sueur -> peau sous consigne
    Tsk_cold = T_air + M / (h_air * A)
    if Tsk_cold <= T_SET:
        return Tsk_cold
    # Branche régulée : le corps tient la consigne T_SET en transpirant
    E_req = M - h_air * A * (T_SET - T_air)
    E_avail = e_air_capacity(T_SET, T_air, RH)
    if E_req <= E_avail:
        return T_SET
    # Branche non compensée : sueur saturée, il faut monter la peau au-dessus
    # de la consigne pour forcer plus de convection -> recherche numérique.
    Ts = np.linspace(T_SET, 45.0, 4000)
    lhs = h_air * A * (Ts - T_air) + np.minimum(
        E_CAP, H_EVAP * A * (p_sat(Ts) - RH * p_sat(T_air)))
    idx = np.argmin(np.abs(lhs - M))
    return Ts[idx]


def q_max_air(T_air, RH, h_air=H_AIR, T_skin_max=T_SET):
    """Puissance max évacuable dans l'air (convection + évaporation plafonnée)."""
    conv = h_air * A * (T_skin_max - T_air)
    evap = e_air_capacity(T_skin_max, T_air, RH)
    return conv + evap


# ==========================================================================
# FIGURE 1 — Température de peau d'équilibre vs température du fluide
#            => LA réponse à la question d'Étienne
# ==========================================================================
def figure_1():
    T = np.linspace(5, 42, 400)
    tsk_eau = skin_temp_water(T, M_REF)
    tsk_air = np.array([skin_temp_air(t, M_REF, RH_REF) for t in T])

    # Point de bascule (confort) : là où les deux courbes se croisent
    diff = tsk_eau - tsk_air
    cross_idx = np.where(np.diff(np.sign(diff)))[0]
    T_star = None
    if len(cross_idx):
        i = cross_idx[0]
        T_star = np.interp(0, [diff[i], diff[i+1]], [T[i], T[i+1]])

    fig, ax = plt.subplots(figsize=(9.5, 5.8))

    # Zones : plus frais dans l'eau (gauche) / plus chaud dans l'eau (droite)
    if T_star is not None:
        ax.axvspan(5, T_star, color=C_EAU, alpha=0.05)
        ax.axvspan(T_star, 42, color=C_AIR, alpha=0.06)

    ax.plot(T, tsk_eau, color=C_EAU, lw=2.4)
    ax.plot(T, tsk_air, color=C_AIR, lw=2.4)

    # Seuil d'hyperthermie (température centrale)
    ax.axhline(T_CORE, color=C_DANGER, lw=1.3, ls="--")
    ax.text(18.5, 38.4, "37 °C — température centrale : au-delà,\n"
            "équilibre impossible → hyperthermie", color=C_DANGER,
            fontsize=8.5, va="center", ha="left")

    # Étiquettes directes des courbes (pas de boîte de légende)
    ax.text(15.5, 35.7, "air  (transpiration)", color=C_AIR, fontsize=10.5,
            fontweight="bold", va="bottom")
    ax.text(29.3, 31.2, "eau", color=C_EAU, fontsize=10.5, fontweight="bold",
            rotation=32, rotation_mode="anchor")

    if T_star is not None:
        ax.axvline(T_star, color=C_INK, lw=1.0, ls=":")
        ax.plot([T_star], [np.interp(T_star, T, tsk_air)], "o", color=C_INK, ms=6, zorder=5)
        ax.annotate(f"Bascule (confort)\nT* ≈ {T_star:.1f} °C",
                    xy=(T_star, np.interp(T_star, T, tsk_air)),
                    xytext=(T_star - 11.5, 29.5),
                    fontsize=9.5, color=C_INK, ha="center",
                    arrowprops=dict(arrowstyle="->", color=C_INK, lw=1))

    ax.annotate("Plus FRAIS\ndans l'eau", xy=(11, 20), color=C_EAU, fontsize=10.5,
                ha="center", alpha=0.9, fontweight="bold")
    ax.annotate("Plus CHAUD\ndans l'eau", xy=(38.5, 22), color=C_AIR, fontsize=10.5,
                ha="center", alpha=0.9, fontweight="bold")

    ax.set_xlabel("Température du fluide  (°C)")
    ax.set_ylabel("Température de peau d'équilibre  (°C)")
    ax.set_title("Température de peau à l'équilibre selon le fluide\n"
                 f"effort modéré (M = {M_REF:.0f} W) · humidité relative {RH_REF*100:.0f} %",
                 fontsize=12.5, loc="left")
    ax.set_xlim(5, 42)
    ax.set_ylim(10, 40)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    fig.tight_layout()
    fig.savefig("analyse/figures/fig1_temperature_peau.png", bbox_inches="tight")
    plt.close(fig)
    return T_star


# ==========================================================================
# FIGURE 2 — Puissance maximale évacuable vs température du fluide
# ==========================================================================
def figure_2():
    T = np.linspace(5, 42, 400)
    qw = q_max_water(T)
    qa = np.array([q_max_air(t, RH_REF) for t in T])

    fig, ax = plt.subplots(figsize=(9.5, 5.8))

    # Région où l'air évacue plus que l'eau
    over = qa > qw
    ax.fill_between(T, qw, qa, where=over, color=C_AIR, alpha=0.10,
                    label="_zone air > eau")

    ax.plot(T, qw, color=C_EAU, lw=2.4, label="Eau (convection seule)")
    ax.plot(T, qa, color=C_AIR, lw=2.4, label="Air (convection + évaporation)")

    # Croisement des capacités
    d = qa - qw
    ci = np.where(np.diff(np.sign(d)))[0]
    if len(ci):
        i = ci[0]
        Tc = np.interp(0, [d[i], d[i+1]], [T[i], T[i+1]])
        ax.axvline(Tc, color=C_INK, lw=1.0, ls=":")
        ax.annotate(f"Capacités égales\n≈ {Tc:.1f} °C", xy=(Tc, np.interp(Tc, T, qw)),
                    xytext=(Tc - 12, 250), fontsize=9.5, color=C_INK,
                    arrowprops=dict(arrowstyle="->", color=C_INK, lw=1))

    # Lignes d'effort : on lit la température de fluide max tolérable
    styles = {"repos": (0, (1, 1)), "modéré": (0, (5, 2)), "intense": (0, (7, 1, 1, 1))}
    for name, M in EFFORTS.items():
        ax.axhline(M, color=C_MUTED, lw=1.1, ls=styles[name])
        ax.text(5.3, M + 12, f"effort {name} — {M:.0f} W", color=C_MUTED, fontsize=8.5)

    ax.set_xlabel("Température du fluide  (°C)")
    ax.set_ylabel("Puissance max évacuable  (W)")
    ax.set_title("Capacité d'évacuation de chaleur selon le fluide\n"
                 f"peau à {T_SET:.0f} °C · humidité relative {RH_REF*100:.0f} %",
                 fontsize=12.5, loc="left")
    ax.set_xlim(5, 42)
    ax.set_ylim(-100, 2000)
    ax.axhline(0, color=C_MUTED, lw=0.8)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig("analyse/figures/fig2_capacite_evacuation.png", bbox_inches="tight")
    plt.close(fig)


# ==========================================================================
# FIGURE 3 — Décomposition des flux dans l'air (convection vs évaporation)
#            vs le flux d'eau (convection seule)
# ==========================================================================
def figure_3():
    T = np.linspace(5, 42, 400)
    conv_air = H_AIR * A * (T_SET - T)                       # peut devenir négatif
    evap_air = np.array([e_air_capacity(T_SET, t, RH_REF) for t in T])
    conv_eau = H_EAU * A * (T_SET - T)

    fig, ax = plt.subplots(figsize=(9.5, 5.8))

    # Air : empilement convection + évaporation (part positive de la convection)
    conv_pos = np.clip(conv_air, 0, None)
    ax.fill_between(T, 0, conv_pos, color=C_AIR, alpha=0.55,
                    label="Air — convection", lw=0)
    ax.fill_between(T, conv_pos, conv_pos + evap_air, color=C_EVAP, alpha=0.80,
                    label="Air — évaporation (sueur)", lw=0)
    ax.plot(T, conv_pos, color="white", lw=1.2)            # séparateur des bandes
    ax.plot(T, conv_air + evap_air, color=C_AIR, lw=1.6)

    # Eau : convection seule
    ax.plot(T, conv_eau, color=C_EAU, lw=2.6, label="Eau — convection seule")

    ax.axhline(0, color=C_MUTED, lw=0.8)
    ax.axvline(T_SET, color=C_MUTED, lw=1.0, ls=":")
    ax.text(T_SET - 0.4, 1580, f"peau = {T_SET:.0f} °C  (convection nulle)",
            color=C_MUTED, fontsize=8.5, rotation=90, va="top", ha="right")

    ax.annotate("Dans l'air, l'évaporation continue de refroidir\n"
                "même quand le fluide est plus chaud que la peau ;\n"
                "dans l'eau, il ne reste plus rien.",
                xy=(40, 300), xytext=(18.5, 1720), fontsize=9, color=C_INK,
                arrowprops=dict(arrowstyle="->", color=C_INK, lw=1))

    ax.set_xlabel("Température du fluide  (°C)")
    ax.set_ylabel("Flux de chaleur évacué  (W)")
    ax.set_title("D'où vient la chaleur évacuée ?  Air (convection + sueur) vs eau\n"
                 f"peau à {T_SET:.0f} °C · humidité relative {RH_REF*100:.0f} %",
                 fontsize=12.5, loc="left")
    ax.set_xlim(5, 42)
    ax.set_ylim(-100, 2000)
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig("analyse/figures/fig3_decomposition_flux.png", bbox_inches="tight")
    plt.close(fig)


# ==========================================================================
# FIGURE 4 — Sensibilités : effort (a) et humidité (b)
# ==========================================================================
def uncompensable_temp_air(RH, M, h_air=H_AIR):
    """Température d'air au-delà de laquelle l'effort M n'est plus compensable."""
    T = np.linspace(20, 60, 4000)
    tsk = np.array([skin_temp_air(t, M, RH, h_air) for t in T])
    over = np.where(tsk >= T_CORE)[0]
    return T[over[0]] if len(over) else np.nan


def uncompensable_temp_water(M, h_eau=H_EAU):
    """Température d'eau au-delà de laquelle l'effort M n'est plus compensable."""
    return T_CORE - M / (h_eau * A)


def figure_4():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4))

    # (a) Point de bascule confort T* = T_SET - M/(h_eau*A) vs effort, pour 3 h_eau
    Ms = np.linspace(50, 900, 200)
    for h_eau, ls, lab in [(100, ":", "eau calme (h=100)"),
                           (200, "-", "référence (h=200)"),
                           (500, "--", "eau agitée / nage (h=500)")]:
        Tstar = T_SET - Ms / (h_eau * A)
        ax1.plot(Ms, Tstar, color=C_EAU, ls=ls, lw=2.0, label=lab)
    for name, M in EFFORTS.items():
        ax1.axvline(M, color=C_MUTED, lw=0.9, ls=(0, (2, 2)))
        ax1.text(M + 8, 35.9, name, rotation=90, color=C_MUTED, fontsize=8.5, va="top")
    ax1.set_xlabel("Effort — puissance métabolique  (W)")
    ax1.set_ylabel("Température de bascule T*  (°C)")
    ax1.set_title("(a) Bascule confort selon l'effort et l'agitation de l'eau",
                  fontsize=11, loc="left")
    ax1.set_ylim(30, 36)
    ax1.legend(loc="lower left", fontsize=8.5)

    # (b) Seuil d'hyperthermie vs humidité : air (dépend de HR) vs eau (constante)
    RHs = np.linspace(0.1, 1.0, 60)
    for M, ls, lab in [(450, "-", "air — effort modéré"),
                       (700, "--", "air — effort intense")]:
        Tunc = [uncompensable_temp_air(rh, M) for rh in RHs]
        ax2.plot(RHs * 100, Tunc, color=C_AIR, ls=ls, lw=2.0, label=lab)
    for M, ls, lab in [(450, "-", "eau — effort modéré"),
                       (700, "--", "eau — effort intense")]:
        Tw = uncompensable_temp_water(M)
        ax2.axhline(Tw, color=C_EAU, ls=ls, lw=2.0, label=lab)
    ax2.set_xlabel("Humidité relative de l'air  (%)")
    ax2.set_ylabel("Température de fluide non compensable  (°C)")
    ax2.set_title("(b) Seuil d'hyperthermie : l'air ne bat l'eau que si l'air est sec",
                  fontsize=11, loc="left")
    ax2.set_ylim(30, 55)
    ax2.legend(loc="upper right", fontsize=8.5)

    fig.suptitle("Sensibilité du basculement eau / air", fontsize=13, x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig("analyse/figures/fig4_sensibilites.png", bbox_inches="tight")
    plt.close(fig)


def print_summary(T_star):
    print("=" * 66)
    print("SYNTHÈSE NUMÉRIQUE")
    print("=" * 66)
    print(f"Surface corporelle A          : {A} m²")
    print(f"h_eau / h_air                 : {H_EAU:.0f} / {H_AIR:.0f} "
          f"= {H_EAU/H_AIR:.0f}x")
    print(f"Plafond évaporatif E_cap      : {E_CAP:.0f} W "
          f"({SWEAT_MAX_LPH} L/h)")
    print(f"Consigne de peau T_set        : {T_SET} °C")
    print("-" * 66)
    print(f"Bascule CONFORT (effort modéré, HR 50%)  T* ≈ {T_star:.1f} °C")
    print("  Formule régime compensé : T* = T_set - M/(h_eau·A)")
    for name, M in EFFORTS.items():
        print(f"    - {name:8s} (M={M:4.0f} W) : "
              f"T* ≈ {T_SET - M/(H_EAU*A):.1f} °C")
    print("-" * 66)
    print("Seuil d'HYPERTHERMIE (non compensable) :")
    for name, M in EFFORTS.items():
        tw = uncompensable_temp_water(M)
        ta_dry = uncompensable_temp_air(0.2, M)
        ta_hum = uncompensable_temp_air(0.8, M)
        print(f"    - {name:8s}: eau {tw:4.1f} °C | "
              f"air sec(20%) {ta_dry:4.1f} °C | air humide(80%) {ta_hum:4.1f} °C")
    print("=" * 66)


if __name__ == "__main__":
    T_star = figure_1()
    figure_2()
    figure_3()
    figure_4()
    print_summary(T_star)
    print("\nFigures écrites dans analyse/figures/")
