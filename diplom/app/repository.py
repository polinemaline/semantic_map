import hashlib
import re
from datetime import datetime
from typing import Any

from .db import get_db
from .services.term_extractor import normalize_for_lookup


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_or_create_term(name: str) -> int:
    db = get_db()
    normalized_name = normalize_for_lookup(name)
    row = db.execute(
        "SELECT id FROM terms WHERE normalized_name = ?",
        (normalized_name,),
    ).fetchone()
    if row:
        return row["id"]

    cursor = db.execute(
        """
        INSERT INTO terms (name, normalized_name, created_at)
        VALUES (?, ?, ?)
        """,
        (name.strip(), normalized_name, now_str()),
    )
    return int(cursor.lastrowid)


def get_or_create_definition(text: str) -> int:
    db = get_db()
    normalized_text = normalize_for_lookup(text)
    row = db.execute(
        "SELECT id FROM definitions WHERE normalized_text = ?",
        (normalized_text,),
    ).fetchone()
    if row:
        return row["id"]

    cursor = db.execute(
        """
        INSERT INTO definitions (text, normalized_text, created_at)
        VALUES (?, ?, ?)
        """,
        (text.strip(), normalized_text, now_str()),
    )
    return int(cursor.lastrowid)


def save_document_with_entries(
    *,
    title: str,
    original_filename: str,
    saved_filename: str,
    file_type: str,
    full_text: str,
    entries: list[dict[str, Any]],
) -> int:
    db = get_db()
    created_at = now_str()
    cursor = db.execute(
        """
        INSERT INTO documents (
            title, original_filename, saved_filename, file_type,
            full_text, extracted_pairs_count, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            original_filename,
            saved_filename,
            file_type,
            full_text,
            len(entries),
            created_at,
        ),
    )
    document_id = int(cursor.lastrowid)

    for entry in entries:
        term_id = get_or_create_term(entry["term"])
        definition_id = get_or_create_definition(entry["definition"])
        db.execute(
            """
            INSERT INTO term_occurrences (
                document_id, term_id, definition_id, source_line, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                document_id,
                term_id,
                definition_id,
                entry.get("source_line", "")[:500],
                created_at,
            ),
        )

    db.commit()
    return document_id


def cleanup_orphan_records() -> None:
    db = get_db()
    db.execute(
        """
        DELETE FROM definitions
        WHERE id NOT IN (
            SELECT DISTINCT definition_id FROM term_occurrences
        )
        """
    )
    db.execute(
        """
        DELETE FROM terms
        WHERE id NOT IN (
            SELECT DISTINCT term_id FROM term_occurrences
        )
        """
    )
    db.commit()


def list_documents(limit: int | None = None):
    db = get_db()
    query = """
        SELECT
            d.id,
            d.title,
            d.original_filename,
            d.file_type,
            d.extracted_pairs_count,
            d.created_at,
            COUNT(o.id) AS occurrences_count,
            COUNT(DISTINCT o.term_id) AS distinct_terms_count
        FROM documents d
        LEFT JOIN term_occurrences o ON o.document_id = d.id
        GROUP BY d.id
        ORDER BY d.id DESC
    """
    params: tuple[Any, ...] = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    return db.execute(query, params).fetchall()


def get_document(document_id: int):
    db = get_db()
    return db.execute(
        """
        SELECT
            id, title, original_filename, saved_filename, file_type,
            full_text, extracted_pairs_count, created_at
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    ).fetchone()


def get_document_occurrences(document_id: int):
    db = get_db()
    return db.execute(
        """
        SELECT
            o.id,
            t.id AS term_id,
            t.name AS term_name,
            df.id AS definition_id,
            df.text AS definition_text,
            df.normalized_text AS definition_normalized,
            o.source_line
        FROM term_occurrences o
        JOIN terms t ON t.id = o.term_id
        JOIN definitions df ON df.id = o.definition_id
        WHERE o.document_id = ?
        ORDER BY t.name COLLATE NOCASE, o.id
        """,
        (document_id,),
    ).fetchall()


def delete_document(document_id: int) -> dict[str, Any] | None:
    db = get_db()
    document = db.execute(
        """
        SELECT id, title, saved_filename
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    ).fetchone()
    if not document:
        return None

    db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    db.commit()
    cleanup_orphan_records()
    return {
        "id": int(document["id"]),
        "title": document["title"],
        "saved_filename": document["saved_filename"],
    }


def list_terms(search_text: str = ""):
    db = get_db()
    normalized_search = f"%{normalize_for_lookup(search_text)}%"
    return db.execute(
        """
        SELECT
            t.id,
            t.name,
            t.normalized_name,
            COUNT(DISTINCT o.document_id) AS documents_count,
            COUNT(DISTINCT df.normalized_text) AS definitions_count
        FROM terms t
        LEFT JOIN term_occurrences o ON o.term_id = t.id
        LEFT JOIN definitions df ON df.id = o.definition_id
        WHERE t.normalized_name LIKE ?
        GROUP BY t.id, t.name, t.normalized_name
        ORDER BY t.name COLLATE NOCASE
        """,
        (normalized_search,),
    ).fetchall()


def get_term(term_id: int):
    db = get_db()
    return db.execute(
        """
        SELECT
            t.id,
            t.name,
            t.normalized_name,
            COUNT(DISTINCT o.document_id) AS documents_count,
            COUNT(DISTINCT df.normalized_text) AS definitions_count
        FROM terms t
        LEFT JOIN term_occurrences o ON o.term_id = t.id
        LEFT JOIN definitions df ON df.id = o.definition_id
        WHERE t.id = ?
        GROUP BY t.id, t.name, t.normalized_name
        """,
        (term_id,),
    ).fetchone()


def get_term_occurrences(term_id: int):
    db = get_db()
    return db.execute(
        """
        SELECT
            o.id,
            d.id AS document_id,
            d.title AS document_title,
            d.original_filename,
            df.text AS definition_text,
            df.normalized_text AS definition_normalized,
            o.source_line
        FROM term_occurrences o
        JOIN documents d ON d.id = o.document_id
        JOIN definitions df ON df.id = o.definition_id
        WHERE o.term_id = ?
        ORDER BY d.title COLLATE NOCASE, o.id
        """,
        (term_id,),
    ).fetchall()


def delete_term(term_id: int) -> dict[str, Any] | None:
    db = get_db()
    term = db.execute(
        """
        SELECT id, name
        FROM terms
        WHERE id = ?
        """,
        (term_id,),
    ).fetchone()
    if not term:
        return None

    db.execute("DELETE FROM term_occurrences WHERE term_id = ?", (term_id,))
    db.execute("DELETE FROM terms WHERE id = ?", (term_id,))
    db.commit()
    cleanup_orphan_records()
    return {
        "id": int(term["id"]),
        "name": term["name"],
    }


def list_conflicting_terms():
    db = get_db()
    return db.execute(
        """
        SELECT
            t.id,
            t.name,
            COUNT(DISTINCT o.document_id) AS documents_count,
            COUNT(DISTINCT df.normalized_text) AS unique_definitions_count
        FROM terms t
        JOIN term_occurrences o ON o.term_id = t.id
        JOIN definitions df ON df.id = o.definition_id
        GROUP BY t.id, t.name
        HAVING COUNT(DISTINCT df.normalized_text) > 1
        ORDER BY unique_definitions_count DESC, t.name COLLATE NOCASE
        """
    ).fetchall()


def get_stats() -> dict[str, int]:
    db = get_db()
    documents_count = db.execute(
        "SELECT COUNT(*) AS count FROM documents"
    ).fetchone()["count"]
    terms_count = db.execute(
        "SELECT COUNT(*) AS count FROM terms"
    ).fetchone()["count"]
    definitions_count = db.execute(
        "SELECT COUNT(*) AS count FROM definitions"
    ).fetchone()["count"]
    conflicts_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM (
            SELECT t.id
            FROM terms t
            JOIN term_occurrences o ON o.term_id = t.id
            JOIN definitions df ON df.id = o.definition_id
            GROUP BY t.id
            HAVING COUNT(DISTINCT df.normalized_text) > 1
        ) AS conflicts
        """
    ).fetchone()["count"]

    return {
        "documents_count": int(documents_count),
        "terms_count": int(terms_count),
        "definitions_count": int(definitions_count),
        "conflicts_count": int(conflicts_count),
    }


def _fetch_occurrence_rows(
    *,
    term_id: int | None = None,
    document_id: int | None = None,
):
    db = get_db()
    query = """
        SELECT
            o.id,
            d.id AS document_id,
            d.title AS document_title,
            d.original_filename,
            t.id AS term_id,
            t.name AS term_name,
            t.normalized_name AS term_normalized,
            df.id AS definition_id,
            df.text AS definition_text,
            df.normalized_text AS definition_normalized,
            o.source_line
        FROM term_occurrences o
        JOIN documents d ON d.id = o.document_id
        JOIN terms t ON t.id = o.term_id
        JOIN definitions df ON df.id = o.definition_id
        WHERE 1 = 1
    """
    params: list[Any] = []

    if term_id is not None:
        query += " AND t.id = ?"
        params.append(term_id)

    if document_id is not None:
        query += " AND d.id = ?"
        params.append(document_id)

    query += """
        ORDER BY d.title COLLATE NOCASE, t.name COLLATE NOCASE, o.id
    """
    return db.execute(query, tuple(params)).fetchall()


def get_term_report_groups():
    rows = _fetch_occurrence_rows()
    term_map: dict[int, dict[str, Any]] = {}

    for row in rows:
        t_id = int(row["term_id"])
        if t_id not in term_map:
            term_map[t_id] = {
                "term_id": t_id,
                "term_name": row["term_name"],
                "documents_count": 0,
                "definitions_count": 0,
                "has_conflict": False,
                "definitions": [],
                "_documents_seen": set(),
                "_definitions_map": {},
            }

        group = term_map[t_id]
        group["_documents_seen"].add(int(row["document_id"]))

        def_key = row["definition_normalized"]
        if def_key not in group["_definitions_map"]:
            group["_definitions_map"][def_key] = {
                "definition_text": row["definition_text"],
                "documents": [],
                "document_ids": [],
                "source_lines": [],
                "_document_seen": set(),
            }
            group["definitions"].append(group["_definitions_map"][def_key])

        def_group = group["_definitions_map"][def_key]
        doc_id = int(row["document_id"])
        if doc_id not in def_group["_document_seen"]:
            def_group["_document_seen"].add(doc_id)
            def_group["documents"].append(
                {
                    "id": doc_id,
                    "title": row["document_title"],
                    "filename": row["original_filename"],
                }
            )
            def_group["document_ids"].append(doc_id)

        source_line = row["source_line"]
        if source_line and source_line not in def_group["source_lines"]:
            def_group["source_lines"].append(source_line)

    result: list[dict[str, Any]] = []
    for group in term_map.values():
        group["documents_count"] = len(group["_documents_seen"])
        group["definitions_count"] = len(group["definitions"])
        group["has_conflict"] = group["definitions_count"] > 1

        for def_group in group["definitions"]:
            def_group["documents"].sort(key=lambda item: item["title"].lower())
            def_group["document_ids"].sort()
            def_group["documents_label"] = ", ".join(
                str(doc_id) for doc_id in def_group["document_ids"]
            )
            def_group.pop("_document_seen", None)

        group["definitions"].sort(
            key=lambda item: (
                len(item["documents"]) * -1,
                item["definition_text"].lower(),
            )
        )
        group.pop("_documents_seen", None)
        group.pop("_definitions_map", None)
        result.append(group)

    result.sort(key=lambda item: item["term_name"].lower())
    return result


def get_document_report_groups():
    rows = _fetch_occurrence_rows()
    doc_map: dict[int, dict[str, Any]] = {}

    for row in rows:
        d_id = int(row["document_id"])
        if d_id not in doc_map:
            doc_map[d_id] = {
                "document_id": d_id,
                "document_title": row["document_title"],
                "original_filename": row["original_filename"],
                "terms": [],
            }

        doc_map[d_id]["terms"].append(
            {
                "term_id": int(row["term_id"]),
                "term_name": row["term_name"],
                "definition_text": row["definition_text"],
            }
        )

    result = list(doc_map.values())
    result.sort(key=lambda item: item["document_title"].lower())
    for group in result:
        group["terms"].sort(key=lambda item: item["term_name"].lower())
    return result


def get_report_export_rows():
    rows: list[dict[str, Any]] = []
    for term_group in get_term_report_groups():
        for def_group in term_group["definitions"]:
            rows.append(
                {
                    "term_id": term_group["term_id"],
                    "term_name": term_group["term_name"],
                    "definition_text": def_group["definition_text"],
                    "document_ids": def_group["documents_label"],
                    "document_titles": ", ".join(
                        doc["title"] for doc in def_group["documents"]
                    ),
                    "documents_count": len(def_group["documents"]),
                    "definitions_count": term_group["definitions_count"],
                    "has_conflict": "Да" if term_group["has_conflict"] else "Нет",
                }
            )
    return rows


def _term_present_in_definition(term_name: str, definition_text: str) -> bool:
    norm_term = normalize_for_lookup(term_name)
    norm_definition = normalize_for_lookup(definition_text)
    if not norm_term or not norm_definition:
        return False

    pattern = (
        r"(?<![0-9A-Za-zА-Яа-яЁё_])"
        + re.escape(norm_term)
        + r"(?![0-9A-Za-zА-Яа-яЁё_])"
    )
    return re.search(pattern, norm_definition) is not None


def _get_term_stats_map(term_ids: list[int]) -> dict[int, dict[str, Any]]:
    unique_ids = sorted({int(term_id) for term_id in term_ids})
    if not unique_ids:
        return {}

    db = get_db()
    placeholders = ",".join("?" for _ in unique_ids)
    rows = db.execute(
        f"""
        SELECT
            t.id,
            t.name,
            COUNT(DISTINCT o.document_id) AS documents_count,
            COUNT(DISTINCT df.normalized_text) AS definitions_count
        FROM terms t
        LEFT JOIN term_occurrences o ON o.term_id = t.id
        LEFT JOIN definitions df ON df.id = o.definition_id
        WHERE t.id IN ({placeholders})
        GROUP BY t.id, t.name
        """,
        tuple(unique_ids),
    ).fetchall()

    return {
        int(row["id"]): {
            "id": int(row["id"]),
            "name": row["name"],
            "documents_count": int(row["documents_count"]),
            "definitions_count": int(row["definitions_count"]),
        }
        for row in rows
    }


def _term_node_color(term_stats: dict[str, Any], selected: bool = False) -> str:
    if int(term_stats.get("definitions_count", 0)) > 1:
        return "#dc2626"
    if selected:
        return "#d97706"
    if int(term_stats.get("documents_count", 0)) > 1:
        return "#16a34a"
    return "#2563eb"


def _empty_map_summary(mode: str = "empty") -> dict[str, Any]:
    return {
        "mode": mode,
        "title": "",
        "documents_count": 0,
        "terms_count": 0,
        "definitions_count": 0,
        "links_count": 0,
    }


def _definition_node_id(*parts: Any) -> str:
    raw = "::".join(str(part) for part in parts)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"definition-{digest}"


def build_semantic_map_data(
    *,
    term_id: int | None = None,
    document_id: int | None = None,
) -> dict[str, Any]:
    if term_id is None and document_id is None:
        return {
            "nodes": [],
            "edges": [],
            "summary": _empty_map_summary(),
        }

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_seen: set[str] = set()
    edge_seen: set[tuple[str, str, str]] = set()

    def add_node(
        node_id: str,
        label: str,
        node_type: str,
        color: str,
        **extra: Any,
    ) -> None:
        if node_id in node_seen:
            return
        node_seen.add(node_id)
        node = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "color": color,
        }
        node.update(extra)
        nodes.append(node)

    def add_edge(source: str, target: str, label: str, color: str) -> None:
        key = (source, target, label)
        if key in edge_seen:
            return
        edge_seen.add(key)
        edges.append(
            {
                "source": source,
                "target": target,
                "label": label,
                "color": color,
            }
        )

    if term_id is not None:
        selected_term = get_term(term_id)
        if not selected_term:
            return {
                "nodes": [],
                "edges": [],
                "summary": _empty_map_summary("term"),
            }

        occurrences = get_term_occurrences(term_id)
        term_stats_map = _get_term_stats_map([term_id])
        selected_term_stats = term_stats_map.get(
            term_id,
            {
                "documents_count": int(selected_term["documents_count"]),
                "definitions_count": int(selected_term["definitions_count"]),
            },
        )
        has_conflict = int(selected_term_stats["definitions_count"]) > 1
        term_color = _term_node_color(selected_term_stats, selected=True)
        main_term_node_id = f"term-{term_id}"

        add_node(
            main_term_node_id,
            selected_term["name"],
            "term",
            term_color,
            definitions_count=int(selected_term_stats["definitions_count"]),
            documents_count=int(selected_term_stats["documents_count"]),
            selected=True,
        )

        doc_ids: set[int] = set()
        definition_node_ids: dict[str, str] = {}
        definition_documents_map: dict[str, set[int]] = {}

        for occurrence in occurrences:
            doc_id = int(occurrence["document_id"])
            doc_ids.add(doc_id)
            document_node_id = f"document-{doc_id}"

            add_node(
                document_node_id,
                occurrence["document_title"],
                "document",
                "#1d4ed8",
                filename=occurrence["original_filename"],
            )
            add_edge(
                main_term_node_id,
                document_node_id,
                "упоминается в документе",
                "#94a3b8",
            )

            def_key = normalize_for_lookup(occurrence["definition_text"])
            if def_key not in definition_node_ids:
                definition_node_ids[def_key] = _definition_node_id(
                    "term-mode",
                    term_id,
                    def_key,
                )
                definition_documents_map[def_key] = set()

            definition_documents_map[def_key].add(doc_id)

            definition_node_id = definition_node_ids[def_key]
            add_node(
                definition_node_id,
                occurrence["definition_text"],
                "definition",
                "#7c3aed",
                term_id=term_id,
                definition_normalized=def_key,
            )
            add_edge(
                document_node_id,
                definition_node_id,
                "содержит определение",
                "#dc2626" if has_conflict else "#94a3b8",
            )

        for def_key, definition_node_id in definition_node_ids.items():
            for node in nodes:
                if node["id"] == definition_node_id:
                    node["document_ids"] = sorted(definition_documents_map.get(def_key, set()))
                    break

        summary = {
            "mode": "term",
            "title": selected_term["name"],
            "documents_count": len(doc_ids),
            "terms_count": 1,
            "definitions_count": len(definition_node_ids),
            "links_count": len(edges),
        }
        return {
            "nodes": nodes,
            "edges": edges,
            "summary": summary,
        }

    document = get_document(document_id)
    if not document:
        return {
            "nodes": [],
            "edges": [],
            "summary": _empty_map_summary("document"),
        }

    occurrences = get_document_occurrences(document_id)
    term_ids = sorted({int(row["term_id"]) for row in occurrences})
    term_stats_map = _get_term_stats_map(term_ids)

    document_node_id = f"document-{document_id}"
    add_node(document_node_id, document["title"], "document", "#1d4ed8")

    definition_node_ids: dict[str, str] = {}
    for occurrence in occurrences:
        t_id = int(occurrence["term_id"])
        term_stats = term_stats_map.get(
            t_id,
            {
                "documents_count": 1,
                "definitions_count": 1,
            },
        )
        term_node_id = f"term-{t_id}"
        add_node(
            term_node_id,
            occurrence["term_name"],
            "term",
            _term_node_color(term_stats, selected=False),
            definitions_count=int(term_stats["definitions_count"]),
            documents_count=int(term_stats["documents_count"]),
        )
        add_edge(document_node_id, term_node_id, "содержит термин", "#94a3b8")

        def_key = normalize_for_lookup(occurrence["definition_text"])
        if def_key not in definition_node_ids:
            definition_node_ids[def_key] = _definition_node_id(
                "document-mode",
                document_id,
                def_key,
            )

        definition_node_id = definition_node_ids[def_key]
        add_node(
            definition_node_id,
            occurrence["definition_text"],
            "definition",
            "#7c3aed",
        )
        add_edge(
            term_node_id,
            definition_node_id,
            "имеет определение",
            "#16a34a" if int(term_stats["definitions_count"]) <= 1 else "#dc2626",
        )

    for occurrence in occurrences:
        source_def_key = normalize_for_lookup(occurrence["definition_text"])
        source_definition_node_id = definition_node_ids[source_def_key]

        for other_row in occurrences:
            other_term_id = int(other_row["term_id"])
            if other_term_id == int(occurrence["term_id"]):
                continue

            if _term_present_in_definition(
                other_row["term_name"],
                occurrence["definition_text"],
            ):
                related_term_node_id = f"term-{other_term_id}"
                add_edge(
                    source_definition_node_id,
                    related_term_node_id,
                    "упоминает термин",
                    "#f59e0b",
                )

    summary = {
        "mode": "document",
        "title": document["title"],
        "documents_count": 1,
        "terms_count": len(term_ids),
        "definitions_count": len(definition_node_ids),
        "links_count": len(edges),
    }
    return {
        "nodes": nodes,
        "edges": edges,
        "summary": summary,
    }