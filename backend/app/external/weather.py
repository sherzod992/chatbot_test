"""
OpenWeatherMap API 클라이언트

이 파일의 역할:
- OpenWeatherMap API와 통신하여 날씨 정보를 가져옴
- 현재 날씨 및 날씨 예보 정보 제공
- 챗봇이 날씨 관련 질문에 답변할 수 있도록 데이터 제공

왜 필요한가:
- 사용자가 "오늘 날씨가 어떤가요?" 같은 질문에 답변
- 날씨에 따른 음식 추천 (예: 비오는 날 따뜻한 국물 요리)
- 실시간 날씨 정보를 챗봇 응답에 통합

주요 기능:
- WeatherClient 클래스: OpenWeatherMap API 클라이언트
- get_current_weather(): 현재 날씨 정보 조회
  - 도시명, 온도, 날씨 설명, 습도, 풍속 등
- get_forecast(): 5일 날씨 예보 조회

API 사용:
- Base URL: https://api.openweathermap.org/data/2.5
- 인증: API Key (appid 파라미터)
- 언어: 한국어 (lang=kr)
- 단위: 섭씨 (units=metric)

통합 방식:
- RAGChain에서 질문에 날씨 관련 키워드가 있으면 자동 호출
- 날씨 정보를 LLM 컨텍스트에 포함하여 답변 생성
- 예: "비오는 날 추천 음식" → 날씨 정보 + 메뉴 추천

에러 처리:
- API 키가 없으면 경고 로그만 남기고 빈 응답 반환
- API 호출 실패 시 에러 정보를 반환하여 LLM이 적절히 처리
"""
