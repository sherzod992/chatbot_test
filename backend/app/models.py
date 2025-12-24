"""
Pydantic 모델: 요청/응답 스키마

이 파일의 역할:
- API 요청과 응답의 데이터 구조를 정의하는 Pydantic 모델
- 데이터 검증과 직렬화/역직렬화 처리
- 타입 안정성 보장 및 자동 문서화 (OpenAPI/Swagger)

왜 필요한가:
- FastAPI는 Pydantic 모델을 기반으로 자동으로 API 문서를 생성
- 요청 데이터의 유효성 검사를 자동으로 수행
- 타입 힌팅을 통해 코드의 가독성과 안정성 향상
- API 스펙을 코드로 명확하게 정의하여 프론트엔드와의 협업 용이

주요 모델:
- ChatMessage: 개별 채팅 메시지 (role, content)
- ChatRequest: 채팅 API 요청 (message, conversation_id, history)
- ChatResponse: 채팅 API 응답 (response, sources, conversation_id, timestamp)
- StreamChunk: 스트리밍 응답 청크 (content, done, sources)
- RestaurantInfo: 음식점 정보 (id, name, address, menu)

사용 예시:
- FastAPI 엔드포인트에서 request: ChatRequest로 타입 검증
- 응답 모델로 response_model=ChatResponse 사용
"""
