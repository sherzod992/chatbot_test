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
              
              console.log(`[onChunk #${Date.now()}] 청크 수신, 누적 길이: ${currentContent.length}, 새 청크: "${chunk.substring(0, 20)}...", 업데이트 #${updateCount}`)
              
              // flushSync를 즉시 호출하여 비동기 배칭 방지
              flushSync(() => {
                // 메시지 업데이트
                setMessages((prev) => {
                  const newMessages = prev.map((msg) => {
                    if (msg.id === assistantMessageId) {
                      // 완전히 새로운 객체 생성
                      return { 
                        id: msg.id,
                        role: msg.role,
                        content: currentContent, // 현재 값 직접 사용
                        isLoading: false,
                        timestamp: new Date() // 매번 새로운 타임스탬프
                      }
                    }
                    return msg
                  })
                  return newMessages
                })
              })
              console.log(`[onChunk] 상태 업데이트 완료 #${updateCount}, 현재 길이: ${currentContent.length}`)
            },
            // onComplete: 완료 시
            (fullResponse: string) => {
              console.log('스트리밍 완료, 전체 길이:', fullResponse.length)
              clearTimeout(streamTimeout)
              
              // 최종 업데이트
              streamedContentRef.current = fullResponse || streamedContentRef.current
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: streamedContentRef.current, isLoading: false }
                    : msg
                )
              )
              setIsLoading(false)
            },
            // onError: 에러 시
            async (err: Error) => {
              console.error('스트리밍 에러:', err)
              clearTimeout(streamTimeout)
              
              // 스트리밍 실패 시 일반 방식으로 fallback
              if (!hasReceivedChunk) {
                console.log('스트리밍 실패, 일반 방식으로 재시도')
                try {
                  const response = await sendChatMessage(request)
                  console.log('일반 API 응답 받음:', response.response.substring(0, 100))
                  setConversationId(response.conversation_id)
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
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
                      msg.id === assistantMessageId
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
                    msg.id === assistantMessageId
                      ? { ...msg, content: streamedContentRef.current || `오류가 발생했습니다: ${err.message}`, isLoading: false }
                      : msg
                  )
                )
                setIsLoading(false)
              }
            }
          )
        } catch (err) {
          console.error('스트리밍 예외:', err)
          clearTimeout(streamTimeout)
          // 스트리밍 실패 시 일반 방식으로 fallback
          try {
            console.log('예외 발생, 일반 방식으로 재시도')
            const response = await sendChatMessage(request)
            console.log('일반 API 응답 받음:', response.response.substring(0, 100))
            setConversationId(response.conversation_id)
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
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
                msg.id === assistantMessageId
                  ? { ...msg, content: `오류가 발생했습니다: ${errorMessage}`, isLoading: false }
                  : msg
              )
            )
            setIsLoading(false)
          }
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
