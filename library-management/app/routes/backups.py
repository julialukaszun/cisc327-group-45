from pathlib import Path

from flask import Blueprint, current_app, jsonify

from app import store
from app.models.backup import Backup

backups_bp = Blueprint("backups", __name__, url_prefix="/backup")


@backups_bp.route("", methods=["GET"])
def get_backup():
    file_path = Path(current_app.config["BACKUP_FILE"])
    if not file_path.is_file():
        return jsonify({"error": "Backup not found"}), 404
    return jsonify(Backup.load(file_path).to_dict())


@backups_bp.route("", methods=["POST"])
def refresh_backup():
    backup = Backup.from_store(store.books.values(), store.members.values())
    backup.save(current_app.config["BACKUP_FILE"])
    return jsonify(backup.to_dict()), 200
