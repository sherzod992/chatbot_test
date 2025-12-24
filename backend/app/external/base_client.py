"""
공통 HTTP 클라이언트 (httpx 기반)

이 파일의 역할:
- 모든 외부 API 클라이언트의 기본 클래스를 제공
- HTTP 요청(GET, POST)을 위한 공통 로직 구현
- 인증 헤더, 타임아웃, 에러 처리 등의 공통 기능 제공
- 코드 재사용 및 일관성 유지

왜 필요한가:
- 각 외부 API 클라이언트에서 중복되는 코드를 제거
- HTTP 요청 로직을 표준화하여 유지보수성 향상
- 에러 처리와 로깅을 중앙에서 관리
- 새로운 외부 API 추가 시 개발 속도 향상

주요 기능:
- BaseAPIClient 클래스: 기본 HTTP 클라이언트
- _get_headers(): 기본 HTTP 헤더 생성 (인증 포함)
- get(): GET 요청 실행 (에러 처리 포함)
- post(): POST 요청 실행 (에러 처리 포함)
- close(): HTTP 클라이언트 연결 종료

특징:
- httpx.AsyncClient 사용 (비동기 HTTP 요청)
- 타임아웃 설정 (기본 30초)
- API 키 기반 인증 (Bearer 토큰)
- HTTP 에러 자동 처리 및 로깅

상속 구조:
- BaseAPIClient를 상속받아 각 API별 특화 기능 추가
- WeatherClient, CalorieClient, KADXClient 등이 상속
"""
