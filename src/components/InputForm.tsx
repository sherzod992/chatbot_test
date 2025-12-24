/**
 * InputForm.tsx
 * 
 * 입력폼 및 전송 버튼 컴포넌트
 * 
 * 이 파일의 역할:
 * - 사용자가 채팅 메시지를 입력하고 전송하는 UI 컴포넌트
 * - 텍스트 입력 필드와 전송 버튼 제공
 * - 입력 검증 및 상태 관리
 * - 키보드 이벤트 처리 (Enter 키로 전송)
 * - 로딩 상태에 따른 UI 비활성화
 * 
 * 왜 필요한가:
 * - 채팅 입력 기능을 독립적인 컴포넌트로 분리
 * - 입력 로직을 재사용 가능하게 만듦
 * - 사용자 경험 향상 (Enter 키 지원, 입력 검증 등)
 * - 일관된 입력 UI 제공
 * - 로딩 상태 관리로 중복 전송 방지
 * 
 * 주요 기능:
 * - InputForm 컴포넌트: 입력 폼
 * - 텍스트 입력 필드 (textarea 또는 input)
 * - 전송 버튼
 * - Enter 키로 메시지 전송 (Shift+Enter는 줄바꿈)
 * - 입력값 검증 (빈 메시지 전송 방지)
 * - 로딩 중일 때 입력 필드 및 버튼 비활성화
 * - 전송 후 입력 필드 초기화
 * - 포커스 관리 (전송 후 입력 필드에 자동 포커스)
 * 
 * 상태 관리:
 * - inputValue: 입력 중인 텍스트 상태
 * - 로컬 상태로 관리하되, 전송 시 부모 컴포넌트에 전달
 * 
 * Props:
 * - onSend: (message: string) => void (메시지 전송 콜백)
 * - isLoading?: boolean (로딩 상태)
 * - disabled?: boolean (비활성화 상태)
 * - placeholder?: string (입력 필드 placeholder)
 * 
 * 키보드 이벤트:
 * - Enter: 메시지 전송 (입력값이 있을 때만)
 * - Shift + Enter: 줄바꿈 (textarea인 경우)
 * 
 * 사용 예시:
 * - <InputForm onSend={handleSendMessage} isLoading={isLoading} />
 * - ChatWindow에서 useChat 훅의 sendMessage 함수를 연결
 */
