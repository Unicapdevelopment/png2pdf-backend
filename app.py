from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile, os
import json
from pdf2image import convert_from_path
import firebase_admin
from firebase_admin import credentials, storage

app = Flask(__name__)
CORS(app)

# ─── Firebase Admin init ──────────────────────────────────────────
service_account_info = json.loads(os.environ['SERVICE_ACCOUNT_KEY'])
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    "storageBucket": "universe-capital-crm.appspot.com"
})
bucket = storage.bucket()

# ─── POST /convert ────────────────────────────────────────────────
@app.route("/convert", methods=["POST"])
def convert_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_file = request.files["file"]
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_file.save(tmp_pdf.name)

    try:
        images = convert_from_path(tmp_pdf.name)  # converts ALL pages
    except Exception as e:
        return jsonify({"error": "Conversion failed", "details": str(e)}), 500

    urls = []
    for idx, img in enumerate(images, start=1):
        tmp_png = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img.save(tmp_png, "PNG")

        blob = bucket.blob(f"converted/{os.path.basename(tmp_pdf.name)}_page_{idx}.png")
        blob.upload_from_filename(tmp_png)
        blob.make_public()
        urls.append(blob.public_url)

        os.remove(tmp_png)

    os.remove(tmp_pdf.name)
    return jsonify({"urls": urls})

# ─── Run server ───────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
