"""Rejoue la recherche hors-ligne sur toutes les parties déjà en cache."""
import json, glob, re, sys
from collections import defaultdict, deque
START, TARGET = (sys.argv[1:3] + ["hugoleborso", "magnuscarlsen"][len(sys.argv[1:3]):])
MIN_PLIES = 20
games = {}
for f in glob.glob(".cache/*.json"):
    d = json.load(open(f))
    if isinstance(d, dict):
        for g in d.get("games", []):
            games[g["url"]] = g
E = defaultdict(dict)  # E[winner][loser] = list of games
for g in games.values():
    if g.get("rules") != "chess": continue
    w, b = g["white"], g["black"]
    if "abandoned" in (w["result"], b["result"]): continue
    if g.get("pgn", "").count("[%clk") < MIN_PLIES: continue
    if w["result"] == "win": win, los = w, b
    elif b["result"] == "win": win, los = b, w
    else: continue
    date = re.search(r'\[Date "([^"]+)"', g["pgn"]).group(1)
    E[win["username"].lower()].setdefault(los["username"].lower(), []).append(
        dict(url=g["url"], tc=g["time_class"], wr=win["rating"], lr=los["rating"], date=date,
             term=re.search(r'\[Termination "([^"]+)"', g["pgn"]).group(1)))
print(len(games), "parties,", sum(len(v) for v in E.values()), "arêtes")

def bfs(src, adj):
    dist = {src: 0}; q = deque([src])
    while q:
        u = q.popleft()
        for v in adj.get(u, {}):
            if v not in dist: dist[v] = dist[u] + 1; q.append(v)
    return dist
R = defaultdict(dict)
for a, nb in E.items():
    for b in nb: R[b][a] = 1
df, db = bfs(START, E), bfs(TARGET, R)
L = df.get(TARGET); print("plus courte chaîne dans le cache :", L)
print("Magnus battu par (dans le cache):", len(R[TARGET]))
# énumère les chaînes de longueur L (et L+1 si demandé)
def paths(maxlen, limit=100000):
    out = []
    def rec(u, path):
        if len(out) >= limit: return
        if u == TARGET: out.append(path[:]); return
        for v in E.get(u, {}):
            if v in path: continue
            if len(path) + db.get(v, 99) <= maxlen:
                path.append(v); rec(v, path); path.pop()
    rec(START, [START]); return out
ps = paths(L)
print(len(ps), f"chaînes de {L} victoires")
def best_game(a, b, pref=None):
    gs = E[a][b]
    return max(gs, key=lambda x: (x["tc"] in ("rapid","blitz"), x["lr"]))
def describe(p):
    return [(a, b, best_game(a, b)) for a, b in zip(p, p[1:])]
scored = []
for p in ps:
    d = describe(p)
    min_gap = min(x["lr"] - x["wr"] for *_, x in d)
    nobullet = all(x["tc"] in ("rapid", "blitz") for *_, x in d)
    dates = [x["date"] for *_, x in d]
    chrono = dates == sorted(dates)
    upsets = sum(x["lr"] > x["wr"] for *_, x in d)
    scored.append((p, d, nobullet, chrono, upsets))
json.dump([[p, d, nb, c, u] for p, d, nb, c, u in scored], open("alt.json", "w"))
print("sans bullet:", sum(s[2] for s in scored), "| chronologiques:", sum(s[3] for s in scored))
print("Joueurs les plus fréquents :")
from collections import Counter
c = Counter(x for s in scored for x in s[0][1:-1])
print(c.most_common(12))
print("1ers maillons :", Counter(s[0][1] for s in scored).most_common(8))
print("derniers maillons (bourreaux de Magnus) :", Counter(s[0][-2] for s in scored).most_common(8))

def show(title, d):
    print("\n##", title)
    for a, b, x in d:
        print(f"  {x['date']} {a} ({x['wr']}) > {b} ({x['lr']}) [{x['tc']}] {x['term']} {x['url']}")
# chaînes de 6 distinctes par bourreau de Magnus
seen = set()
for p, d, *_ in scored:
    if p[-2] not in seen:
        seen.add(p[-2]); show(f"6 victoires via {p[-2]}", d)
# 7 victoires : sans bullet, et chronologique
p7 = paths(L + 1, 300000)
print("\n", len(p7), "chaînes de ≤7")
def ok_nb(p): return all(any(g["tc"] in ("rapid","blitz") for g in E[a][b]) for a, b in zip(p, p[1:]))
nb = [p for p in p7 if ok_nb(p)]
print("sans bullet:", len(nb))
if nb:
    p = min(nb, key=len)
    show(f"sans bullet ({len(p)-1})", [(a, b, max([g for g in E[a][b] if g["tc"] in ("rapid","blitz")], key=lambda g: g["lr"])) for a, b in zip(p, p[1:])])
def chrono(p):  # choix glouton de la partie la plus tôt possible après la précédente
    t, out = "", []
    for a, b in zip(p, p[1:]):
        c = sorted([g for g in E[a][b] if g["date"] >= t], key=lambda g: g["date"])
        if not c: return None
        out.append((a, b, c[0])); t = c[0]["date"]
    return out
ch = [(p, chrono(p)) for p in p7]; ch = [x for x in ch if x[1]]
print("chronologiques:", len(ch))
if ch:
    p, d = min(ch, key=lambda x: len(x[0])); show(f"chronologique ({len(p)-1})", d)
