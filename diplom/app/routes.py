import csv
import io
import json
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    Response,
)
from werkzeug.utils import secure_filename

from .repository import (
    build_semantic_map_data,
    delete_document,
    delete_term,
    get_document,
    get_document_occurrences,
    get_document_report_groups,
    get_report_export_rows,
    get_stats,
    get_term,
    get_term_occurrences,
    get_term_report_groups,
    list_conflicting_terms,
    list_documents,
    list_terms,
    save_document_with_entries,
)
from .services.document_parser import extract_text
from .services.term_extractor import extract_glossary_entries


bp = Blueprint("main", __name__)


def is_allowed_file(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/")
def index():
    stats = get_stats()
    recent_documents = list_documents(limit=5)
    return render_template(
        "index.html",
        stats=stats,
        recent_documents=recent_documents,
    )


@bp.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        title = request.form.get("title", "").strip()

        if not uploaded_file or not uploaded_file.filename:
            flash("Сначала выберите PDF или DOCX файл.", "error")
            return redirect(url_for("main.upload"))

        if not is_allowed_file(uploaded_file.filename):
            flash("Поддерживаются только PDF и DOCX.", "error")
            return redirect(url_for("main.upload"))

        original_filename = uploaded_file.filename
        safe_name = secure_filename(original_filename)
        extension = Path(safe_name).suffix.lower()
        saved_filename = f"{uuid4().hex}{extension}"
        save_path = Path(current_app.config["UPLOAD_FOLDER"]) / saved_filename

        try:
            uploaded_file.save(save_path)

            text = extract_text(save_path)
            if not text.strip():
                raise ValueError(
                    "Не удалось извлечь текст. Для MVP нужны текстовые PDF или DOCX."
                )

            entries = extract_glossary_entries(text)

            document_id = save_document_with_entries(
                title=title or Path(original_filename).stem,
                original_filename=original_filename,
                saved_filename=saved_filename,
                file_type=extension.lstrip("."),
                full_text=text,
                entries=entries,
            )

            flash(
                f"Документ загружен. Найдено терминов: {len(entries)}.",
                "success",
            )
            return redirect(url_for("main.document_detail", document_id=document_id))

        except Exception as exc:
            if save_path.exists():
                save_path.unlink()
            flash(f"Ошибка обработки файла: {exc}", "error")
            return redirect(url_for("main.upload"))

    return render_template("upload.html")


@bp.route("/documents")
def documents():
    documents_list = list_documents()
    return render_template("documents.html", documents=documents_list)


@bp.route("/documents/<int:document_id>")
def document_detail(document_id: int):
    document = get_document(document_id)
    if not document:
        abort(404)

    occurrences = get_document_occurrences(document_id)

    return render_template(
        "document_detail.html",
        document=document,
        occurrences=occurrences,
    )


@bp.route("/documents/<int:document_id>/delete", methods=["POST"])
def document_delete(document_id: int):
    deleted = delete_document(document_id)
    if not deleted:
        abort(404)

    file_path = Path(current_app.config["UPLOAD_FOLDER"]) / deleted["saved_filename"]
    if file_path.exists():
        file_path.unlink()

    flash(f"Документ «{deleted['title']}» удалён.", "success")
    return redirect(url_for("main.documents"))


@bp.route("/terms")
def terms():
    query = request.args.get("q", "").strip()
    terms_list = list_terms(query)
    return render_template(
        "terms.html",
        terms=terms_list,
        query=query,
    )


@bp.route("/terms/<int:term_id>")
def term_detail(term_id: int):
    term = get_term(term_id)
    if not term:
        abort(404)

    occurrences = get_term_occurrences(term_id)

    grouped_definitions: list[dict] = []
    index_by_normalized: dict[str, dict] = {}

    for row in occurrences:
        normalized_key = row["definition_normalized"]

        if normalized_key not in index_by_normalized:
            group = {
                "definition_text": row["definition_text"],
                "documents": [],
                "source_lines": [],
            }
            index_by_normalized[normalized_key] = group
            grouped_definitions.append(group)

        index_by_normalized[normalized_key]["documents"].append(
            {
                "id": row["document_id"],
                "title": row["document_title"],
                "filename": row["original_filename"],
            }
        )
        index_by_normalized[normalized_key]["source_lines"].append(row["source_line"])

    has_conflict = len(grouped_definitions) > 1

    return render_template(
        "term_detail.html",
        term=term,
        grouped_definitions=grouped_definitions,
        has_conflict=has_conflict,
    )


@bp.route("/terms/<int:term_id>/delete", methods=["POST"])
def term_delete(term_id: int):
    deleted = delete_term(term_id)
    if not deleted:
        abort(404)

    flash(f"Термин «{deleted['name']}» удалён.", "success")
    return redirect(url_for("main.terms"))


@bp.route("/compare")
def compare():
    conflicts = list_conflicting_terms()
    return render_template("compare.html", conflicts=conflicts)


@bp.route("/report")
def report():
    stats = get_stats()
    conflicts = list_conflicting_terms()
    term_groups = get_term_report_groups()
    document_groups = get_document_report_groups()

    return render_template(
        "report.html",
        stats=stats,
        conflicts=conflicts,
        term_groups=term_groups,
        document_groups=document_groups,
    )


@bp.route("/report.csv")
def download_report():
    rows = get_report_export_rows()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        [
            "ID термина",
            "Термин",
            "Определение",
            "ID документов",
            "Документы",
            "Количество документов",
            "Количество разных определений у термина",
            "Есть конфликт определений",
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row["term_id"],
                row["term_name"],
                row["definition_text"],
                row["document_ids"],
                row["document_titles"],
                row["documents_count"],
                row["definitions_count"],
                row["has_conflict"],
            ]
        )

    csv_content = output.getvalue()
    output.close()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=term_report.csv"
        },
    )


@bp.route("/semantic-map")
def semantic_map():
    selected_term_id = request.args.get("term_id", type=int)
    selected_document_id = request.args.get("document_id", type=int)

    if selected_term_id:
        selected_document_id = None

    if selected_term_id is not None:
        term = get_term(selected_term_id)
        if not term:
            abort(404)

    if selected_document_id is not None:
        document = get_document(selected_document_id)
        if not document:
            abort(404)

    map_data = build_semantic_map_data(
        term_id=selected_term_id,
        document_id=selected_document_id,
    )

    return render_template(
        "semantic_map.html",
        documents=list_documents(),
        terms=list_terms(),
        selected_term_id=selected_term_id,
        selected_document_id=selected_document_id,
        map_summary=map_data["summary"],
        nodes_json=json.dumps(map_data["nodes"], ensure_ascii=False),
        edges_json=json.dumps(map_data["edges"], ensure_ascii=False),
    )