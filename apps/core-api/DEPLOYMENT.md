# Core API 배포 가이드

## OCR 기능 배포

이 애플리케이션은 Tesseract OCR을 사용하여 포트폴리오 이미지를 분석합니다.

### Docker 배포 (권장)

Dockerfile에 Tesseract가 포함되어 있어 별도 설치 없이 배포 가능합니다.

```bash
# Docker 이미지 빌드
docker build -t core-api:latest .

# Docker 컨테이너 실행
docker run -d \
  -p 8080:8080 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=your-db-name \
  -e DB_USER=your-db-user \
  -e DB_PASSWORD=your-db-password \
  -e REDIS_HOST=your-redis-host \
  -e REDIS_PORT=6379 \
  -e JWT_SECRET=your-jwt-secret \
  core-api:latest
```

### 환경 변수

필수 환경 변수:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=portrally
DB_USER=postgres
DB_PASSWORD=your-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# JWT
JWT_SECRET=your-secret-key

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Cookies
COOKIE_DOMAIN=
COOKIE_SECURE=false

# OCR (Tesseract) - Docker에서는 Dockerfile에 기본값 설정되어 있음
# TESSERACT_DATA_PATH=/usr/share/tessdata  # Alpine Linux 기본 경로
# JNA_LIBRARY_PATH=/usr/lib  # Alpine Linux 기본 경로
```

**중요:**
- 로컬 개발(macOS): `.env.local`에서 Homebrew 경로 사용
- Docker: Dockerfile에 Alpine Linux 경로가 자동 설정됨

### Kubernetes 배포

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: core-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: core-api
  template:
    metadata:
      labels:
        app: core-api
    spec:
      containers:
      - name: core-api
        image: core-api:latest
        ports:
        - containerPort: 8080
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        # ... 기타 환경 변수
```

### 로컬 개발 환경

로컬에서 개발 시 Tesseract 설치 및 환경 변수 설정 필요:

**macOS:**
```bash
# Tesseract 설치
brew install tesseract tesseract-lang

# .env.local에 추가
TESSERACT_DATA_PATH=/opt/homebrew/share/tessdata
JNA_LIBRARY_PATH=/opt/homebrew/lib
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-kor tesseract-ocr-eng
```

**CentOS/RHEL:**
```bash
sudo yum install tesseract tesseract-langpack-kor tesseract-langpack-eng
```

### 트러블슈팅

#### Tesseract 라이브러리를 찾을 수 없는 경우

**로컬 개발:**
- Tesseract가 설치되었는지 확인: `which tesseract`
- 재설치: `brew reinstall tesseract tesseract-lang`

**Docker:**
- Dockerfile에 Tesseract 설치가 포함되어 있는지 확인
- 이미지 재빌드: `docker build --no-cache -t core-api:latest .`

#### OCR 성능 최적화

- 이미지 크기: 2000x2000px 이하 권장
- 지원 포맷: PNG, JPEG, WEBP
- 한글 인식률 향상: 고해상도 이미지 사용

### 향후 개선 사항

배포 환경에 따라 다음 OCR 솔루션으로 전환 가능:

1. **AWS Textract** - AWS 환경
2. **Google Cloud Vision** - GCP 환경
3. **Azure Computer Vision** - Azure 환경

관리형 서비스 사용 시 서버 부하 감소 및 인식률 향상 기대.
