"""Utility script to build clean Italian Wordle dictionary."""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
import unicodedata
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Optional, Set, Tuple

BUNDLED_DICT_PATH = Path(__file__).parent / "data" / "dictionary.json.gz"

DICT_280K_URL = (
    "https://raw.githubusercontent.com/napolux/paroleitaliane/main/paroleitaliane/280000_parole_italiane.txt"
)
FREQ_URL = (
    "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/it/it_50k.txt"
)
NVDB_URL = (
    "https://raw.githubusercontent.com/simo-mazzoli/vocabolario-di-base/master/De_Mauro_vocabolario_base.csv"
)
CURATED5_URL = (
    "https://raw.githubusercontent.com/pietroppeter/wordle-it/master/dict/curated.txt"
)
WORDLIST5_URL = (
    "https://raw.githubusercontent.com/pietroppeter/wordle-it/master/dict/word_list.txt"
)
BADWORDS_URL = (
    "https://raw.githubusercontent.com/napolux/paroleitaliane/main/paroleitaliane/lista_badwords.txt"
)
REMOVE_URL = (
    "https://raw.githubusercontent.com/pietroppeter/wordle-it/master/dict/word_list_remove.txt"
)
NAMES_URL = (
    "https://raw.githubusercontent.com/napolux/paroleitaliane/main/paroleitaliane/9000_nomi_propri.txt"
)

# Common loanwords ending in consonant widely used in Italian as nouns
LOANWORDS_CONS = {
    "BAR", "GAS", "GOL", "PUB", "BUS", "FAN", "TRAM", "CHEF", "CLUB", "FILM", "TEST", "STOP",
    "JAZZ", "QUIZ", "LOOK", "POST", "ROCK", "TEAM", "WEB", "ZOOM", "ALBUM", "ALCOL", "BAZAR",
    "BIDET", "CLOWN", "COLON", "CURRY", "FORUM", "HOTEL", "JEANS", "LASER", "LOBBY", "MODEM",
    "NYLON", "OVEST", "REBUS", "RELAX", "RIBES", "ROBOT", "SPECK", "SPORT", "TOTEM", "VIRUS",
    "SCOOTER", "COMPUTER", "FESTIVAL", "BACON", "CRICKET", "DESKTOP", "DISPLAY", "EBOOK",
    "EMAIL", "EXPORT", "GARAGE", "GANGSTER", "HAMBURGER", "IMPORT", "INTERNET", "KAPUTT",
    "MANAGER", "MONITOR", "PARTNER", "POKER", "POSTER", "RADAR", "RECORD", "RESORT",
    "SHAMPOO", "SNACK", "SOCCER", "SPONSOR", "STAND", "SUPER", "SURF", "TENNIS", "TICKET",
    "TRAILER", "TUNNEL", "VOUCHER", "WEEKEND", "WHISKY", "YOGURT",
}

# Preposizioni articolate, pronomi, congiunzioni, avverbi che NON devono essere soluzioni segrete
FUNCTION_WORDS = {
    "COME", "DOVE", "QUANDO", "PERCHE", "POICHE", "BENCHE", "SEBBE", "QUINDI", "DUNQUE",
    "ANCHE", "NEANCHE", "NEMMENO", "NEPPURE", "QUASI", "FORSE", "CIRCA", "SOPRA", "SOTTO",
    "DENTRO", "FUORI", "AVANTI", "DIETRO", "PRESSO", "LUNGO", "SENZA", "VERSO", "CONTRO",
    "INSIEME", "TUTTAVIA", "INFATTI", "ALMENO", "INVECE", "MENTRE", "OPPURE", "OVVERO",
    "DALLO", "DELLA", "NELLA", "SULLO", "DALLA", "DELLE", "NELLE", "SULLE", "DEGLI", "DAGLI",
    "COLLA", "COLLE", "COLLO", "COGLI", "SUGLI", "NEGLI", "DELLO", "NELLO",
    "QUESTO", "QUELLO", "QUESTA", "QUELLA", "QUESTI", "QUELLI", "QUESTE", "QUELLE",
    "QUANTO", "QUANTA", "QUANTI", "QUANTE", "QUALE", "QUALI", "QUALCHE",
    "LORO", "ESSO", "ESSA", "ESSI", "ESSE", "EGLI", "ELLA", "COLUI", "COLEI", "COLORO",
    "COSTUI", "COSTEI", "QUALCUNO", "QUALCOSA", "OGNUNO", "CIASCUNO", "CIASCUNA",
    "NIENTE", "NULLA", "NESSUNO", "NESSUNA", "ALTRO", "ALTRA", "ALTRI", "ALTRE",
}

# Whitelists of native nouns ending in consonant+vowel clusters that resemble clitic infinitives
ALLOWED_RLA = {"PERLA", "CIARLA", "MERLA", "SBERLA"}
ALLOWED_RLO = {"TARLO", "MERLO", "CARLO"}
ALLOWED_RLE = {"PERLE", "CIARLE", "MERLE", "SBERLE"}
ALLOWED_RLI = {"TARLI", "MERLI"}
ALLOWED_RNE = {
    "CARNE", "LUCERNE", "CISTERNE", "ADORNE", "ALTERNE", "ESTERNE", "INTERNE", "MODERNE",
    "GOVERNE", "CAVERNE", "LANTERNE", "TAVERNE", "TERNE",
}
ALLOWED_RSI = {
    "CORSI", "DISCORSI", "PERCORSI", "CONCORSI", "RICORSI", "MORSI", "ORSI", "TRASCORSI",
    "SOCCORSI", "RIMORSI", "PARSI",
}
ALLOWED_RCI = {"MERCI", "CALCI", "SORCI", "MARCI", "ARCI", "FORCI", "QUERCI", "TORCI"}
ALLOWED_RVI = {"CORVI", "NERVI", "CERVI"}
ALLOWED_RMI = {
    "ARMI", "ALLARMI", "VERMI", "FERMI", "GERMI", "TERMI", "INFERMI", "CONFERMI",
    "SCHERMI", "UNIFORMI",
}
ALLOWED_RTI = {
    "ARTI", "PORTI", "PARTI", "CORTI", "ESPERTI", "COPERTI", "APERTI", "INCERTI",
    "SCOPERTI", "CONVERTI", "INVERTI", "REPERTI", "INSERTI", "DIVVERTI", "ASSORTI", "RISORTI",
}

CLITIC_EXACT = {
    "MELO", "MELA", "MELI", "MELE", "MENE",
    "TELO", "TELA", "TELI", "TELE", "TENE",
    "SELO", "SELA", "SELI", "SELE", "SENE",
    "CELO", "CELA", "CELI", "CELE", "CENE",
    "VELO", "VELA", "VELI", "VELE", "VENE",
    "GLIELO", "GLIELA", "GLIELI", "GLIELE", "GLIENE",
    "TIENITI", "PRENDITI", "FACCI", "DICCI", "DIGLI", "FAGLI", "FALLO", "DILLO",
    "DAMMI", "DACCI", "DAGLI", "FAMMI", "FANNE", "DIMMI", "DINNE", "DILLE", "DILLA", "DILLI",
    "FALLE", "FALLA", "FALLI", "TENERSI",
    "FARLO", "FARLA", "FARLI", "FARLE", "FARMI", "FARTI", "FARCI", "FARVI", "FARSI", "FARNE",
    "DARLO", "DARLA", "DARLI", "DARLE", "DARMI", "DARTI", "DARCI", "DARVI", "DARSI", "DARNE",
    "DIRLO", "DIRLA", "DIRLI", "DIRLE", "DIRMI", "DIRTI", "DIRCI", "DIRVI", "DIRSI", "DIRNE",
    "AMALA", "VEDIL", "SVISA",
}

# Obscure, technical, ambiguous, or bizarre words to exclude from targets
OBSCURE_TARGETS = {
    # 4 letters
    "TARE", "GORE", "COLI", "MERE", "ANTE", "ANDE", "DODO", "SAVI", "IDRA", "BIDE", "BEVA",
    "POVI", "PONE", "TRAI", "AMBO", "TIMO", "COCA", "BOIA", "DITE", "ALDO", "ALMA", "ALPI",
    "ALFA", "ANDO", "ARGO", "ARTU", "ASIA", "ASMA", "AGII", "CALA", "CALE", "CALI", "CAPA",
    "CAVE", "CIBA", "EFFE", "ELLE", "EMME", "ENNE", "ERRE", "ESSE", "ETTO", "FUSA", "FUSE",
    "LAMA", "LAME", "MENA", "MENI", "MERA", "MERI", "MERO", "MOTA", "MOTE", "MURA", "MUSA",
    "MUSE", "NANA", "NANE", "NATA", "NONA", "NONI", "NOVI", "ODIA", "ODII", "OLIA", "ORCA",
    "ORCI", "PELA", "PENE", "PENI", "PESA", "PESE", "POCA", "PUPA", "PUPE", "RADA", "RADE",
    "RADI", "RADO", "RESA", "RESE", "RISA", "RISE", "RISI", "SODA", "SODE", "SODI", "SODO",
    "TIPA", "TIPE", "TOPA", "TUBA", "TUBE", "VAGA", "VANA", "VANE", "VANI",
    # 5 letters
    "SVISA", "OPTAI", "OZIAI", "PENAI", "TOSAI", "OLIAI", "DOMAI", "CELAI", "BADAI", "BARAI",
    "CAVAI", "CIBAI", "COLAI", "COVAI", "ERRAI", "NEVAI", "PELAI", "POSAI", "REMAI", "SUDAI",
    "URLAI", "VELAI", "VINAI", "VOLAI", "ADUSO", "AFIDI", "AGAPE", "ANCIA", "AMALA", "DILLE",
    "DILLA", "DILLI", "DILLO", "FALLE", "FALLA", "FALLI", "FALLO", "DAMMI", "DACCI", "DAGLI",
    "FAMMI", "FANNE", "DIMMI", "DINNE", "FARE", "DARE", "DIRE", "BERE", "UDIRE", "USCIRE",
    "DALLO", "DELLA", "NELLA", "SULLO", "DALLA", "DELLE", "NELLE", "SULLE", "DEGLI", "DAGLI",
    "COLLA", "COLLE", "COLLO", "COGLI", "SUGLI", "NEGLI",
}

# Desinenze verbali coniugate personali da escludere tassativamente dai bersagli
VERBAL_ENDINGS = (
    "VAMO", "VATE", "VANO", "REMO", "RETE", "RANNO", "RESTE", "REBBE", "REMMO", "REBBERO",
    "ASSERO", "ESSERO", "ISSERO", "ASSIAMO", "ESSIAMO", "ISSIAMO", "ASTE", "ESTE", "ISTE",
    "AMMO", "EMMO", "IMMO", "ARONO", "ERON", "IRONO", "ANDO", "ENDO",
)


def normalize_word(word: str) -> str:
    """Normalize word to uppercase ASCII letters (A-Z), removing accents."""
    w = unicodedata.normalize("NFD", word.strip().lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return w.upper()


def is_roman(word: str) -> bool:
    """Return True if word is pure Roman numeral representation."""
    if not word.isalpha() or not word.isascii():
        return False
    return bool(re.fullmatch(r"[IVXLCDM]+", word)) and ("X" in word or "V" in word or len(word) >= 4)


def has_clitic(word: str) -> bool:
    """Return True if word is an enclitic verb formation."""
    if word in CLITIC_EXACT:
        return True
    if any(word.endswith(x) for x in [
        "MELO", "MELA", "MELI", "MELE", "MENE",
        "TELO", "TELA", "TELI", "TELE", "TENE",
        "SELO", "SELA", "SELI", "SELE", "SENE",
        "GLIELO", "GLIELA", "GLIELI", "GLIELE", "GLIENE",
    ]):
        return True
    if word.endswith("RLA") and word not in ALLOWED_RLA:
        return True
    if word.endswith("RLO") and word not in ALLOWED_RLO:
        return True
    if word.endswith("RLE") and word not in ALLOWED_RLE:
        return True
    if word.endswith("RLI") and word not in ALLOWED_RLI:
        return True
    if word.endswith("RNE") and word not in ALLOWED_RNE:
        return True
    if word.endswith("RSI") and word not in ALLOWED_RSI:
        return True
    if word.endswith("RCI") and word not in ALLOWED_RCI:
        return True
    if word.endswith("RVI") and word not in ALLOWED_RVI:
        return True
    if word.endswith("RMI") and word not in ALLOWED_RMI:
        return True
    if word.endswith("RTI") and word not in ALLOWED_RTI:
        return True
    return False


def build_clean_dictionary(
    output_path: Path,
    callback: Optional[Callable[[str], None]] = None,
) -> Tuple[int, int]:
    """Download clean Italian linguistic sources and compile verified dictionary."""
    if callback:
        callback("Download vocabolario completo 280k...")
    req280 = urllib.request.urlopen(DICT_280K_URL, timeout=30)
    lex280 = set(
        normalize_word(l)
        for l in req280.read().decode("utf-8").splitlines()
        if l.strip()
    )

    if callback:
        callback("Download Nuovo Vocabolario di Base (De Mauro)...")
    req_nvdb = urllib.request.urlopen(NVDB_URL, timeout=30)
    content_nvdb = req_nvdb.read().decode("utf-8")
    reader_nvdb = csv.DictReader(io.StringIO(content_nvdb))

    noun_lemmas: Set[Tuple[str, str]] = set()
    adj_lemmas: Set[str] = set()

    for r in reader_nvdb:
        lemma = normalize_word(r.get("parola", ""))
        pos = r.get("pos", "")
        gender = r.get("gender", "")

        # Exclude pure verbs and infinitive verbs (es. fare, andare, parlare, bere)
        if pos == "verbo" or (pos.startswith("verbo") and lemma.endswith(("ARE", "ERE", "IRE"))):
            continue

        if "sostantivo" in pos:
            noun_lemmas.add((lemma, gender))
        elif "aggettivo" in pos:
            adj_lemmas.add(lemma)

    if callback:
        callback("Download liste Wordle curate (5 lettere)...")
    req_wl5 = urllib.request.urlopen(WORDLIST5_URL, timeout=30)
    wl5 = set(
        normalize_word(l)
        for l in req_wl5.read().decode("utf-8").splitlines()
        if l.strip()
    )

    if callback:
        callback("Download filtri blacklist e nomi propri...")
    req_bad = urllib.request.urlopen(BADWORDS_URL, timeout=30)
    badwords = set(
        normalize_word(l)
        for l in req_bad.read().decode("utf-8").splitlines()
        if l.strip()
    )

    req_rem = urllib.request.urlopen(REMOVE_URL, timeout=30)
    rem_words = set(
        normalize_word(l)
        for l in req_rem.read().decode("utf-8").splitlines()
        if l.strip()
    )
    blacklist = badwords | rem_words

    req_nomi = urllib.request.urlopen(NAMES_URL, timeout=30)
    nomi = set(
        normalize_word(l)
        for l in req_nomi.read().decode("utf-8").splitlines()
        if l.strip()
    )
    all_noun_lemmas_set = {lem for lem, _ in noun_lemmas}
    pure_names = nomi - all_noun_lemmas_set - adj_lemmas

    if callback:
        callback("Generazione sostantivi e aggettivi (singolari/plurali)...")

    # Regular inflection of nouns and adjectives
    valid_nouns_adjs: Set[str] = set()

    for lemma, gender in noun_lemmas:
        if lemma in lex280:
            valid_nouns_adjs.add(lemma)
        if "invariabile" in gender:
            continue
        if "femminile" in gender:
            if lemma.endswith("A") and lemma[:-1] + "E" in lex280:
                valid_nouns_adjs.add(lemma[:-1] + "E")
            elif lemma.endswith("E") and lemma[:-1] + "I" in lex280:
                valid_nouns_adjs.add(lemma[:-1] + "I")
        else:  # maschile
            if lemma.endswith("O") and lemma[:-1] + "I" in lex280:
                valid_nouns_adjs.add(lemma[:-1] + "I")
            elif lemma.endswith("A") and lemma[:-1] + "I" in lex280:
                valid_nouns_adjs.add(lemma[:-1] + "I")
            elif lemma.endswith("E") and lemma[:-1] + "I" in lex280:
                valid_nouns_adjs.add(lemma[:-1] + "I")
            elif lemma.endswith("CO") and lemma[:-2] + "CHI" in lex280:
                valid_nouns_adjs.add(lemma[:-2] + "CHI")
            elif lemma.endswith("GO") and lemma[:-2] + "GHI" in lex280:
                valid_nouns_adjs.add(lemma[:-2] + "GHI")

    for lemma in adj_lemmas:
        if lemma in lex280:
            valid_nouns_adjs.add(lemma)
        if lemma.endswith("O"):
            for end in ["A", "I", "E"]:
                c = lemma[:-1] + end
                if c in lex280:
                    valid_nouns_adjs.add(c)
        elif lemma.endswith("E"):
            c = lemma[:-1] + "I"
            if c in lex280:
                valid_nouns_adjs.add(c)

    if callback:
        callback("Filtro e suddivisione per lunghezze 4..8...")

    target_pool = (
        (valid_nouns_adjs | LOANWORDS_CONS)
        - FUNCTION_WORDS
        - OBSCURE_TARGETS
        - blacklist
        - pure_names
    )

    data = {"targets": {}, "guesses": {}}

    for length in (4, 5, 6, 7, 8):
        targets = sorted(
            w for w in target_pool
            if len(w) == length
            and not is_roman(w)
            and not has_clitic(w)
            and not any(w.endswith(e) for e in VERBAL_ENDINGS)
            and (w[-1] in "AEIOU" or w in LOANWORDS_CONS)
        )

        pool = {w for w in lex280 if len(w) == length}
        if length == 5:
            pool |= wl5

        guesses = sorted(
            set(w for w in pool if w not in blacklist and not is_roman(w))
            | set(targets)
        )

        data["targets"][str(length)] = targets
        data["guesses"][str(length)] = guesses

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))

    tot_targets = sum(len(v) for v in data["targets"].values())
    tot_guesses = sum(len(v) for v in data["guesses"].values())
    return tot_targets, tot_guesses


if __name__ == "__main__":
    def print_progress(msg: str) -> None:
        print(f" • {msg}")

    print("Building dictionary.json.gz...")
    t, g = build_clean_dictionary(BUNDLED_DICT_PATH, callback=print_progress)
    print(f"Done! {t:,} targets, {g:,} guesses saved to {BUNDLED_DICT_PATH}.")
