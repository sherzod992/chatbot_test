"""
FastAPI 애플리케이션: SSE/WebSocket 엔드포인트
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, StreamChunk, Source
from app.rag_chain import get_rag_chain
from app.utils import logger
import json
import uuid
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="전주 음식점 챗봇 API",
    description="RAG 기반 음식점 메뉴 검색 챗봇",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "전주 음식점 챗봇 API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "chat_stream": "/chat/stream",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    일반 채팅 요청 (JSON 응답)
    
    - 질문을 받아 벡터 검색 + LLM을 통해 답변 생성
    - 전체 응답을 한 번에 반환
    """
    try:
        # RAG 체인 가져오기
        rag_chain = get_rag_chain()
        
        # 대화 기록 변환
        history = None
        if request.history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        
        # RAG 체인 실행
        result = rag_chain.invoke(
            question=request.message,
            conversation_id=request.conversation_id,
            history=history
        )
        
        # 소스 변환
        sources = [
            Source(
                content=s.get("content", ""),
                metadata=s.get("metadata", {}),
                score=s.get("score")
            )
            for s in result.get("sources", [])
        ]
        
        # 추천 메뉴 변환
        from app.models import RecommendedMenu
        recommended_menus = [
            RecommendedMenu(
                restaurant_name=m.get("restaurant_name", ""),
                menu_name=m.get("menu_name", ""),
                price=m.get("price", ""),
                calories=m.get("calories", ""),
                address=m.get("address", ""),
                category=m.get("category", ""),
                score=m.get("score")
            )
            for m in result.get("recommended_menus", [])
        ]
        
        # 응답 생성
        response = ChatResponse(
            response=result.get("response", ""),
            sources=sources,
            recommended_menus=recommended_menus,
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"채팅 요청 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    스트리밍 채팅 요청 (SSE)
    
    - 질문을 받아 벡터 검색 + LLM을 통해 답변 생성
    - 응답을 청크 단위로 스트리밍
    """
    try:
        # RAG 체인 가져오기
        rag_chain = get_rag_chain()
        
        # 대화 기록 변환
        history = None
        if request.history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.history
            ]
        
        async def generate():
            """스트리밍 생성기"""
            full_content = ""
            sources = []
            
            try:
                # 벡터 검색으로 소스 먼저 가져오기
                vectorstore = rag_chain.vectorstore
                search_results = vectorstore.similarity_search(request.message, k=4)
                sources = [
                    {
                        "content": r.get("content", ""),
                        "metadata": r.get("metadata", {}),
                        "score": r.get("score")
                    }
                    for r in search_results
                ]
                
                # 스트리밍 응답 생성
                async for chunk in rag_chain.stream(
                    question=request.message,
                    conversation_id=request.conversation_id,
                    history=history
                ):
                    full_content += chunk
                    # SSE 형식으로 전송
                    chunk_data = StreamChunk(
                        content=chunk,
                        done=False,
                        sources=None
                    )
                    yield f"data: {chunk_data.model_dump_json()}\n\n"
                
                # 완료 신호
                final_chunk = StreamChunk(
                    content="",
                    done=True,
                    sources=[
                        Source(
                            content=s.get("content", ""),
                            metadata=s.get("metadata", {}),
                            score=s.get("score")
                        )
                        for s in sources
                    ]
                )
                yield f"data: {final_chunk.model_dump_json()}\n\n"
                
            except Exception as e:
                logger.error(f"스트리밍 오류: {e}", exc_info=True)
                error_chunk = StreamChunk(
                    content=f"오류가 발생했습니다: {str(e)}",
                    done=True,
                    sources=[]
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
        
        return EventSourceResponse(generate())
        
    except Exception as e:
        logger.error(f"스트리밍 요청 처리 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("챗봇 서버 시작")
    logger.info("벡터 저장소 초기화 중...")
    # 벡터 저장소 초기화 (지연 로딩)
    get_rag_chain()
    logger.info("서버 준비 완료")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("챗봇 서버 종료")
