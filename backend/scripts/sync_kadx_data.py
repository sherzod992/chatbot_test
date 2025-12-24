"""
KADX 데이터 동기화 스크립트
KADX API에서 알레르기 데이터를 가져와서 저장

이 파일의 역할:
- KADX API에서 식품 알레르기 및 영양 정보를 주기적으로 가져옴
- 가져온 데이터를 CSV 파일로 저장하여 로컬에서 활용
- API 호출 제한을 고려한 배치 작업 처리

왜 필요한가:
- 최신 알레르기 정보를 정기적으로 업데이트
- API 호출 비용 절감 (로컬 캐시 활용)
- 네트워크 오류나 API 장애 시에도 데이터 사용 가능
- 배치 작업으로 대량 데이터를 효율적으로 처리

주요 기능:
- sync_kadx_allergy_data(): 알레르기 데이터 동기화
  - 주요 알레르기 유발 식품 목록을 API에서 조회
  - CSV 파일로 저장 (backend/data/kadx_allergy.csv)
- sync_kadx_nutrition_data(): 영양 정보 데이터 동기화
  - 주요 식품의 영양 정보를 조회
  - 데이터 수집 및 반환

동기화 대상:
- 알레르기 정보: 우유, 계란, 밀, 대두, 땅콩, 견과류, 갑각류, 생선, 조개류, 육류
- 영양 정보: 쌀, 보리, 옥수수, 콩, 팥, 녹두, 배추, 무, 당근, 오이, 토마토, 양파

실행 흐름:
1. KADX API 클라이언트 생성
2. 각 식품에 대해 API 호출 (1초 간격으로 제한)
3. 응답 데이터 수집
4. CSV 파일로 저장 (UTF-8 with BOM으로 한글 지원)
5. 저장된 데이터 개수 로깅

데이터 저장 형식:
- CSV 파일: backend/data/kadx_allergy.csv
- 컬럼: food (식품명), allergy_info (알레르기 정보 JSON)

언제 실행하나:
- 프로젝트 최초 설정 시 (초기 데이터 로드)
- 정기적인 데이터 업데이트 (cron, 스케줄러)
- 알레르기 정보가 변경되었을 때 수동 실행

API 호출 제한:
- 각 호출 사이에 1초 대기 (rate limiting)
- API 사용량 모니터링 필요

사용 방법:
- python scripts/sync_kadx_data.py
- 알레르기 데이터만: sync_kadx_allergy_data() 실행
- 영양 정보도: sync_kadx_nutrition_data() 주석 해제
"""
