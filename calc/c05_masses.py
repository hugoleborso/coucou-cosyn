"""
COSYN-30 -- BILAN DE MASSE detaille.

Chaque ligne est marquee :
  [C] calculee a partir de la geometrie et de la masse volumique
  [E] estimee d'apres des composants existants du marche (+/- incertitude)
L'objectif de 8,00 kg est confronte a la somme et a son incertitude cumulee.
"""
from __future__ import annotations
import json
import numpy as np

import c02_cadre as C
from params import Geo as G, Loads as LD, MAT

AL = MAT["AL7075T6"]


def tube_mass(key, length):
    s = C.SEC[key]
    return s.mass_per_m * length


def rim_mass():
    b, h, t = G.rim_w, G.rim_h, G.rim_t
    A = b * h - (b - 2 * t) * (h - 2 * t)
    L = 2 * np.pi * G.rim_r_mid
    return A * L * AL["rho"]


def tread_mass():
    R_out = G.rim_r_mid + G.rim_h / 2
    L = 2 * np.pi * (R_out + G.tread_t / 2)
    V = L * G.tread_w * G.tread_t
    return V * MAT["PU85A"]["rho"] * G.tread_rho_rel + 0.020   # + cordage aramide


def spoke_mass():
    from c03_roue import spoke_geom
    L, _ = spoke_geom()
    A_eq = np.pi * (0.5 * (G.spoke_d + G.spoke_d_mid)) ** 2 / 4
    return G.n_spokes * (A_eq * L * MAT["INOX_RAYON"]["rho"] + 0.0009)


def frame_tube_masses():
    m = C.build_frame()
    out = {}
    for e in m.beams:
        if e["sec"].name == "rigide":
            continue
        L = np.linalg.norm(m.nodes[e["n2"]] - m.nodes[e["n1"]])
        out[e["sec"].name] = out.get(e["sec"].name, 0.0) + e["sec"].mass_per_m * L
    return out


def bom():
    ft = frame_tube_masses()
    tubes_poutre = sum(v for k, v in ft.items() if k.startswith(("poutre", "j")))
    items = [
        # (groupe, designation, masse kg, type, incertitude relative)
        ("Roues", "Jante : 8 arcs extrudes 7075-T6 24x22x1.5", 2 * rim_mass(), "C", 0.05),
        ("Roues", "Tenons coniques d'arc (8/roue, 7075 usine)",
         2 * G.n_seg * 0.0090, "E", 0.20),
        ("Roues", "Cordon captif aramide 4 mm + embouts", 2 * 0.035, "E", 0.20),
        ("Roues", f"Rayons inox {G.n_spokes} x Ø1.8/1.6 + ecrous",
         2 * spoke_mass(), "C", 0.08),
        ("Roues", f"Inserts de siege de rayon ({G.n_spokes}/roue)",
         2 * G.n_spokes * 0.0012, "E", 0.20),
        ("Roues", "Moyeu a brides ecartables + came + roulements", 2 * 0.290, "E", 0.15),
        ("Roues", "Bande de roulement PU alveolaire + cordage", 2 * tread_mass(), "C", 0.12),
        ("Roues", "Disque de frein Ø140 + visserie", 2 * 0.090, "E", 0.10),

        ("Cadre", "Poutre principale 3 etages + douilles", tubes_poutre, "C", 0.05),
        ("Cadre", "Bras arriere monobranche + hauban + mat",
         ft.get("base", 0) + ft.get("hauban", 0) + ft.get("mat_selle", 0), "C", 0.05),
        ("Cadre", "Tube de direction + jeu de direction",
         ft.get("tube_dir", 0) + 0.090, "C", 0.10),
        ("Cadre", "Fourche monobras + te", ft.get("fourreau", 0) + 0.095, "C", 0.12),
        ("Cadre", "Tourillons de roue AV/AR + ecrous centraux",
         2 * 0.105, "E", 0.15),
        ("Cadre", "Raccords colles-goupilles (6)", 6 * 0.045, "E", 0.20),
        ("Cadre", "Boitier de pedalier (axe + roulements)", 0.180, "E", 0.10),

        ("Cadre", "Expandeurs coniques + leviers (5)", 5 * 0.055, "E", 0.20),
        ("Cadre", "Charnieres mat de selle + poutre (2)", 2 * 0.075, "E", 0.20),

        ("Poste de pilotage", "Colonne de direction 2 etages",
         ft.get("col1", 0) + ft.get("col2", 0), "C", 0.05),
        ("Poste de pilotage", "Demi-cintres repliables + charniere",
         ft.get("cintre", 0) + 0.070, "C", 0.15),
        ("Poste de pilotage", "Poignees + leviers de frein", 0.150, "E", 0.10),

        ("Selle", "Tige de selle 3 etages",
         sum(v for k, v in ft.items() if k.startswith("tds")), "C", 0.05),
        ("Selle", "Selle compacte + chariot", 0.220, "E", 0.10),

        ("Transmission", "Manivelles 152 mm demontables (vis auto-extractibles)",
         ft.get("manivelle", 0) + 0.075, "C", 0.15),
        ("Transmission", "Plateau 34 d. + araignee", 0.100, "E", 0.10),
        ("Transmission", "Chaine 1/2 x 3/32 (86 maillons)", 0.250, "E", 0.08),
        ("Transmission", "Roue libre 12 d. + tendeur", 0.130, "E", 0.12),
        ("Transmission", "Pedales pliantes (paire)", 0.190, "E", 0.10),

        ("Freinage", "Etriers mecaniques a disque (2)", 0.210, "E", 0.10),
        ("Freinage", "Cables + gaines + butees", 0.110, "E", 0.15),

        ("Suspension", "Elements elastomere AV + AR (30 mm)", 2 * 0.110, "E", 0.20),

        ("Divers", "Visserie, butees, temoins, protections", 0.150, "E", 0.25),
    ]
    return items


def main():
    items = bom()
    groupes = {}
    for g, d, m, t, u in items:
        groupes.setdefault(g, []).append((d, m, t, u))

    print("=" * 92)
    print("BILAN DE MASSE COSYN-30")
    print("=" * 92)
    total = 0.0
    var = 0.0
    for g, lst in groupes.items():
        sub = sum(x[1] for x in lst)
        print(f"\n{g.upper()}  ({sub*1000:.0f} g)")
        for d, m, t, u in lst:
            print(f"   [{t}] {d:<52}{m*1000:8.0f} g   +/-{u*100:3.0f}%")
            total += m
            var += (m * u) ** 2
    sd = np.sqrt(var)
    print("\n" + "=" * 92)
    print(f"{'TOTAL':<58}{total*1000:8.0f} g   +/- {sd*1000:.0f} g")
    print(f"{'Objectif':<58}{LD.m_bike_target*1000:8.0f} g")
    print(f"{'Marge':<58}{(LD.m_bike_target-total)*1000:8.0f} g "
          f"({100*(LD.m_bike_target-total)/LD.m_bike_target:+.1f} %)")
    p = 100 * 0.5 * (1 + __import__("math").erf((LD.m_bike_target - total) / (sd * np.sqrt(2)))) \
        if sd > 0 else 100.0
    print(f"Probabilite de tenir 8,00 kg (loi normale sur les incertitudes) : {p:.0f} %")
    print("=" * 92)

    print("\nRepartition")
    for g, lst in sorted(groupes.items(), key=lambda kv: -sum(x[1] for x in kv[1])):
        sub = sum(x[1] for x in lst)
        bar = "#" * int(round(40 * sub / total))
        print(f"  {g:<18}{sub*1000:7.0f} g  {100*sub/total:5.1f} %  {bar}")

    print("\nLeviers d'allegement identifies")
    lev = [("Fourche + poutre en carbone stratifie", 0.250,
            "gain net apres surdimensionnement des zones d'appui"),
           ("Jante 7075 -> jante carbone enroulee", 0.240,
            "necessite de repenser le tenon conique (insert titane colle)"),
           ("Bande alveolaire -> boyau pneumatique repliable", 0.090,
            "gagne aussi 64 W de resistance au roulement, perd l'increvabilite"),
           ("Chaine -> courroie crantee + poulies", -0.050,
            "plus lourd mais supprime le graissage"),
           ("Suppression de la suspension elastomere", 0.220,
            "DECONSEILLE : multiplie par 2.7 les efforts de choc")]
    for d, gmass, note in lev:
        print(f"   {d:<50}{gmass*1000:+7.0f} g   {note}")

    with open("../out/masses.json", "w") as f:
        json.dump(dict(items=[dict(groupe=g, designation=d, kg=m, type=t, u=u)
                              for g, d, m, t, u in items],
                       total_kg=total, ecart_type_kg=sd,
                       objectif_kg=LD.m_bike_target), f, indent=1, default=float)


if __name__ == "__main__":
    main()
