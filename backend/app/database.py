"""
MySQL 데이터베이스 연결 및 음식점 데이터 추출

이 파일의 역할:
- MySQL 데이터베이스와의 연결 관리
- 음식점 및 메뉴 데이터를 데이터베이스에서 조회
- 데이터베이스 연결 풀 관리 및 쿼리 실행
- 싱글톤 패턴으로 데이터베이스 인스턴스 관리

왜 필요한가:
- RAG 시스템이 참조할 음식점 메뉴 데이터의 소스
- 데이터베이스에서 구조화된 음식점 정보를 효율적으로 추출
- 벡터 DB에 저장할 원본 데이터 제공
- 데이터베이스 연결을 중앙에서 관리하여 리소스 효율성 향상

주요 기능:
- Database 클래스: MySQL 연결 및 쿼리 실행 관리
- get_all_restaurants(): 모든 음식점 목록 조회
- get_restaurant_menu(): 특정 음식점의 메뉴 목록 조회
- get_restaurants_with_menus(): 음식점과 메뉴를 함께 조회
- get_database(): 싱글톤 데이터베이스 인스턴스 반환

데이터 구조:
- restaurants 테이블: 음식점 기본 정보 (id, name, address, description, category 등)
- menus 테이블: 메뉴 정보 (id, restaurant_id, name, price, allergen_info, nutrition_info 등)

사용 흐름:
1. 벡터 DB 초기화 시 음식점 데이터를 가져와서 벡터화
2. RAG 검색 시 데이터베이스의 최신 정보를 참조 가능
"""
