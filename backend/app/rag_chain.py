"""
Advanced RAG 체인: 검색 + LLM + 외부 API
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.vectorstore import get_vectorstore
from app.utils import logger
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class RAGChain:
    """RAG 파이프라인 관리 클래스"""
    
    def __init__(self):
        """RAG 체인 초기화"""
        # OpenAI LLM 초기화
        # ChatOpenAI는 환경 변수 OPENAI_API_KEY를 자동으로 읽어옵니다
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # GPT-4o-mini 모델 사용
            temperature=0.7,
            max_tokens=500  # 응답 길이 제한으로 속도 개선
        )
        
        # 벡터 저장소 가져오기
        self.vectorstore = get_vectorstore()
        
        # 대화 기록 관리 (간단한 리스트로 관리)
        self.memories: Dict[str, List[BaseMessage]] = {}
        
        # 프롬프트 템플릿 (간소화된 형식)
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """너는 전주 지역 음식점과 음식 추천만 제공하는 챗봇입니다.

🚫 절대 규칙:
1. 제공된 음식점 데이터(RAG/벡터 DB)만 사용하세요.
2. 존재하지 않는 음식점이나 메뉴를 만들어내지 마세요.
3. 정보가 부족하면 솔직하게 부족하다고 말하세요.
4. 답변은 짧고 실용적으로 작성하세요.
5. 검색된 메뉴 중 2-3개를 추천하세요.
6. 각 메뉴의 음식점명, 메뉴명, 가격, 칼로리, 주소를 명확히 제시하세요.
7. 사용자 요구사항(가격, 칼로리, 카테고리)을 반영하세요.

메뉴 목록:
{context}"""),
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
        """검색 결과를 컨텍스트 문자열로 변환 (간소화된 형식)"""
        if not search_results:
            return "검색된 메뉴 정보가 없습니다."
        
        # 상위 5개만 사용하여 프롬프트 길이 단축
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):
            metadata = result.get("metadata", {})
            
            # 간결한 한 줄 형식으로 변경
            restaurant_name = metadata.get("restaurant_name", "")
            menu_name = metadata.get("menu_name", "")
            price = metadata.get("price", "")
            calories = metadata.get("calories", "")
            address = metadata.get("address", "")
            category = metadata.get("category", "")
            
            # 한 줄로 압축: "1. 음식점명 - 메뉴명 (가격원, 칼로리kcal) [주소]"
            menu_info = f"{i}. {restaurant_name} - {menu_name}"
            if price:
                menu_info += f" ({price}원"
                if calories:
                    menu_info += f", {calories}kcal"
                menu_info += ")"
            if address:
                menu_info += f" [{address}]"
            if category:
                menu_info += f" ({category})"
            
            context_parts.append(menu_info)
        
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
            step_times = {}
            total_start = time.time()
            
            # 1. 사용자 선호도 추출
            start = time.time()
            preferences = self._extract_preferences(question)
            step_times['preference_extraction'] = time.time() - start
            logger.info(f"추출된 선호도: {preferences}")
            
            # 2. 벡터 검색 (필터링 적용)
            start = time.time()
            logger.info(f"질문 검색 중: {question}")
            if preferences.get("category") or preferences.get("max_price") or preferences.get("max_calories"):
                # 필터링 검색 사용
                search_results = self.vectorstore.search_with_filters(
                    query=question,
                    category=preferences.get("category"),
                    max_price=preferences.get("max_price"),
                    max_calories=preferences.get("max_calories"),
                    k=5  # 8 → 5로 줄여서 프롬프트 길이 단축
                )
            else:
                # 일반 검색
                search_results = self.vectorstore.similarity_search(question, k=5)  # 8 → 5로 줄임
            step_times['vector_search'] = time.time() - start
            
            # 3. 컨텍스트 포맷팅
            start = time.time()
            context = self._format_context(search_results)
            step_times['context_formatting'] = time.time() - start
            
            # 4. 대화 기록 준비
            start = time.time()
            memory = self._get_memory(conversation_id)
            
            # history가 제공되면 메모리에 추가
            if history:
                for msg in history:
                    if msg.get("role") == "user":
                        memory.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        memory.append(AIMessage(content=msg.get("content", "")))
            step_times['memory_preparation'] = time.time() - start
            
            # 5. 프롬프트 생성
            start = time.time()
            chat_history = memory[-6:] if len(memory) > 6 else memory  # 최근 6개만
            
            prompt = self.prompt_template.format_messages(
                context=context,
                history="\n".join([f"{'사용자' if isinstance(m, HumanMessage) else '챗봇'}: {m.content}" 
                                  for m in chat_history]),
                question=question,
                chat_history=chat_history
            )
            step_times['prompt_creation'] = time.time() - start
            
            # 6. LLM 호출
            start = time.time()
            logger.info("LLM 호출 중...")
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            step_times['llm_call'] = time.time() - start
            
            # 7. 대화 기록에 추가
            start = time.time()
            memory.append(HumanMessage(content=question))
            memory.append(AIMessage(content=answer))
            
            # 8. 소스 정보 및 추천 메뉴 준비
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
            step_times['result_preparation'] = time.time() - start
            
            # 총 시간 계산
            total_time = time.time() - total_start
            step_times['total'] = total_time
            
            # 단계별 시간 로그 출력
            logger.info("=" * 60)
            logger.info("단계별 응답 시간 분석")
            logger.info("=" * 60)
            for step, elapsed in step_times.items():
                percentage = (elapsed / total_time * 100) if total_time > 0 else 0
                logger.info(f"  {step:25s}: {elapsed:6.2f}초 ({percentage:5.1f}%)")
            logger.info("=" * 60)
            
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
                    k=5  # 8 → 5로 줄여서 프롬프트 길이 단축
                )
            else:
                search_results = self.vectorstore.similarity_search(question, k=5)  # 8 → 5로 줄임
            
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
                # chunk가 AIMessageChunk인 경우 처리
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    # content가 문자열이 아닌 경우 변환
                    if not isinstance(content, str):
                        content = str(content) if content is not None else ""
                else:
                    content = str(chunk) if chunk is not None else ""
                
                # 빈 문자열이 아닌 경우에만 yield
                if content and content.strip():
                    full_response += content
                    yield content
                # 빈 문자열이어도 None이 아닌 경우 처리 (예: 공백 문자)
                elif content is not None and len(content) > 0:
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
