from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from .db import get_db


profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


def default_display_name(email: str | None, username: str | None = None) -> str:
    email_value = (email or "").strip()
    username_value = (username or "").strip()

    if "@" in email_value:
        return email_value.split("@", 1)[0]

    if username_value:
        return username_value

    if email_value:
        return email_value

    return "Пользователь"


def get_profile_user_by_id(user_id: int | None) -> dict | None:
    if not user_id:
        return None

    db = get_db()
    row = db.execute(
        """
        SELECT
            id,
            email,
            username,
            display_name,
            password_hash,
            avatar_filename,
            created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if not row:
        return None

    display_name = (row["display_name"] or "").strip()
    if not display_name:
        display_name = default_display_name(row["email"], row["username"])

    avatar_filename = row["avatar_filename"]
    avatar_url = None
    if avatar_filename:
        avatar_url = url_for("profile.avatar_file", filename=avatar_filename)

    return {
        "id": int(row["id"]),
        "email": row["email"],
        "username": row["username"],
        "display_name": display_name,
        "password_hash": row["password_hash"],
        "avatar_filename": avatar_filename,
        "avatar_url": avatar_url,
        "created_at": row["created_at"],
    }


@profile_bp.app_context_processor
def inject_profile_user():
    user_id = session.get("user_id")
    return {
        "profile_user": get_profile_user_by_id(user_id),
    }


def is_allowed_avatar(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in current_app.config["ALLOWED_AVATAR_EXTENSIONS"]


def delete_old_avatar(filename: str | None) -> None:
    if not filename:
        return

    avatar_path = Path(current_app.config["AVATAR_FOLDER"]) / filename
    if avatar_path.exists():
        avatar_path.unlink()


@profile_bp.route("/avatar/<path:filename>")
def avatar_file(filename: str):
    safe_name = secure_filename(Path(filename).name)
    if not safe_name:
        abort(404)

    avatar_path = Path(current_app.config["AVATAR_FOLDER"]) / safe_name
    if not avatar_path.exists():
        abort(404)

    return send_file(avatar_path, as_attachment=False, max_age=0)


@profile_bp.route("/update", methods=["POST"])
def update_profile():
    if g.current_user is None:
        return redirect(url_for("main.login"))

    user_id = int(session["user_id"])
    profile_user = get_profile_user_by_id(user_id)
    if not profile_user:
        abort(404)

    display_name = request.form.get("display_name", "").strip()
    if not display_name:
        display_name = default_display_name(
            profile_user["email"],
            profile_user["username"],
        )

    avatar_file = request.files.get("avatar")
    avatar_filename = profile_user["avatar_filename"]

    if avatar_file and avatar_file.filename:
        if not is_allowed_avatar(avatar_file.filename):
            flash("Фото должно быть в формате PNG, JPG, JPEG или WEBP.", "error")
            return redirect(request.referrer or url_for("main.index"))

        original_name = secure_filename(avatar_file.filename)
        extension = Path(original_name).suffix.lower()
        new_avatar_filename = f"user_{user_id}_{uuid4().hex}{extension}"
        save_path = Path(current_app.config["AVATAR_FOLDER"]) / new_avatar_filename

        avatar_file.save(save_path)

        delete_old_avatar(avatar_filename)
        avatar_filename = new_avatar_filename

    db = get_db()
    db.execute(
        """
        UPDATE users
        SET display_name = ?, avatar_filename = ?
        WHERE id = ?
        """,
        (display_name, avatar_filename, user_id),
    )
    db.commit()

    flash("Профиль обновлен.", "success")
    return redirect(request.referrer or url_for("main.index"))


@profile_bp.route("/password", methods=["POST"])
def change_password():
    if g.current_user is None:
        return redirect(url_for("main.login"))

    user_id = int(session["user_id"])
    profile_user = get_profile_user_by_id(user_id)
    if not profile_user:
        abort(404)

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    new_password_repeat = request.form.get("new_password_repeat", "")

    if not current_password or not new_password or not new_password_repeat:
        flash("Заполните все поля для смены пароля.", "error")
        return redirect(request.referrer or url_for("main.index"))

    if not check_password_hash(profile_user["password_hash"], current_password):
        flash("Текущий пароль введен неверно.", "error")
        return redirect(request.referrer or url_for("main.index"))

    if len(new_password) < 6:
        flash("Новый пароль должен быть не короче 6 символов.", "error")
        return redirect(request.referrer or url_for("main.index"))

    if check_password_hash(profile_user["password_hash"], new_password):
        flash("Новый пароль не должен совпадать с текущим.", "error")
        return redirect(request.referrer or url_for("main.index"))

    if new_password != new_password_repeat:
        flash("Новый пароль и повтор пароля не совпадают.", "error")
        return redirect(request.referrer or url_for("main.index"))

    db = get_db()
    db.execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
        """,
        (generate_password_hash(new_password), user_id),
    )
    db.commit()

    flash("Пароль изменен.", "success")
    return redirect(request.referrer or url_for("main.index"))