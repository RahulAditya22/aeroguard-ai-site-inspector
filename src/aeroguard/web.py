"""Flask web application for the AeroGuard inspection pipeline."""

import csv
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .config import Settings, settings
from .pipeline import InspectionPipeline

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def create_app(
    app_settings: Settings | None = None,
    pipeline: InspectionPipeline | None = None,
) -> Flask:
    cfg = app_settings or settings
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["MAX_CONTENT_LENGTH"] = cfg.max_image_mb * 1024 * 1024
    inspection_pipeline = pipeline

    def get_pipeline() -> InspectionPipeline:
        nonlocal inspection_pipeline
        if inspection_pipeline is None:
            cfg.validate()
            inspection_pipeline = InspectionPipeline(cfg)
        return inspection_pipeline

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "aeroguard"})

    @app.get("/api/incidents")
    def incidents():
        path = cfg.data_dir / "incidents.csv"
        if not path.exists():
            return jsonify([])
        with path.open("r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        rows.reverse()
        return jsonify(rows)

    @app.post("/api/inspect")
    def inspect():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return jsonify({"error": "Please select an image to inspect."}), 400

        suffix = Path(uploaded.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify({"error": "Unsupported image type. Use JPG, PNG, or WEBP."}), 400

        filename = secure_filename(uploaded.filename) or "inspection_image"
        with tempfile.TemporaryDirectory(prefix="aeroguard_") as temp_dir:
            image_path = Path(temp_dir) / filename
            uploaded.save(image_path)
            try:
                record = get_pipeline().inspect_one(image_path)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            except (FileNotFoundError, OSError) as exc:
                return jsonify({"error": str(exc)}), 400
            except Exception:
                app.logger.exception("Inspection failed")
                return jsonify({"error": "Inspection failed. Check the server logs for details."}), 502

        return jsonify(record.model_dump(mode="json")), 200

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": f"Image exceeds the {cfg.max_image_mb} MB upload limit."}), 413

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
