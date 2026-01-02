import { useState, useCallback, useRef, useEffect } from 'react'
import { flushSync } from 'react-dom'
import { Message } from '@/types/chat'
import { sendChatMessage, sendChatMessageStream } from '@/services/api'
import { ChatRequest } from '@/types/chat'

interface UseChatReturn {
  messages: Message[]
  isLoading: boolean
  error: string | null
  sendMessage: (content: string, useStreaming?: boolean) => Promise<void>
  clearMessages: () => void
  conversationId: string | null
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const streamedContentRef = useRef<string>('')
  const updateCounterRef = useRef<number>(0)
  const currentAssistantMessageIdRef = useRef<string | null>(null)

  // 메시지 전송
  const sendMessage = useCallback(async (content: string, useStreaming = true) => {
    if (!content.trim() || isLoading) return

    // 사용자 메시지 추가
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    // 보조 메시지 생성 (스트리밍용)
    const assistantMessageId = (Date.now() + 1).toString()
    currentAssistantMessageIdRef.current = assistantMessageId
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }
    setMessages((prev) => [...prev, assistantMessage])

    try {
      const request: ChatRequest = {
        message: content.trim(),
        conversation_id: conversationId || undefined,
        history: messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      }

      if (useStreaming) {
        // 스트리밍 방식
        streamedContentRef.current = ''
        let hasReceivedChunk = false
        const streamTimeout = setTimeout(() => {
          if (!hasReceivedChunk) {
            console.warn('스트리밍 타임아웃, 일반 방식으로 전환')
          }
        }, 10000) // 10초 타임아웃
        
        console.log('스트리밍 모드로 요청 전송')
        
        try {
          await sendChatMessageStream(
            request,
            // onChunk: 청크 수신 시 (즉시 처리)
            (chunk: string) => {
              hasReceivedChunk = true
              clearTimeout(streamTimeout)
              streamedContentRef.current += chunk
              updateCounterRef.current += 1
              const currentContent = streamedContentRef.current
              const updateCount = updateCounterRef.current
              const msgId = currentAssistantMessageIdRef.current
              
              const chunkReceiveTime = Date.now()
              console.log(`[onChunk ${chunkReceiveTime}] 청크 수신, 누적 길이: ${currentContent.length}, 새 청크: "${chunk.substring(0, 20)}...", 업데이트 #${updateCount}, msgId: ${msgId}`)
              
              if (!msgId) {
                console.warn('assistantMessageId가 없습니다')
                return
              }
              
              // flushSync를 즉시 호출하여 비동기 배칭 방지 및 동기적 DOM 업데이트 보장
              // requestAnimationFrame 없이 직접 호출하여 지연 최소화
              flushSync(() => {
                setMessages((prev) => {
                  // 이전 메시지 배열을 재사용하여 불필요한 복사 방지
                  const msgIndex = prev.findIndex(msg => msg.id === msgId)
                  if (msgIndex === -1) {
                    console.warn('메시지를 찾을 수 없습니다:', msgId)
                    return prev
                  }
                  
                  // 해당 메시지만 새 객체로 교체
                  const newMessages = [...prev]
                  newMessages[msgIndex] = {
                    ...newMessages[msgIndex],
                    content: streamedContentRef.current,
                    isLoading: false,
                  }
                  return newMessages
                })
              })
              
              const updateCompleteTime = Date.now()
              console.log(`[onChunk ${updateCompleteTime}] 상태 업데이트 완료 #${updateCount}, 현재 길이: ${currentContent.length}, 처리 시간: ${updateCompleteTime - chunkReceiveTime}ms`)
            },
            // onComplete: 완료 시
            (fullResponse: string) => {
              console.log('스트리밍 완료, 전체 길이:', fullResponse.length)
              clearTimeout(streamTimeout)
              const msgId = currentAssistantMessageIdRef.current
              
              // 최종 업데이트
              streamedContentRef.current = fullResponse || streamedContentRef.current
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === msgId
                    ? { ...msg, content: streamedContentRef.current, isLoading: false }
                    : msg
                )
              )
              setIsLoading(false)
              currentAssistantMessageIdRef.current = null
            },
            // onError: 에러 시
            async (err: Error) => {
              console.error('스트리밍 에러:', err)
              clearTimeout(streamTimeout)
              const msgId = currentAssistantMessageIdRef.current
              
              // 스트리밍 실패 시 일반 방식으로 fallback
              if (!hasReceivedChunk) {
                console.log('스트리밍 실패, 일반 방식으로 재시도')
                try {
                  const response = await sendChatMessage(request)
                  console.log('일반 API 응답 받음:', response.response.substring(0, 100))
                  setConversationId(response.conversation_id)
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === msgId
                        ? { ...msg, content: response.response, isLoading: false }
                        : msg
                    )
                  )
                  setIsLoading(false)
                  setError(null)
                } catch (fallbackErr) {
                  console.error('Fallback도 실패:', fallbackErr)
                  setError(err.message)
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === msgId
                        ? { ...msg, content: `오류가 발생했습니다: ${err.message}`, isLoading: false }
                        : msg
                    )
                  )
                  setIsLoading(false)
                }
              } else {
                setError(err.message)
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === msgId
                      ? { ...msg, content: streamedContentRef.current || `오류가 발생했습니다: ${err.message}`, isLoading: false }
                      : msg
                  )
                )
                setIsLoading(false)
              }
              currentAssistantMessageIdRef.current = null
            }
          )
        } catch (err) {
          console.error('스트리밍 예외:', err)
          clearTimeout(streamTimeout)
          const msgId = currentAssistantMessageIdRef.current
          // 스트리밍 실패 시 일반 방식으로 fallback
          try {
            console.log('예외 발생, 일반 방식으로 재시도')
            const response = await sendChatMessage(request)
            console.log('일반 API 응답 받음:', response.response.substring(0, 100))
            setConversationId(response.conversation_id)
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === msgId
                  ? { ...msg, content: response.response, isLoading: false }
                  : msg
              )
            )
            setIsLoading(false)
          } catch (fallbackErr) {
            console.error('Fallback도 실패:', fallbackErr)
            const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
            setError(errorMessage)
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === msgId
                  ? { ...msg, content: `오류가 발생했습니다: ${errorMessage}`, isLoading: false }
                  : msg
              )
            )
            setIsLoading(false)
          }
          currentAssistantMessageIdRef.current = null
        }
      } else {
        // 일반 방식
        console.log('일반 API 방식으로 요청')
        const response = await sendChatMessage(request)
        console.log('일반 API 응답 받음, 길이:', response.response.length)
        
        setConversationId(response.conversation_id)
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: response.response, isLoading: false }
              : msg
          )
        )
        setIsLoading(false)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
      setError(errorMessage)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: '오류가 발생했습니다.', isLoading: false }
            : msg
        )
      )
      setIsLoading(false)
    }
  }, [messages, conversationId, isLoading])

  // 메시지 초기화
  const clearMessages = useCallback(() => {
    setMessages([]) 
    setConversationId(null)
    setError(null)
  }, [])

  // 컴포넌트 언마운트 시 
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    conversationId,
  }
}
