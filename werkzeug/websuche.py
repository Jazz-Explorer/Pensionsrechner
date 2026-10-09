"""Werte aus Webseiten ermitteln (Vorschläge – müssen vom Benutzer geprüft werden).

Lädt eine Seite (HTML oder JSON-Parameterdatei), wandelt sie in Text um und
sucht zu jedem Parameter Zahlen in der Nähe passender Schlüsselwörter.
Damit nichts Falsches gefunden wird, muss jede Zahl
  - zum Typ passen (Betrag oder Prozentsatz),
  - in einem plausiblen Bereich um den aktuellen Wert liegen,
  - bevorzugt im Umfeld des gesuchten Jahres stehen.
Gibt es mehrere Kandidaten, gewinnt: passendes Jahr > häufigste Nennung > Nähe
zum Schlüsselwort.
"""

import bisect
import html
import json
import re
import urllib.request

# (Name, URL mit {jahr}, Inhalt)
WEBQUELLEN = [
    ("WKO – Einkommensteuer & Absetzbeträge {jahr}",
     "https://www.wko.at/steuern/einkommen-koerperschaftsteuer-{jahr}",
     "Steuertarif, Pensionistenabsetzbetrag"),
    ("WKO – Beitragswesen Selbständige {jahr}",
     "https://www.wko.at/entlohnung/beitragswesen-selbstaendige-{jahr}",
     "SVS-Sätze, Versicherungsgrenze, Mindest-/Höchstbeitragsgrundlage, Unfallversicherung"),
    ("WKO – Gewerbliche SV-Beiträge (aktuell)",
     "https://www.wko.at/sozialversicherung/gewerbliche-sozialversicherungsbeitraege-ausmass",
     "SVS-Sätze und Beitragsgrundlagen für Gewerbetreibende"),
    ("Forvis Mazars – Personalverrechnungswerte 2026",
     "https://www.forvismazars.com/at/de/unsere-expertise/outsourcing/hr-payroll/"
     "newsletter-pv-arbeitsrecht-oktober-2025/personalverrechnungswerte-fuer-das-jahr-2026",
     "Steuertarif, Pensionistenabsetzbetrag, Höchstbeitragsgrundlage (nur 2026)"),
    ("finanz.at – Pensionistenabsetzbetrag",
     "https://www.finanz.at/steuern/pensionistenabsetzbetrag/",
     "Pensionistenabsetzbetrag inkl. Folgejahr"),
    ("finanzinfo.at – Einkommensteuer",
     "https://finanzinfo.at/steuern/einkommensteuer/",
     "Steuertarif"),
    ("raisin.com – Einkommensteuer",
     "https://www.raisin.com/de-at/steuer/einkommensteuer/",
     "Steuertarif"),
    ("selbststaendig-machen.at – SVS-Beiträge",
     "https://selbststaendig-machen.at/svs-beitraege-mindestbeitragsgrundlage/",
     "SVS-Sätze, Mindest-/Höchstbeitragsgrundlage"),
]

_KW_TARIF = r"Tarif\w*|Steuersatz|Steuerstufe|Einkommensteuer\w*|Grenzsteuersatz"
TARIF = [f"est_grenze_{i}" for i in range(1, 7)]
_KW_PAB = r"(?<!erhöhter )(?<!erhöhte )(?<!Erhöhter )Pensionistenabsetzbetr\w*"
_KW_PAB_ERH = r"[Ee]rhöhte[rn]? Pensionistenabsetzbetr\w*"

# key: (Schlüsselwort-Regex, Typ, Toleranz oder (min, max), Fenster in Zeichen)
REGELN = {
    "est_grenze_1": (_KW_TARIF, "betrag", 0.12, 600),
    "est_grenze_2": (_KW_TARIF, "betrag", 0.12, 600),
    "est_grenze_3": (_KW_TARIF, "betrag", 0.12, 600),
    "est_grenze_4": (_KW_TARIF, "betrag", 0.12, 600),
    "est_grenze_5": (_KW_TARIF, "betrag", 0.12, 600),
    "est_grenze_6": (_KW_TARIF, "betrag", (900000, 1100000), 600),
    "gfb_satz": (r"Grundfreibetrag|Gewinnfreibetrag", "prozent", (10, 20), 200),
    "gfb_max_gewinn": (r"Grundfreibetrag|Gewinnfreibetrag", "betrag", 0.08, 250),
    "vfb_grenze": (r"Veranlagungsfreibetrag", "betrag", 0.15, 250),
    "vfb_ende": (r"Veranlagungsfreibetrag", "betrag", 0.15, 250),
    "pab": (_KW_PAB, "betrag", 0.12, 400),
    "pab_von": (_KW_PAB, "betrag", 0.12, 400),
    "pab_bis": (_KW_PAB, "betrag", 0.12, 400),
    "pab_erh": (_KW_PAB_ERH, "betrag", 0.12, 600),
    "pab_erh_von": (_KW_PAB_ERH, "betrag", 0.12, 600),
    "pab_erh_bis": (_KW_PAB_ERH, "betrag", 0.12, 600),
    "pension_kv": (r"Krankenversicherung\w*[^.\n]{0,80}Pensionist\w*|Pensionist\w*[^.\n]{0,80}Krankenversicherung\w*",
                   "prozent", (4, 8), 150),
    "sz_freibetrag": (r"Sonderzahlung\w*|Jahressechstel", "betrag", 0.1, 300),
    "sz_freigrenze": (r"Sonderzahlung\w*|Jahressechstel", "betrag", 0.1, 300),
    "svs_grenze": (r"Versicherungsgrenze", "betrag", 0.12, 150),
    "gfg_monat": (r"Geringfügigkeitsgrenze", "betrag", 0.12, 150),
    "svs_mbgl": (r"Mindestbeitragsgrundlage|\bMBG\b", "betrag", 0.12, 150),
    "svs_hbgl": (r"Höchstbeitragsgrundlage|\bHBG\b", "betrag", 0.12, 150),
    "svs_kv": (r"Krankenversicherung", "prozent", (5, 9), 300),
    "svs_pv": (r"Pensionsversicherung", "prozent", (15, 23), 300),
    "svs_sv": (r"Selbst?ständigenvorsorge", "prozent", (0.8, 3), 200),
    "svs_uv": (r"Unfallversicherung", "betrag", 0.15, 200),
    "gsvg_ku_gewinn": (r"Kleinunternehmer\w*", "betrag", 0.12, 300),
    "gsvg_ku_umsatz": (r"Kleinunternehmer\w*", "betrag", 0.15, 300),
    "ku_grenze": (r"Kleinunternehmer\w*", "betrag", 0.15, 300),
    "ba_basis": (r"Basispauschal\w*", "prozent", (10, 16), 250),
    "ba_ku_dl": (r"Kleinunternehmerpauschal\w*", "prozent", (15, 30), 300),
    "ba_ku_sonst": (r"Kleinunternehmerpauschal\w*", "prozent", (35, 55), 300),
}

_ZAHL = re.compile(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?(?!\d)(\s*(?:Mio\.?|Million\w*))?")
_PROZENT = re.compile(r"\s*(%|Prozent)")
_JAHR = re.compile(r"(?<!\d)(20\d\d)(?!\d)")


class Seite:
    """Eine geladene Seite als Text mit vorab ermittelten Zahlen und Jahresangaben."""

    def __init__(self, name, url, text, titel=""):
        self.name, self.url, self.text = name, url, text
        self.titel_jahre = {int(j) for j in _JAHR.findall(titel or "")}
        self.zahlen = []  # (pos, ende, wert, ist_prozent)
        for m in _ZAHL.finditer(text):
            ganz = m.group(1).replace(".", "")
            wert = float(ganz + ("." + m.group(2) if m.group(2) else ""))
            if m.group(3):
                wert *= 1_000_000
            prozent = bool(_PROZENT.match(text, m.end()))
            self.zahlen.append((m.start(), m.end(), wert, prozent))
        self._pos = [z[0] for z in self.zahlen]
        self.jahre = [(m.start(), int(m.group(1))) for m in _JAHR.finditer(text)]
        self._jpos = [j[0] for j in self.jahre]

    def satzanfang(self, pos):
        a = max(self.text.rfind("\n", 0, pos), self.text.rfind(". ", 0, pos))
        return a + 1

    def jahr_score(self, pos, zieljahr):
        """+2: Jahresangabe im selben Satz passt, -2: anderes Jahr im Satz,
        sonst Seitentitel: +1 passt, -1 nur andere Jahre, 0 unbekannt.
        Jahresangaben in bereits geschlossenen Klammern – „(2027: 1.044 Euro)“ –
        gelten nicht für spätere Zahlen."""
        anfang = self.satzanfang(pos)
        i = bisect.bisect_left(self._jpos, pos) - 1
        while i >= 0 and self.jahre[i][0] >= anfang:
            jp, j = self.jahre[i]
            zwischen = self.text[jp:pos]
            if zwischen.count(")") > zwischen.count("("):
                i -= 1
                continue
            return 2 if j == zieljahr else -2
        if zieljahr in self.titel_jahre:
            return 1 if len(self.titel_jahre) == 1 else 0
        return -1 if self.titel_jahre else 0


def html_zu_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<(br|/p|/div|/tr|/li|/h\d|/td|/th|/dt|/dd)[^>]*>", "\n", raw)
    t = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    t = re.sub(r"[ \t\xa0 ]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def titel_aus_html(raw):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    return " ".join(html.unescape(m.group(1)).split()) if m else ""


def laden(url, timeout=15):
    """Lädt URL oder Datei. Liefert ('json', objekt, '') oder ('text', text, titel)."""
    url = url.strip()
    if url.lower().startswith(("http://", "https://", "file:")):
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Pensionszuverdienstrechner",
            "Accept-Language": "de-AT,de;q=0.9"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            daten = r.read()
            zeichensatz = r.headers.get_content_charset() or "utf-8"
        roh = daten.decode(zeichensatz, "replace")
    else:
        with open(url, encoding="utf-8-sig") as f:
            roh = f.read()
    s = roh.lstrip("﻿ \r\n\t")
    if s.startswith("{"):
        try:
            return "json", json.loads(s), ""
        except ValueError:
            pass
    return "text", html_zu_text(roh), titel_aus_html(roh)


def _passt(wert, prozent, typ, grenze, aktuell):
    if typ == "prozent" and not prozent:
        return False
    if typ == "betrag" and prozent:
        return False
    if isinstance(grenze, tuple):
        lo, hi = grenze
    else:
        lo, hi = aktuell * (1 - grenze), aktuell * (1 + grenze)
    return lo <= wert <= hi


def kandidaten(seite, p_aktuell, zieljahr):
    """{key: {wert: {"jahr": score, "stimmen": n, "abstand": d, "kontext": str}}}"""
    erg = {}
    for key, (kw, typ, grenze, fenster) in REGELN.items():
        aktuell = p_aktuell.get(key)
        if aktuell is None:
            continue
        werte = {}
        for m in re.finditer(kw, seite.text):
            von = bisect.bisect_left(seite._pos, m.end())
            bis = bisect.bisect_left(seite._pos, m.end() + fenster)
            for pos, ende, wert, prozent in seite.zahlen[von:bis]:
                if not _passt(wert, prozent, typ, grenze, aktuell):
                    continue
                score = seite.jahr_score(pos, zieljahr)
                w = werte.setdefault(round(wert, 4), {"jahr": score, "stimmen": 0,
                                                      "abstand": pos - m.end(), "kontext": ""})
                w["stimmen"] += 1
                if score > w["jahr"] or (score == w["jahr"] and pos - m.end() < w["abstand"]) or not w["kontext"]:
                    w["jahr"] = max(w["jahr"], score)
                    w["abstand"] = min(w["abstand"], pos - m.end())
                    a = max(m.start(), pos - 140)
                    w["kontext"] = " ".join(seite.text[a:ende + 50].split())
        if werte:
            erg[key] = werte
    return erg


def seiten_laden(zieljahr, fortschritt=None, cache=None):
    """Lädt alle vordefinierten Webquellen für ein Jahr. Liefert (seiten, fehler)."""
    cache = {} if cache is None else cache
    seiten, fehler = [], []
    for i, (name, url, _inhalt) in enumerate(WEBQUELLEN):
        n, u = name.format(jahr=zieljahr), url.format(jahr=zieljahr)
        if fortschritt:
            fortschritt(i, len(WEBQUELLEN), n)
        try:
            if u not in cache:
                cache[u] = laden(u)
            art, inhalt, titel = cache[u]
            if art == "text":
                seiten.append(Seite(n, u, inhalt, titel))
        except Exception as ex:  # Netzwerk, HTTP-Fehler
            fehler.append(f"{n}: {ex}")
    return seiten, fehler


def ermitteln(p_aktuell, param_jahr, heute=None, fortschritt=None, mindest_bestaetigt=10):
    """Sucht aktuelle Werte in allen Quellen und wählt das passende Jahr.

    Ab Oktober wird zuerst das Folgejahr versucht; werden dafür weniger als
    `mindest_bestaetigt` Werte mit passender Jahresangabe gefunden, gilt das
    laufende Jahr. Liefert (jahr, ergebnis, quellen, fehler)."""
    import datetime
    h = heute or datetime.date.today()
    basis = max(int(param_jahr or h.year), h.year)
    jahre = [basis + 1, basis] if (h.month >= 10 and basis == h.year) else [basis]
    cache = {}
    for j in jahre:
        seiten, fehler = seiten_laden(j, fortschritt, cache)
        erg = auswerten(seiten, p_aktuell, j)
        if j == jahre[-1] or sum(1 for v in erg.values() if v["jahr_ok"]) >= mindest_bestaetigt:
            return j, erg, [s.name for s in seiten], fehler
    return jahre[-1], {}, [], []


def auswerten(seiten, p_aktuell, zieljahr):
    """Ermittelt je Parameter den besten Wert über alle Seiten.

    Liefert {key: {"wert", "quellen": [namen], "kontext", "jahr_ok", "stimmen"}}.
    """
    gesammelt = {}  # key -> wert -> aggregiert
    tarif_saetze = []  # (score, werte-tupel, seite, kontext) – Tarifstufen nur gemeinsam von einer Seite
    for s in seiten:
        kand = kandidaten(s, p_aktuell, zieljahr)
        bester = {}
        for key in TARIF:
            if key in kand:
                wert, info = max(kand[key].items(),
                                 key=lambda kv: (kv[1]["jahr"], kv[1]["stimmen"], -kv[1]["abstand"]))
                bester[key] = (wert, info)
        if all(k in bester for k in TARIF[:5]):
            werte_t = tuple(bester[k][0] if k in bester else None for k in TARIF)
            kette = [w for w in werte_t if w is not None]
            if all(a < b for a, b in zip(kette, kette[1:])):
                score = min(bester[k][1]["jahr"] for k in TARIF[:5])
                tarif_saetze.append((score, werte_t, s.name, bester["est_grenze_1"][1]["kontext"]))
        for key, werte in kand.items():
            if key in TARIF:
                continue
            for wert, info in werte.items():
                g = gesammelt.setdefault(key, {}).setdefault(
                    wert, {"jahr": -9, "stimmen": 0, "abstand": 10**9, "quellen": [], "kontext": ""})
                g["stimmen"] += info["stimmen"]
                if s.name not in g["quellen"]:
                    g["quellen"].append(s.name)
                if (info["jahr"], -info["abstand"]) > (g["jahr"], -g["abstand"]):
                    g["jahr"], g["abstand"] = info["jahr"], info["abstand"]
                    g["kontext"] = f"{s.name}: …{info['kontext']}…"
    ergebnis = {}
    for key, werte in gesammelt.items():
        wert, g = max(werte.items(),
                      key=lambda kv: (kv[1]["jahr"], len(kv[1]["quellen"]), kv[1]["stimmen"], -kv[1]["abstand"]))
        if g["jahr"] < 0:  # nur Werte eines anderen Jahres gefunden
            continue
        ergebnis[key] = {"wert": wert, "quellen": g["quellen"], "kontext": g["kontext"],
                         "jahr_ok": g["jahr"] > 0, "stimmen": g["stimmen"]}
    # Tarifstufen: Satz mit bestem Jahresbezug, bei Gleichstand den von den meisten Seiten bestätigten
    if tarif_saetze:
        def gewicht(t):
            return (t[0], sum(1 for u in tarif_saetze if u[1][:5] == t[1][:5]))
        score, werte_t, _name, kontext = max(tarif_saetze, key=gewicht)
        if score >= 0:
            quellen = [u[2] for u in tarif_saetze if u[1][:5] == werte_t[:5]]
            for key, wert in zip(TARIF, werte_t):
                if wert is not None:
                    ergebnis[key] = {"wert": wert, "quellen": quellen, "kontext": f"{quellen[0]}: …{kontext}…",
                                     "jahr_ok": score > 0, "stimmen": len(quellen)}
    return ergebnis
