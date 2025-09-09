#!/bin/bash
cd /home/weschen/HK_insurance/hk-ia-function
source venv/bin/activate
export FIRESTORE_EMULATOR_HOST="127.0.0.1:8081"
export FIREBASE_AUTH_EMULATOR_HOST="127.0.0.1:9099"

echo "檢查環境變數..."
echo "FIRESTORE_EMULATOR_HOST: $FIRESTORE_EMULATOR_HOST"
echo "FIREBASE_AUTH_EMULATOR_HOST: $FIREBASE_AUTH_EMULATOR_HOST"

echo "嘗試啟動 Flask..."
python main_firebase.py
