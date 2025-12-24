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
- SentenceTransformers: 로컬 임베딩 모델 (한국어 지원)
- LangChain: RAG 시스템 구축

작동 원리:
1. 음식점 메뉴 텍스트를 로컬 임베딩 모델로 벡터화
2. 벡터를 ChromaDB에 저장 (메타데이터 포함)
3. 사용자 질문을 벡터로 변환하여 유사한 메뉴 검색
4. 검색된 문서를 LLM의 컨텍스트로 제공
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb.utils import embedding_functions
from app.utils import logger, CHROMA_DB_PATH


class VectorStore:
    """ChromaDB 벡터 저장소 관리 클래스"""
    
    def __init__(self, collection_name: str = "restaurant_menu"):
        self.collection_name = collection_name
        self.persist_directory = str(CHROMA_DB_PATH)
        
        # 로컬 임베딩 모델 사용 (한국어 지원)
        # jhgan/ko-sroberta-multitask: 한국어 전용 임베딩 모델
        # 또는 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' (다국어)
        logger.info("로컬 임베딩 모델 로딩 중...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},  # GPU가 있으면 'cuda'로 변경 가능
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("로컬 임베딩 모델 로딩 완료")
        
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """벡터 저장소 초기화"""
        try:
            # ChromaDB 클라이언트 생성
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 컬렉션 가져오기 또는 생성
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"기존 컬렉션 로드: {self.collection_name}")
            except:
                # 컬렉션이 없으면 생성
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "음식점 메뉴 데이터"}
                )
                logger.info(f"새 컬렉션 생성: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"벡터 저장소 초기화 실패: {e}")
            raise
    
    def _embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        return self.embeddings.embed_query(text)
    
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """문서 추가"""
        try:
            # 텍스트를 벡터로 변환
            logger.info(f"{len(texts)}개 문서를 벡터로 변환 중...")
            embeddings_list = []
            for i, text in enumerate(texts):
                if (i + 1) % 50 == 0:
                    logger.info(f"진행 중: {i + 1}/{len(texts)}")
                embedding = self._embed_text(text)
                embeddings_list.append(embedding)
            
            # ID가 없으면 자동 생성
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            # ChromaDB에 추가
            self.collection.add(
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas or [{}] * len(texts),
                ids=ids
            )
            logger.info(f"{len(texts)}개 문서 추가 완료")
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """유사도 검색"""
        try:
            # 쿼리를 벡터로 변환
            query_embedding = self._embed_text(query)
            
            # ChromaDB에서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter
            )
            
            # 결과 포맷팅
            formatted_results = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "score": results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return []
    
    def similarity_search_with_retriever(
        self,
        query: str,
        k: int = 4
    ) -> List[Dict[str, Any]]:
        """Retriever 스타일 검색 (점수 제외)"""
        results = self.similarity_search(query, k=k)
        return [
            {
                "content": r["content"],
                "metadata": r["metadata"]
            }
            for r in results
        ]
    
    def delete_collection(self):
        """컬렉션 삭제"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"컬렉션 삭제 완료: {self.collection_name}")
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")
            raise


# 싱글톤 인스턴스
vectorstore_instance: Optional[VectorStore] = None


def get_vectorstore() -> VectorStore:
    """벡터 저장소 인스턴스 가져오기"""
    global vectorstore_instance
    if vectorstore_instance is None:
        vectorstore_instance = VectorStore()
    return vectorstore_instance
