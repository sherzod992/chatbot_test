/**
 * chat.ts
 * 
 * 채팅 관련 TypeScript 타입 정의 파일
 * 
 * 이 파일의 역할:
 * - 채팅 애플리케이션에서 사용하는 모든 타입과 인터페이스를 정의
 * - 타입 안정성을 보장하여 런타임 에러 방지
 * - 백엔드 API와의 통신 시 데이터 구조를 명확히 정의
 * - 코드 자동완성과 타입 체크 지원
 * 
 * 왜 필요한가:
 * - TypeScript의 타입 시스템을 활용하여 개발 생산성 향상
 * - 백엔드 API 응답과 프론트엔드에서 사용하는 데이터 구조 일치 보장
 * - 컴포넌트 간 데이터 전달 시 타입 안정성 확보
 * - 코드 리팩토링 시 타입 오류를 컴파일 타임에 발견
 * 
 * 주요 타입 정의:
 * - Message: 개별 채팅 메시지 (role: 'user' | 'assistant', content: string)
 * - ChatRequest: 백엔드에 전송하는 채팅 요청 (message, conversation_id, history)
 * - ChatResponse: 백엔드에서 받는 채팅 응답 (response, sources, conversation_id, timestamp)
 * - StreamChunk: SSE 스트리밍 응답 청크 (content, done, sources)
 * - Source: 참조 소스 정보 (content, metadata 등)
 * 
 * 사용 예시:
 * - import { Message, ChatRequest } from './types/chat';
 * - 컴포넌트나 훅에서 타입을 import하여 사용
 * - API 호출 시 요청/응답 데이터의 타입 지정
 */
