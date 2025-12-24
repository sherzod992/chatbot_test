"""
Advanced RAG 체인: 검색 + LLM + 외부 API
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.vectorstore import get_vectorstore
from app.utils import logger
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 (환경 변수에서 가져오기)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


class RAGChain:
    """RAG 파이프라인 관리 클래스"""
    
    def __init__(self):
        """RAG 체인 초기화"""
        # OpenAI LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # 또는 "gpt-4", "gpt-4-turbo-preview"
            openai_api_key=OPENAI_API_KEY,
            temperature=0.7
        )
        
        # 벡터 저장소 가져오기
        self.vectorstore = get_vectorstore()
        
        # 대화 기록 관리 (간단한 리스트로 관리)
        self.memories: Dict[str, List[BaseMessage]] = {}
        
        # 프롬프트 템플릿 (추천 중심)
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """당신은 전주 지역 음식점 메뉴를 추천하는 전문 챗봇입니다.

추천 규칙:
1. 사용자의 질문과 선호도를 파악하여 적합한 메뉴를 추천합니다.
2. 검색된 메뉴 중에서 최소 2-3개를 추천하며, 각 메뉴의 장점을 설명합니다.
3. 각 추천 메뉴에 대해 다음 정보를 명확히 제시합니다:
   - 음식점명
   - 메뉴명
   - 가격
   - 칼로리
   - 주소
4. 가격대, 칼로리, 카테고리 등 사용자 요구사항을 반영하여 추천합니다.
5. 비교 정보를 제공하여 사용자가 선택할 수 있도록 돕습니다.
6. 친절하고 추천하는 톤으로 답변하며, 각 메뉴의 특징을 강조합니다.
7. 검색된 정보가 없거나 부족하면 솔직하게 말하고, 다른 질문을 제안합니다.

검색된 메뉴 정보:
{context}

이전 대화:
{history}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
    
    def _get_memory(self, conversation_id: Optional[str] = None) -> List[BaseMessage]:
        """대화 기록 가져오기 또는 생성"""
        if conversation_id is None:
            conversation_id = "default"
        
        if conversation_id not in self.memories:
            self.memories[conversation_id] = []
        
        return self.memories[conversation_id]
    
    def _extract_preferences(self, question: str) -> Dict[str, Any]:
        """질문에서 사용자 선호도 추출"""
        preferences = {
            "category": None,
            "price_range": None,
            "max_price": None,
            "max_calories": None,
            "keywords": []
        }
        
        question_lower = question.lower()
        
        # 카테고리 추출
        categories = ["한식", "중식", "일식", "양식", "분식", "치킨", "피자", "카페"]
        for cat in categories:
            if cat in question:
                preferences["category"] = cat
                break
        
        # 가격 관련 키워드
        price_keywords = {
            "저렴": "low",
            "싼": "low",
            "저가": "low",
            "비싼": "high",
            "고급": "high",
            "프리미엄": "high",
            "적당한": "medium"
        }
        for keyword, range_type in price_keywords.items():
            if keyword in question_lower:
                preferences["price_range"] = range_type
                break
        
        # 가격 숫자 추출 (예: "1만원 이하", "15000원")
        import re
        price_matches = re.findall(r'(\d+)\s*만?\s*원', question)
        if price_matches:
            try:
                price = int(price_matches[0])
                if "만" in question or price > 1000:
                    price = price * 10000 if price < 1000 else price
                preferences["max_price"] = price
            except ValueError:
                pass
        
        # 칼로리 관련
        if "칼로리" in question or "다이어트" in question_lower or "저칼로리" in question_lower:
            calorie_matches = re.findall(r'(\d+)\s*칼로리', question)
            if calorie_matches:
                try:
                    preferences["max_calories"] = int(calorie_matches[0])
                except ValueError:
                    pass
        
        return preferences
    
    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """검색 결과를 컨텍스트 문자열로 변환 (추천 중심)"""
        if not search_results:
            return "검색된 메뉴 정보가 없습니다."
        
        context_parts = []
        context_parts.append("=== 추천 가능한 메뉴 목록 ===\n")
        
        for i, result in enumerate(search_results, 1):
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0.0)
            
            context_parts.append(f"[추천 옵션 {i}]")
            
            # 메타데이터에서 정보 추출
            restaurant_name = metadata.get("restaurant_name", "")
            menu_name = metadata.get("menu_name", "")
            price = metadata.get("price", "")
            calories = metadata.get("calories", "")
            address = metadata.get("address", "")
            category = metadata.get("category", "")
            
            # 구조화된 정보 제공
            if restaurant_name:
                context_parts.append(f"음식점: {restaurant_name}")
            if menu_name:
                context_parts.append(f"메뉴: {menu_name}")
            if category:
                context_parts.append(f"카테고리: {category}")
            if price:
                context_parts.append(f"가격: {price}원")
            if calories:
                context_parts.append(f"칼로리: {calories}kcal")
            if address:
                context_parts.append(f"주소: {address}")
            
            # 상세 정보
            context_parts.append(f"상세: {content}")
            context_parts.append(f"유사도 점수: {score:.4f}")
            context_parts.append("")
        
        context_parts.append("=== 추천 가이드 ===")
        context_parts.append("위 메뉴들 중에서 사용자의 요구사항에 맞는 2-3개를 추천하고,")
        context_parts.append("각 메뉴의 특징(가격, 칼로리, 맛 등)을 비교하여 설명해주세요.")
        
        return "\n".join(context_parts)
    
    def invoke(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        질문을 받아 RAG를 통해 답변 생성
        
        Args:
            question: 사용자 질문
            conversation_id: 대화 ID (선택사항)
            history: 대화 기록 (선택사항)
        
        Returns:
            답변과 소스 정보를 포함한 딕셔너리
        """
        try:
            # 1. 사용자 선호도 추출
            preferences = self._extract_preferences(question)
            logger.info(f"추출된 선호도: {preferences}")
            
            # 2. 벡터 검색 (필터링 적용)
            logger.info(f"질문 검색 중: {question}")
            if preferences.get("category") or preferences.get("max_price") or preferences.get("max_calories"):
                # 필터링 검색 사용
                search_results = self.vectorstore.search_with_filters(
                    query=question,
                    category=preferences.get("category"),
                    max_price=preferences.get("max_price"),
                    max_calories=preferences.get("max_calories"),
                    k=8
                )
            else:
                # 일반 검색
                search_results = self.vectorstore.similarity_search(question, k=8)
            
            # 3. 컨텍스트 포맷팅
            context = self._format_context(search_results)
            
            # 3. 대화 기록 준비
            memory = self._get_memory(conversation_id)
            
            # history가 제공되면 메모리에 추가
            if history:
                for msg in history:
                    if msg.get("role") == "user":
                        memory.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        memory.append(AIMessage(content=msg.get("content", "")))
            
            # 4. 프롬프트 생성
            chat_history = memory[-6:] if len(memory) > 6 else memory  # 최근 6개만
            
            prompt = self.prompt_template.format_messages(
                context=context,
                history="\n".join([f"{'사용자' if isinstance(m, HumanMessage) else '챗봇'}: {m.content}" 
                                  for m in chat_history]),
                question=question,
                chat_history=chat_history
            )
            
            # 5. LLM 호출
            logger.info("LLM 호출 중...")
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # 6. 대화 기록에 추가
            memory.append(HumanMessage(content=question))
            memory.append(AIMessage(content=answer))
            
            # 7. 소스 정보 및 추천 메뉴 준비
            sources = []
            recommended_menus = []
            
            for r in search_results[:5]:  # 상위 5개만 추천
                metadata = r.get("metadata", {})
                source_info = {
                    "content": r.get("content", ""),
                    "metadata": metadata,
                    "score": r.get("score")
                }
                sources.append(source_info)
                
                # 추천 메뉴 정보 추출
                if metadata.get("menu_name") and metadata.get("restaurant_name"):
                    recommended_menus.append({
                        "restaurant_name": metadata.get("restaurant_name", ""),
                        "menu_name": metadata.get("menu_name", ""),
                        "price": str(metadata.get("price", "")),
                        "calories": str(metadata.get("calories", "")),
                        "address": metadata.get("address", ""),
                        "category": metadata.get("category", ""),
                        "score": r.get("score")
                    })
            
            return {
                "response": answer,
                "sources": sources,
                "recommended_menus": recommended_menus
            }
            
        except Exception as e:
            logger.error(f"RAG 체인 실행 오류: {e}", exc_info=True)
            return {
                "response": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "sources": []
            }
    
    async def stream(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        """
        스트리밍 방식으로 답변 생성
        
        Args:
            question: 사용자 질문
            conversation_id: 대화 ID (선택사항)
            history: 대화 기록 (선택사항)
        
        Yields:
            답변의 청크 문자열
        """
        try:
            # 1. 사용자 선호도 추출
            preferences = self._extract_preferences(question)
            
            # 2. 벡터 검색 (필터링 적용)
            if preferences.get("category") or preferences.get("max_price") or preferences.get("max_calories"):
                search_results = self.vectorstore.search_with_filters(
                    query=question,
                    category=preferences.get("category"),
                    max_price=preferences.get("max_price"),
                    max_calories=preferences.get("max_calories"),
                    k=8
                )
            else:
                search_results = self.vectorstore.similarity_search(question, k=8)
            
            context = self._format_context(search_results)
            
            # 2. 대화 기록 준비
            memory = self._get_memory(conversation_id)
            if history:
                for msg in history:
                    if msg.get("role") == "user":
                        memory.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        memory.append(AIMessage(content=msg.get("content", "")))
            
            chat_history = memory[-6:] if len(memory) > 6 else memory
            
            # 3. 프롬프트 생성
            prompt = self.prompt_template.format_messages(
                context=context,
                history="\n".join([f"{'사용자' if isinstance(m, HumanMessage) else '챗봇'}: {m.content}" 
                                  for m in chat_history]),
                question=question,
                chat_history=chat_history
            )
            
            # 4. 스트리밍 호출
            full_response = ""
            async for chunk in self.llm.astream(prompt):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if content:
                    full_response += content
                    yield content
            
            # 5. 대화 기록에 추가
            memory.append(HumanMessage(content=question))
            memory.append(AIMessage(content=full_response))
            
        except Exception as e:
            logger.error(f"스트리밍 오류: {e}", exc_info=True)
            yield f"죄송합니다. 오류가 발생했습니다: {str(e)}"


# 싱글톤 인스턴스
_rag_chain_instance: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """RAG 체인 인스턴스 가져오기"""
    global _rag_chain_instance
    if _rag_chain_instance is None:
        _rag_chain_instance = RAGChain()
    return _rag_chain_instance
