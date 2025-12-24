"""
외부 API 클라이언트 모듈

이 파일의 역할:
- external 패키지를 Python 패키지로 만드는 초기화 파일
- 외부 API 클라이언트들을 쉽게 import할 수 있도록 export
- 패키지 레벨에서 사용 가능한 클래스들을 정의

왜 필요한가:
- 외부 API 클라이언트들을 모듈화하여 관리
- 다른 모듈에서 from app.external import WeatherClient 형태로 간편하게 사용
- 패키지 내부 구조를 숨기고 필요한 것만 노출 (캡슐화)

Export되는 클래스:
- BaseAPIClient: 모든 외부 API 클라이언트의 기본 클래스
- WeatherClient: OpenWeatherMap 날씨 API 클라이언트
- CalorieClient: Nutritionix 칼로리 API 클라이언트
- KADXClient: KADX 농식품 데이터 API 클라이언트

사용 예시:
- from app.external import WeatherClient, CalorieClient
- 각 클라이언트는 BaseAPIClient를 상속받아 공통 기능 사용
"""
