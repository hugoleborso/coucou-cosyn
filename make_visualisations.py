"""
Génère les visualisations de l'analyse (PNG dans viz/).

Principes dataviz appliqués : formes choisies selon le message, palette
catégorielle validée CVD (blue/orange/violet), marques fines, grille discrète,
étiquettes directes, légende présente dès 2 séries.

Palette (validée par scripts/validate_palette.js du skill dataviz) :
  - couronne  : petite (93/94) = bleu #2a78d6 · grande (77) = orange #eb6834
  - dép.      : 93 bleu #2a78d6 · 94 violet #4a3aa7 · 77 orange #eb6834
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import pandas as pd

# ---- tokens ----
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e6e3"
BLUE, ORANGE, VIOLET = "#2a78d6", "#eb6834", "#4a3aa7"
DEP_COLOR = {"93": BLUE, "94": VIOLET, "77": ORANGE}
DEP_LABEL = {"93": "93 — Seine-Saint-Denis", "94": "94 — Val-de-Marne", "77": "77 — Seine-et-Marne"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.size": 12, "font.family": "DejaVu Sans",
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID,
})


def base_ax(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)


def is_grande(zone):
    return "Seine et Marne" in zone


df = pd.read_csv("data/lycees_with_times.csv")
df["dep"] = df["dep"].astype(str)
zone = pd.read_csv("data/agg_by_zone.csv").sort_values("temps_min_moyen_min")


# ============ 1. Temps min moyen par zone (barres) ============
def chart_avg():
    d = zone.sort_values("temps_min_moyen_min", ascending=True)
    colors = [ORANGE if is_grande(z) else BLUE for z in d["zone"]]
    fig, ax = plt.subplots(figsize=(11, 7))
    y = range(len(d))
    ax.barh(y, d["temps_min_moyen_min"], color=colors, height=0.66, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(d["zone"])
    for i, v in enumerate(d["temps_min_moyen_min"]):
        ax.text(v + 2, i, f"{v:.0f}", va="center", ha="left", color=INK2, fontsize=11)
    ax.xaxis.grid(True, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Temps minimal moyen depuis le 118 rue d'Aboukir (min)")
    ax.set_title("Temps de trajet moyen par zone ALADDIN", fontsize=16, fontweight="bold",
                 color=INK, loc="left", pad=14)
    ax.set_xlim(0, max(d["temps_min_moyen_min"]) * 1.12)
    base_ax(ax)
    ax.legend(handles=[Patch(color=BLUE, label="Petite couronne (93/94)"),
                       Patch(color=ORANGE, label="Grande couronne (77)")],
              loc="lower right", frameon=False, fontsize=11)
    fig.tight_layout()
    fig.savefig("viz/zone_avg_time.png", dpi=150)
    plt.close(fig)


# ============ 2. Nombre de lycées par zone (barres) ============
def chart_count():
    d = zone.sort_values("nb_lycees", ascending=True)
    colors = [ORANGE if is_grande(z) else BLUE for z in d["zone"]]
    fig, ax = plt.subplots(figsize=(11, 7))
    y = range(len(d))
    ax.barh(y, d["nb_lycees"], color=colors, height=0.66, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(d["zone"])
    for i, v in enumerate(d["nb_lycees"]):
        ax.text(v + 0.25, i, f"{v}", va="center", ha="left", color=INK2, fontsize=11)
    ax.xaxis.grid(True, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Nombre de lycées publics")
    ax.set_title("Nombre de lycées publics par zone ALADDIN", fontsize=16, fontweight="bold",
                 color=INK, loc="left", pad=14)
    ax.set_xlim(0, max(d["nb_lycees"]) * 1.12)
    base_ax(ax)
    ax.legend(handles=[Patch(color=BLUE, label="Petite couronne (93/94)"),
                       Patch(color=ORANGE, label="Grande couronne (77)")],
              loc="lower right", frameon=False, fontsize=11)
    fig.tight_layout()
    fig.savefig("viz/zone_count.png", dpi=150)
    plt.close(fig)


# ============ 3. Boîtes à moustaches par zone (outliers) ============
def chart_boxplot():
    order = zone.sort_values("temps_min_median_min", ascending=True)["zone"].tolist()
    data = [df.loc[df["zone"] == z, "temps_min_min"].dropna().values for z in order]
    means = [s.mean() for s in data]
    XMAX = 175  # au-delà : outliers "vélo seul" (lycées 77 lointains sans TC)

    fig, ax = plt.subplots(figsize=(12, 7.5))
    bp = ax.boxplot(data, orientation="horizontal", widths=0.6, patch_artist=True,
                    showfliers=True, flierprops=dict(marker="o", markersize=4,
                    markerfacecolor=INK2, markeredgecolor="none", alpha=0.45),
                    medianprops=dict(color=INK, linewidth=2),
                    whiskerprops=dict(color=INK2, linewidth=1.2),
                    capprops=dict(color=INK2, linewidth=1.2))
    for patch, z in zip(bp["boxes"], order):
        patch.set_facecolor(ORANGE if is_grande(z) else BLUE)
        patch.set_alpha(0.55)
        patch.set_edgecolor(ORANGE if is_grande(z) else BLUE)
    # moyenne (losange) pour montrer l'écart moyenne vs médiane
    ax.scatter(means, range(1, len(order) + 1), marker="D", s=42, color=INK,
               zorder=5, label="Moyenne")
    # outliers hors cadre : marqueur ">" clampé au bord + label court empilé
    outlier_notes = []
    offs = [0.0, 0.26, -0.26]
    for i, z in enumerate(order, start=1):
        outs = sorted([v for v in data[i - 1] if v > XMAX], reverse=True)
        for j, v in enumerate(outs):
            commune = df.loc[(df["zone"] == z) & (df["temps_min_min"] == v), "commune"].iloc[0]
            yy = i + offs[j % 3]
            ax.plot(XMAX, yy, marker=">", color=ORANGE, markersize=10, clip_on=False, zorder=6)
            ax.text(XMAX - 3, yy, f"{v:.0f} min", ha="right", va="center",
                    fontsize=8.5, color=ORANGE, fontweight="bold")
            outlier_notes.append(f"{commune} {v:.0f}")
    ax.set_yticks(range(1, len(order) + 1))
    ax.set_yticklabels(order)
    ax.set_xlim(0, XMAX + 8)
    ax.xaxis.grid(True, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Temps minimal (vélo ou transports) par lycée — min")
    ax.set_title("Distribution des temps par zone — médiane, quartiles et outliers",
                 fontsize=16, fontweight="bold", color=INK, loc="left", pad=14)
    base_ax(ax)
    ax.legend(handles=[Patch(color=BLUE, alpha=0.55, label="Petite couronne (93/94)"),
                       Patch(color=ORANGE, alpha=0.55, label="Grande couronne (77)"),
                       Line2D([0], [0], marker="D", color="none", markerfacecolor=INK,
                              markersize=8, label="Moyenne"),
                       Line2D([0], [0], color=INK, lw=2, label="Médiane")],
              loc="lower right", frameon=False, fontsize=10)
    fig.text(0.012, 0.045,
             "Lecture : la moyenne (losange) est tirée à droite de la médiane en Seine-et-Marne, signe d'outliers.",
             fontsize=9.5, color=INK2)
    fig.text(0.012, 0.012,
             "Outliers vélo seul (> " + str(XMAX) + " min) : " + " · ".join(outlier_notes) + " min.",
             fontsize=9.5, color=ORANGE)
    fig.tight_layout(rect=(0, 0.075, 1, 1))
    fig.savefig("viz/zone_boxplot.png", dpi=150)
    plt.close(fig)


# ============ 4. Vélo vs transports (nuage) ============
def chart_scatter():
    fig, ax = plt.subplots(figsize=(9.5, 9))
    lim = 150
    ax.plot([0, lim], [0, lim], color=INK2, lw=1, ls="--", zorder=2)
    ax.text(lim * 0.97, lim * 0.99, "vélo = transports", color=INK2, fontsize=10,
            ha="right", va="top", rotation=45, rotation_mode="anchor")
    for dep in ["93", "94", "77"]:
        s = df[df["dep"] == dep]
        ax.scatter(s["transport_temps_min"], s["velo_temps_min"], s=46,
                   color=DEP_COLOR[dep], alpha=0.8, edgecolor=SURFACE, linewidth=0.6,
                   label=DEP_LABEL[dep], zorder=3)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal")
    ax.grid(True, color=GRID, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Temps transports en commun (min)")
    ax.set_ylabel("Temps vélo (min)")
    ax.set_title("Vélo vs transports par lycée", fontsize=16, fontweight="bold",
                 color=INK, loc="left", pad=14)
    ax.text(0, -22, "Au-dessus de la diagonale : les transports sont plus rapides que le vélo. "
            "5 lycées 77 sans solution transports ne sont pas représentés.",
            fontsize=9, color=INK2)
    base_ax(ax)
    ax.legend(loc="upper left", frameon=False, fontsize=11, title="Département")
    fig.tight_layout()
    fig.savefig("viz/bike_vs_transport.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_avg()
    chart_count()
    chart_boxplot()
    chart_scatter()
    print("Charts written to viz/: zone_avg_time.png, zone_count.png, zone_boxplot.png, bike_vs_transport.png")
