"""
Aggregate the enriched lycées dataframe.

Always produces:
  - data/agg_by_commune.csv       : count + avg(min time) per commune
  - data/agg_by_departement.csv   : count + avg(min time) per département (77/93/94)

If a commune -> zone mapping is available at data/zones_mapping.csv
(columns: commune,zone), it also produces the requested ALADDIN-zone rollup:
  - data/agg_by_zone.csv          : count + avg(min time) per zone
and reports any communes that could not be matched to a zone.

Commune names are normalised (accent/case/punctuation-insensitive) so the
zone list pasted from aladdin.ac-creteil.fr matches the dataset reliably.
"""
import os
import unicodedata
import pandas as pd


def norm(name):
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("-", " ").replace("'", " ")
    s = s.replace("ST ", "SAINT ").replace("STE ", "SAINTE ")
    # collapse arrondissement suffixes e.g. "PARIS 12E" -> "PARIS"
    s = " ".join(s.split())
    return s


def main():
    df = pd.read_csv("data/lycees_with_times.csv")
    df["temps_min_min"] = pd.to_numeric(df["temps_min_min"], errors="coerce")

    # ---- by commune ----
    by_commune = (
        df.groupby("commune")
        .agg(nb_lycees=("code_uai", "count"),
             temps_min_moyen_min=("temps_min_min", "mean"))
        .reset_index()
        .sort_values("nb_lycees", ascending=False)
    )
    by_commune["temps_min_moyen_min"] = by_commune["temps_min_moyen_min"].round(1)
    by_commune.to_csv("data/agg_by_commune.csv", index=False)

    # ---- by département ----
    by_dep = (
        df.groupby("dep")
        .agg(nb_lycees=("code_uai", "count"),
             temps_min_moyen_min=("temps_min_min", "mean"))
        .reset_index()
        .sort_values("dep")
    )
    by_dep["temps_min_moyen_min"] = by_dep["temps_min_moyen_min"].round(1)
    by_dep.to_csv("data/agg_by_departement.csv", index=False)

    print("=== Aggregation by département ===")
    print(by_dep.to_string(index=False))
    print(f"\n=== Aggregation by commune (top 15 of {len(by_commune)}) ===")
    print(by_commune.head(15).to_string(index=False))

    # ---- by zone (only if mapping available) ----
    if os.path.exists("data/zones_mapping.csv"):
        zmap = pd.read_csv("data/zones_mapping.csv")
        zmap["_key"] = zmap["commune"].map(norm)
        lookup = dict(zip(zmap["_key"], zmap["zone"]))
        df["zone"] = df["commune"].map(lambda c: lookup.get(norm(c)))
        unmatched = sorted(df.loc[df["zone"].isna(), "commune"].unique())
        if unmatched:
            print(f"\n[!] {len(unmatched)} communes not matched to a zone:")
            for c in unmatched:
                print("   -", c)
        by_zone = (
            df.dropna(subset=["zone"]).groupby("zone")
            .agg(nb_lycees=("code_uai", "count"),
                 temps_min_moyen_min=("temps_min_min", "mean"),
                 temps_min_median_min=("temps_min_min", "median"),
                 temps_min_min_min=("temps_min_min", "min"),
                 temps_min_max_min=("temps_min_min", "max"))
            .reset_index()
            .sort_values("temps_min_moyen_min")
        )
        for c in ["temps_min_moyen_min", "temps_min_median_min",
                  "temps_min_min_min", "temps_min_max_min"]:
            by_zone[c] = by_zone[c].round(1)
        by_zone.to_csv("data/agg_by_zone.csv", index=False)
        df.to_csv("data/lycees_with_times.csv", index=False)  # persist zone col
        print("\n=== Aggregation by ZONE (ALADDIN Créteil) ===")
        print(by_zone.to_string(index=False))
    else:
        print("\n[i] data/zones_mapping.csv not found -> by-zone rollup skipped.")
        print("    Provide the aladdin commune->zone list to produce agg_by_zone.csv.")


if __name__ == "__main__":
    main()
