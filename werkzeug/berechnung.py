"""Rechenkern Pensionsrechner Österreich 2026.

Reguläre Alterspension (Lohnsteuer durch die PVA) plus freiberuflicher
Zuverdienst als Neuer Selbständiger (SVS, Einkommensteuerveranlagung).
Alle Zahlen kommen aus dem Parameter-Dictionary und sind in der GUI
einstellbar.
"""

import math

# ---------------------------------------------------------------------------
# Parameter: (Schlüssel, Gruppe, Bezeichnung, Standardwert, Einheit)
# ---------------------------------------------------------------------------
PARAMETER_DEF = [
    # Einkommensteuer-Tarif 2026 (§ 33 EStG, BGBl. II Nr. 191/2025)
    ("est_grenze_1", "Einkommensteuer-Tarif", "Tarifstufe 1 bis", 13539.0, "€"),
    ("est_grenze_2", "Einkommensteuer-Tarif", "Tarifstufe 2 bis", 21992.0, "€"),
    ("est_grenze_3", "Einkommensteuer-Tarif", "Tarifstufe 3 bis", 36458.0, "€"),
    ("est_grenze_4", "Einkommensteuer-Tarif", "Tarifstufe 4 bis", 70365.0, "€"),
    ("est_grenze_5", "Einkommensteuer-Tarif", "Tarifstufe 5 bis", 104859.0, "€"),
    ("est_grenze_6", "Einkommensteuer-Tarif", "Tarifstufe 6 bis", 1000000.0, "€"),
    ("est_satz_1", "Einkommensteuer-Tarif", "Steuersatz Stufe 1", 0.0, "%"),
    ("est_satz_2", "Einkommensteuer-Tarif", "Steuersatz Stufe 2", 20.0, "%"),
    ("est_satz_3", "Einkommensteuer-Tarif", "Steuersatz Stufe 3", 30.0, "%"),
    ("est_satz_4", "Einkommensteuer-Tarif", "Steuersatz Stufe 4", 40.0, "%"),
    ("est_satz_5", "Einkommensteuer-Tarif", "Steuersatz Stufe 5", 48.0, "%"),
    ("est_satz_6", "Einkommensteuer-Tarif", "Steuersatz Stufe 6", 50.0, "%"),
    ("est_satz_7", "Einkommensteuer-Tarif", "Steuersatz darüber", 55.0, "%"),
    # Freibeträge
    ("gfb_satz", "Freibeträge", "Grundfreibetrag (Gewinnfreibetrag)", 15.0, "%"),
    ("gfb_max_gewinn", "Freibeträge", "Grundfreibetrag max. Gewinn", 33000.0, "€"),
    ("vfb_grenze", "Freibeträge", "Veranlagungsfreibetrag bis", 730.0, "€"),
    ("vfb_ende", "Freibeträge", "Veranlagungsfreibetrag eingeschliffen bis", 1460.0, "€"),
    # Pensionistenabsetzbetrag
    ("pab", "Pensionistenabsetzbetrag", "Pensionistenabsetzbetrag", 1020.0, "€/Jahr"),
    ("pab_von", "Pensionistenabsetzbetrag", "Einschleifung ab Pensionseinkünften", 21614.0, "€"),
    ("pab_bis", "Pensionistenabsetzbetrag", "Einschleifung bis (= 0)", 31494.0, "€"),
    ("pab_erh", "Pensionistenabsetzbetrag", "Erhöhter Pensionistenabsetzbetrag", 1502.0, "€/Jahr"),
    ("pab_erh_von", "Pensionistenabsetzbetrag", "Erhöhter PAB: Einschleifung ab", 24616.0, "€"),
    ("pab_erh_bis", "Pensionistenabsetzbetrag", "Erhöhter PAB: Einschleifung bis", 31494.0, "€"),
    # Pension
    ("pension_anzahl", "Pension", "Pensionsbezüge pro Jahr", 14.0, "×"),
    ("pension_kv", "Pension", "KV-Beitrag von der Pension", 6.0, "%"),
    ("sz_freibetrag", "Pension", "Sonderzahlungen: Freibetrag", 620.0, "€"),
    ("sz_freigrenze", "Pension", "Sonderzahlungen: Freigrenze", 2100.0, "€"),
    ("sz_satz", "Pension", "Sonderzahlungen: Steuersatz", 6.0, "%"),
    ("sz_einschleif", "Pension", "Sonderzahlungen: Einschleifsatz über Freigrenze", 30.0, "%"),
    # SVS Neue Selbständige
    ("svs_grenze", "SVS (Neue Selbständige)", "Versicherungsgrenze (Gewinn)", 6613.20, "€/Jahr"),
    ("svs_kv", "SVS (Neue Selbständige)", "Krankenversicherung", 6.8, "%"),
    ("svs_pv", "SVS (Neue Selbständige)", "Pensionsversicherung", 18.5, "%"),
    ("svs_sv", "SVS (Neue Selbständige)", "Selbständigenvorsorge", 1.53, "%"),
    ("svs_uv", "SVS (Neue Selbständige)", "Unfallversicherung (fix)", 12.95, "€/Monat"),
    ("svs_hbgl", "SVS (Neue Selbständige)", "Höchstbeitragsgrundlage", 97020.0, "€/Jahr"),
    ("svs_mbgl", "SVS (Neue Selbständige)", "Mindestbeitragsgrundlage", 6613.20, "€/Jahr"),
    # Gewerbetreibende (GSVG)
    ("gsvg_ku_gewinn", "Gewerbetreibende (GSVG)", "Befreiung KV/PV: max. Gewinn", 6613.20, "€/Jahr"),
    ("gsvg_ku_umsatz", "Gewerbetreibende (GSVG)", "Befreiung KV/PV: max. Umsatz", 55000.0, "€/Jahr"),
    ("wko_grundumlage", "Gewerbetreibende (GSVG)", "WKO-Grundumlage", 150.0, "€/Jahr"),
    # Betriebsausgaben-Pauschalen
    ("ba_basis", "Betriebsausgaben", "Basispauschalierung", 15.0, "%"),
    ("ba_basis_max_umsatz", "Betriebsausgaben", "Basispauschalierung max. Umsatz", 420000.0, "€"),
    ("ba_ku_dl", "Betriebsausgaben", "KU-Pauschalierung Dienstleistung", 20.0, "%"),
    ("ba_ku_sonst", "Betriebsausgaben", "KU-Pauschalierung sonstige", 45.0, "%"),
    ("ku_grenze", "Betriebsausgaben", "Kleinunternehmergrenze (USt/KU-Pausch.)", 55000.0, "€"),
    # Pensionsarten: Zuverdienstregeln
    ("gfg_monat", "Pensionsarten / Zuverdienst", "Geringfügigkeitsgrenze (monatlich)", 551.10, "€/Monat"),
    ("wegfall_toleranz", "Pensionsarten / Zuverdienst", "Vorzeitige Pension: Toleranz Überschreitung/Jahr", 40.0, "% GFG"),
    ("korridor_bonus", "Pensionsarten / Zuverdienst", "Korridorpension: Erhöhung je Wegfallmonat", 0.55, "%"),
    ("inv_grenze_1", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Gesamteinkommen Stufe 1 über", 1599.99, "€/Monat"),
    ("inv_grenze_2", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Stufe 2 über", 2400.09, "€/Monat"),
    ("inv_grenze_3", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Stufe 3 über", 3199.99, "€/Monat"),
    ("inv_satz_1", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Anrechnung Stufe 1", 30.0, "%"),
    ("inv_satz_2", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Anrechnung Stufe 2", 40.0, "%"),
    ("inv_satz_3", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Anrechnung Stufe 3", 50.0, "%"),
    ("inv_max", "Pensionsarten / Zuverdienst", "Teilpension (IP/BU): Anrechnung max.", 50.0, "% Pension"),
    # Tabelle / Warnung
    ("tab_von", "Tabelle", "Tabelle: Start (Std/Woche)", 1.0, "h"),
    ("tab_bis", "Tabelle", "Tabelle: Ende (Std/Woche)", 30.0, "h"),
    ("tab_schritt", "Tabelle", "Tabelle: Schrittweite (Std/Woche)", 1.0, "h"),
    ("tab_umsatz_von", "Tabelle", "Tabelle: Start (Umsatz)", 2000.0, "€"),
    ("tab_umsatz_bis", "Tabelle", "Tabelle: Ende (Umsatz)", 60000.0, "€"),
    ("tab_umsatz_schritt", "Tabelle", "Tabelle: Schrittweite (Umsatz)", 2000.0, "€"),
]

PARAMETER_STANDARD = {k: v for k, _, _, v, _ in PARAMETER_DEF}

PENSION_ARTEN = {
    "regulaer": "Reguläre Alterspension (ab Regelpensionsalter)",
    "korridor": "Korridorpension",
    "langzeit": "Vorzeitige Alterspension – Langzeitversicherte („Hacklerregelung“)",
    "schwerarbeit": "Schwerarbeitspension",
    "teilpension": "Teilpension (seit 2026)",
    "invaliditaet": "Invaliditäts-/Berufsunfähigkeits-/Erwerbsunfähigkeitspension",
    "witwe": "Witwen-/Witwerpension",
}
# Pensionsarten, die bei Zuverdienst über der Geringfügigkeitsgrenze (mit PV-Pflicht) wegfallen
WEGFALL_ARTEN = ("korridor", "langzeit", "schwerarbeit", "teilpension")

PENSION_MODI = {
    "brutto_monat": "Brutto pro Monat (14× jährlich)",
    "brutto_jahr": "Brutto pro Jahr (gesamt)",
    "netto_monat": "Netto pro Monat (wird zurückgerechnet)",
}
ZUV_MODI = {
    "stunden": "Stundensatz × Stunden × Wochen",
    "umsatz_jahr": "Jahresumsatz",
    "umsatz_monat": "Monatsumsatz (× 12)",
    "gewinn_jahr": "Gewinn vor SVS direkt (Jahr)",
}
BA_MODI = {
    "betrag_jahr": "Tatsächliche Ausgaben € / Jahr",
    "betrag_monat": "Tatsächliche Ausgaben € / Monat",
    "prozent": "Prozent vom Umsatz",
    "basis": "Basispauschalierung (15 %)",
    "ku_dl": "KU-Pauschalierung Dienstleistung (20 %)",
    "ku_sonst": "KU-Pauschalierung sonstige (45 %)",
}

EINGABEN_STANDARD = {
    "pension_art": "regulaer",
    "taetigkeitsmonate": 12.0,
    "pension_modus": "brutto_monat",
    "pension_betrag": 2000.0,
    "zuv_modus": "stunden",
    "stundensatz": 50.0,
    "std_woche": 5.0,
    "wochen": 46.0,
    "umsatz_jahr": 12000.0,
    "umsatz_monat": 1000.0,
    "gewinn_jahr": 10000.0,
    "ba_modus": "betrag_jahr",
    "ba_betrag": 1000.0,
    "ba_prozent": 10.0,
    "zus_ausgaben": 0.0,
    "erh_pab": False,
    "gewerbe": False,
    "gsvg_befreiung": True,
    "neugruender": False,
    "svs_uv_an": True,
    "svs_sv_an": True,
    "hbgl_mehrfach": True,
    "vfb_an": True,
}


# ---------------------------------------------------------------------------
# Steuerfunktionen
# ---------------------------------------------------------------------------
def tarifsteuer(einkommen, p):
    """Einkommensteuer nach § 33 Abs. 1 EStG (vor Absetzbeträgen)."""
    if einkommen <= 0:
        return 0.0
    grenzen = [p[f"est_grenze_{i}"] for i in range(1, 7)] + [math.inf]
    saetze = [p[f"est_satz_{i}"] for i in range(1, 8)]
    steuer, unten = 0.0, 0.0
    for oben, satz in zip(grenzen, saetze):
        if einkommen > unten:
            steuer += (min(einkommen, oben) - unten) * satz / 100.0
        unten = oben
    return steuer


def grenzsteuersatz(einkommen, p):
    grenzen = [p[f"est_grenze_{i}"] for i in range(1, 7)]
    for i, g in enumerate(grenzen):
        if einkommen <= g:
            return p[f"est_satz_{i + 1}"]
    return p["est_satz_7"]


def pensionistenabsetzbetrag(pensionseinkuenfte, p, erhoeht=False):
    if pensionseinkuenfte <= 0:
        return 0.0
    if erhoeht:
        betrag, von, bis = p["pab_erh"], p["pab_erh_von"], p["pab_erh_bis"]
    else:
        betrag, von, bis = p["pab"], p["pab_von"], p["pab_bis"]
    if pensionseinkuenfte <= von:
        return betrag
    if pensionseinkuenfte >= bis or bis <= von:
        return 0.0
    return betrag * (bis - pensionseinkuenfte) / (bis - von)


def sonderzahlung_steuer(bemessung, p):
    """Lohnsteuer auf 13./14. Pension (§ 67 Abs. 1 EStG)."""
    if bemessung <= p["sz_freigrenze"]:
        return 0.0
    normal = (bemessung - p["sz_freibetrag"]) * p["sz_satz"] / 100.0
    einschleif = (bemessung - p["sz_freigrenze"]) * p["sz_einschleif"] / 100.0
    return max(0.0, min(normal, einschleif))


def veranlagungsfreibetrag(einkuenfte, p):
    """Freibetrag für Nicht-Lohneinkünfte bis 730 €, eingeschliffen bis 1.460 €."""
    g, e = p["vfb_grenze"], p["vfb_ende"]
    if einkuenfte <= 0:
        return 0.0
    if einkuenfte <= g:
        return einkuenfte
    if einkuenfte >= e:
        return 0.0
    return max(0.0, g - (einkuenfte - g) * g / (e - g))


# ---------------------------------------------------------------------------
# Pension
# ---------------------------------------------------------------------------
def pension_aus_brutto_monat(monat, p, erh_pab, wegfall_monate=0, anrechnung=0.0, anr_monate=0):
    """Jahreswerte der Pension. wegfall_monate: Monate, in denen die Pension
    wegen Zuverdienst ruht (13./14. anteilig); anrechnung: Kürzung pro Monat
    (Teilpension bei Invaliditäts-/BU-Pension) für anr_monate Monate."""
    anzahl = p["pension_anzahl"]
    lfd_monate = min(anzahl, 12.0)
    sz_anzahl = max(0.0, anzahl - 12.0)
    faktor = (12 - wegfall_monate) / 12.0
    lfd = monat * lfd_monate * faktor - anrechnung * anr_monate
    sz = monat * sz_anzahl * faktor - anrechnung * sz_anzahl * anr_monate / 12.0
    kv_satz = p["pension_kv"] / 100.0
    kv_lfd, kv_sz = lfd * kv_satz, sz * kv_satz
    einkuenfte = lfd - kv_lfd  # laufende Pensionseinkünfte (Tarif)
    lst_tarif = tarifsteuer(einkuenfte, p)
    pab = pensionistenabsetzbetrag(einkuenfte, p, erh_pab)
    lst_lfd = max(0.0, lst_tarif - pab)
    lst_sz = sonderzahlung_steuer(sz - kv_sz, p)
    netto = lfd + sz - kv_lfd - kv_sz - lst_lfd - lst_sz
    return {
        "monat": monat,
        "lfd": lfd,
        "sz": sz,
        "brutto": lfd + sz,
        "kv": kv_lfd + kv_sz,
        "einkuenfte": einkuenfte,
        "pab": pab,
        "lst_lfd": lst_lfd,
        "lst_sz": lst_sz,
        "lst": lst_lfd + lst_sz,
        "netto": netto,
        "netto_monat_lfd": (lfd - kv_lfd - lst_lfd) / lfd_monate if lfd_monate else 0.0,
        "lfd_monate": lfd_monate,
        "sz_anzahl": sz_anzahl,
        "wegfall_monate": wegfall_monate,
        "anrechnung": anrechnung,
        "anr_monate": anr_monate,
    }


def pension_wirkung(gewinn_vor_sv, svs, pension, e, p):
    """Auswirkung des Zuverdienstes auf die Pension je nach Pensionsart.

    Erwerbseinkommen pro Monat = Gewinn vor SVS ÷ Tätigkeitsmonate.
    - Vorzeitige Pensionen (Korridor, Langzeitversicherte, Schwerarbeit,
      Teilpension): Wegfall in den Tätigkeitsmonaten, wenn das Einkommen über
      der Geringfügigkeitsgrenze liegt UND Pflichtversicherung in der PV
      besteht (Toleranz: Jahressumme der Überschreitung bis x % der GFG).
    - Invaliditäts-/BU-/EU-Pension: Teilpension – Anrechnungsbetrag aus den
      Gesamteinkommensteilen (30/40/50 %), höchstens Erwerbseinkommen und
      höchstens 50 % der Pension (Steigerungsbetrag ≈ Bruttopension).
    """
    art = e.get("pension_art", "regulaer")
    monate = int(min(12, max(1, round(e.get("taetigkeitsmonate", 12)))))
    einkommen_monat = max(0.0, gewinn_vor_sv) / monate
    gfg = p["gfg_monat"]
    w = {"art": art, "monate": monate, "einkommen_monat": einkommen_monat, "wegfall": 0,
         "anrechnung": 0.0, "gesamteinkommen": 0.0}
    if art in WEGFALL_ARTEN:
        ueber = (einkommen_monat - gfg) * monate
        if svs["pflicht"] and einkommen_monat > gfg and ueber > p["wegfall_toleranz"] / 100.0 * gfg:
            w["wegfall"] = monate
    elif art == "invaliditaet" and einkommen_monat > gfg:
        pm = pension["monat"]
        g = pm + einkommen_monat
        w["gesamteinkommen"] = g
        stufen = [(p["inv_grenze_1"], p["inv_grenze_2"], p["inv_satz_1"]),
                  (p["inv_grenze_2"], p["inv_grenze_3"], p["inv_satz_2"]),
                  (p["inv_grenze_3"], math.inf, p["inv_satz_3"])]
        anr = sum(max(0.0, min(g, oben) - unten) * satz / 100.0 for unten, oben, satz in stufen)
        w["anrechnung"] = max(0.0, min(anr, einkommen_monat, pm * p["inv_max"] / 100.0))
    return w


def wegfall_grenzen(e, p):
    """Gewinne vor SVS, ab denen die Pension wegfällt bzw. gekürzt wird (für den
    ungünstigen Bereich)."""
    art = e.get("pension_art", "regulaer")
    monate = int(min(12, max(1, round(e.get("taetigkeitsmonate", 12)))))
    gfg = p["gfg_monat"]
    if art in WEGFALL_ARTEN:
        einkommen = monate * gfg + p["wegfall_toleranz"] / 100.0 * gfg
        pflicht = versicherungsgrenze(e, p) or 0.0
        return [max(einkommen, pflicht)]
    if art == "invaliditaet":
        return [monate * gfg]
    return []


def pension_brutto_aus_netto(netto_monat, p, erh_pab):
    """Rückrechnung: laufende Netto-Monatspension -> Brutto-Monatspension."""
    if netto_monat <= 0:
        return 0.0
    lo, hi = netto_monat, netto_monat * 3 + 1000
    for _ in range(80):
        mid = (lo + hi) / 2
        if pension_aus_brutto_monat(mid, p, erh_pab)["netto_monat_lfd"] < netto_monat:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 2)


def pension_brutto_monat(e, p):
    modus, betrag = e["pension_modus"], max(0.0, e["pension_betrag"])
    if modus == "brutto_jahr":
        return betrag / p["pension_anzahl"] if p["pension_anzahl"] else 0.0
    if modus == "netto_monat":
        return pension_brutto_aus_netto(betrag, p, e["erh_pab"])
    return betrag


# ---------------------------------------------------------------------------
# Zuverdienst
# ---------------------------------------------------------------------------
def umsatz_aus_eingaben(e):
    m = e["zuv_modus"]
    if m == "stunden":
        return max(0.0, e["stundensatz"] * e["std_woche"] * e["wochen"])
    if m == "umsatz_monat":
        return max(0.0, e["umsatz_monat"] * 12)
    if m == "gewinn_jahr":
        return max(0.0, e["gewinn_jahr"])
    return max(0.0, e["umsatz_jahr"])


TATSAECHLICHE_BA = ("betrag_jahr", "betrag_monat", "prozent")


def kammerumlage(e, p):
    """WKO-Grundumlage (nur Gewerbe; bei 'Gewinn direkt' bereits im Gewinn enthalten)."""
    if e.get("gewerbe") and e["zuv_modus"] != "gewinn_jahr":
        return p["wko_grundumlage"]
    return 0.0


def betriebsausgaben(umsatz, e, p):
    if e["zuv_modus"] == "gewinn_jahr":
        return 0.0
    m = e["ba_modus"]
    # Grundumlage ist bei tatsächlichen Ausgaben absetzbar, bei Pauschalierung abgegolten
    kammer = kammerumlage(e, p) if m in TATSAECHLICHE_BA else 0.0
    if m == "betrag_jahr":
        return e["ba_betrag"] + kammer
    if m == "betrag_monat":
        return e["ba_betrag"] * 12 + kammer
    if m == "prozent":
        return umsatz * e["ba_prozent"] / 100.0 + kammer
    zus = max(0.0, e.get("zus_ausgaben", 0.0))
    if m == "basis":
        return min(umsatz, p["ba_basis_max_umsatz"]) * p["ba_basis"] / 100.0 + zus
    if m == "ku_dl":
        return umsatz * p["ba_ku_dl"] / 100.0 + zus
    if m == "ku_sonst":
        return umsatz * p["ba_ku_sonst"] / 100.0 + zus
    return 0.0


def versicherungsgrenze(e, p):
    """Gewinngrenze, ab der KV/PV-Beiträge auf den ganzen Gewinn anfallen.
    None = keine Grenze (Gewerbe ohne Befreiung: Mindestbeiträge ab 0 €)."""
    if e.get("gewerbe"):
        return p["gsvg_ku_gewinn"] if e.get("gsvg_befreiung") else None
    return p["svs_grenze"]


def svs_beitraege(gewinn_vor_sv, umsatz, pension_jahr_brutto, e, p):
    """SVS-Beiträge (endgültige Beitragsgrundlage = Gewinn vor SV-Beiträgen).

    Neue Selbständige: Pflicht erst über der Versicherungsgrenze.
    Gewerbetreibende: Pflicht ab Gewerbeschein; Pensionisten können sich bei
    Umsatz <= 55.000 € und Gewinn <= 6.613,20 € von KV/PV befreien lassen
    (Kleinunternehmer-Ausnahme). Die UV ist bei Gewerbe immer zu zahlen.
    """
    gewerbe = bool(e.get("gewerbe"))
    r = {"art": "GSVG" if gewerbe else "Neue Selbständige", "pflicht": False, "befreit": False,
         "mindest": False, "bgl_kv": 0.0, "bgl_pv": 0.0, "kv": 0.0, "pv": 0.0,
         "sv": 0.0, "uv": 0.0, "summe": 0.0}
    uv = p["svs_uv"] * 12
    if gewerbe:
        if (e.get("gsvg_befreiung") and umsatz <= p["gsvg_ku_umsatz"]
                and gewinn_vor_sv <= p["gsvg_ku_gewinn"]):
            r["befreit"] = True
            r["uv"] = r["summe"] = uv
            return r
    elif gewinn_vor_sv <= p["svs_grenze"]:
        return r
    r["pflicht"] = True
    hbgl, mbgl = p["svs_hbgl"], p["svs_mbgl"]
    r["mindest"] = gewinn_vor_sv < mbgl
    bgl = min(max(gewinn_vor_sv, mbgl), hbgl)
    # Neugründer: KV-Beitragsgrundlage in den ersten 2 Jahren fix (keine Nachbemessung)
    bgl_kv = mbgl if e.get("neugruender") else bgl
    if e["hbgl_mehrfach"]:  # Pension zählt in der KV zur Höchstbeitragsgrundlage
        bgl_kv = max(0.0, min(bgl_kv, hbgl - pension_jahr_brutto))
    r["bgl_kv"], r["bgl_pv"] = bgl_kv, bgl
    r["kv"] = bgl_kv * p["svs_kv"] / 100.0
    r["pv"] = bgl * p["svs_pv"] / 100.0
    r["sv"] = bgl * p["svs_sv"] / 100.0 if e["svs_sv_an"] else 0.0
    r["uv"] = uv if (gewerbe or e["svs_uv_an"]) else 0.0
    r["summe"] = r["kv"] + r["pv"] + r["sv"] + r["uv"]
    return r


def berechne_mit_umsatz(umsatz, e, p, pension=None):
    """Vollständige Jahresberechnung für einen gegebenen Umsatz."""
    if pension is None:
        pension = pension_aus_brutto_monat(pension_brutto_monat(e, p), p, e["erh_pab"])
    pension_voll = pension
    ba = betriebsausgaben(umsatz, e, p)
    gewinn_vor_sv = umsatz - ba
    svs = svs_beitraege(gewinn_vor_sv, umsatz, pension_voll["brutto"], e, p)
    wirkung = pension_wirkung(gewinn_vor_sv, svs, pension_voll, e, p)
    if wirkung["wegfall"] or wirkung["anrechnung"]:
        pension = pension_aus_brutto_monat(pension_voll["monat"], p, e["erh_pab"], wirkung["wegfall"],
                                           wirkung["anrechnung"], wirkung["monate"] if wirkung["anrechnung"] else 0)
    kammer = kammerumlage(e, p)
    # bei Pauschalierung ist die Grundumlage nicht absetzbar, kostet aber trotzdem
    kammer_bar = kammer if e["ba_modus"] not in TATSAECHLICHE_BA else 0.0
    gewinn = gewinn_vor_sv - svs["summe"]
    gfb = max(0.0, min(gewinn, p["gfb_max_gewinn"])) * p["gfb_satz"] / 100.0
    einkuenfte_sa = gewinn - gfb
    vfb = veranlagungsfreibetrag(einkuenfte_sa, p) if (e["vfb_an"] and pension["brutto"] > 0) else 0.0
    einkuenfte_stpfl = einkuenfte_sa - vfb

    einkommen = max(0.0, pension["einkuenfte"] + einkuenfte_stpfl)
    est_tarif = tarifsteuer(einkommen, p)
    est_gesamt = max(0.0, est_tarif - pension["pab"])
    mehrsteuer = est_gesamt - pension["lst_lfd"]

    netto_gesamt = pension["netto"] + gewinn_vor_sv - svs["summe"] - mehrsteuer - kammer_bar
    # Netto-Effekt des Zuverdienstes = Gesamtnetto minus Nettopension ohne Zuverdienst
    netto_zuv = netto_gesamt - pension_voll["netto"]
    return {
        "pension_voll": pension_voll,
        "wirkung": wirkung,
        "pensionsverlust_brutto": pension_voll["brutto"] - pension["brutto"],
        "pensionsverlust_netto": pension_voll["netto"] - pension["netto"],
        "umsatz": umsatz,
        "ba": ba,
        "kammer": kammer,
        "kammer_bar": kammer_bar,
        "gewinn_vor_sv": gewinn_vor_sv,
        "svs": svs,
        "gewinn": gewinn,
        "gfb": gfb,
        "einkuenfte_sa": einkuenfte_sa,
        "vfb": vfb,
        "einkuenfte_stpfl": einkuenfte_stpfl,
        "einkommen": einkommen,
        "est_tarif": est_tarif,
        "est_gesamt": est_gesamt,
        "mehrsteuer": mehrsteuer,
        "grenzsteuersatz": grenzsteuersatz(einkommen, p),
        "netto_zuv": netto_zuv,
        "netto_zuv_monat": netto_zuv / 12.0,
        "anteil_umsatz": netto_zuv / umsatz * 100.0 if umsatz > 0 else 0.0,
        "anteil_gewinn": netto_zuv / gewinn_vor_sv * 100.0 if gewinn_vor_sv > 0 else 0.0,
        "netto_gesamt": netto_gesamt,
        "netto_gesamt_monat": netto_gesamt / 12.0,
        "pension": pension,
    }


def _umsatz_fuer_gewinn(ziel, e, p):
    """Kleinster Umsatz, bei dem der Gewinn vor SV den Zielwert übersteigt."""
    lo, hi = 0.0, 1.0
    while umsatz_minus_ba(hi, e, p) <= ziel:
        hi *= 2
        if hi > 1e9:
            return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if umsatz_minus_ba(mid, e, p) <= ziel:
            lo = mid
        else:
            hi = mid
    return hi


def umsatz_minus_ba(u, e, p):
    return u - betriebsausgaben(u, e, p)


def unguenstiger_bereich(e, p, pension=None):
    """Umsatz-/Gewinnbereich knapp über der Versicherungsgrenze, in dem netto
    weniger bleibt als knapp unter der Grenze."""
    if pension is None:
        pension = pension_aus_brutto_monat(pension_brutto_monat(e, p), p, e["erh_pab"])
    kandidaten = []
    vg = versicherungsgrenze(e, p)
    if vg is not None:
        kandidaten.append(("svs", vg))
    kandidaten += [("pension", g) for g in wegfall_grenzen(e, p)]
    bereiche = []
    for grund, grenze in kandidaten:
        b = _bereich_ab(grenze, e, p, pension)
        if b:
            b["grund"] = grund
            bereiche.append(b)
    if not bereiche:
        return None
    bester = max(bereiche, key=lambda b: (b["umsatz_ende"], -b["umsatz_grenze"]))
    # reicht der Bereich wegen Pensionswegfall/-kürzung so weit, ist das der Grund
    if any(b["grund"] == "pension" and b["umsatz_ende"] >= bester["umsatz_ende"] - 1 for b in bereiche):
        bester["grund"] = "pension"
    return bester


def _bereich_ab(grenze, e, p, pension):
    u_grenze = _umsatz_fuer_gewinn(grenze, e, p)
    if u_grenze is None:
        return None
    u_unter = max(0.0, u_grenze - 0.01)
    netto_unter = berechne_mit_umsatz(u_unter, e, p, pension)["netto_zuv"]
    lo, hi = u_grenze, u_grenze + 1.0
    while berechne_mit_umsatz(hi, e, p, pension)["netto_zuv"] < netto_unter:
        hi = lo + (hi - lo) * 2
        if hi > 1e8:
            return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if berechne_mit_umsatz(mid, e, p, pension)["netto_zuv"] < netto_unter:
            lo = mid
        else:
            hi = mid
    u_be = hi
    if u_be - u_grenze < 0.5:  # kein Rückgang an dieser Grenze
        return None
    return {
        "umsatz_grenze": u_grenze,
        "umsatz_ende": u_be,
        "gewinn_grenze": grenze,
        "gewinn_ende": umsatz_minus_ba(u_be, e, p),
        "netto_unter": netto_unter,
    }


def berechne(e, p):
    """Hauptberechnung aus den Eingaben."""
    pension = pension_aus_brutto_monat(pension_brutto_monat(e, p), p, e["erh_pab"])
    umsatz = umsatz_aus_eingaben(e)
    r = berechne_mit_umsatz(umsatz, e, p, pension)
    r["stunden_jahr"] = e["std_woche"] * e["wochen"] if e["zuv_modus"] == "stunden" else None
    r["netto_pro_stunde"] = (r["netto_zuv"] / r["stunden_jahr"]) if r["stunden_jahr"] else None
    plus = berechne_mit_umsatz(umsatz + 100.0, e, p, pension)
    r["grenz_netto_100"] = plus["netto_zuv"] - r["netto_zuv"]
    r["ungünstig"] = unguenstiger_bereich(e, p, pension)
    r["warnungen"] = warnungen(r, e, p)
    return r


def stunden_fuer_umsatz(u, e):
    f = e["stundensatz"] * e["wochen"]
    return u / f if f > 0 else None


def warnungen(r, e, p):
    w = []
    ub = r["ungünstig"]
    g = r["gewinn_vor_sv"]
    s = r["svs"]
    gewerbe = bool(e.get("gewerbe"))
    grenzname = "Befreiungsgrenze (KV/PV)" if gewerbe else "SVS-Versicherungsgrenze"
    if gewerbe and e.get("gsvg_befreiung") and r["umsatz"] > p["gsvg_ku_umsatz"]:
        w.append(("rot", f"Umsatz über {fmt(p['gsvg_ku_umsatz'])}: Die KV/PV-Befreiung für Kleinunternehmer "
                         "ist nicht möglich – volle GSVG-Beiträge."))
    if gewerbe and not e.get("gsvg_befreiung") and g <= p["gsvg_ku_gewinn"] and r["umsatz"] <= p["gsvg_ku_umsatz"]:
        e2 = dict(e, gsvg_befreiung=True)
        ersparnis = berechne_mit_umsatz(r["umsatz"], e2, p, r["pension_voll"])["netto_zuv"] - r["netto_zuv"]
        w.append(("orange", f"Ohne Befreiung zahlen Sie GSVG-Beiträge"
                            f"{' auf die Mindestbeitragsgrundlage' if s['mindest'] else ''}. Mit beantragter "
                            f"Kleinunternehmer-Befreiung (KV/PV) blieben netto {fmt(ersparnis)} pro Jahr mehr."))
    w += pension_warnungen(r, e, p)
    if ub and ub.get("grund") == "pension":
        grenzname = "Zuverdienstgrenze (Pensionswegfall bzw. -kürzung)"
    if ub and ub["umsatz_grenze"] <= r["umsatz"] < ub["umsatz_ende"]:
        warum = ("Ab dort entfällt bzw. kürzt sich Ihre Pension (und es fallen SVS-Beiträge an)"
                 if ub.get("grund") == "pension" else "Ab dort fallen SVS-Beiträge auf den ganzen Gewinn an")
        txt = (f"UNGÜNSTIGER BEREICH: Der Gewinn liegt über der {grenzname} ({fmt(ub['gewinn_grenze'])}). "
               f"{warum}. Netto bleibt weniger als knapp unter der Grenze "
               f"({fmt(ub['netto_unter'])}). Erst ab einem Umsatz von {fmt(ub['umsatz_ende'])} "
               f"(Gewinn vor SV {fmt(ub['gewinn_ende'])}) lohnt sich der Mehrverdienst.")
        if e["zuv_modus"] == "stunden":
            h1 = stunden_fuer_umsatz(ub["umsatz_grenze"], e)
            h2 = stunden_fuer_umsatz(ub["umsatz_ende"], e)
            if h1 is not None:
                txt += f" Entspricht ca. {h1:.1f} bis {h2:.1f} Std/Woche."
        w.append(("rot", txt))
    elif ub and r["umsatz"] < ub["umsatz_grenze"] and g > ub["gewinn_grenze"] * 0.85:
        w.append(("orange", f"Hinweis: Der Gewinn ({fmt(g)}) liegt knapp unter der {grenzname} "
                            f"({fmt(ub['gewinn_grenze'])}). Ein Überschreiten kostet rückwirkend Beiträge für das "
                            f"ganze Jahr; sinnvoll erst ab Umsatz {fmt(ub['umsatz_ende'])}."))
    if s["pflicht"] and e.get("neugruender"):
        w.append(("info", "Neugründer: KV-Beitragsgrundlage in den ersten beiden Kalenderjahren fix auf der "
                          "Mindestbeitragsgrundlage (keine Nachbemessung) – ab Jahr 3 KV auf den tatsächlichen Gewinn."))
    if gewerbe and s["befreit"]:
        w.append(("info", "Kleinunternehmer-Befreiung: keine KV/PV-Beiträge, nur Unfallversicherung. Die Befreiung "
                          "muss bei der SVS beantragt werden und fällt rückwirkend weg, wenn eine Grenze überschritten wird."))
    if r["umsatz"] > p["ku_grenze"]:
        w.append(("rot", f"Umsatz über der Kleinunternehmergrenze ({fmt(p['ku_grenze'])}): Sie müssen 20 % "
                         "Umsatzsteuer auf Ihre Rechnungen aufschlagen und ans Finanzamt abführen. Der Stundensatz "
                         "hier ist Ihr Honorar ohne USt"
                         + (f" – auf der Rechnung stehen dann {fmt(e['stundensatz'] * 1.2)} pro Stunde."
                            if e["zuv_modus"] == "stunden" else ".")))
    if e["ba_modus"] in ("ku_dl", "ku_sonst") and e["zuv_modus"] != "gewinn_jahr" and r["umsatz"] > p["ku_grenze"]:
        w.append(("rot", "Die Kleinunternehmer-Pauschalierung ist bei diesem Umsatz nicht zulässig."))
    if e["ba_modus"] == "basis" and e["zuv_modus"] != "gewinn_jahr" and r["umsatz"] > p["ba_basis_max_umsatz"]:
        w.append(("rot", "Die Basispauschalierung ist bei diesem Umsatz nicht zulässig."))
    if r["einkuenfte_sa"] > p["vfb_grenze"]:
        w.append(("info", f"Pflichtveranlagung: Einkünfte aus selbständiger Arbeit über {fmt(p['vfb_grenze'])} – "
                          "Einkommensteuererklärung erforderlich (Nachzahlung der Mehrsteuer)."))
    if (r["svs"]["pflicht"] and e["hbgl_mehrfach"] and not e.get("neugruender")
            and r["svs"]["bgl_kv"] < min(r["gewinn_vor_sv"], p["svs_hbgl"])):
        w.append(("info", "Mehrfachversicherung: KV-Beitragsgrundlage wegen Höchstbeitragsgrundlage gekürzt."))
    if r["gewinn_vor_sv"] < 0:
        w.append(("orange", "Verlust aus dem Zuverdienst – wird mit der Pension ausgeglichen (Steuergutschrift max. bis 0)."))
    return w


def pension_warnungen(r, e, p):
    """Hinweise abhängig von der Pensionsart."""
    w = []
    wk = r["wirkung"]
    art = wk["art"]
    name = PENSION_ARTEN.get(art, art)
    gfg = p["gfg_monat"]
    m = wk["monate"]
    if wk["wegfall"]:
        bis = wegfall_grenzen(e, p)[0]
        w.append(("rot", f"PENSION ENTFÄLLT: Bei der {name} darf vor dem Regelpensionsalter nur bis zur "
                         f"Geringfügigkeitsgrenze ({fmt(gfg)}/Monat) dazuverdient werden, wenn eine "
                         f"Pflichtversicherung in der Pensionsversicherung entsteht. Ihr Erwerbseinkommen beträgt ca. "
                         f"{fmt(wk['einkommen_monat'])}/Monat – die Pension entfällt für {m} Monat(e): "
                         f"−{fmt(r['pensionsverlust_brutto'])} brutto bzw. −{fmt(r['pensionsverlust_netto'])} netto "
                         f"im Jahr. Unschädlich ist ein Gewinn vor SVS bis ca. {fmt(bis)} im Jahr."))
        if art == "korridor":
            w.append(("info", f"Korridorpension: Für jeden Monat des Wegfalls erhöht sich die spätere Alterspension "
                              f"um {zk(p['korridor_bonus'])} % – hier {m} × {zk(p['korridor_bonus'])} % = "
                              f"{zk(m * p['korridor_bonus'])} %."))
        elif art in ("langzeit", "schwerarbeit"):
            w.append(("info", "Die Alterspension wird bei Erreichen des Regelpensionsalters neu berechnet; Monate "
                              "des Wegfalls wegen Erwerbstätigkeit erhöhen sie."))
    elif art in WEGFALL_ARTEN and wk["einkommen_monat"] > gfg * 0.85:
        w.append(("orange", f"Achtung {name}: Ihr Erwerbseinkommen (ca. {fmt(wk['einkommen_monat'])}/Monat) liegt "
                            f"nahe der Geringfügigkeitsgrenze ({fmt(gfg)}/Monat). Darüber – mit Pflichtversicherung in "
                            "der Pensionsversicherung – entfällt die Pension."))
    if art == "teilpension":
        w.append(("info", "Teilpension (seit 2026): setzt eine vereinbarte Arbeitszeitreduktion in einem "
                          "Dienstverhältnis voraus. Eine selbständige Tätigkeit über der Geringfügigkeitsgrenze mit "
                          "Pflichtversicherung lässt sie vor dem Regelpensionsalter entfallen – bitte bei PVA/SVS klären."))
    if art in WEGFALL_ARTEN:
        w.append(("info", f"Annahme: Erwerbseinkommen pro Monat = Gewinn vor SVS ÷ {m} Tätigkeitsmonat(e); "
                          f"Toleranz bis {zk(p['wegfall_toleranz'], 0)} % der Geringfügigkeitsgrenze pro Jahr. "
                          "Die genaue Prüfung macht die Pensionsversicherung."))
    if art == "invaliditaet":
        if wk["anrechnung"]:
            w.append(("orange", f"TEILPENSION: Erwerbseinkommen ca. {fmt(wk['einkommen_monat'])}/Monat über der "
                                f"Geringfügigkeitsgrenze, Gesamteinkommen {fmt(wk['gesamteinkommen'])}/Monat. Die "
                                f"Pension wird um {fmt(wk['anrechnung'])}/Monat gekürzt ({m} Monate, 13./14. anteilig): "
                                f"−{fmt(r['pensionsverlust_brutto'])} brutto bzw. −{fmt(r['pensionsverlust_netto'])} "
                                "netto im Jahr."))
        elif wk["einkommen_monat"] > gfg:
            w.append(("info", f"Gesamteinkommen {fmt(wk['gesamteinkommen'])}/Monat bis {fmt(p['inv_grenze_1'])} – "
                              "keine Kürzung der Pension."))
        w.append(("info", "Annahme Teilpension: Steigerungsbetrag = Bruttopension (ohne Zuschläge). Der Prozentsatz "
                          "wird bei Pensionsanpassung, neuer Erwerbstätigkeit oder auf Antrag neu festgestellt."))
    if art == "witwe":
        w.append(("info", "Witwen-/Witwerpension: Der Zuverdienst führt nicht zum Wegfall. Eigenes Einkommen kann aber "
                          "bei einer Neubemessung die Höhe der Hinterbliebenenpension beeinflussen – nicht berechnet."))
    if art == "regulaer" and r["svs"]["pflicht"]:
        w.append(("info", "Besonderer Höherversicherungsbetrag: Ihre PV-Beiträge erhöhen die Pension ab dem "
                          "Kalenderjahr nach Aufnahme der Tätigkeit."))
    return w


def zk(x, n=2):
    return fmt(x, n, "")


def tabelle(e, p, werte, modus_stunden):
    """Liefert Zeilen für die Tabelle. werte = Stunden/Woche oder Umsätze."""
    pension = pension_aus_brutto_monat(pension_brutto_monat(e, p), p, e["erh_pab"])
    ub = unguenstiger_bereich(e, p, pension)
    zeilen = []
    for x in werte:
        u = e["stundensatz"] * x * e["wochen"] if modus_stunden else x
        r = berechne_mit_umsatz(u, e, p, pension)
        if r["wirkung"]["wegfall"]:
            status = "Pension entfällt"
        elif r["wirkung"]["anrechnung"]:
            status = "Teilpension"
        elif r["svs"]["befreit"]:
            status = "befreit"
        elif not r["svs"]["pflicht"]:
            status = "unter Grenze"
        elif ub and u < ub["umsatz_ende"]:
            status = "ungünstig"
        elif r["svs"]["mindest"]:
            status = "Mindestbeitrag"
        else:
            status = "OK"
        r["x"] = x
        r["status"] = status
        zeilen.append(r)
    return zeilen, ub


def fmt(x, nachkomma=2, einheit=" €"):
    if x is None:
        return "–"
    s = f"{x:,.{nachkomma}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + einheit


def fmt_p(x):
    return fmt(x, 1, " %")
