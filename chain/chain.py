"""Chaîne de victoires Chess.com : hugoleborso -> ... -> magnuscarlsen.
A -> B signifie "A a battu B". Recherche bidirectionnelle best-first :
 - avant (depuis moi) : on suit les victoires, en priorisant les adversaires battus les mieux classés
 - arrière (depuis Magnus) : on suit les défaites, en priorisant les vainqueurs les moins bien classés
Le score combine écart d'Elo, profondeur, et activité (nb de parties vues) pour éviter les impasses.
"""
import heapq, json, math, os, sys, time, hashlib
from concurrent.futures import ThreadPoolExecutor
import requests

START, TARGET = sys.argv[1].lower(), sys.argv[2].lower()
MONTHS = int(os.environ.get("MONTHS", 4))
MIN_PLIES = int(os.environ.get("MIN_PLIES", 20))
EXTRA_AFTER = int(os.environ.get("EXTRA_AFTER", 60))  # expansions supplémentaires pour raccourcir
MAX_EXPANSIONS = int(os.environ.get("MAX_EXP", 400))
CACHE = os.path.join(os.path.dirname(__file__), ".cache"); os.makedirs(CACHE, exist_ok=True)
S = requests.Session(); S.headers["User-Agent"] = "win-chain-finder/1.0 (contact: hugoleborso on chess.com)"

def get(url):
    p = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".json")
    if os.path.exists(p):
        return json.load(open(p))
    for attempt in range(6):
        r = S.get(url, timeout=30)
        if r.status_code == 429: time.sleep(2 ** attempt); continue
        if r.status_code in (404, 410): data = {}; break
        r.raise_for_status(); data = r.json(); break
    else:
        data = {}
    json.dump(data, open(p, "w")); return data

def games(user):
    arch = get(f"https://api.chess.com/pub/player/{user}/games/archives").get("archives", [])[-MONTHS:]
    with ThreadPoolExecutor(4) as ex:
        return [g for m in ex.map(get, arch) for g in m.get("games", [])]

def edges(user, want):  # want="win" -> adversaires battus ; "loss" -> vainqueurs
    out = {}
    for g in games(user):
        if g.get("rules") != "chess": continue
        # une vraie victoire : pas d'abandon de connexion, au moins MIN_PLIES demi-coups joués
        if "abandoned" in (g["white"]["result"], g["black"]["result"]): continue
        if g.get("pgn", "").count("[%clk") < MIN_PLIES: continue
        w, b = g["white"], g["black"]
        me, op = (w, b) if w["username"].lower() == user else (b, w)
        if me["username"].lower() != user: continue
        ok = me["result"] == "win" if want == "win" else op["result"] == "win"
        if ok:
            o = op["username"].lower(); r = op.get("rating", 0)
            if o not in out or r > out[o][0]:
                out[o] = (r, g["url"], g.get("time_class"), me.get("rating"))
    return out

def rating_of(user):
    st = get(f"https://api.chess.com/pub/player/{user}/stats")
    return max([v["last"]["rating"] for k, v in st.items() if k.startswith("chess_") and k != "chess_daily" and "last" in v] or [0])

R_START, R_TARGET = rating_of(START), rating_of(TARGET)
print(f"{START} ~{R_START}  ->  {TARGET} ~{R_TARGET}", flush=True)
DEPTH_PEN = 150  # coût d'un maillon, exprimé en points d'Elo

# parent[side][node] = (prev_node, game_info)
parent = {"f": {START: None}, "b": {TARGET: None}}
depth = {"f": {START: 0}, "b": {TARGET: 0}}
seen_count = {"f": {}, "b": {}}
heap = {"f": [(0, START)], "b": [(0, TARGET)]}
expanded = {"f": set(), "b": set()}

def chain(meet):
    left, n = [], meet
    while parent["f"][n]: p, info = parent["f"][n]; left.append((p, n, info)); n = p
    left.reverse(); right, n = [], meet
    while parent["b"][n]: p, info = parent["b"][n]; right.append((n, p, info)); n = p
    return left + right

def prio(side, r, d, cnt):
    gap = (R_TARGET - r) if side == "f" else (r - R_START)
    return gap + DEPTH_PEN * d - 40 * math.log1p(cnt)

best = None
for it in range(MAX_EXPANSIONS):
    side = "f" if len(heap["f"]) and (it % 2 == 0 or not heap["b"]) else "b"
    if not heap[side]: break
    _, u = heapq.heappop(heap[side])
    if u in expanded[side]: continue
    expanded[side].add(u)
    other = "b" if side == "f" else "f"
    nb = edges(u, "win" if side == "f" else "loss")
    print(f"[{it}] {side} expand {u} (d={depth[side][u]}) -> {len(nb)} voisins", flush=True)
    for o, (r, url, tc, ur) in nb.items():
        seen_count[side][o] = seen_count[side].get(o, 0) + 1
        if o not in parent[side]:
            parent[side][o] = (u, (url, tc, ur, r) if side == "f" else (url, tc, r, ur)); depth[side][o] = depth[side][u] + 1
            heapq.heappush(heap[side], (prio(side, r, depth[side][o], seen_count[side][o]), o))
        if o in parent[other]:
            L = depth[side][o] + depth[other][o]
            if best is None or L < best[0]:
                best = (L, chain(o)); best_it = it; print(f"*** chaîne trouvée : {L} victoires via {o}", flush=True)
    if best and it >= best_it + EXTRA_AFTER:
        break
if best:
    print(f"\n=== {best[0]} victoires ===")
    for a, b, (url, tc, ra, rb) in best[1]:
        print(f"{a} ({ra}) bat {b} ({rb}) [{tc}] {url}")
    json.dump(best[1], open(os.path.join(os.path.dirname(__file__), "best.json"), "w"), indent=1)
else:
    print("pas de chaîne trouvée")
