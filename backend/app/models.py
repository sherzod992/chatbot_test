"""
Pydantic 모델: 요청/응답 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """개별 채팅 메시지"""
    role: str = Field(..., description="메시지 역할: 'user' 또는 'assistant'")
    content: str = Field(..., description="메시지 내용")


class ChatRequest(BaseModel):
    """채팅 API 요청"""
    message: str = Field(..., description="사용자 메시지")
    conversation_id: Optional[str] = Field(None, description="대화 ID (선택사항)")
    history: Optional[List[ChatMessage]] = Field(default=[], description="대화 기록 (선택사항)")


class Source(BaseModel):
    """검색 결과 소스"""
    content: str = Field(..., description="검색된 문서 내용")
    metadata: Dict[str, Any] = Field(default={}, description="메타데이터")
    score: Optional[float] = Field(None, description="유사도 점수")




class StreamChunk(BaseModel):
    """스트리밍 응답 청크"""
    content: str = Field(..., description="청크 내용")
    done: bool = Field(default=False, description="스트리밍 완료 여부")
    sources: Optional[List[Source]] = Field(None, description="참조된 소스 (완료 시)")


class RecommendedMenu(BaseModel):
    """추천 메뉴 정보"""
    restaurant_name: str = Field(..., description="음식점명")
    menu_name: str = Field(..., description="메뉴명")
    price: str = Field(..., description="가격")
    calories: str = Field(..., description="칼로리")
    address: str = Field(..., description="주소")
    category: str = Field(..., description="카테고리")
    score: Optional[float] = Field(None, description="유사도 점수")


class ChatResponse(BaseModel):
    """채팅 API 응답"""
    response: str = Field(..., description="챗봇 응답")
    sources: List[Source] = Field(default=[], description="참조된 소스")
    recommended_menus: List[RecommendedMenu] = Field(default=[], description="추천 메뉴 목록")
    conversation_id: Optional[str] = Field(None, description="대화 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")


class RestaurantInfo(BaseModel):
    """음식점 정보"""
    id: str = Field(..., description="음식점 ID")
    name: str = Field(..., description="음식점명")
    address: str = Field(..., description="주소")
    category: str = Field(..., description="카테고리")
    menu: Optional[Dict[str, Any]] = Field(None, description="메뉴 정보")
