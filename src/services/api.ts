import axios from 'axios'
import { EventSourcePolyfill } from 'event-source-polyfill'
import { ChatRequest, ChatResponse, ChatResponseSchema } from '@/types/chat'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60초 타임아웃
})

// 일반 채팅 요청
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>('/chat', request)
  
  // Zod로 응답 검증
  return ChatResponseSchema.parse(response.data)
}

// 스트리밍 채팅 요청 (SSE) - EventSourcePolyfill + 자동 재시도
export const sendChatMessageStream = async (
  request: ChatRequest,
  onChunk: (chunk: string) => void,
  onComplete: (fullResponse: string) => void,
  onError: (error: Error) => void
): Promise<void> => {
  return new Promise((resolve, reject) => {
    let fullResponse = ''
    let retryCount = 0
    const maxRetries = 3
    let retryTimeout: NodeJS.Timeout | null = null
    let eventSource: EventSourcePolyfill | null = null
    let isCompleted = false
    
    const cleanup = () => {
      if (retryTimeout) {
        clearTimeout(retryTimeout)
        retryTimeout = null
      }
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }
    
    const connect = () => {
      try {
        // POST 요청을 위해 URL에 데이터를 인코딩하거나, 
        // fetch를 사용하여 스트림을 받은 후 EventSource처럼 처리
        // EventSourcePolyfill은 POST를 직접 지원하지 않으므로 fetch 사용
        
        console.log('스트리밍 요청 시작:', request)
        
        fetch(`${API_BASE_URL}/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          body: JSON.stringify(request),
        }).then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const reader = response.body?.getReader()
          const decoder = new TextDecoder()
          let buffer = ''

          if (!reader) {
            throw new Error('Response body is not readable')
          }

          console.log('스트리밍 읽기 시작')
          
          const processStream = async () => {
            try {
              while (true) {
                const { done, value } = await reader.read()
                
                if (done) {
                  // 버퍼에 남은 데이터 처리
                  if (buffer.trim()) {
                    processBuffer(buffer)
                  }
                  if (!isCompleted) {
                    console.log('스트리밍 완료, 전체 응답 길이:', fullResponse.length)
                    isCompleted = true
                    onComplete(fullResponse)
                    cleanup()
                    resolve()
                  }
                  break
                }

                // 받은 데이터를 즉시 디코딩
                const chunk = decoder.decode(value, { stream: true })
                buffer += chunk
                
                // SSE 형식: "data: {...}\n\n" - 즉시 처리
                while (buffer.includes('\n\n')) {
                  const endIndex = buffer.indexOf('\n\n')
                  const eventData = buffer.substring(0, endIndex)
                  buffer = buffer.substring(endIndex + 2)
                  processBuffer(eventData)
                }
              }
            } catch (streamError) {
              if (!isCompleted) {
                handleError(streamError)
              }
            }
          }
          
          const processBuffer = (eventData: string) => {
            const lines = eventData.split('\n')
            for (const line of lines) {
              const trimmed = line.trim()
              if (!trimmed || !trimmed.startsWith('data: ')) continue
              
              try {
                let jsonStr = trimmed.slice(6).trim()
                
                // 중복된 "data: " 제거
                while (jsonStr.startsWith('data: ')) {
                  jsonStr = jsonStr.slice(6).trim()
                }
                
                if (!jsonStr) continue
                
                const data = JSON.parse(jsonStr)
                
                // content 처리
                if (data.content && typeof data.content === 'string' && data.content.length > 0) {
                  fullResponse += data.content
                  console.log(`[청크] 누적 길이: ${fullResponse.length}, 새 청크: "${data.content.substring(0, 20)}..."`)
                  onChunk(data.content)
                }
                
                // 완료 신호
                if (data.done === true) {
                  console.log('스트리밍 완료 신호 수신')
                  isCompleted = true
                  onComplete(fullResponse)
                  cleanup()
                  resolve()
                  return
                }
              } catch (e) {
                console.warn('JSON 파싱 실패:', trimmed.substring(0, 100), e)
              }
            }
          }
          
          processStream()
        }).catch(error => {
          handleError(error)
        })
        
      } catch (error) {
        handleError(error)
      }
    }
    
    const handleError = (error: any) => {
      cleanup()
      
      if (retryCount < maxRetries && !isCompleted) {
        retryCount++
        const delay = Math.pow(2, retryCount) * 1000 // 지수 백오프: 2초, 4초, 8초
        console.log(`재시도 ${retryCount}/${maxRetries} (${delay}ms 후)`, error)
        
        retryTimeout = setTimeout(() => {
          connect()
        }, delay)
      } else {
        console.error('스트리밍 오류 (최대 재시도 초과):', error)
        isCompleted = true
        onError(error instanceof Error ? error : new Error('Unknown error'))
        reject(error)
      }
    }
    
    // 초기 연결
    connect()
  })
}

// 헬스 체크
export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await apiClient.get('/health')
    return response.status === 200
  } catch {
    return false
  }
}

export default apiClient

