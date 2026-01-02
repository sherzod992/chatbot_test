"""
FastAPI 애플리케이션: SSE/WebSocket 엔드포인트
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from app.models import ChatRequest, ChatResponse, StreamChunk, Source
from app.rag_chain import get_rag_chain
from app.utils import logger, validate_question
import json
import uuid
import time
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
        # 질문 검증 (LLM 호출 전에 수행)
        is_valid, rejection_message = validate_question(request.message)
        if not is_valid:
            # 거절 메시지만 반환 (소스 없음, 추천 메뉴 없음)
            return ChatResponse(
                response=rejection_message,
                sources=[],
                recommended_menus=[],
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                timestamp=datetime.now()
            )
        
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
    # 요청 받은 시간 기록
    request_start_time = time.time()
    
    try:
        # 질문 검증 (LLM 호출 전에 수행)
        is_valid, rejection_message = validate_question(request.message)
        if not is_valid:
            # 거절 메시지를 스트리밍 형식으로 즉시 반환
            async def reject():
                # 거절 메시지를 한 번에 전송
                chunk = StreamChunk(
                    content=rejection_message,
                    done=True,
                    sources=[]
                )
                yield f"data: {chunk.model_dump_json()}\n\n"
            
            return EventSourceResponse(
                reject(),
                headers={
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Cache-Control": "no-cache",
                    "Content-Type": "text/event-stream",
                }
            )
        
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
                # 벡터 검색으로 소스 먼저 가져오기 (필수)
                vectorstore = rag_chain.vectorstore
                search_results = vectorstore.similarity_search(request.message, k=5)
                sources = [
                    {
                        "content": r.get("content", ""),
                        "metadata": r.get("metadata", {}),
                        "score": r.get("score")
                    }
                    for r in search_results
                ]
                
                # 스트리밍 시작 시간 기록
                stream_start_time = time.time()
                request_to_stream_time = stream_start_time - request_start_time
                logger.info("스트리밍 시작")
                logger.info(f"[요청 처리] 요청 수신부터 스트리밍 시작까지: {request_to_stream_time:.3f}초")
                
                chunk_count = 0
                sent_count = 0
                async for chunk in rag_chain.stream(
                    question=request.message,
                    conversation_id=request.conversation_id,
                    history=history
                ):
                    chunk_count += 1
                    full_content += chunk
                    logger.info(f"청크 #{chunk_count} 생성, 길이: {len(chunk) if chunk else 0}, 내용: '{chunk[:50] if chunk else ''}...'")
                    
                    # 완전히 빈 청크만 스킵 (공백이 있어도 전송)
                    if not chunk or (isinstance(chunk, str) and chunk == ""):
                        logger.debug(f"완전히 빈 청크 스킵: chunk_count={chunk_count}")
                        continue
                    
                    # SSE 형식으로 즉시 전송
                    sent_count += 1
                    chunk_data = StreamChunk(
                        content=chunk,
                        done=False,
                        sources=None
                    )
                    # SSE 형식: "data: {json}\n\n" - 명시적으로 포맷팅
                    sse_data = f"data: {chunk_data.model_dump_json()}\n\n"
                    logger.info(f"청크 #{sent_count} 전송, SSE 길이: {len(sse_data)}, content: {chunk[:30]}...")
                    yield sse_data
                
                # 스트리밍 완료 시간 기록
                stream_end_time = time.time()
                stream_duration = stream_end_time - stream_start_time
                total_duration = stream_end_time - request_start_time
                
                logger.info(f"스트리밍 완료, 생성된 청크: {chunk_count}개, 전송된 청크: {sent_count}개, 전체 길이: {len(full_content)}")
                logger.info(f"[요약] 스트리밍 소요 시간: {stream_duration:.3f}초, 전체 요청 처리 시간: {total_duration:.3f}초")
                
                # 최소 하나의 청크도 전송되지 않았다면 에러 청크 전송
                if sent_count == 0:
                    logger.warning("스트리밍 중 청크를 받지 못했습니다")
                    error_chunk = StreamChunk(
                        content="응답을 생성하는 중 오류가 발생했습니다.",
                        done=True,
                        sources=[]
                    )
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                    return
                
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
        
        # SSE 헤더 설정 (버퍼링 방지 및 연결 유지)
        return EventSourceResponse(
            generate(),
            headers={
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Nginx 버퍼링 방지
                "Cache-Control": "no-cache",
                "Content-Type": "text/event-stream",
            }
        )
        
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
