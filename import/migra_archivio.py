#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIGRAZIONE ARCHIVIO — da Fladynance a Thesyum
==============================================
Prende l'archivio notizie di Fladynance (state/macro_db.json) e lo importa
nell'archivio di Thesyum, MA:
  1. tiene solo le notizie dei temi che interessano a Thesyum (mercati),
     scartando calcio/gaming/cronaca/sport ecc.
  2. rimappa i nomi dei temi dal formato Fladynance a quello Thesyum
  3. NON tocca nulla del trading (predictions_log.json viene ignorato)
  4. non crea duplicati se lo esegui piu' volte

USO:
  1. Metti questo file nella root della repo Thesyum
  2. Copia il file macro_db.json di Fladynance in una cartella "import/"
     (crea la cartella e mettici dentro macro_db.json)
  3. Lancia:  python migra_archivio.py
  4. Controlla l'output, poi committa

Se vuoi solo vedere cosa farebbe SENZA scrivere niente:
  python migra_archivio.py --dry-run
"""

import os, sys, json, hashlib

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
FLADYNANCE_DB = "import/macro_db.json"        # file sorgente (da Fladynance)
THESYUM_ARCHIVE = "state/news_archive.json"   # file destinazione (Thesyum)

DRY_RUN = "--dry-run" in sys.argv

# ---------------------------------------------------------------------------
# MAPPATURA TEMI: Fladynance -> Thesyum
# A sinistra i temi che usa Fladynance (visti nel suo macro_db.json).
# A destra la categoria Thesyum corrispondente, oppure None per SCARTARE.
# ---------------------------------------------------------------------------
TEMA_MAP = {
    # --- ENERGIA ---
    "energia_petrolio_gas": "energia",
    "uranio_nucleare": "energia",

    # --- METALLI PREZIOSI ---
    "metalli_preziosi": "metalli_preziosi",

    # --- METALLI INDUSTRIALI ---
    "metalli_industriali": "metalli_industriali",

    # --- TERRE RARE ---
    "terre_rare": "terre_rare_critici",

    # --- AGRICOLE ---
    "agricole_food": "agricole",

    # --- SHIPPING ---
    "shipping_logistica": "shipping_logistica",

    # --- AI / SEMICONDUTTORI ---
    "ai_data_center": "ai_semiconduttori",
    "semiconduttori": "ai_semiconduttori",

    # --- DIFESA / GEOPOLITICA ---
    "difesa_riarmo": "difesa_geopolitica",
    "geopolitica_sanzioni": "difesa_geopolitica",

    # --- TEMI FINANZIARI GENERICI: li teniamo, mappati a "macro" ---
    "mercati_azionari": "macro",
    "finanza_bancaria": "macro",
    "fiscalita_politica_economica": "macro",
    "crypto_valute_digitali": "macro",

    # --- DA SCARTARE (rumore non-mercato): mappati a None ---
    "clima_meteo_estremo": None,
    "diritti_civili_sviluppo": None,
    "sport_eventi": None,
    "gaming_intrattenimento": None,
    "retail_consumi": None,
    "infrastrutture_trasporti": None,
    "automotive_mobilita": None,
    "criminalita_sicurezza": None,
}

# I temi non elencati sopra vengono scartati di default (prudente).
SCARTA_SE_SCONOSCIUTO = True


def carica(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def salva(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def chiave_notizia(n):
    """Chiave stabile per dedup: usa 'key' se c'e', altrimenti hash di url+sintesi."""
    if n.get("key"):
        return n["key"]
    base = (n.get("url","") + n.get("sintesi","")).encode("utf-8")
    return hashlib.md5(base).hexdigest()[:16]


def main():
    print("="*60)
    print("  MIGRAZIONE ARCHIVIO — Fladynance -> Thesyum")
    if DRY_RUN:
        print("  MODALITA' DRY-RUN (non scrive niente)")
    print("="*60)

    # 1. carico la sorgente
    src = carica(FLADYNANCE_DB)
    if src is None:
        print(f"\nERRORE: non trovo {FLADYNANCE_DB}")
        print("Crea la cartella 'import/' e mettici dentro il macro_db.json")
        print("scaricato dalla repo Fladynance.")
        sys.exit(1)

    if not isinstance(src, list):
        print(f"\nERRORE: {FLADYNANCE_DB} non e' una lista di notizie.")
        sys.exit(1)

    print(f"\nNotizie nel file Fladynance: {len(src)}")

    # 2. carico la destinazione (se esiste gia')
    dst = carica(THESYUM_ARCHIVE) or []
    if not isinstance(dst, list):
        dst = []
    print(f"Notizie gia' presenti in Thesyum: {len(dst)}")

    # chiavi gia' presenti, per non duplicare
    presenti = {chiave_notizia(n) for n in dst}

    # 3. filtro e rimappo
    importate = 0
    scartate_tema = 0
    scartate_dup = 0
    conteggio_per_cat = {}

    for n in src:
        tema_orig = n.get("tema", "")
        # decido la categoria Thesyum
        if tema_orig in TEMA_MAP:
            cat_thesyum = TEMA_MAP[tema_orig]
        else:
            cat_thesyum = None if SCARTA_SE_SCONOSCIUTO else "macro"

        if cat_thesyum is None:
            scartate_tema += 1
            continue

        k = chiave_notizia(n)
        if k in presenti:
            scartate_dup += 1
            continue

        # costruisco la voce nel formato Thesyum
        voce = {
            "key": k,
            "data": n.get("data", ""),
            "categoria": cat_thesyum,
            "tema_originale": tema_orig,
            "sintesi": n.get("sintesi", ""),
            "impatto": n.get("impatto", "neutro"),
            "rilevanza": n.get("rilevanza", "media"),
            "fonte": n.get("fonte", ""),
            "url": n.get("url", ""),
            "importato_da": "fladynance",
        }
        dst.append(voce)
        presenti.add(k)
        importate += 1
        conteggio_per_cat[cat_thesyum] = conteggio_per_cat.get(cat_thesyum, 0) + 1

    # 4. report
    print(f"\n{'─'*60}")
    print("RISULTATO:")
    print(f"  Importate:            {importate}")
    print(f"  Scartate (tema off):  {scartate_tema}")
    print(f"  Scartate (duplicati): {scartate_dup}")
    print(f"  Totale in archivio:   {len(dst)}")
    print(f"\nImportate per categoria:")
    for cat, num in sorted(conteggio_per_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat:<22} {num}")

    # 5. scrivo
    if DRY_RUN:
        print(f"\n[DRY-RUN] Non ho scritto niente. Togli --dry-run per salvare.")
    else:
        salva(THESYUM_ARCHIVE, dst)
        print(f"\n✓ Salvato in {THESYUM_ARCHIVE}")
        print(f"  Ora committa: git add {THESYUM_ARCHIVE} && git commit -m 'import archivio Fladynance'")

    print("="*60)


if __name__ == "__main__":
    main()
