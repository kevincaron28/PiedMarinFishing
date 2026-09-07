# -*- coding: utf-8 -*-
"""Convertisseur metrique -> imperial pour les reperes des fiches d'espece.

Le ministere publie en centimetres et en kilogrammes; sur un bateau au Quebec
on parle en pouces et en livres. Plutot que d'ecrire les deux dans les
donnees — ou elles finiraient par se contredire — la valeur reste en metrique
et la conversion est calculee au build.
"""
import re

def _n(txt):
    return float(txt.replace(",", ".").replace(" ", "").replace(" ", ""))

def _fmt(v, dec=0):
    s = ("%.*f" % (dec, v)).rstrip("0").rstrip(".") if dec else "%d" % round(v)
    return s.replace(".", ",")

def _fmt_en(v, dec=0):
    return ("%.*f" % (dec, v)).rstrip("0").rstrip(".") if dec else "%d" % round(v)

NUM = r"\d+(?:[.,]\d+)?"

def convert(text, lang="fr"):
    """Ajoute l'equivalent imperial apres chaque mesure metrique.

    Les intervalles sont traites AVANT les valeurs seules, et remplaces par un
    jeton le temps du second passage : sans ca, « 25 a 113 cm » devenait
    « 25 a 113 cm (44 po) (10 a 44 po) », la regle des valeurs seules ayant
    retrouve le « 113 cm » a l'interieur du texte deja converti.
    """
    if not text:
        return text
    fm = _fmt if lang == "fr" else _fmt_en
    U = {"in": "po", "ft": "pi", "lb": "lb", "oz": "oz"} if lang == "fr" else \
        {"in": "in", "ft": "ft", "lb": "lb", "oz": "oz"}
    JOIN = " à " if lang == "fr" else " to "
    held = []

    def keep(s):
        held.append(s)
        return "\x00%d\x00" % (len(held) - 1)

    def pouces(v):
        """Un decimal sous 3 po : « 4 a 5 cm » donnait « 2 a 2 po »."""
        return fm(v, 1 if v < 3 else 0)

    def grammes(v_g):
        """Au-dela d'une livre, on parle en livres. « 600 g (21,2 oz) » est
        exact et illisible pour quelqu'un qui pese ses poissons."""
        return (fm(v_g * 0.00220462, 1), U["lb"]) if v_g >= 454 \
            else (fm(v_g * 0.035274, 1), U["oz"])

    def rng(m, factor, unit, dec=0):
        a, b = _n(m.group(1)), _n(m.group(2))
        if unit == U["oz"]:
            (va, ua), (vb, ub) = grammes(a), grammes(b)
            if ua == ub:
                return keep("%s (%s%s%s %s)" % (m.group(0), va, JOIN, vb, ua))
            return keep("%s (%s %s%s%s %s)" % (m.group(0), va, ua, JOIN, vb, ub))
        f = pouces if unit == U["in"] else (lambda v: fm(v, dec))
        sa, sb = f(a * factor), f(b * factor)
        if sa == sb:
            return keep("%s (%s %s)" % (m.group(0), sa, unit))
        return keep("%s (%s%s%s %s)" % (m.group(0), sa, JOIN, sb, unit))

    def one(m, factor, unit, dec=0):
        v = _n(m.group(1))
        if unit == U["oz"]:
            val, u = grammes(v)
            return keep("%s (%s %s)" % (m.group(0), val, u))
        f = pouces if unit == U["in"] else (lambda x: fm(x, dec))
        return keep("%s (%s %s)" % (m.group(0), f(v * factor), unit))

    # Les metres deviennent pieds-pouces sous 3 m — c'est l'echelle d'un
    # poisson, et « 4 pi 11 po » est ce qu'on dit sur un bateau, pas
    # « 4,9 pi ». Au-dela, c'est une profondeur : le pied entier suffit, et
    # « 147 pi 8 po » de fond serait une precision inventee.
    def metres(m, *_):
        vals = [g for g in m.groups() if g]
        parts = []
        for v in vals:
            ft_total = _n(v) * 3.28084
            if _n(v) < 3:
                ft = int(ft_total)
                inch = int(round((ft_total - ft) * 12))
                if inch == 12:
                    ft, inch = ft + 1, 0
                parts.append("%d %s%s" % (ft, U["ft"],
                                          " %d %s" % (inch, U["in"]) if inch else ""))
            else:
                parts.append("%d %s" % (round(ft_total), U["ft"]))
        return keep("%s (%s)" % (m.group(0), JOIN.join(parts)))

    SPEC = [(r"cm\b", 0.393701, U["in"], 0),
            (r"m\b(?!m)", metres, None, 0),
            (r"kg\b", 2.20462, U["lb"], 1),
            (r"g\b(?!\w)", 0.035274, U["oz"], 1)]
    out = text
    for pat, factor, unit, dec in SPEC:
        fn = factor if callable(factor) else (
            lambda m, f=factor, u=unit, d=dec: rng(m, f, u, d))
        out = re.sub(r"(%s)\s*(?:à|to)\s*(%s)\s*%s" % (NUM, NUM, pat), fn, out)
    for pat, factor, unit, dec in SPEC:
        fn = factor if callable(factor) else (
            lambda m, f=factor, u=unit, d=dec: one(m, f, u, d))
        out = re.sub(r"(%s)\s*%s" % (NUM, pat), fn, out)
    for i, s in enumerate(held):
        out = out.replace("\x00%d\x00" % i, s)
    return out


if __name__ == "__main__":
    tests = [
        "25 à 113 cm — peut dépasser 1,5 m",
        "Peut dépasser 40 kg",
        "0,5 à 1,5 kg en moyenne; plus de 5 kg possible",
        "Eaux chaudes, 20 à 26 °C",
        "Généralement moins de 150 g",
        "0,75 à 2 m, sur fond de roche et de gravier",
        "Rang de précarité S4",
        "Mi-juin à juillet, en eau vive, quand l'eau approche 21 °C",
        "14 à 23 cm — peut dépasser 30 cm",
        "Surtout à moins de 9 m, parfois à plus de 45 m",
        "1 300 à 15 000 œufs par période de fraie",
        "300 000 à 600 000 œufs par kilogramme de poids corporel",
        "Jusqu'à 5,5 kg",
        "Plus de 10 ans",
    ]
    for t in tests:
        print("  %-58s -> %s" % (t, convert(t)))
    print()
    for t in ["25 to 113 cm — can exceed 1.5 m", "Up to 5.5 kg", "Warm water, 20 to 26 °C",
              "Generally under 150 g", "Mostly under 9 m, occasionally over 45 m"]:
        print("  %-58s -> %s" % (t, convert(t, "en")))
