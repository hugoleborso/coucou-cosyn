"""COSYN-30 -- lance toute la chaine de calcul et archive le rapport brut."""
import io, sys, contextlib, subprocess, pathlib

ETAPES = [
    ("test_fem", "Validation du solveur elements finis"),
    ("params", "Parametrage et geometrie cycle"),
    ("c02_cadre", "Verification structurelle du cadre"),
    ("c03_roue", "Roue deployable a jante segmentee"),
    ("c04_telescopes", "Emmanchements telescopiques"),
    ("c05_masses", "Bilan de masse"),
    ("c06_encombrement", "Encombrement / rangement dans le sac"),
    ("c07_fatigue", "Tenue en fatigue sur spectre"),
    ("c08_plans", "Generation des plans SVG"),
]

if __name__ == "__main__":
    out = pathlib.Path("../out/rapport-calculs.txt")
    buf = io.StringIO()
    for mod, titre in ETAPES:
        print(f"--> {titre} ({mod}.py)", file=sys.stderr)
        head = f"\n\n{'#'*100}\n# {titre}   [{mod}.py]\n{'#'*100}\n"
        buf.write(head)
        r = subprocess.run([sys.executable, f"{mod}.py"], capture_output=True,
                           text=True)
        buf.write(r.stdout)
        if r.returncode:
            buf.write("\nERREUR:\n" + r.stderr)
            print(r.stderr, file=sys.stderr)
    out.write_text(buf.getvalue())
    print(f"\nRapport complet : {out} ({len(buf.getvalue())} caracteres)",
          file=sys.stderr)
