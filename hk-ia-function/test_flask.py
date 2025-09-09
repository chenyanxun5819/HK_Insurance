#!/usr/bin/env python3
"""
最簡單的 Flask 測試
"""
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    print("🚀 啟動簡單 Flask 測試")
    app.run(host="0.0.0.0", port=8000, debug=False)
