import { User, Bot, Loader2 } from 'lucide-react'
import { Message } from '@/types/chat'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user'
  // message.content를 직접 사용 (상태 중복 방지)
  // React가 props 변경을 감지하도록 함

  return (
    <div
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}
    >
      {/* 아바타 */}
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-primary-500 text-white'
            : 'bg-gray-800 text-gray-200'
        }`}
      >
        {isUser ? (
          <User size={20} />
        ) : (
          <Bot size={20} />
        )}
      </div>

      {/* 메시지 내용 */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-500 text-white rounded-tr-sm'
              : 'bg-gray-800 text-gray-100 rounded-tl-sm'
          }`}
        >
          {message.isLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="animate-spin" size={16} />
              <span className="text-sm">답변을 생성하고 있습니다...</span>
            </div>
          ) : message.content ? (
            <p className="text-sm whitespace-pre-wrap break-words" key={`content-${message.content.length}`}>{message.content}</p>
          ) : (
            <p className="text-sm text-gray-400 italic">응답을 기다리는 중...</p>
          )}
        </div>
        <span className="text-xs text-gray-400 mt-1">
          {message.timestamp.toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>
    </div>
  )
}
