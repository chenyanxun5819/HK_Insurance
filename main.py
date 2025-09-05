from flask import Flask, request, jsonify
from takepdf import run_crawler, query_name
import os

app = Flask(__name__)

BUCKET_NAME = os.environ.get("BUCKET_NAME", "hk-ia-db")
DB_FILE = os.environ.get("DB_FILE", "aml_profiles.db")

@app.route("/update", methods=["GET", "POST"])
def update():
    try:
        run_crawler(bucket_name=BUCKET_NAME, db_file=DB_FILE)
        return "更新完成", 200
    except Exception as e:
        return str(e), 500

@app.route("/query", methods=["GET"])
def query():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "缺少 name 參數"}), 400
    try:
        found, matches = query_name(bucket_name=BUCKET_NAME, db_file=DB_FILE, name=name)
        return jsonify({"found": found, "matches": matches}), 200
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
