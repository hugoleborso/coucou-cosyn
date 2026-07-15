import json, pandas as pd

data = json.load(open("data/lycees_raw.geojson", encoding="utf-8"))
rows = []
for f in data["features"]:
    p = f["properties"]
    if p.get("academie") == "Créteil" and p.get("statut") == "public":
        lon, lat = f["geometry"]["coordinates"]
        rows.append({
            "code_uai": p.get("code_uai"),
            "nom_etablissement": p.get("nom_etablissement"),
            "nature_uai": p.get("nature_uai"),
            "statut": p.get("statut"),
            "academie": p.get("academie"),
            "dep": p.get("dep"),
            "commune": p.get("libelle"),
            "code_insee": p.get("code_insee"),
            "code_postal": p.get("code_postal"),
            "adresse_postale": p.get("adresse_postale"),
            "lat": lat,
            "lon": lon,
        })
df = pd.DataFrame(rows)
df.to_csv("data/lycees_creteil_public.csv", index=False)
print("Rows:", len(df))
print("Departments:", df["dep"].value_counts().to_dict())
print("Distinct communes:", df["commune"].nunique())
print(df[["code_uai","nom_etablissement","commune","lat","lon"]].head().to_string())
