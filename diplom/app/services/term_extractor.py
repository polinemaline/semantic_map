from __future__ import annotations

import re
import unicodedata
from typing import Iterable


CYRILLIC_RE = r"А-Яа-яЁё"
LATIN_RE = r"A-Za-z"
LETTER_RE = rf"{LATIN_RE}{CYRILLIC_RE}"

SOFT_HYPHEN_MARK = "\ue000"

FRAME_BORDER_CHARS = "_-—–─━═=|│┃║┌┐└┘┏┓┗┛╭╮╰╯╔╗╚╝╠╣╦╩╬+"

TOKEN_RE = re.compile(
    rf"\([A-Za-zА-Яа-яЁё0-9\-]+\)|"
    rf"[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)*"
)

SEPARATOR_RE = re.compile(r"\s(?:—|–|-)\s")

ABBREVIATION_PATTERN = re.compile(
    r"(?P<left>[^()\n]{5,300}?)"
    r"\(\s*далее\s+(?:—|–|-)\s+"
    r"(?P<abbr>[A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-]{1,20})\s*\)",
    re.IGNORECASE,
)

ABBREVIATION_LIST_ITEM_RE = re.compile(
    r"(?ms)"
    r"(?:^|[;:\n])\s*"
    r"(?:[-—–]\s*)?"
    r"(?P<abbr>[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*(?:\s+[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9]*){0,3})"
    r"\s*[-—–]\s*"
    r"(?P<definition>.*?)(?=(?:[;]\s*(?:[-—–]\s*)?[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*(?:\s+[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9]*){0,3}\s*[-—–])|\n\s*(?:[-—–]\s*)?[A-ZА-ЯЁ][A-ZА-ЯЁ0-9]*(?:\s+[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9]*){0,3}\s*[-—–]|\Z)"
)

GOST_GLOSSARY_HEADER_RE = re.compile(
    r"(?im)^\s*(?P<section>\d+)?\s*"
    r"Термины(?:\s+и\s+определения|,\s*определения\s+и\s+сокращения)?\s*$"
)

STATIC_GLOSSARY_END_RE = re.compile(
    r"(?im)^\s*(?:Алфавитный указатель|Библиография|Ключевые слова|УДК)\b"
)

ENTRY_OR_SECTION_START_RE = re.compile(
    r"(?m)^\s*(?P<num>\d+(?:\.\d+){1,4})\b(?P<body>[^\n]*)"
)

LEGACY_52653_ARTICLE_BLOCK_RE = re.compile(
    r"(?ms)^\s*(?P<num>3\.\d+\.\d+)\s*(?:\n+|\s+)"
    r"(?P<body>.*?)"
    r"(?="
    r"^\s*3\.\d+\.\d+\s*(?:\n+|\s+)|"
    r"^\s*3\.\d+\s+[^\n]+|"
    r"^\s*4\s+\S|"
    r"^\s*Алфавитный указатель|"
    r"^\s*Библиография|"
    r"^\s*Ключевые слова|"
    r"\Z)"
)

BAD_EDGE_WORDS = {
    "и",
    "или",
    "а",
    "но",
    "что",
    "кто",
    "который",
    "которая",
    "которые",
    "это",
    "этот",
    "эта",
    "эти",
    "он",
    "она",
    "оно",
    "они",
    "мы",
    "вы",
    "ты",
    "я",
    "не",
    "да",
    "нет",
    "ли",
    "нибудь",
    "рисунок",
    "рис",
    "таблица",
    "табл",
    "приложение",
    "пример",
    "примечание",
    "гост",
}

BAD_TERM_PREFIXES = (
    "гост",
    "дата введения",
    "поправка к гост",
    "федеральное агентство",
    "национальный стандарт",
    "содержание",
    "предисловие",
    "введение",
    "библиография",
    "ключевые слова",
)

BAD_TERM_SENTENCE_WORDS = {
    "должен",
    "должна",
    "должно",
    "должны",
    "применен",
    "применена",
    "применено",
    "применены",
    "применяется",
    "применяются",
    "обеспечивает",
    "обеспечивают",
    "обеспечивать",
    "учитывает",
    "учитывают",
    "учитывать",
    "отражает",
    "отражают",
    "отражать",
    "использует",
    "используют",
    "использовать",
    "создает",
    "создают",
    "создавать",
    "включает",
    "включают",
    "включать",
    "содержит",
    "содержат",
    "содержать",
    "позволяет",
    "позволяют",
    "позволять",
}

BAD_DEFINITION_PREFIXES = ("200", "19", "18", "17", "16")

BAD_PLAIN_DEFINITION_START_WORDS = {
    "в",
    "во",
    "на",
    "по",
    "при",
    "для",
    "из",
    "с",
    "со",
    "у",
    "к",
    "ко",
    "от",
    "до",
    "об",
    "о",
    "под",
    "над",
    "между",
    "через",
    "после",
    "перед",
}

PREPOSITIONS_FOR_TAIL = (
    " на ",
    " в ",
    " во ",
    " по ",
    " для ",
    " об ",
    " о ",
    " от ",
    " про ",
)

ALLOWED_LATIN_ABBREVIATIONS = {
    "API",
    "ASCII",
    "BIM",
    "CSCL",
    "CSS",
    "CSV",
    "DNS",
    "DOM",
    "HTML",
    "HTTP",
    "HTTPS",
    "ICT",
    "IOM",
    "IP",
    "ISO",
    "IT",
    "JSON",
    "LCMS",
    "LMS",
    "LOM",
    "LTS",
    "MLR",
    "PDF",
    "RDF",
    "SGA",
    "SQL",
    "TCP",
    "TLS",
    "URI",
    "URL",
    "USB",
    "UTF",
    "WEB",
    "XML",
    "XSD",
}

LATIN_NOISE_WORDS = {
    "and",
    "apprentissage",
    "blended",
    "block",
    "blocks",
    "cell",
    "class",
    "collaborative",
    "column",
    "communication",
    "computer",
    "confidential",
    "content",
    "corporate",
    "data",
    "database",
    "distant",
    "document",
    "documentary",
    "education",
    "electronic",
    "false",
    "figure",
    "file",
    "formation",
    "hypermedia",
    "image",
    "information",
    "informaftion",
    "input",
    "learning",
    "line",
    "management",
    "medium",
    "message",
    "metadata",
    "mobile",
    "multimedia",
    "name",
    "network",
    "none",
    "null",
    "object",
    "objective",
    "off",
    "on",
    "open",
    "operator",
    "output",
    "page",
    "product",
    "resource",
    "row",
    "security",
    "signature",
    "software",
    "system",
    "table",
    "teacher",
    "technology",
    "telecommunication",
    "text",
    "training",
    "true",
    "type",
    "value",
    "word",
}

KNOWN_FUSED_WORDS = {
    "базаданных": "база данных",
    "информационныхтехнологий": "информационных технологий",
    "информационнотелекоммуникационной": "информационно-телекоммуникационной",
    "сопределением": "с определением",
    "образуетего": "образует его",
}


def _strip_combining_marks(value: str) -> str:
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def normalize_unicode(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = _strip_combining_marks(value)
    value = value.replace("\xa0", " ")
    value = value.replace("\u202f", " ")
    value = value.replace("\ufeff", "")
    value = value.replace("\u00ad", SOFT_HYPHEN_MARK)
    value = value.replace("￾", SOFT_HYPHEN_MARK)
    value = value.replace("\x02", SOFT_HYPHEN_MARK)
    value = value.replace("﹣", "-")
    value = value.replace("‐", "-")
    value = value.replace("−", "-")
    return value


def remove_frame_artifacts(value: str) -> str:
    border_class = re.escape(FRAME_BORDER_CHARS)
    cleaned_lines: list[str] = []

    for raw_line in value.splitlines():
        line = raw_line.strip()
        compact = re.sub(r"\s+", "", line)

        if compact and re.fullmatch(rf"[{border_class}]{{3,}}", compact):
            continue

        raw_line = re.sub(rf"^\s*(?:[{border_class}]\s*){{3,}}", "", raw_line)
        raw_line = re.sub(rf"(?:\s*[{border_class}]){{3,}}\s*$", "", raw_line)
        raw_line = re.sub(rf"^\s*[|│┃║]\s+(?=[{LETTER_RE}])", "", raw_line)
        raw_line = re.sub(rf"\s+[|│┃║]\s*$", "", raw_line)

        cleaned_lines.append(raw_line)

    return "\n".join(cleaned_lines)


def apply_known_fused_words(value: str) -> str:
    for wrong, replacement in KNOWN_FUSED_WORDS.items():

        def replace(match: re.Match[str], replacement: str = replacement) -> str:
            original = match.group(0)
            if original and original[0].isupper():
                return replacement[:1].upper() + replacement[1:]
            return replacement

        value = re.sub(
            rf"(?<![{LETTER_RE}]){re.escape(wrong)}(?![{LETTER_RE}])",
            replace,
            value,
            flags=re.IGNORECASE,
        )

    return value


def strip_trailing_english_column(line: str) -> str:
    if not re.search(rf"[{CYRILLIC_RE}]", line):
        return line.rstrip()

    return re.sub(
        rf"(?<=[{CYRILLIC_RE}{SOFT_HYPHEN_MARK}0-9\]\).,;:])"
        rf"\s{{2,}}[A-Za-z][A-Za-z0-9\s;,\-/()]*$",
        "",
        line.rstrip(),
    ).rstrip()


def _is_allowed_latin_token(token: str) -> bool:
    clear = token.strip("()[]{}.,;:!?\"'«»„“”")
    if not clear:
        return False

    if clear.upper() in ALLOWED_LATIN_ABBREVIATIONS:
        return True

    if clear.isupper() and 2 <= len(clear) <= 10:
        return True

    return False


def remove_latin_noise_inside_russian(value: str) -> str:
    token_pattern = re.compile(
        rf"(?P<left>[{CYRILLIC_RE}]{{2,}})\s+"
        rf"(?P<latin>[A-Za-z]{{2,}})\s+"
        rf"(?P<right>[{CYRILLIC_RE}]{{2,}})"
    )

    def replace(match: re.Match[str]) -> str:
        latin = match.group("latin")
        if _is_allowed_latin_token(latin):
            return match.group(0)
        return f"{match.group('left')} {match.group('right')}"

    previous = None
    current = value
    for _ in range(4):
        if current == previous:
            break
        previous = current
        current = token_pattern.sub(replace, current)

    return current


def clean_line(value: str) -> str:
    value = normalize_unicode(value)
    value = remove_frame_artifacts(value)
    value = value.replace(SOFT_HYPHEN_MARK, "")
    value = apply_known_fused_words(value)
    value = remove_latin_noise_inside_russian(value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    value = re.sub(r"([«„“])\s+", r"\1", value)
    value = re.sub(r"\s+([»”])", r"\1", value)
    return value.strip()


def normalize_for_lookup(value: str) -> str:
    value = clean_line(value).lower().replace("ё", "е")
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"_", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def token_words(value: str) -> list[str]:
    tokens = TOKEN_RE.findall(value)
    return [t for t in tokens if not (t.startswith("(") and t.endswith(")"))]


def first_word(value: str) -> str:
    words = token_words(value)
    if not words:
        return ""
    return normalize_for_lookup(words[0])


def token_starts_upper(token: str) -> bool:
    raw = token.strip("()")
    return bool(raw) and raw[0].isalpha() and raw[0].isupper()


def contains_bad_mixed_token(value: str) -> bool:
    for token in TOKEN_RE.findall(value):
        clear = token.strip("()")
        has_cyrillic = re.search(rf"[{CYRILLIC_RE}]", clear) is not None
        has_latin = re.search(r"[A-Za-z]", clear) is not None

        if has_cyrillic and has_latin:
            if "-" in clear:
                parts = clear.split("-")
                if all(
                    _is_allowed_latin_token(part)
                    or re.fullmatch(rf"[{CYRILLIC_RE}]+", part)
                    for part in parts
                ):
                    continue

            if re.match(r"^[A-Z]{2,10}[А-Яа-яЁё]+$", clear):
                continue

            return True

    return False


def has_unwanted_latin_noise(value: str) -> bool:
    words = token_words(value)
    if not words:
        return False

    has_cyrillic_word = False

    for word in words:
        clear = word.strip("()")
        if re.search(rf"[{CYRILLIC_RE}]", clear):
            has_cyrillic_word = True
            continue

        if re.fullmatch(r"[A-Za-z][A-Za-z0-9\-]*", clear):
            if _is_allowed_latin_token(clear):
                continue

            if clear.lower() in LATIN_NOISE_WORDS:
                return True

            if has_cyrillic_word and clear.islower() and len(clear) > 2:
                return True

    return False


def looks_like_term(term: str) -> bool:
    term = clean_line(term)

    if len(term) < 2 or len(term) > 180:
        return False

    if not re.search(rf"[{LETTER_RE}]", term):
        return False

    # Термин не должен содержать двоеточие.
    # Если двоеточие оказалось внутри term, значит парсер захватил
    # кусок уже готовой пары "термин: определение" как новый термин.
    # Пример ошибки:
    # "знания: Совокупность фактов, событий, убеждений..."
    if ":" in term:
        return False

    if contains_bad_mixed_token(term) or has_unwanted_latin_noise(term):
        return False

    term_norm = normalize_for_lookup(term)
    if not term_norm:
        return False

    if term_norm.startswith(BAD_TERM_PREFIXES):
        return False

    words = token_words(term)
    if not words:
        return False

    if len(words) > 12:
        return False

    normalized_words = {normalize_for_lookup(word) for word in words}

    # Обычные фразы-требования или фрагменты предложений не должны
    # становиться терминами.
    if "должен" in normalized_words:
        return False
    if "должна" in normalized_words:
        return False
    if "должно" in normalized_words:
        return False
    if "должны" in normalized_words:
        return False
    if "обеспечивает" in normalized_words:
        return False
    if "обеспечивают" in normalized_words:
        return False
    if "обеспечивать" in normalized_words:
        return False
    if "учитывает" in normalized_words:
        return False
    if "учитывают" in normalized_words:
        return False
    if "учитывать" in normalized_words:
        return False
    if "отражает" in normalized_words:
        return False
    if "отражают" in normalized_words:
        return False
    if "отражать" in normalized_words:
        return False
    if "использует" in normalized_words:
        return False
    if "используют" in normalized_words:
        return False
    if "использовать" in normalized_words:
        return False
    if "создает" in normalized_words:
        return False
    if "создают" in normalized_words:
        return False
    if "создавать" in normalized_words:
        return False
    if "включает" in normalized_words:
        return False
    if "включают" in normalized_words:
        return False
    if "включать" in normalized_words:
        return False
    if "содержит" in normalized_words:
        return False
    if "содержат" in normalized_words:
        return False
    if "содержать" in normalized_words:
        return False
    if "позволяет" in normalized_words:
        return False
    if "позволяют" in normalized_words:
        return False
    if "позволять" in normalized_words:
        return False
    if "применен" in normalized_words:
        return False
    if "применена" in normalized_words:
        return False
    if "применено" in normalized_words:
        return False
    if "применены" in normalized_words:
        return False
    if "применяется" in normalized_words:
        return False
    if "применяются" in normalized_words:
        return False

    first_norm = normalize_for_lookup(words[0])
    last_norm = normalize_for_lookup(words[-1])

    if first_norm in BAD_EDGE_WORDS or last_norm in BAD_EDGE_WORDS:
        return False

    if re.fullmatch(r"[\d\s\-–—()]+", term):
        return False

    if term.endswith((".", ",", ";")):
        return False

    return True


def looks_like_abbreviation_term(term: str) -> bool:
    term = clean_line(term)
    words = term.split()

    if not words or len(words) > 4:
        return False

    if len(term) > 60:
        return False

    has_latin_or_upper = False

    for word in words:
        clear = word.strip("()[]{}.,;:!?\"'«»„“”")
        if not clear:
            return False

        if clear.upper() in ALLOWED_LATIN_ABBREVIATIONS:
            has_latin_or_upper = True
            continue

        if re.fullmatch(r"[A-ZА-ЯЁ0-9]{2,15}", clear):
            has_latin_or_upper = True
            continue

        if re.fullmatch(r"[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё0-9]{1,20}", clear):
            has_latin_or_upper = True
            continue

        return False

    return has_latin_or_upper


def looks_like_definition(definition: str, require_eto: bool = False) -> bool:
    definition = clean_line(definition)

    if len(definition) < 5:
        return False

    if not re.search(rf"[{LETTER_RE}]", definition):
        return False

    if contains_bad_mixed_token(definition):
        return False

    if require_eto and not definition.lower().startswith("это"):
        return False

    if len(definition.split()) < 2:
        return False

    if re.fullmatch(r"[\d\s\-–—./]+", definition):
        return False

    if definition.lower().startswith(BAD_DEFINITION_PREFIXES):
        return False

    return True


def cleanup_text_for_extraction(text: str) -> str:
    text = normalize_unicode(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = remove_frame_artifacts(text)

    lines = [strip_trailing_english_column(line) for line in text.splitlines()]
    text = "\n".join(lines)

    text = re.sub(
        rf"([{LETTER_RE}]{{2,}})\s*{SOFT_HYPHEN_MARK}\s*\n\s*([{LETTER_RE}]{{2,}})",
        r"\1\2",
        text,
    )
    text = re.sub(
        rf"([{LETTER_RE}]{{2,}})-\s*\n\s*([{LETTER_RE}]{{2,}})",
        r"\1\2",
        text,
    )

    text = text.replace(SOFT_HYPHEN_MARK, "")

    cleaned_lines = [clean_line(line) if line.strip() else "" for line in text.split("\n")]
    text = "\n".join(cleaned_lines)

    text = remove_frame_artifacts(text)
    text = apply_known_fused_words(text)
    text = remove_latin_noise_inside_russian(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def trim_quotes(value: str) -> str:
    return clean_line(value).strip(" \"'«»„“”")


def looks_like_gost_document(text: str) -> bool:
    lowered = text.lower().replace("ё", "е")
    return (
        "гост р" in lowered
        or "национальный стандарт" in lowered
        or "исо/мэк" in lowered
        or "iso/iec" in lowered
    )


def _glossary_area_has_numbered_entries(area: str) -> bool:
    return bool(
        re.search(r"(?m)^\s*\d+(?:\.\d+){1,4}\b[^\n:]{0,700}:", area)
        or (
            re.search(r"(?m)^\s*\d+(?:\.\d+){1,4}\s*$", area)
            and ":" in area
        )
    )


def _build_glossary_area_from_header(text: str, header_match: re.Match[str]) -> str | None:
    tail = text[header_match.end() :]
    section_number = header_match.group("section")
    end_candidates: list[int] = []

    static_end = STATIC_GLOSSARY_END_RE.search(tail)
    if static_end:
        end_candidates.append(static_end.start())

    if section_number and section_number.isdigit():
        next_section = int(section_number) + 1
        next_section_match = re.search(
            rf"(?im)^\s*{next_section}\s+[А-ЯA-ZЁ][^\n]*$",
            tail,
        )
        if next_section_match:
            end_candidates.append(next_section_match.start())

    end = min(end_candidates) if end_candidates else len(tail)
    area = tail[:end].strip()
    return area or None


def find_gost_glossary_areas(text: str) -> list[str]:
    candidates: list[tuple[int, str]] = []
    fallback_candidates: list[str] = []

    for match in GOST_GLOSSARY_HEADER_RE.finditer(text):
        area = _build_glossary_area_from_header(text, match)
        if not area:
            continue

        section_number = match.group("section")
        has_entries = _glossary_area_has_numbered_entries(area)

        if has_entries:
            priority = 0 if section_number else 1
            candidates.append((priority, area))
        else:
            fallback_candidates.append(area)

    if candidates:
        candidates.sort(key=lambda item: item[0])
        return [area for _, area in candidates]

    return fallback_candidates[:1]


def find_gost_glossary_area(text: str) -> str | None:
    areas = find_gost_glossary_areas(text)
    return areas[0] if areas else None


def extract_general_candidate_area(text: str) -> str:
    lowered = text.lower().replace("ё", "е")
    start = 0

    start_markers = [
        "\n1 область применения",
        "\n1 общие положения",
        "\n1 ",
    ]

    found_starts = []
    for marker in start_markers:
        idx = lowered.find(marker)
        if idx != -1:
            found_starts.append(idx)

    if found_starts:
        start = min(found_starts)

    end = len(text)
    end_markers = [
        "\nалфавитный указатель",
        "\nбиблиография",
        "\nключевые слова",
        "\nудк ",
    ]

    found_ends = []
    for marker in end_markers:
        idx = lowered.find(marker, start + 1)
        if idx != -1:
            found_ends.append(idx)

    if found_ends:
        end = min(found_ends)

    return text[start:end].strip()


def is_reference_line(line: str) -> bool:
    line = clean_line(line)
    if not line:
        return False

    if line.startswith("[") and "ГОСТ" in line.upper():
        return True

    upper = line.upper()

    if upper.startswith("ГОСТ ") or upper.startswith("ГОСТ Р "):
        return True

    if upper.startswith("ISO") or upper.startswith("IEC") or upper.startswith("RFC"):
        return True

    return False


def is_note_line(line: str) -> bool:
    line = clean_line(line).lower().replace("ё", "е")
    compact = re.sub(r"\s+", "", line)

    return (
        line.startswith("примечание")
        or line.startswith("примечания")
        or compact.startswith("примечание")
        or compact.startswith("примечания")
    )


def is_english_glossary_line(line: str) -> bool:
    line = clean_line(line)
    if not line:
        return False

    has_cyrillic = bool(re.search(rf"[{CYRILLIC_RE}]", line))
    has_latin = bool(re.search(r"[A-Za-z]", line))

    return has_latin and not has_cyrillic


def is_page_marker_line(line: str) -> bool:
    line = clean_line(line)

    if not line:
        return True

    if re.fullmatch(r"[IVXLCM]+", line):
        return True

    if re.fullmatch(r"\d+", line):
        return True

    if re.fullmatch(r"ГОСТ\s+Р\s+\d+\s*[—-]\s*\d+", line, flags=re.IGNORECASE):
        return True

    if "ГОСТ Р 52653" in line:
        return True

    if "ГОСТ Р 55750" in line:
        return True

    if "ГОСТ Р 59870" in line:
        return True

    if "ГОСТ Р 59871" in line:
        return True

    if "ГОСТ Р ИСО/МЭК" in line:
        return True

    if line.lower() == "издание официальное":
        return True
    if "ISO/IEC 2382" in line.upper():
        return True

    if "IEC 2382" in line.upper():
        return True

    if "ИСО/МЭК 2382" in line.upper():
        return True

    if "IEC ELECTROPEDIA" in line.upper():
        return True
    
    return False


def cleanup_definition_block(definition_block: str) -> str:
    lines: list[str] = []

    for raw_line in definition_block.splitlines():
        line = strip_trailing_english_column(raw_line)
        line = clean_line(line)

        if not line:
            continue

        if is_note_line(line):
            break

        if is_reference_line(line):
            break

        if is_page_marker_line(line):
            continue

        if is_english_glossary_line(line):
            continue

        if re.fullmatch(r"\d+(?:\.\d+){0,2}\s+.+", line) and ":" not in line:
            continue

        lines.append(line)

    definition = " ".join(lines)
    definition = clean_line(definition)
    definition = re.sub(r"\s+\[\s*ГОСТ.*$", "", definition, flags=re.IGNORECASE)
    definition = re.sub(r"\s+ГОСТ\s+Р\s+.*$", "", definition, flags=re.IGNORECASE)
    definition = re.sub(r"\s+статья\s+\d+(?:\.\d+)*\s*$", "", definition, flags=re.IGNORECASE)

    return definition


def remove_multilingual_equivalents(term_part: str) -> str:
    term_part = clean_line(term_part)

    term_part = re.sub(
        r"\s*\((?=[^)]*\b(?:en|fr|de|англ|фр)\b)[^)]*\)\s*$",
        "",
        term_part,
        flags=re.IGNORECASE,
    )
    term_part = re.sub(
        r"\s*\[(?=[^\]]*\b(?:en|fr|de|англ|фр)\b)[^\]]*\]\s*$",
        "",
        term_part,
        flags=re.IGNORECASE,
    )

    return clean_line(term_part)


def split_term_and_short_form(term_part: str) -> tuple[str, str | None]:
    term_part = clean_line(term_part)

    if ";" not in term_part:
        return term_part, None

    left, right = term_part.split(";", 1)
    left = clean_line(left)
    right = clean_line(right)

    if right and len(right) <= 40 and not has_unwanted_latin_noise(right):
        return left, right

    return term_part, None


def is_abbreviation_section_heading(term_part: str) -> bool:
    normalized = normalize_for_lookup(term_part)
    return (
        "сокращения" in normalized
        and (
            "применены следующие сокращения" in normalized
            or "применяются следующие сокращения" in normalized
            or "настоящем стандарте применены" in normalized
        )
    )


def _block_has_colon_before_sentence_text(block: str) -> bool:
    colon_pos = block.find(":")
    if colon_pos == -1:
        return False

    before_colon = clean_line(block[:colon_pos])
    before_colon = re.sub(r"^\d+(?:\.\d+)*\s*", "", before_colon).strip()

    if not before_colon:
        return False

    if is_abbreviation_section_heading(before_colon):
        return False

    words = token_words(before_colon)
    if len(words) > 14:
        return False

    normalized_words = {normalize_for_lookup(word) for word in words}
    if normalized_words & BAD_TERM_SENTENCE_WORDS:
        return False

    return True


def parse_structured_article_body(body: str) -> dict | None:
    body = body.strip()
    body = re.sub(r"^\d+(?:\.\d+)*\s*", "", body).strip()

    colon_pos = body.find(":")

    if colon_pos == -1 or colon_pos > 700:
        return None

    if not _block_has_colon_before_sentence_text(body):
        return None

    term_part = clean_line(body[:colon_pos])
    definition_block = body[colon_pos + 1 :]

    term_part = re.sub(r"^\d+(?:\.\d+)*\s*", "", term_part).strip()
    term_part = remove_multilingual_equivalents(term_part)

    if is_abbreviation_section_heading(term_part):
        return None

    term, short_form = split_term_and_short_form(term_part)
    term = clean_line(term)
    definition = cleanup_definition_block(definition_block)

    if not looks_like_term(term):
        return None

    if not looks_like_definition(definition):
        return None

    entry = {
        "term": term,
        "definition": definition,
        "source_line": clean_line(f"{term_part}: {definition}")[:500],
    }

    if short_form and looks_like_term(short_form):
        entry["short_form"] = short_form

    return entry


def cleanup_abbreviation_definition(value: str) -> str:
    value = clean_line(value)

    # Убираем хвосты колонтитулов, которые иногда приклеиваются к последнему
    # элементу списка сокращений, например:
    # "Метаданные для записи ресурса обучения; 2 ГОСТ Р 55750-2013"
    value = re.sub(
        r"\s*;?\s*\d{1,4}\s+ГОСТ\s+Р\s+[\d\s./А-Яа-яA-Za-zЁё\-]+$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s*;?\s*ГОСТ\s+Р\s+[\d\s./А-Яа-яA-Za-zЁё\-]+$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s*;?\s*\d{1,4}\s+ГОСТ\s+Р\s+И?С?О?/?М?Э?К?\s*[\d\s./А-Яа-яA-Za-zЁё\-]+$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = value.strip(" ;,.")
    value = re.sub(r"\s+", " ", value)

    return value


def extract_abbreviation_list_entries(text: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    if not re.search(r"(?i)\b(?:сокращения|аббревиатуры)\b", text):
        return results

    for match in ABBREVIATION_LIST_ITEM_RE.finditer(text):
        abbr = clean_line(match.group("abbr"))
        definition = cleanup_abbreviation_definition(match.group("definition"))

        if not looks_like_abbreviation_term(abbr):
            continue

        if not looks_like_definition(definition):
            continue

        key = (
            normalize_for_lookup(abbr),
            normalize_for_lookup(definition),
        )

        if key in seen:
            continue

        seen.add(key)
        results.append(
            {
                "term": abbr,
                "definition": definition,
                "source_line": clean_line(f"{abbr} - {definition}")[:500],
            }
        )

    return results


def _append_entry_if_unique(
    results: list[dict],
    seen: set[tuple[str, str]],
    entry: dict | None,
) -> None:
    if not entry:
        return

    key = (
        normalize_for_lookup(entry["term"]),
        normalize_for_lookup(entry["definition"]),
    )

    if key in seen:
        return

    seen.add(key)
    results.append(entry)


def extract_legacy_52653_entries(glossary_area: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in LEGACY_52653_ARTICLE_BLOCK_RE.finditer(glossary_area):
        entry = parse_structured_article_body(match.group("body"))
        _append_entry_if_unique(results, seen, entry)

    return results


def extract_generic_numbered_entries(glossary_area: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()
    starts = list(ENTRY_OR_SECTION_START_RE.finditer(glossary_area))

    for index, match in enumerate(starts):
        block_start = match.start()
        block_end = starts[index + 1].start() if index + 1 < len(starts) else len(glossary_area)
        block = glossary_area[block_start:block_end].strip()

        if ":" not in block:
            continue

        entry = parse_structured_article_body(block)
        _append_entry_if_unique(results, seen, entry)

    return results


def extract_loose_numbered_entries(text: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    pattern = re.compile(
        r"(?ms)"
        r"^\s*(?P<num>\d+(?:\.\d+){1,4})\s+"
        r"(?P<body>.*?)(?="
        r"^\s*\d+(?:\.\d+){1,4}\s+|"
        r"^\s*[4-9]\s+[А-ЯA-ZЁ]|"
        r"^\s*Алфавитный указатель|"
        r"^\s*Библиография|"
        r"^\s*Ключевые слова|"
        r"^\s*УДК|"
        r"\Z)"
    )

    for match in pattern.finditer(text):
        block = f"{match.group('num')} {match.group('body')}".strip()
        if ":" not in block:
            continue

        entry = parse_structured_article_body(block)
        _append_entry_if_unique(results, seen, entry)

    return results


def extract_structured_gost_entries(glossary_area: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entry in extract_abbreviation_list_entries(glossary_area):
        _append_entry_if_unique(results, seen, entry)

    for entry in extract_legacy_52653_entries(glossary_area):
        _append_entry_if_unique(results, seen, entry)

    for entry in extract_generic_numbered_entries(glossary_area):
        _append_entry_if_unique(results, seen, entry)

    for entry in extract_loose_numbered_entries(glossary_area):
        _append_entry_if_unique(results, seen, entry)

    return results


def choose_tail_term_phrase(left_context: str) -> str | None:
    left_context = trim_quotes(left_context)

    if not left_context:
        return None

    if "," in left_context:
        left_context = left_context.split(",")[-1].strip()

    for prep in PREPOSITIONS_FOR_TAIL:
        prepared = f" {left_context.lower()} "
        if prep in prepared:
            pos = prepared.rfind(prep)
            tail = prepared[pos + len(prep) :].strip()
            if tail:
                candidate = trim_quotes(tail)
                if looks_like_term(candidate):
                    return candidate

    tokens = TOKEN_RE.findall(left_context)
    if not tokens:
        return None

    best_candidate = None
    best_score = -10_000

    for size in range(1, min(10, len(tokens)) + 1):
        candidate_tokens = tokens[-size:]
        candidate = trim_quotes(" ".join(candidate_tokens))

        if not looks_like_term(candidate):
            continue

        words = [t for t in candidate_tokens if not (t.startswith("(") and t.endswith(")"))]
        if not words:
            continue

        score = 0
        score += min(len(words), 8)

        if any(t.startswith("(") and t.endswith(")") for t in candidate_tokens):
            score += 6

        if token_starts_upper(words[0]):
            score += 2

        if len(words) >= 2 and token_starts_upper(words[0]) and token_starts_upper(words[1]):
            score -= 5

        lowered_words = [normalize_for_lookup(w) for w in words]
        if len(words) >= 5 and any(
            w in {"в", "во", "на", "по", "для", "из", "с", "со", "при"}
            for w in lowered_words
        ):
            score -= 2

        if score > best_score:
            best_score = score
            best_candidate = candidate

    return best_candidate


def is_non_definition_dash_case(term: str, definition: str) -> bool:
    definition_start = first_word(definition)
    if definition_start not in BAD_PLAIN_DEFINITION_START_WORDS:
        return False

    words = token_words(term)
    if len(words) < 4:
        return False

    normalized_words = [normalize_for_lookup(word) for word in words]
    if "и" in normalized_words or "в" in normalized_words or "на" in normalized_words:
        return True

    return False


def extract_right_definition(right_context: str) -> str:
    right_context = right_context.lstrip(" \t\n\r\"'«»„“")

    end = len(right_context)
    for match in re.finditer(r"[.!?\n]", right_context):
        end = match.start()
        break

    definition = right_context[:end]
    definition = trim_quotes(definition)

    if definition.endswith(("»", "\"", "'")):
        definition = definition[:-1].strip()

    return clean_line(definition)


def extract_left_clause(left_context: str) -> str:
    boundaries = [
        left_context.rfind("."),
        left_context.rfind("!"),
        left_context.rfind("?"),
        left_context.rfind("\n"),
        left_context.rfind(";"),
        left_context.rfind(":"),
        left_context.rfind("«"),
        left_context.rfind("»"),
        left_context.rfind("\""),
    ]

    cut = max(boundaries)
    if cut != -1:
        left_context = left_context[cut + 1 :]

    return trim_quotes(left_context)


def extract_dash_entries(text: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in SEPARATOR_RE.finditer(text):
        sep_start = match.start()
        sep_end = match.end()

        left_context = text[max(0, sep_start - 250) : sep_start]
        right_context = text[sep_end : sep_end + 800]

        left_clause = extract_left_clause(left_context)
        if not left_clause:
            continue

        definition = extract_right_definition(right_context)
        if not definition:
            continue

        require_eto = definition.lower().startswith("это")
        if not looks_like_definition(definition, require_eto=require_eto):
            continue

        term = choose_tail_term_phrase(left_clause)
        if not term:
            continue

        if is_non_definition_dash_case(term, definition):
            continue

        key = (
            normalize_for_lookup(term),
            normalize_for_lookup(definition),
        )

        if key in seen:
            continue

        seen.add(key)
        results.append(
            {
                "term": clean_line(term),
                "definition": clean_line(definition),
                "source_line": clean_line(f"{left_clause} — {definition}")[:500],
            }
        )

    return results


def extract_abbreviation_entries(text: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in ABBREVIATION_PATTERN.finditer(text):
        left = trim_quotes(match.group("left"))
        abbr = trim_quotes(match.group("abbr"))

        full_term = choose_tail_term_phrase(left)
        if not full_term:
            continue

        if not looks_like_term(abbr):
            continue

        if not looks_like_definition(full_term):
            continue

        key = (
            normalize_for_lookup(abbr),
            normalize_for_lookup(full_term),
        )

        if key in seen:
            continue

        seen.add(key)
        results.append(
            {
                "term": clean_line(abbr),
                "definition": clean_line(full_term),
                "source_line": clean_line(f"{full_term} (далее — {abbr})")[:500],
            }
        )

    return results


def expand_short_form_entries(entries: Iterable[dict]) -> list[dict]:
    expanded: list[dict] = []

    for entry in entries:
        expanded.append(entry)

        short_form = clean_line(str(entry.get("short_form", "")))
        term = clean_line(str(entry.get("term", "")))

        if not short_form:
            continue

        if normalize_for_lookup(short_form) == normalize_for_lookup(term):
            continue

        if not looks_like_term(short_form):
            continue

        expanded.append(
            {
                "term": short_form,
                "definition": term,
                "source_line": clean_line(f"{short_form}: {term}")[:500],
            }
        )

    return expanded


def deduplicate_entries(entries: Iterable[dict]) -> list[dict]:
    unique_entries: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entry in expand_short_form_entries(entries):
        term = clean_line(str(entry.get("term", "")))
        definition = clean_line(str(entry.get("definition", "")))

        if not looks_like_term(term) and not looks_like_abbreviation_term(term):
            continue

        if not looks_like_definition(definition):
            continue

        key = (
            normalize_for_lookup(term),
            normalize_for_lookup(definition),
        )

        if key in seen:
            continue

        seen.add(key)

        normalized_entry = dict(entry)
        normalized_entry["term"] = term
        normalized_entry["definition"] = definition
        normalized_entry["source_line"] = clean_line(
            str(entry.get("source_line", f"{term}: {definition}"))
        )[:500]

        normalized_entry.pop("short_form", None)
        unique_entries.append(normalized_entry)

    return unique_entries


def merge_entry_lists(*lists: Iterable[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entries in lists:
        for entry in entries:
            key = (
                normalize_for_lookup(str(entry.get("term", ""))),
                normalize_for_lookup(str(entry.get("definition", ""))),
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(entry)

    return merged

def detect_target_gost_number(text: str) -> str | None:
    normalized = normalize_for_lookup(text)

    if "гост р 59870 2021" in normalized or "гост р 59870" in normalized:
        return "59870"

    if "гост р 59871 2021" in normalized or "гост р 59871" in normalized:
        return "59871"

    return None


def extract_target_gost_section_3(text: str) -> str | None:
    section_start = re.search(
        r"(?im)^\s*3\s+Термины\s+и\s+определения\s*$",
        text,
    )

    if not section_start:
        return None

    tail = text[section_start.end() :]

    section_end = re.search(
        r"(?im)^\s*4\s+[А-ЯA-ZЁ][^\n]*$",
        tail,
    )

    if section_end:
        return tail[: section_end.start()].strip()

    static_end = STATIC_GLOSSARY_END_RE.search(tail)
    if static_end:
        return tail[: static_end.start()].strip()

    return tail.strip()


def is_target_gost_page_noise(line: str) -> bool:
    line = clean_line(line)

    if not line:
        return True

    if re.fullmatch(r"\d+\s*ГОСТ\s+Р\s+5987[01]\s*[—-]\s*2021", line, flags=re.IGNORECASE):
        return True

    if re.fullmatch(r"ГОСТ\s+Р\s+5987[01]\s*[—-]\s*2021", line, flags=re.IGNORECASE):
        return True

    if "ГОСТ Р 59870" in line or "ГОСТ Р 59871" in line:
        return True

    if re.fullmatch(r"[_\-—–─━═=\s]{5,}", line):
        return True

    if line.lower() == "издание официальное":
        return True

    return False


def normalize_target_gost_block(block: str) -> str:
    cleaned_lines: list[str] = []

    for raw_line in block.splitlines():
        line = clean_line(raw_line)

        if is_target_gost_page_noise(line):
            continue

        line = re.sub(r"[_\-—–─━═=]{5,}", " ", line)
        line = clean_line(line)

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def parse_target_gost_numbered_block(block: str) -> dict | None:
    block = re.sub(r"^\s*3\.\d{1,2}\s*", "", block.strip(), count=1)
    block = normalize_target_gost_block(block)

    if not block or ":" not in block:
        return None

    colon_pos = block.find(":")
    term_part = block[:colon_pos]
    definition_block = block[colon_pos + 1 :]

    term_part = remove_multilingual_equivalents(term_part)
    term_part = re.sub(r"[_\-—–─━═=]{2,}", " ", term_part)
    term_part = clean_line(term_part)

    if is_abbreviation_section_heading(term_part):
        return None

    term, short_form = split_term_and_short_form(term_part)
    term = clean_line(term)

    definition = cleanup_definition_block(definition_block)

    if not looks_like_term(term):
        return None

    if not looks_like_definition(definition):
        return None

    entry = {
        "term": term,
        "definition": definition,
        "source_line": clean_line(f"{term_part}: {definition}")[:500],
    }

    if short_form and looks_like_term(short_form):
        entry["short_form"] = short_form

    return entry


def extract_target_gost_numbered_entries(text: str) -> list[dict]:
    gost_number = detect_target_gost_number(text)
    if gost_number not in {"59870", "59871"}:
        return []

    expected_last_number = 17 if gost_number == "59870" else 30

    section = extract_target_gost_section_3(text)
    if not section:
        return []

    section = normalize_unicode(section)
    section = remove_frame_artifacts(section)
    section = section.replace(SOFT_HYPHEN_MARK, "")

    starts = list(
        re.finditer(
            r"(?m)^\s*3\.(?P<number>\d{1,2})\b[^\n]*",
            section,
        )
    )

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for index, match in enumerate(starts):
        number = int(match.group("number"))

        if number < 1 or number > expected_last_number:
            continue

        block_start = match.start()
        block_end = starts[index + 1].start() if index + 1 < len(starts) else len(section)
        block = section[block_start:block_end].strip()

        entry = parse_target_gost_numbered_block(block)
        _append_entry_if_unique(results, seen, entry)

    return results
def detect_iso_iec_2382_36_document(text: str) -> bool:
    normalized = normalize_for_lookup(text)
    upper_text = text.upper()

    return (
        "2382 36" in normalized
        and (
            "iso iec" in normalized
            or "исо мэк" in normalized
            or "IEC ELECTROPEDIA" in upper_text
            or "электропедия" in normalized
        )
    )


def extract_iso_iec_2382_36_area(text: str) -> str | None:
    first_article = re.search(
        r"(?m)^\s*3\.1\.1\b[^\n]*$",
        text,
    )

    if not first_article:
        return None

    tail = text[first_article.start() :]

    end_match = re.search(
        r"(?im)^\s*(?:"
        r"4\s+[А-ЯA-ZЁ]|"
        r"Алфавитный\s+указатель|"
        r"Библиография|"
        r"Приложение|"
        r"УДК"
        r")\b",
        tail,
    )

    if end_match:
        return tail[: end_match.start()].strip()

    return tail.strip()


def is_iso_iec_2382_36_noise_line(line: str) -> bool:
    line = clean_line(line)

    if not line:
        return True

    if is_page_marker_line(line):
        return True

    if is_reference_line(line):
        return True

    if is_english_glossary_line(line):
        return True

    if re.fullmatch(r"3\.\d+\s+[А-ЯA-ZЁ][^\n]*", line):
        return True

    if re.fullmatch(r"[_\-—–─━═=\s]{5,}", line):
        return True

    normalized = normalize_for_lookup(line)

    if normalized in {
        "общие термины",
        "термины и определения",
        "термины определения и сокращения",
    }:
        return True

    return False


def prepare_iso_iec_2382_36_block_lines(block: str) -> list[str]:
    lines: list[str] = []

    for raw_line in block.splitlines():
        line = clean_line(raw_line)

        if is_iso_iec_2382_36_noise_line(line):
            continue

        line = re.sub(r"^\s*3\.\d+\.\d+\s*", "", line).strip()
        line = clean_line(line)

        if not line:
            continue

        lines.append(line)

    return lines


def parse_iso_iec_2382_36_block(block: str) -> dict | None:
    lines = prepare_iso_iec_2382_36_block_lines(block)

    if len(lines) < 2:
        return None

    term = remove_multilingual_equivalents(lines[0])
    term = clean_line(term)

    definition_lines = lines[1:]
    definition = cleanup_definition_block("\n".join(definition_lines))

    definition = re.sub(
        r"\s+\[\s*SOURCE.*$",
        "",
        definition,
        flags=re.IGNORECASE,
    )
    definition = re.sub(
        r"\s+\[\s*ИСТОЧНИК.*$",
        "",
        definition,
        flags=re.IGNORECASE,
    )
    definition = clean_line(definition)

    if not looks_like_term(term):
        return None

    if not looks_like_definition(definition):
        return None

    return {
        "term": term,
        "definition": definition,
        "source_line": clean_line(f"{term}: {definition}")[:500],
    }


def extract_iso_iec_2382_36_entries(text: str) -> list[dict]:
    if not detect_iso_iec_2382_36_document(text):
        return []

    area = extract_iso_iec_2382_36_area(text)

    if not area:
        return []

    starts = list(
        re.finditer(
            r"(?m)^\s*(?P<number>3\.\d+\.\d+)\b(?P<tail>[^\n]*)$",
            area,
        )
    )

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for index, match in enumerate(starts):
        block_start = match.start()
        block_end = starts[index + 1].start() if index + 1 < len(starts) else len(area)
        block = area[block_start:block_end].strip()

        entry = parse_iso_iec_2382_36_block(block)
        _append_entry_if_unique(results, seen, entry)

    return results

def extract_glossary_entries(text: str) -> list[dict]:
    cleaned_text = cleanup_text_for_extraction(text)

    iso_iec_2382_36_entries = extract_iso_iec_2382_36_entries(cleaned_text)
    target_gost_entries = extract_target_gost_numbered_entries(cleaned_text)

    glossary_areas = find_gost_glossary_areas(cleaned_text)

    if glossary_areas:
        structured_groups: list[dict] = []
        abbreviation_groups: list[dict] = []

        for glossary_area in glossary_areas:
            structured_groups.extend(extract_structured_gost_entries(glossary_area))
            abbreviation_groups.extend(extract_abbreviation_entries(glossary_area))
            abbreviation_groups.extend(extract_abbreviation_list_entries(glossary_area))

        structured_entries = merge_entry_lists(
            iso_iec_2382_36_entries,
            target_gost_entries,
            structured_groups,
            abbreviation_groups,
        )

        if structured_entries:
            return deduplicate_entries(structured_entries)

    candidate_area = extract_general_candidate_area(cleaned_text)

    candidate_structured = extract_structured_gost_entries(candidate_area)
    candidate_abbreviation_list = extract_abbreviation_list_entries(candidate_area)
    abbreviation_entries = extract_abbreviation_entries(candidate_area)

    structured_entries = merge_entry_lists(
        iso_iec_2382_36_entries,
        target_gost_entries,
        candidate_structured,
        candidate_abbreviation_list,
        abbreviation_entries,
    )

    if structured_entries:
        return deduplicate_entries(structured_entries)

    if looks_like_gost_document(cleaned_text):
        return deduplicate_entries(
            iso_iec_2382_36_entries
            + target_gost_entries
            + abbreviation_entries
            + candidate_abbreviation_list
        )

    dash_entries = extract_dash_entries(candidate_area)

    return deduplicate_entries(
        iso_iec_2382_36_entries
        + target_gost_entries
        + abbreviation_entries
        + candidate_abbreviation_list
        + dash_entries
    )