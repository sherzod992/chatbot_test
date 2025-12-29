import { useState, FormEvent } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'

const messageSchema = z.object({
  message: z.string().min(1, '메시지를 입력하세요'),
})

type MessageFormData = z.infer<typeof messageSchema>

interface InputFormProps {
  onSubmit: (message: string) => void
  isLoading: boolean
}

export const InputForm = ({ onSubmit, isLoading }: InputFormProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<MessageFormData>({
    resolver: zodResolver(messageSchema),
  })

  const onFormSubmit = (data: MessageFormData) => {
    onSubmit(data.message)
    reset()
  }

  return (
    <form
      onSubmit={handleSubmit(onFormSubmit)}
      className="sticky bottom-0 bg-gray-900 border-t border-gray-800 p-4"
    >
      <div className="flex gap-2 items-end">
        <div className="flex-1">
          <textarea
            {...register('message')}
            placeholder="메시지를 입력하세요..."
            rows={1}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 text-white placeholder-gray-400 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            style={{
              minHeight: '48px',
              maxHeight: '120px',
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(onFormSubmit)()
              }
            }}
            disabled={isLoading}
          />
          {errors.message && (
            <p className="text-xs text-red-400 mt-1">{errors.message.message}</p>
          )}
        </div>
        <motion.button
          type="submit"
          disabled={isLoading}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-primary-500 text-white px-6 py-3 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 hover:bg-primary-600 transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              <span>전송 중...</span>
            </>
          ) : (
            <>
              <Send size={18} />
              <span>전송</span>
            </>
          )}
        </motion.button>
      </div>
    </form>
  )
}
