# 전주 음식점 챗봇 백엔드

RAG(Retrieval-Augmented Generation) 기반 음식점 메뉴 검색 챗봇의 백엔드 서버입니다.

## 📋 목차

1. [사전 준비 사항](#사전-준비-사항)
2. [설치 방법](#설치-방법)
3. [벡터 DB 초기화](#벡터-db-초기화)
4. [서버 실행 방법](#서버-실행-방법)
5. [API 엔드포인트](#api-엔드포인트)
6. [테스트](#테스트)
7. [문제 해결](#문제-해결)

---

## 사전 준비 사항

### 필수 요구사항

- **Python 3.11.x** 또는 **3.12.x** (권장)
- **가상환경** (이미 `venv` 디렉토리가 존재함)
- **OpenAI API 키** (`.env` 파일에 설정)

### 환경 변수 설정

`backend/.env` 파일에 OpenAI API 키를 설정해야 합니다:

```env
OPENAI_API_KEY=your-api-key-here
```

> 📝 `.env` 파일이 없다면 생성하고 위 내용을 추가하세요.

---

## 설치 방법

### 1. 가상환경 활성화

#### Windows PowerShell
```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

#### Windows CMD
```cmd
cd backend
venv\Scripts\activate.bat
```

#### Mac/Linux
```bash
cd backend
source venv/bin/activate
```

### 2. 패키지 설치 (필요시)

가상환경이 활성화된 상태에서:

```bash
pip install -r requirements.txt
```

> 💡 이미 패키지가 설치되어 있다면 이 단계는 건너뛰어도 됩니다.

---

## 벡터 DB 초기화

**중요**: 서버를 처음 실행하거나 CSV 데이터가 변경된 경우 벡터 DB를 초기화해야 합니다.

### 실행 방법

```bash
# 가상환경 활성화 상태에서
python scripts/init_vectorstore.py
```

### 실행 과정

1. **CSV 파일 읽기**: `data/restaurant_menu_data.csv`에서 데이터 로드
2. **문서 변환**: 각 메뉴를 검색 가능한 텍스트 문서로 변환
3. **벡터화**: 텍스트를 벡터(숫자 배열)로 변환 (임베딩 모델 사용)
4. **저장**: ChromaDB에 벡터와 메타데이터 저장
5. **테스트 검색**: 정상 작동 확인

### 예상 출력

```
벡터 저장소 초기화 시작 (CSV 파일에서)
CSV 파일 로딩: backend\data\restaurant_menu_data.csv
총 X개 음식점 데이터 로드 완료
477개 문서를 벡터 저장소에 추가 중...
진행 중: 50/477
진행 중: 100/477
...
벡터 저장소 초기화 완료: 477개 문서 저장
테스트 검색 수행: '전주비빔밥'
테스트 검색 결과: 3개 결과
```

### 저장 위치

벡터 DB는 다음 위치에 저장됩니다:
```
backend/chroma_db/
├── chroma.sqlite3          # 메인 데이터베이스
└── [UUID]/                 # 벡터 인덱스 파일들
```

> ⚠️ **주의**: 벡터 DB를 초기화하면 기존 데이터가 삭제되고 새로 생성됩니다.

---

## 서버 실행 방법

### 방법 1: uvicorn 직접 실행 (권장)

```bash
# 가상환경 활성화 상태에서
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**옵션 설명**:
- `--reload`: 코드 변경 시 자동 재시작 (개발 시 편리)
- `--host 0.0.0.0`: 모든 네트워크 인터페이스에서 접근 허용
- `--port 8000`: 포트 번호 (변경 가능)

### 방법 2: run_test.py 사용

서버 실행과 테스트를 함께 수행:

```bash
python run_test.py
```

### 서버 실행 확인

서버가 정상적으로 실행되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 브라우저에서 확인

- **API 문서**: http://localhost:8000/docs
- **헬스 체크**: http://localhost:8000/health
- **루트 엔드포인트**: http://localhost:8000/

정상 동작 시 다음 JSON 응답을 확인할 수 있습니다:
```json
{
  "message": "전주 음식점 챗봇 API",
  "version": "1.0.0",
  "endpoints": {
    "chat": "/chat",
    "chat_stream": "/chat/stream",
    "health": "/health",
    "docs": "/docs"
  }
}
```

---

## API 엔드포인트

### 1. POST /chat

일반 채팅 요청 (전체 응답을 한 번에 반환)

**요청 예시**:
```json
{
  "message": "비빔밥 가격이 얼마인가요?",
  "conversation_id": "optional-conversation-id",
  "history": []
}
```

**응답 예시**:
```json
{
  "response": "비빔밥의 가격은 8000원입니다...",
  "sources": [...],
  "recommended_menus": [...],
  "conversation_id": "...",
  "timestamp": "2024-01-01T00:00:00"
}
```

### 2. POST /chat/stream

스트리밍 채팅 요청 (SSE - Server-Sent Events)

실시간으로 답변이 스트리밍되는 방식입니다.

### 3. GET /health

서버 상태 확인

**응답**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00"
}
```

### 4. GET /docs

Swagger UI API 문서 (자동 생성)

---

## 테스트

### API 테스트

서버가 실행된 상태에서:

```bash
# 가상환경 활성화 상태에서
python test_api.py
```

### OpenAI API 키 테스트

```bash
python test_openai_key.py
```

---

## 문제 해결

### 1. 포트가 이미 사용 중인 경우

**에러 메시지**:
```
Error: [Errno 48] Address already in use
```

**해결 방법**:
- 다른 포트 사용: `--port 8080`
- 기존 프로세스 종료

### 2. 벡터 DB가 없는 경우

**에러 메시지**:
```
검색 결과가 없습니다
```

**해결 방법**:
벡터 DB 초기화를 실행하세요:
```bash
python scripts/init_vectorstore.py
```

### 3. OpenAI API 키 오류

**에러 메시지**:
```
401 - Invalid API Key
```

**해결 방법**:
1. `.env` 파일 확인
2. API 키가 올바른지 확인
3. OpenAI Platform에서 API 키 권한 확인 (Chat completions Read 권한 필요)

### 4. 크레딧 부족 오류

**에러 메시지**:
```
429 - Insufficient quota
```

**해결 방법**:
OpenAI Platform에서 크레딧을 충전하세요.

### 5. 가상환경 활성화 오류 (PowerShell)

**에러 메시지**:
```
실행 정책 때문에 스크립트를 실행할 수 없습니다
```

**해결 방법**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 프로젝트 구조

```
backend/
├── app/                    # 애플리케이션 코드
│   ├── main.py            # FastAPI 메인 애플리케이션
│   ├── rag_chain.py       # RAG 체인 로직
│   ├── vectorstore.py     # 벡터 저장소 관리
│   ├── models.py          # 데이터 모델
│   └── utils.py           # 유틸리티 함수
├── scripts/                # 스크립트
│   └── init_vectorstore.py # 벡터 DB 초기화 스크립트
├── data/                   # 데이터 파일
│   └── restaurant_menu_data.csv
├── chroma_db/              # 벡터 DB 저장 위치
├── venv/                   # 가상환경
├── .env                    # 환경 변수 (생성 필요)
├── requirements.txt        # Python 패키지 목록
└── README.md              # 이 파일
```

---

## 추가 문서

- [벡터 DB 설정 가이드](VECTORSTORE_SETUP.md)
- [챗봇 통합 흐름](CHATBOT_INTEGRATION_FLOW.md)
- [프론트엔드 구현 가이드](FRONTEND_IMPLEMENTATION_GUIDE.md)

---

## 빠른 시작 요약

```bash
# 1. 가상환경 활성화
cd backend
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# 2. 벡터 DB 초기화 (최초 1회 또는 데이터 변경 시)
python scripts/init_vectorstore.py

# 3. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. 브라우저에서 확인
# http://localhost:8000/docs
```

---

## 라이선스

이 프로젝트는 교육 목적으로 만들어졌습니다.

