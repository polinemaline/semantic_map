from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


MODEL_NAME = os.getenv(
    "TERM_NLI_MODEL_NAME",
    "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli",
)

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
    chars = []
    for ch in value:
        if ch.isalnum() or ch.isspace():
            chars.append(ch)
        else:
            chars.append(" ")
    return " ".join("".join(chars).split())


def _first_word(value: str) -> str:
    parts = _normalize(value).split()
    return parts[0] if parts else ""


def _word_count(value: str) -> int:
    return len(_normalize(value).split())


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
def _load_bundle():
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception:
        return None

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        model.eval()
        return {
            "torch": torch,
            "tokenizer": tokenizer,
            "model": model,
        }
    except Exception:
        return None


def _get_label_indexes(model) -> tuple[int, int, int]:
    entailment_idx = None
    neutral_idx = None
    contradiction_idx = None

    label2id = getattr(model.config, "label2id", {}) or {}
    for label_name, idx in label2id.items():
        name = str(label_name).lower()
        if "entail" in name:
            entailment_idx = int(idx)
        elif "neutral" in name:
            neutral_idx = int(idx)
        elif "contrad" in name:
            contradiction_idx = int(idx)

    if entailment_idx is None or neutral_idx is None or contradiction_idx is None:
        # fallback под порядок из model card
        entailment_idx = 0
        neutral_idx = 1
        contradiction_idx = 2

    return entailment_idx, neutral_idx, contradiction_idx


def _score_once(
    premise: str,
    hypothesis: str,
) -> dict[str, float]:
    bundle = _load_bundle()
    if bundle is None:
        return {
            "entailment": 0.0,
            "neutral": 0.0,
            "contradiction": 0.0,
        }

    torch = bundle["torch"]
    tokenizer = bundle["tokenizer"]
    model = bundle["model"]

    inputs = tokenizer(
        premise,
        hypothesis,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits[0], dim=-1).cpu().tolist()

    entailment_idx, neutral_idx, contradiction_idx = _get_label_indexes(model)

    return {
        "entailment": float(probs[entailment_idx]),
        "neutral": float(probs[neutral_idx]),
        "contradiction": float(probs[contradiction_idx]),
    }


def should_keep_plain_candidate(
    term: str,
    definition: str,
    source_line: str,
) -> tuple[bool, dict[str, Any]]:
    """
    Используется только для случаев вида:
    term — definition
    где definition не начинается с "это".
    """

    term = _clean(term)
    definition = _clean(definition)
    source_line = _clean(source_line)

    if _is_hard_negative(term, definition):
        return False, {"reason": "hard_negative_rule"}

    bundle = _load_bundle()
    if bundle is None:
        return True, {"reason": "fallback_rules_only"}

    premise = source_line or f"{term} — {definition}"

    hypothesis_a = f'Фрагмент содержит определение термина "{term}".'
    hypothesis_b = f'"{definition}" является определением термина "{term}".'

    score_a = _score_once(premise, hypothesis_a)
    score_b = _score_once(premise, hypothesis_b)

    entailment = (score_a["entailment"] + score_b["entailment"]) / 2.0
    contradiction = (score_a["contradiction"] + score_b["contradiction"]) / 2.0
    neutral = (score_a["neutral"] + score_b["neutral"]) / 2.0

    threshold = 0.43

    first_word = _first_word(definition)
    if first_word in PREPOSITION_STARTS:
        threshold = 0.68

    short_term = _word_count(term) <= 2
    short_definition = _word_count(definition) <= 8
    if short_term and short_definition:
        threshold -= 0.05

    keep = entailment >= threshold or (
        entailment > contradiction and entailment >= threshold - 0.04
    )

    return keep, {
        "reason": "nli_filter",
        "entailment": round(entailment, 4),
        "neutral": round(neutral, 4),
        "contradiction": round(contradiction, 4),
        "threshold": round(threshold, 4),
    }