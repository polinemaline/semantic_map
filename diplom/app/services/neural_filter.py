from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

MODEL_NAME = os.getenv(
    "TERM_NN_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

POSITIVE_DEFINITION_PROTOTYPES = [
    "это определенный набор элементов данных для описания ресурса",
    "это определенный структурированный набор спецификаций",
    "это совокупность правил, методов и средств",
    "это объект, используемый для хранения и обработки данных",
    "набор элементов данных для описания объекта",
    "именованный набор связанных элементов данных",
    "совокупность взаимосвязанных программных и технических средств",
    "электронный образовательный ресурс",
    "информационная система, предназначенная для обработки данных",
]

NEGATIVE_DEFINITION_PROTOTYPES = [
    "на официальном сайте федерального агентства",
    "в ежемесячном информационном указателе",
    "в информационной системе общего пользования",
    "в сети интернет",
    "по состоянию на апрель 2008 года",
    "до 2008 07 01",
    "при прямом указании на это в действующем законодательстве",
]

POSITIVE_PAIR_PROTOTYPES = [
    "Запись метаданных ЭОР — это определенный набор элементов данных для описания ресурса",
    "Прикладной профиль — это определенный структурированный набор спецификаций",
    "Метаданные — именованный набор связанных элементов данных",
    "Информационная система — совокупность программных и технических средств",
]

NEGATIVE_PAIR_PROTOTYPES = [
    "текст изменений и поправок — в ежемесячном информационном указателе",
    "ссылочных стандартов в информационной системе общего пользования — на официальном сайте федерального агентства",
    "дата введения — 2008 07 01",
    "уведомление и тексты — в информационной системе общего пользования",
]

HARD_NEGATIVE_DEFINITION_STARTS = (
    "на официальном сайте",
    "в ежемесячном",
    "в информационной системе общего пользования",
    "в сети интернет",
    "по состоянию на",
)

PREPOSITION_STARTS = {
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


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip()


def _normalize(value: str) -> str:
    value = _clean(value).lower().replace("ё", "е")
    normalized = []
    for ch in value:
        if ch.isalnum() or ch.isspace():
            normalized.append(ch)
        else:
            normalized.append(" ")
    return " ".join("".join(normalized).split())


def _word_count(value: str) -> int:
    return len([part for part in _normalize(value).split() if part])


def _first_word(value: str) -> str:
    parts = _normalize(value).split()
    return parts[0] if parts else ""


def _is_hard_negative(term: str, definition: str) -> bool:
    definition_norm = _normalize(definition)
    term_words = _word_count(term)

    if definition_norm.startswith(HARD_NEGATIVE_DEFINITION_STARTS) and term_words >= 4:
        return True

    first_word = _first_word(definition)
    if first_word in PREPOSITION_STARTS and term_words >= 6:
        return True

    return False


@lru_cache(maxsize=1)
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    try:
        return SentenceTransformer(MODEL_NAME)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _get_prototype_embeddings():
    model = _get_model()
    if model is None:
        return None

    positive_def = model.encode(
        POSITIVE_DEFINITION_PROTOTYPES,
        normalize_embeddings=True,
    )
    negative_def = model.encode(
        NEGATIVE_DEFINITION_PROTOTYPES,
        normalize_embeddings=True,
    )
    positive_pair = model.encode(
        POSITIVE_PAIR_PROTOTYPES,
        normalize_embeddings=True,
    )
    negative_pair = model.encode(
        NEGATIVE_PAIR_PROTOTYPES,
        normalize_embeddings=True,
    )

    return {
        "positive_def": positive_def,
        "negative_def": negative_def,
        "positive_pair": positive_pair,
        "negative_pair": negative_pair,
    }


def _max_similarity(vector, matrix) -> float:
    best = -1.0
    for row in matrix:
        score = float(vector @ row)
        if score > best:
            best = score
    return best


def should_keep_candidate(
    term: str,
    definition: str,
    *,
    explicit_eto: bool = False,
) -> tuple[bool, dict[str, Any]]:
    """
    Возвращает:
    - keep: оставить пару или нет
    - debug: служебная информация
    """

    term = _clean(term)
    definition = _clean(definition)

    if explicit_eto:
        return True, {"reason": "explicit_eto"}

    if _is_hard_negative(term, definition):
        return False, {"reason": "hard_negative_rule"}

    model = _get_model()
    prototypes = _get_prototype_embeddings()

    if model is None or prototypes is None:
        return True, {"reason": "fallback_rules_only"}

    pair_text = f"{term} — {definition}"

    definition_embedding = model.encode([definition], normalize_embeddings=True)[0]
    pair_embedding = model.encode([pair_text], normalize_embeddings=True)[0]

    positive_def_score = _max_similarity(definition_embedding, prototypes["positive_def"])
    negative_def_score = _max_similarity(definition_embedding, prototypes["negative_def"])
    positive_pair_score = _max_similarity(pair_embedding, prototypes["positive_pair"])
    negative_pair_score = _max_similarity(pair_embedding, prototypes["negative_pair"])

    final_score = (
        (positive_def_score * 0.55 + positive_pair_score * 0.45)
        - (negative_def_score * 0.55 + negative_pair_score * 0.45)
    )

    first_word = _first_word(definition)

    threshold = -0.02
    if first_word in PREPOSITION_STARTS:
        threshold = 0.08

    keep = final_score >= threshold

    return keep, {
        "reason": "neural_filter",
        "score": round(final_score, 4),
        "threshold": threshold,
        "positive_def_score": round(positive_def_score, 4),
        "negative_def_score": round(negative_def_score, 4),
        "positive_pair_score": round(positive_pair_score, 4),
        "negative_pair_score": round(negative_pair_score, 4),
    }