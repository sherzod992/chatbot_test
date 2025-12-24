# 챗봇 연동 흐름 설명서

이 문서는 사용자가 질문을 입력했을 때부터 챗봇이 응답을 반환할 때까지의 전체 처리 흐름을 단계별로 설명합니다.

## 📋 목차

1. [전체 흐름 개요](#전체-흐름-개요)
2. [단계별 상세 설명](#단계별-상세-설명)
3. [주요 컴포넌트 설명](#주요-컴포넌트-설명)
4. [데이터 흐름도](#데이터-흐름도)

---

## 전체 흐름 개요

```
사용자 질문 입력
    ↓
FastAPI 엔드포인트 (/chat 또는 /chat/stream)
    ↓
RAGChain.invoke() 또는 RAGChain.stream()
    ↓
VectorStore.similarity_search() - 벡터 검색
    ↓
검색 결과를 컨텍스트로 포맷팅
    ↓
LLM (ChatOpenAI) 호출 - 답변 생성
    ↓
응답 반환 (JSON 또는 SSE 스트리밍)
```

---

## 단계별 상세 설명

### 1단계: 사용자 질문 입력 및 API 요청

**위치**: 프론트엔드 → `backend/app/main.py`

사용자가 프론트엔드에서 질문을 입력하면, HTTP POST 요청이 백엔드로 전송됩니다.

**요청 형식**:
```json
{
  "message": "전주에서 저렴한 한식 추천해줘",
  "conversation_id": "optional-conversation-id",
  "history": [
    {"role": "user", "content": "이전 질문"},
    {"role": "assistant", "content": "이전 답변"}
  ]
}
```

**엔드포인트**:
- 일반 응답: `POST /chat`
- 스트리밍 응답: `POST /chat/stream`

---

### 2단계: FastAPI 엔드포인트에서 요청 수신

**파일**: `backend/app/main.py`  
**함수**: `chat()` 또는 `chat_stream()`

#### 2-1. 일반 채팅 엔드포인트 (`/chat`)

```python
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
```

**처리 과정**:
1. `ChatRequest` 모델로 요청 데이터 검증
2. `get_rag_chain()` 호출하여 RAGChain 인스턴스 가져오기
3. 대화 기록(history)을 딕셔너리 형식으로 변환
4. `rag_chain.invoke()` 호출하여 답변 생성

**코드 위치**: `backend/app/main.py:54-119`

#### 2-2. 스트리밍 채팅 엔드포인트 (`/chat/stream`)

```python
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
```

**처리 과정**:
1. `get_rag_chain()` 호출
2. 내부 `generate()` 함수에서 `rag_chain.stream()` 호출
3. SSE(Server-Sent Events) 형식으로 청크 단위 응답 전송

**코드 위치**: `backend/app/main.py:122-203`

---

### 3단계: RAGChain 초기화 및 인스턴스 가져오기

**파일**: `backend/app/rag_chain.py`  
**함수**: `get_rag_chain()`

**처리 과정**:
1. 싱글톤 패턴으로 RAGChain 인스턴스 확인
2. 인스턴스가 없으면 새로 생성
3. `RAGChain.__init__()` 실행:
   - `ChatOpenAI` LLM 초기화 (GPT-3.5-turbo)
   - `get_vectorstore()` 호출하여 벡터스토어 연결
   - 대화 기록 저장소 초기화
   - 프롬프트 템플릿 설정

**코드 위치**: `backend/app/rag_chain.py:363-368`

**초기화 코드**:
```python
def __init__(self):
    self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    self.vectorstore = get_vectorstore()  # 벡터스토어 연결
    self.memories: Dict[str, List[BaseMessage]] = {}
    self.prompt_template = ChatPromptTemplate.from_messages([...])
```

**코드 위치**: `backend/app/rag_chain.py:21-61`

---

### 4단계: 사용자 선호도 추출

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain._extract_preferences()`

**처리 과정**:
질문에서 다음 정보를 추출합니다:
- **카테고리**: 한식, 중식, 일식, 양식, 분식, 치킨, 피자, 카페
- **가격대**: 저렴, 싼, 비싼, 고급, 프리미엄
- **최대 가격**: "1만원 이하", "15000원" 등 숫자 추출
- **최대 칼로리**: "500칼로리 이하" 등 숫자 추출
- **키워드**: 질문에서 중요한 단어 추출

**예시**:
- 입력: "전주에서 저렴한 한식 1만원 이하로 추천해줘"
- 출력: `{"category": "한식", "price_range": "low", "max_price": 10000, ...}`

**코드 위치**: `backend/app/rag_chain.py:73-128`

---

### 5단계: 벡터스토어에서 유사 메뉴 검색

**파일**: `backend/app/rag_chain.py` → `backend/app/vectorstore.py`  
**함수**: `RAGChain.invoke()` → `VectorStore.similarity_search()` 또는 `VectorStore.search_with_filters()`

#### 5-1. 검색 방식 결정

**조건부 분기**:
- 선호도(카테고리, 가격, 칼로리)가 있으면 → `search_with_filters()` 사용
- 선호도가 없으면 → `similarity_search()` 사용

**코드 위치**: `backend/app/rag_chain.py:202-213`

#### 5-2. 벡터 검색 실행

**파일**: `backend/app/vectorstore.py`  
**함수**: `VectorStore.similarity_search()` 또는 `VectorStore.search_with_filters()`

**처리 과정**:
1. **질문을 벡터로 변환**: 
   - `_embed_text()` 호출
   - 한국어 임베딩 모델(`jhgan/ko-sroberta-multitask`) 사용
   - 질문 텍스트를 숫자 벡터로 변환

2. **ChromaDB에서 유사도 검색**:
   - 변환된 벡터와 저장된 메뉴 벡터 간 코사인 유사도 계산
   - 상위 k개(기본 8개) 결과 반환
   - 각 결과에 유사도 점수(score) 포함

3. **필터링 적용** (필터 검색인 경우):
   - 카테고리 필터
   - 가격 범위 필터
   - 칼로리 범위 필터

**반환 형식**:
```python
[
    {
        "content": "메뉴 상세 설명 텍스트",
        "metadata": {
            "restaurant_name": "음식점명",
            "menu_name": "메뉴명",
            "price": 10000,
            "calories": 500,
            "address": "주소",
            "category": "한식"
        },
        "score": 0.85  # 유사도 점수 (낮을수록 유사)
    },
    ...
]
```

**코드 위치**: 
- `backend/app/vectorstore.py:131-162` (일반 검색)
- `backend/app/vectorstore.py:164-230` (필터 검색)

---

### 6단계: 검색 결과를 컨텍스트로 포맷팅

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain._format_context()`

**처리 과정**:
검색된 메뉴 정보를 LLM이 이해하기 쉬운 텍스트 형식으로 변환합니다.

**포맷팅 내용**:
- 각 메뉴의 음식점명, 메뉴명, 가격, 칼로리, 주소, 카테고리
- 상세 설명 텍스트
- 유사도 점수
- 추천 가이드 문구

**출력 예시**:
```
=== 추천 가능한 메뉴 목록 ===

[추천 옵션 1]
음식점: 전주 한정식
메뉴: 비빔밥
카테고리: 한식
가격: 8000원
칼로리: 450kcal
주소: 전주시 완산구...
상세: 전통 비빔밥으로...
유사도 점수: 0.8234

[추천 옵션 2]
...
```

**코드 위치**: `backend/app/rag_chain.py:130-176`

---

### 7단계: 대화 기록 준비

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain._get_memory()`

**처리 과정**:
1. `conversation_id`로 대화 기록 가져오기 (없으면 "default" 사용)
2. 요청에 포함된 `history`를 메모리에 추가
3. 최근 6개 메시지만 사용 (컨텍스트 길이 제한)

**코드 위치**: `backend/app/rag_chain.py:63-71, 218-230`

---

### 8단계: LLM 프롬프트 생성

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain.invoke()` 내부

**처리 과정**:
프롬프트 템플릿에 다음 정보를 채워넣습니다:
- **시스템 프롬프트**: 챗봇의 역할과 추천 규칙
- **컨텍스트**: 검색된 메뉴 정보 (6단계에서 포맷팅된 결과)
- **이전 대화**: 최근 6개 메시지
- **사용자 질문**: 현재 질문

**프롬프트 구조**:
```
시스템 메시지:
- 챗봇 역할 설명
- 추천 규칙
- 검색된 메뉴 정보: {context}
- 이전 대화: {history}

이전 대화 기록:
- 사용자: 이전 질문
- 챗봇: 이전 답변

현재 질문: {question}
```

**코드 위치**: `backend/app/rag_chain.py:232-238`

---

### 9단계: LLM 호출 및 답변 생성

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain.invoke()` → `self.llm.invoke()`

**처리 과정**:
1. **LLM 호출**:
   - `ChatOpenAI` 모델 사용 (GPT-3.5-turbo)
   - 생성된 프롬프트를 LLM에 전달
   - LLM이 컨텍스트를 바탕으로 답변 생성

2. **답변 추출**:
   - LLM 응답에서 텍스트 내용 추출
   - `response.content` 속성 사용

**코드 위치**: `backend/app/rag_chain.py:240-243`

**스트리밍 방식** (9-2):
- `rag_chain.stream()` 사용 시
- `self.llm.astream()` 호출
- 답변을 청크 단위로 점진적 생성
- 각 청크를 즉시 전송

**코드 위치**: `backend/app/rag_chain.py:287-356`

---

### 10단계: 대화 기록 저장

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain.invoke()` 내부

**처리 과정**:
1. 사용자 질문을 `HumanMessage`로 메모리에 추가
2. 생성된 답변을 `AIMessage`로 메모리에 추가
3. 다음 대화에서 컨텍스트로 활용

**코드 위치**: `backend/app/rag_chain.py:245-247`

---

### 11단계: 응답 데이터 구성

**파일**: `backend/app/rag_chain.py` → `backend/app/main.py`

#### 11-1. RAGChain에서 반환 데이터 구성

**파일**: `backend/app/rag_chain.py`  
**함수**: `RAGChain.invoke()`

**반환 형식**:
```python
{
    "response": "생성된 답변 텍스트",
    "sources": [
        {
            "content": "검색된 문서 내용",
            "metadata": {...},
            "score": 0.85
        },
        ...
    ],
    "recommended_menus": [
        {
            "restaurant_name": "음식점명",
            "menu_name": "메뉴명",
            "price": "10000",
            "calories": "500",
            "address": "주소",
            "category": "한식",
            "score": 0.85
        },
        ...
    ]
}
```

**코드 위치**: `backend/app/rag_chain.py:249-278`

#### 11-2. FastAPI에서 최종 응답 생성

**파일**: `backend/app/main.py`  
**함수**: `chat()`

**처리 과정**:
1. RAGChain 결과를 Pydantic 모델로 변환
2. `ChatResponse` 객체 생성:
   - `response`: 답변 텍스트
   - `sources`: 검색 소스 목록
   - `recommended_menus`: 추천 메뉴 목록
   - `conversation_id`: 대화 ID
   - `timestamp`: 응답 시간

3. JSON 형식으로 직렬화하여 반환

**코드 위치**: `backend/app/main.py:81-115`

---

### 12단계: 클라이언트로 응답 전송

**파일**: `backend/app/main.py`

#### 12-1. 일반 응답 (`/chat`)

- 전체 응답을 한 번에 JSON으로 반환
- 프론트엔드가 응답을 받아 화면에 표시

#### 12-2. 스트리밍 응답 (`/chat/stream`)

- SSE(Server-Sent Events) 형식으로 청크 단위 전송
- 각 청크는 `StreamChunk` 모델로 구성:
  ```json
  {
    "content": "답변의 일부",
    "done": false,
    "sources": null
  }
  ```
- 마지막 청크에서 `done: true`와 `sources` 정보 포함

**코드 위치**: `backend/app/main.py:142-199`

---

## 주요 컴포넌트 설명

### 1. RAGChain 클래스

**파일**: `backend/app/rag_chain.py`

**역할**:
- RAG(Retrieval-Augmented Generation) 파이프라인 관리
- 벡터 검색과 LLM을 연결하는 핵심 컴포넌트

**주요 메서드**:
- `invoke()`: 일반 답변 생성
- `stream()`: 스트리밍 답변 생성
- `_extract_preferences()`: 사용자 선호도 추출
- `_format_context()`: 검색 결과 포맷팅
- `_get_memory()`: 대화 기록 관리

### 2. VectorStore 클래스

**파일**: `backend/app/vectorstore.py`

**역할**:
- ChromaDB 벡터 데이터베이스 관리
- 텍스트를 벡터로 변환 (임베딩)
- 유사도 기반 검색 수행

**주요 메서드**:
- `similarity_search()`: 일반 유사도 검색
- `search_with_filters()`: 필터링 검색
- `add_documents()`: 문서 추가
- `_embed_text()`: 텍스트 벡터화

### 3. FastAPI 엔드포인트

**파일**: `backend/app/main.py`

**역할**:
- HTTP 요청/응답 처리
- 클라이언트와 RAGChain 사이의 인터페이스

**주요 엔드포인트**:
- `POST /chat`: 일반 채팅
- `POST /chat/stream`: 스트리밍 채팅
- `GET /health`: 헬스 체크

### 4. 데이터 모델

**파일**: `backend/app/models.py`

**주요 모델**:
- `ChatRequest`: 요청 데이터
- `ChatResponse`: 응답 데이터
- `Source`: 검색 소스 정보
- `RecommendedMenu`: 추천 메뉴 정보
- `StreamChunk`: 스트리밍 청크

---

## 데이터 흐름도

```
┌─────────────────┐
│   사용자 질문    │
│  "저렴한 한식"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI 엔드   │
│  /chat 또는     │
│  /chat/stream   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  get_rag_chain()│
│  RAGChain 인스턴스│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ _extract_       │
│ preferences()   │
│ {category, price}│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ vectorstore.    │
│ similarity_     │
│ search()        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ChromaDB        │
│ 벡터 검색       │
│ 유사 메뉴 8개   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ _format_        │
│ context()       │
│ 컨텍스트 문자열 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 프롬프트 생성   │
│ (시스템+컨텍스트│
│ +이전대화+질문) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ChatOpenAI      │
│ LLM 호출        │
│ 답변 생성       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 응답 구성       │
│ {response,      │
│  sources,       │
│  menus}         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JSON/SSE 응답   │
│ 클라이언트 전송 │
└─────────────────┘
```

---

## 핵심 연동 포인트

### 1. 싱글톤 패턴

- `get_rag_chain()`: RAGChain 인스턴스를 한 번만 생성하여 재사용
- `get_vectorstore()`: VectorStore 인스턴스를 한 번만 생성하여 재사용
- 메모리 효율성과 성능 최적화

### 2. 벡터 검색 연동

- 질문 → 벡터 변환 → 유사도 검색 → 관련 메뉴 반환
- 필터링 기능으로 정확한 검색 결과 제공

### 3. 컨텍스트 주입

- 검색된 메뉴 정보를 LLM 프롬프트에 포함
- LLM이 실제 데이터를 바탕으로 답변 생성

### 4. 대화 기록 관리

- `conversation_id`로 대화 구분
- 최근 6개 메시지만 컨텍스트로 사용 (토큰 제한 고려)

---

## 에러 처리

각 단계에서 예외가 발생하면:
1. 로깅: `logger.error()`로 오류 기록
2. 사용자 친화적 메시지 반환
3. HTTP 500 에러 또는 에러 메시지 포함 응답

**에러 처리 위치**:
- `backend/app/rag_chain.py:280-285`
- `backend/app/main.py:117-119, 201-203`

---

## 성능 최적화 포인트

1. **벡터 검색**: k=8로 상위 8개만 검색 (필요시 조정)
2. **대화 기록**: 최근 6개만 사용하여 토큰 수 제한
3. **싱글톤 패턴**: 인스턴스 재사용으로 초기화 시간 절약
4. **스트리밍**: 긴 답변의 경우 스트리밍으로 사용자 경험 개선

---

## 참고 파일

- `backend/app/main.py`: FastAPI 엔드포인트
- `backend/app/rag_chain.py`: RAG 파이프라인
- `backend/app/vectorstore.py`: 벡터 검색
- `backend/app/models.py`: 데이터 모델
- `backend/app/utils.py`: 유틸리티 함수

---

**작성일**: 2024년  
**버전**: 1.0.0

