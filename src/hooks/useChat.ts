/**
 * useChat.ts
 * 
 * 채팅 기능을 위한 React Custom Hook
 * 
 * 이 파일의 역할:
 * - 채팅 관련 비즈니스 로직을 컴포넌트에서 분리
 * - SSE(Server-Sent Events) 연결을 관리하여 실시간 스트리밍 응답 처리
 * - REST API 호출을 통해 일반 채팅 요청 처리
 * - 채팅 메시지 상태 관리 (메시지 목록, 로딩 상태, 에러 상태)
 * - 메시지 전송, 수신, 스트리밍 처리 로직 캡슐화
 * 
 * 왜 필요한가:
 * - 컴포넌트의 가독성 향상 (UI 로직과 비즈니스 로직 분리)
 * - 채팅 기능을 여러 컴포넌트에서 재사용 가능
 * - 복잡한 상태 관리 로직을 중앙에서 관리
 * - 테스트 작성이 용이 (훅을 독립적으로 테스트 가능)
 * - SSE 연결 관리, 에러 핸들링 등 복잡한 로직을 추상화
 * 
 * 주요 기능:
 * - useChat(): 채팅 훅의 메인 함수
 * - sendMessage(): 메시지 전송 함수 (일반 API 또는 SSE 스트리밍)
 * - messages: 현재 대화 메시지 목록 상태
 * - isLoading: 로딩 상태 관리
 * - error: 에러 상태 관리
 * - conversationId: 대화 세션 ID 관리
 * - SSE 연결 관리 및 이벤트 리스너 처리
 * - 메시지 스트리밍 수신 및 상태 업데이트
 * 
 * 통신 방식:
 * 1. 일반 REST API: POST /chat
 *    - 전체 응답을 한 번에 받음
 *    - 간단한 요청에 사용
 * 
 * 2. SSE 스트리밍: POST /chat/stream
 *    - 서버에서 실시간으로 청크 단위 응답 수신
 *    - 타이핑 효과를 위한 스트리밍 방식
 *    - EventSource API 사용
 * 
 * 사용 예시:
 * - const { messages, sendMessage, isLoading, error } = useChat();
 * - ChatWindow 컴포넌트에서 훅을 호출하여 채팅 기능 사용
 */
