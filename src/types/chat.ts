import { z } from 'zod'

// Zod 스키마 정의
export const SourceSchema = z.object({
  content: z.string(),
  metadata: z.record(z.any()),
  score: z.number().optional(),
})

export const RecommendedMenuSchema = z.object({
  restaurant_name: z.string(),
  menu_name: z.string(),
  price: z.string(),
  calories: z.string(),
  address: z.string(),
  category: z.string(),
  score: z.number().optional(),
})

export const ChatResponseSchema = z.object({
  response: z.string(),
  sources: z.array(SourceSchema),
  recommended_menus: z.array(RecommendedMenuSchema),
  conversation_id: z.string(),
  timestamp: z.string(),
})

export const ChatRequestSchema = z.object({
  message: z.string().min(1),
  conversation_id: z.string().optional(),
  history: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string(),
  })).optional(),
})

// TypeScript 타입 정의
export type Source = z.infer<typeof SourceSchema>
export type RecommendedMenu = z.infer<typeof RecommendedMenuSchema>
export type ChatResponse = z.infer<typeof ChatResponseSchema>
export type ChatRequest = z.infer<typeof ChatRequestSchema>

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isLoading?: boolean
}

export interface StreamChunk {
  content: string
  done: boolean
  sources?: Source[]
}
