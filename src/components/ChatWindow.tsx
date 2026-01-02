import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useChat } from '@/hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { InputForm } from './InputForm'
import { AlertCircle, Trash2 } from 'lucide-react'

export const ChatWindow = () => {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 새 메시지가 추가되거나 업데이트되면 스크롤 (실시간 스트리밍 지원)
  useEffect(() => {
    // requestAnimationFrame을 사용하여 DOM 업데이트 후 스크롤
    // 스트리밍 중에는 즉시 스크롤하여 실시간 업데이트 보장
    const timeoutId = setTimeout(() => {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: isLoading ? 'auto' : 'smooth' })
      })
    }, 0)
    
    return () => clearTimeout(timeoutId)
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-screen bg-black">
      {/* 헤더 */}
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">전주 음식점 챗봇</h1>
          <p className="text-sm text-gray-400">메뉴 추천을 도와드립니다</p>
        </div>
        {messages.length > 0 && (
          <motion.button
            onClick={clearMessages}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            className="p-2 text-gray-400 hover:text-red-500 transition-colors"
            title="대화 초기화"
          >
            <Trash2 size={20} />
          </motion.button>
        )}
      </header>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-6 bg-black">
        {messages.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center h-full text-center"
          >
            <div className="bg-gray-800 rounded-full p-6 mb-4 shadow-lg">
              <svg
                className="w-16 h-16 text-primary-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              안녕하세요! 👋
            </h2>
            <p className="text-gray-300 mb-4">
              전주 지역 음식점 메뉴를 추천해드립니다
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {['점심 메뉴 추천해줘', '저렴한 한식 추천', '칼로리 낮은 메뉴'].map(
                (suggestion) => (
                  <motion.button
                    key={suggestion}
                    onClick={() => sendMessage(suggestion)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-full text-sm text-gray-200 hover:bg-gray-700 transition-colors"
                  >
                    {suggestion}
                  </motion.button>
                )
              )}
            </div>
          </motion.div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {messages.map((message) => (
              <MessageBubble 
                key={message.id} 
                message={message} 
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        {/* 에러 메시지 */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-lg flex items-center gap-2 shadow-lg"
          >
            <AlertCircle size={20} />
            <span className="text-sm">{error}</span>
          </motion.div>
        )}
      </div>

      {/* 입력 폼 */}
      <InputForm onSubmit={sendMessage} isLoading={isLoading} />
    </div>
  )
}
