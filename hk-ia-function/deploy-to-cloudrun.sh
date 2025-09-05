# 部署到 Google Cloud Run 指令

PROJECT_ID="hk-insurance-crawler"

# 1. 建立 Docker 映像檔
docker build -t hk-insurance-aml .

# 2. 標記映像檔
docker tag hk-insurance-aml gcr.io/$PROJECT_ID/hk-insurance-aml

# 3. 推送到 Google Container Registry
docker push gcr.io/$PROJECT_ID/hk-insurance-aml

# 4. 部署到 Cloud Run
gcloud run deploy hk-insurance-aml \
    --image gcr.io/$PROJECT_ID/hk-insurance-aml \
    --platform managed \
    --region asia-east1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1

# 5. 設置環境變數 (如果需要)
gcloud run services update hk-insurance-aml \
    --set-env-vars PORT=8080 \
    --region asia-east1
