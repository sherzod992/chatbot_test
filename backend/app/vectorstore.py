"""
ChromaDB 벡터 저장소 관리

이 파일의 역할:
- ChromaDB 벡터 데이터베이스와의 연결 및 관리
- 음식점 메뉴 데이터를 벡터로 변환하여 저장
- 유사도 검색 기능 제공 (사용자 질문과 유사한 메뉴 찾기)
- LangChain과 ChromaDB를 연동하여 RAG 시스템 구축

왜 필요한가:
- RAG(Retrieval-Augmented Generation)의 핵심 컴포넌트
- 사용자의 자연어 질문을 벡터로 변환하여 관련 메뉴 검색
- 대량의 음식점 메뉴 데이터를 효율적으로 검색
- 의미 기반 검색으로 키워드 매칭보다 정확한 결과 제공

주요 기능:
- VectorStore 클래스: 벡터 저장소 관리 및 검색
- add_documents(): 문서를 벡터로 변환하여 저장
- similarity_search(): 유사도 기반 검색 (점수 포함)
- similarity_search_with_retriever(): LangChain Retriever 사용 검색
- delete_collection(): 컬렉션 삭제 (초기화용)

기술 스택:
- ChromaDB: 벡터 데이터베이스 (로컬 파일 기반)
- GoogleGenerativeAIEmbeddings: 텍스트를 벡터로 변환
- LangChain Chroma: LangChain과 ChromaDB 통합

작동 원리:
1. 음식점 메뉴 텍스트를 Google Embedding API로 벡터화
2. 벡터를 ChromaDB에 저장 (메타데이터 포함)
3. 사용자 질문을 벡터로 변환하여 유사한 메뉴 검색
4. 검색된 문서를 LLM의 컨텍스트로 제공
"""
