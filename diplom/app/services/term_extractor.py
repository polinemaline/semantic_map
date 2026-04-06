from __future__ import annotations

import re


TOKEN_RE = re.compile(
    r"\([A-Za-zА-Яа-яЁё0-9\-]+\)|[A-Za-zА-Яа-яЁё0-9]+(?:-[A-Za-zА-Яа-яЁё0-9]+)*"
)

SEPARATOR_RE = re.compile(r"\s(?:—|–|-)\s")

ABBREVIATION_PATTERN = re.compile(
    r"(?P<left>[^()\n]{5,300}?)\(\s*далее\s+(?:—|–|-)\s+(?P<abbr>[A-ZА-ЯЁ0-9][A-ZА-ЯЁ0-9\-]{1,20})\s*\)",
    re.IGNORECASE,
)

GOST_GLOSSARY_HEADER_RE = re.compile(
    r"(?im)^\s*3\s+Термины(?:\s+и\s+определения|,\s*определения\s+и\s+сокращения)\s*$"
)

GOST_GLOSSARY_END_RE = re.compile(
    r"(?im)^\s*(?:4\s+\S|Алфавитный указатель|Библиография)\b"
)

ARTICLE_BLOCK_RE = re.compile(
    r"(?ms)^\s*(?P<num>3\.\d+\.\d+)\s*(?:\n+|\s+)(?P<body>.*?)(?="
    r"^\s*3\.\d+\.\d+\s*(?:\n+|\s+)|"
    r"^\s*3\.\d+\s+[^\n]+|"
    r"^\s*4\s+\S|"
    r"^\s*Алфавитный указатель|"
    r"^\s*Библиография|"
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

BAD_DEFINITION_PREFIXES = (
    "200",
    "19",
    "18",
    "17",
    "16",
)

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


def clean_line(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.replace("￾", "")
    value = value.replace("\ufeff", "")
    value = value.replace("\u00ad", "")
    value = re.sub(r"\s+", " ", value)
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


def looks_like_term(term: str) -> bool:
    term = clean_line(term)

    if len(term) < 2 or len(term) > 220:
        return False

    if not re.search(r"[A-Za-zА-Яа-яЁё]", term):
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

    first_norm = normalize_for_lookup(words[0])
    last_norm = normalize_for_lookup(words[-1])

    if first_norm in BAD_EDGE_WORDS or last_norm in BAD_EDGE_WORDS:
        return False

    if re.fullmatch(r"[\d\s\-–—()]+", term):
        return False

    if term.endswith((".", ",", ":", ";")):
        return False

    return True


def looks_like_definition(definition: str, require_eto: bool = False) -> bool:
    definition = clean_line(definition)

    if len(definition) < 5:
        return False

    if not re.search(r"[A-Za-zА-Яа-яЁё]", definition):
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
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("￾", "")
    text = text.replace("\ufeff", "")
    text = text.replace("\u00ad", "")

    text = re.sub(
        r"([A-Za-zА-Яа-яЁё]{2,})\-\n([A-Za-zА-Яа-яЁё]{2,})",
        r"\1\2",
        text,
    )

    text = re.sub(
        r"([A-Za-zА-Яа-яЁё]{2,})(?:—|–)\n([A-Za-zА-Яа-яЁё]{2,})",
        r"\1\2",
        text,
    )

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text


def trim_quotes(value: str) -> str:
    return clean_line(value).strip(" \"'«»„“”")


def looks_like_gost_document(text: str) -> bool:
    lowered = text.lower().replace("ё", "е")
    return "гост р" in lowered or "национальный стандарт" in lowered


def find_gost_glossary_area(text: str) -> str | None:
    header_match = GOST_GLOSSARY_HEADER_RE.search(text)
    if not header_match:
        return None

    tail = text[header_match.end():]
    end_match = GOST_GLOSSARY_END_RE.search(tail)

    if end_match:
        area = tail[: end_match.start()]
    else:
        area = tail

    return area.strip() or None


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
    return line.startswith("примечание") or line.startswith("примечания")


def is_english_glossary_line(line: str) -> bool:
    line = clean_line(line)
    if not line:
        return False

    has_cyrillic = bool(re.search(r"[А-Яа-яЁё]", line))
    has_latin = bool(re.search(r"[A-Za-z]", line))

    if has_latin and not has_cyrillic:
        return True

    return False


def is_page_marker_line(line: str) -> bool:
    line = clean_line(line)
    if not line:
        return True

    if re.fullmatch(r"[IVXLCM]+", line):
        return True

    if re.fullmatch(r"\d+", line):
        return True

    return False


def cleanup_definition_block(definition_block: str) -> str:
    lines: list[str] = []

    for raw_line in definition_block.splitlines():
        line = clean_line(raw_line)
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

        lines.append(line)

    definition = " ".join(lines)
    definition = clean_line(definition)

    definition = re.sub(r"\s+\[\s*ГОСТ.*$", "", definition, flags=re.IGNORECASE)
    definition = re.sub(r"\s+ГОСТ\s+Р\s+.*$", "", definition, flags=re.IGNORECASE)

    return definition


def split_term_and_short_form(term_part: str) -> tuple[str, str | None]:
    term_part = clean_line(term_part)

    if ";" not in term_part:
        return term_part, None

    left, right = term_part.split(";", 1)
    left = clean_line(left)
    right = clean_line(right)

    if right and len(right) <= 30:
        return left, right

    return term_part, None


def parse_structured_article_body(body: str) -> dict | None:
    body = body.strip()
    colon_pos = body.find(":")

    if colon_pos == -1 or colon_pos > 250:
        return None

    term_part = clean_line(body[:colon_pos])
    definition_block = body[colon_pos + 1:]

    term_part = re.sub(r"^\d+(?:\.\d+)*\s*", "", term_part).strip()
    term, short_form = split_term_and_short_form(term_part)

    definition = cleanup_definition_block(definition_block)

    if not looks_like_term(term):
        return None

    if not looks_like_definition(definition):
        return None

    entry = {
        "term": term,
        "definition": definition,
        "source_line": f"{term_part}: {definition}"[:500],
    }

    if short_form:
        entry["short_form"] = short_form

    return entry


def extract_structured_gost_entries(glossary_area: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in ARTICLE_BLOCK_RE.finditer(glossary_area):
        body = match.group("body")
        entry = parse_structured_article_body(body)
        if not entry:
            continue

        key = (
            normalize_for_lookup(entry["term"]),
            normalize_for_lookup(entry["definition"]),
        )

        if key in seen:
            continue

        seen.add(key)
        results.append(entry)

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
            tail = prepared[pos + len(prep):].strip()
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

    return definition


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
        left_context = left_context[cut + 1:]

    return trim_quotes(left_context)


def extract_dash_entries(text: str) -> list[dict]:
    results: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for match in SEPARATOR_RE.finditer(text):
        sep_start = match.start()
        sep_end = match.end()

        left_context = text[max(0, sep_start - 250):sep_start]
        right_context = text[sep_end:sep_end + 800]

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
                "term": term,
                "definition": definition,
                "source_line": f"{left_clause} — {definition}"[:500],
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
                "term": abbr,
                "definition": full_term,
                "source_line": f"{full_term} (далее — {abbr})"[:500],
            }
        )

    return results


def deduplicate_entries(entries: list[dict]) -> list[dict]:
    unique_entries: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for entry in entries:
        key = (
            normalize_for_lookup(entry["term"]),
            normalize_for_lookup(entry["definition"]),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_entries.append(entry)

    return unique_entries


def extract_glossary_entries(text: str):
    cleaned_text = cleanup_text_for_extraction(text)

    glossary_area = find_gost_glossary_area(cleaned_text)
    if glossary_area:
        structured_entries = extract_structured_gost_entries(glossary_area)
        return deduplicate_entries(structured_entries)

    candidate_area = extract_general_candidate_area(cleaned_text)

    abbreviation_entries = extract_abbreviation_entries(candidate_area)

    if looks_like_gost_document(cleaned_text):
        return deduplicate_entries(abbreviation_entries)

    dash_entries = extract_dash_entries(candidate_area)
    return deduplicate_entries(abbreviation_entries + dash_entries)