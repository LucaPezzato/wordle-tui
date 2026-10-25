"""Utility script to build clean Italian Wordle dictionary."""

from __future__ import annotations

import gzip
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

# Common loanwords ending in consonant widely used in Italian
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
        callback("Download indice di frequenza d'uso...")
    req_freq = urllib.request.urlopen(FREQ_URL, timeout=30)
    freq_dict: Dict[str, int] = {}
    for line in req_freq.read().decode("utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            w = normalize_word(parts[0])
            freq_dict[w] = max(freq_dict.get(w, 0), int(parts[1]))

    if callback:
        callback("Download Nuovo Vocabolario di Base (De Mauro)...")
    req_nvdb = urllib.request.urlopen(NVDB_URL, timeout=30)
    nvdb_lemmas: Set[str] = set()
    for l in req_nvdb.read().decode("utf-8").splitlines()[1:]:
        parts = l.split(",")
        if parts:
            nvdb_lemmas.add(normalize_word(parts[0]))

    if callback:
        callback("Download liste Wordle curate (5 lettere)...")
    req_cur = urllib.request.urlopen(CURATED5_URL, timeout=30)
    cur5 = set(
        normalize_word(l)
        for l in req_cur.read().decode("utf-8").splitlines()
        if l.strip()
    )

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
    pure_names = nomi - nvdb_lemmas

    if callback:
        callback("Curatela e selezione parole per lunghezze 4..8...")

    def is_clean_target(word: str, length: int, min_freq: int = 35) -> bool:
        if len(word) != length:
            return False
        if word in blacklist or word in pure_names:
            return False
        if is_roman(word):
            return False
        if word[-1] not in "AEIOU" and word not in LOANWORDS_CONS:
            return False
        if has_clitic(word):
            return False
        if word not in lex280 and word not in cur5:
            return False
        freq = freq_dict.get(word, 0)
        if freq < min_freq and word not in nvdb_lemmas:
            return False
        # Rare 1st-person passato remoto in -AI
        if word.endswith("AI") and freq < 100 and word not in nvdb_lemmas:
            return False
        return True

    data = {"targets": {}, "guesses": {}}

    for length in (4, 5, 6, 7, 8):
        all_cands = {w for w in lex280 if len(w) == length}
        if length == 5:
            all_cands |= cur5

        targets = sorted(
            w for w in all_cands if is_clean_target(w, length, min_freq=35)
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
