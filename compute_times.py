"""
Compute transport times from 118 rue d'Aboukir (Paris) to each lycée using
the Île-de-France Mobilités PRIM APIs:
  - BIKE      : Geovelo route planner  (POST marketplace/computedroutes)
  - TRANSPORT : Navitia journey planner (GET  marketplace/v2/navitia/journeys)

Durations are stored in seconds and minutes. Results are written incrementally
to data/lycees_with_times.csv so progress is never lost.
"""
import json, time, sys, os
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Clé API PRIM lue dans l'environnement — ne jamais committer la clé en clair.
#   export PRIM_API_KEY="votre_cle"
API_KEY = os.environ.get("PRIM_API_KEY")
if not API_KEY:
    raise SystemExit("Définir la variable d'environnement PRIM_API_KEY (clé API PRIM IDFM).")
BASE = "https://prim.iledefrance-mobilites.fr/marketplace"

# Origin: 118 rue d'Aboukir, 75002 Paris (geocoded via BAN / api-adresse)
ORIGIN_LAT, ORIGIN_LON = 48.868771, 2.350606

BIKE_URL = f"{BASE}/computedroutes?instructions=false&elevations=false&geometry=false&single_result=true&bike_stations=false&objects_as_ids=true"
NAV_URL = f"{BASE}/v2/navitia/journeys"

session = requests.Session()


def bike_seconds(lat, lon):
    """Geovelo bike route duration (seconds) from origin to (lat, lon)."""
    body = {
        "waypoints": [
            {"latitude": ORIGIN_LAT, "longitude": ORIGIN_LON, "title": "Aboukir"},
            {"latitude": lat, "longitude": lon, "title": "lycee"},
        ],
        "transportModes": ["BIKE"],
        "bikeDetails": {
            "profile": "MEDIAN",
            "bikeType": "TRADITIONAL",
            "averageSpeed": 15,
            "eBike": False,
        },
    }
    headers = {
        "apikey": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Source": "prim",
    }
    r = session.post(BIKE_URL, headers=headers, data=json.dumps(body), timeout=40)
    r.raise_for_status()
    routes = r.json()
    if not routes:
        return None
    # single_result=true -> take the (single) recommended route duration
    durs = [rt.get("duration") for rt in routes if rt.get("duration") is not None]
    return min(durs) if durs else None


def transport_seconds(lat, lon):
    """Navitia public-transport journey duration (seconds), fastest journey."""
    params = {
        "from": f"{ORIGIN_LON};{ORIGIN_LAT}",  # Navitia expects lon;lat
        "to": f"{lon};{lat}",
    }
    headers = {"apikey": API_KEY, "Accept": "application/json"}
    r = session.get(NAV_URL, headers=headers, params=params, timeout=40)
    r.raise_for_status()
    data = r.json()
    journeys = data.get("journeys") or []
    durs = [j.get("duration") for j in journeys if j.get("duration") is not None]
    return min(durs) if durs else None


def with_retry(fn, *args, tries=4):
    last = None
    for i in range(tries):
        try:
            return fn(*args), None
        except Exception as e:  # noqa
            last = e
            time.sleep(1.5 * (i + 1))
    return None, str(last)


def process(idx, row):
    lat, lon = row["lat"], row["lon"]
    b, be = with_retry(bike_seconds, lat, lon)
    t, te = with_retry(transport_seconds, lat, lon)
    return idx, b, t, be, te


def main():
    df = pd.read_csv("data/lycees_creteil_public.csv")
    df["velo_temps_s"] = pd.NA
    df["transport_temps_s"] = pd.NA
    errors = []

    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(process, i, df.loc[i]): i for i in df.index}
        done = 0
        for fut in as_completed(futs):
            idx, b, t, be, te = fut.result()
            df.at[idx, "velo_temps_s"] = b
            df.at[idx, "transport_temps_s"] = t
            if be:
                errors.append((idx, "bike", be))
            if te:
                errors.append((idx, "transport", te))
            done += 1
            if done % 10 == 0 or done == len(df):
                print(f"  {done}/{len(df)} done", flush=True)
                df.to_csv("data/lycees_with_times.csv", index=False)

    # minutes + min column
    df["velo_temps_min"] = pd.to_numeric(df["velo_temps_s"], errors="coerce") / 60
    df["transport_temps_min"] = pd.to_numeric(df["transport_temps_s"], errors="coerce") / 60
    df["temps_min_s"] = df[["velo_temps_s", "transport_temps_s"]].apply(
        lambda r: pd.to_numeric(r, errors="coerce").min(), axis=1
    )
    df["temps_min_min"] = df["temps_min_s"] / 60
    df.to_csv("data/lycees_with_times.csv", index=False)

    print("=== SUMMARY ===")
    print("rows:", len(df))
    print("bike ok:", df["velo_temps_s"].notna().sum(), "/ transport ok:", df["transport_temps_s"].notna().sum())
    print("errors:", len(errors))
    for e in errors[:20]:
        print("  ", e)
    print(df[["nom_etablissement", "commune", "velo_temps_min", "transport_temps_min", "temps_min_min"]].head(10).to_string())


if __name__ == "__main__":
    main()
