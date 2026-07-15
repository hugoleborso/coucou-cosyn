"""
Parse data/zones_source.txt (pasted from aladdin.ac-creteil.fr/.../liste_zones.php)
into data/zones_mapping.csv with columns: commune,zone.

A line is a zone header if it starts with "zone" (any case); otherwise a
non-empty line after the first header is a commune. The "(Commune de référence)"
suffix is stripped.
"""
import csv
import re

rows = []
current_zone = None
with open("data/zones_source.txt", encoding="utf-8") as f:
    for raw in f:
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("liste des zones"):
            continue
        if line.lower().startswith("zone"):
            # normalise leading word to "Zone"
            current_zone = "Zone " + line[len("zone"):].strip()
            continue
        if current_zone is None:
            continue
        commune = re.sub(r"\s*\(Commune de r[ée]f[ée]rence\)\s*$", "", line, flags=re.I).strip()
        rows.append((commune, current_zone))

# 3 communes hosting a lycée that the page does not list individually, but which
# fall clearly inside a single zone on the ALADDIN zone map. Assigned to the zone
# of their nearest already-classified lycée (1.6–4.4 km away), matching the map polygons.
MANUAL_ADDITIONS = [
    ("Chailly-en-Brie", "Zone Centre Seine et Marne"),  # jouxte Coulommiers (4.4 km)
    ("La Rochette", "Zone Sud Seine et Marne"),          # jouxte Dammarie-les-Lys (1.6 km)
    ("Saint-Mammès", "Zone Sud Seine et Marne"),         # jouxte Champagne-sur-Seine (2.4 km)
]
rows.extend(MANUAL_ADDITIONS)

with open("data/zones_mapping.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["commune", "zone"])
    w.writerows(rows)

zones = {}
for c, z in rows:
    zones.setdefault(z, 0)
    zones[z] += 1
print(f"{len(rows)} communes across {len(zones)} zones")
for z, n in zones.items():
    print(f"  {z}: {n}")
