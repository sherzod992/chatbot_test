"""
FastAPI 애플리케이션: SSE/WebSocket 엔드포인트

이 파일의 역할:
- FastAPI 애플리케이션의 진입점 및 라우팅 정의
- REST API, SSE(Server-Sent Events), WebSocket 엔드포인트 제공
- CORS 설정 및 미들웨어 구성
- 애플리케이션 생명주기 관리 (startup/shutdown)

왜 필요한가:
- 프론트엔드와 백엔드를 연결하는 API 서버
- 다양한 통신 방식 지원 (일반 HTTP, 스트리밍, 실시간)
- REST API: 일반적인 요청-응답 패턴
- SSE: 서버에서 클라이언트로 스트리밍 데이터 전송
- WebSocket: 양방향 실시간 통신

주요 엔드포인트:
- GET /: 루트 엔드포인트 (API 정보)
- GET /health: 헬스 체크
- POST /chat: 일반 채팅 요청 (JSON 응답)
- POST /chat/stream: 스트리밍 채팅 요청 (SSE)
- WebSocket /ws: WebSocket 기반 실시간 채팅

통신 방식 비교:
1. POST /chat: 
   - 단순한 요청-응답
   - 전체 응답을 한 번에 반환
   - 구현이 간단하고 안정적

2. POST /chat/stream:
   - Server-Sent Events (SSE)
   - 응답을 청크 단위로 스트리밍
   - 사용자 경험 향상 (타이핑 효과)

3. WebSocket /ws:
   - 양방향 실시간 통신
   - 지속적인 연결 유지
   - 낮은 지연시간

구성 요소:
- RAGChain: 챗봇 로직 처리
- CORS: 프론트엔드 접근 허용
- 이벤트 핸들러: 애플리케이션 시작/종료 시 리소스 관리
"""
