"""
Advanced RAG 체인: 검색 + LLM + 외부 API

이 파일의 역할:
- RAG(Retrieval-Augmented Generation) 파이프라인 구축
- 벡터 검색으로 관련 컨텍스트를 가져와 LLM에 전달
- 외부 API(날씨, 칼로리, 알레르기 정보)를 통합하여 응답 생성
- 대화 기록 관리 및 컨텍스트 유지

왜 필요한가:
- 단순 LLM 응답보다 정확하고 최신 정보를 제공
- 벡터 검색으로 관련 음식점 메뉴 정보를 찾아 답변
- 외부 API를 활용하여 실시간 정보(날씨, 칼로리 등) 제공
- 대화 맥락을 유지하여 연속적인 대화 가능

주요 기능:
- RAGChain 클래스: RAG 파이프라인 관리
- invoke(): 질문을 받아 검색 + LLM + 외부 API를 통해 응답 생성
- stream(): 스트리밍 방식으로 응답 생성
- _check_external_api_needed(): 질문에 따라 필요한 외부 API 호출 결정

작동 흐름:
1. 사용자 질문 수신
2. 벡터 저장소에서 유사한 메뉴 정보 검색 (Retrieval)
3. 질문 내용 분석하여 필요한 외부 API 호출 (날씨/칼로리/알레르기)
4. 검색된 컨텍스트 + 외부 API 데이터 + 대화 기록을 LLM에 전달
5. LLM이 종합적인 답변 생성 (Generation)

통합 요소:
- VectorStore: 관련 메뉴 정보 검색
- ChatGoogleGenerativeAI: Gemini LLM으로 답변 생성
- WeatherClient: 날씨 정보 제공
- CalorieClient: 칼로리 정보 제공
- KADXClient: 알레르기 정보 제공
- ConversationBufferMemory: 대화 기록 관리
"""
