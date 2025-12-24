# 프론트엔드 구현 가이드 (모바일 웹뷰용)

이 문서는 모바일 앱에 통합할 챗봇 프론트엔드를 구현하는 방법을 단계별로 설명합니다.

## 📋 목차

1. [개요](#개요)
2. [기술 스택](#기술-스택)
3. [프로젝트 구조](#프로젝트-구조)
4. [단계별 구현 가이드](#단계별-구현-가이드)
5. [모바일 최적화](#모바일-최적화)
6. [백엔드 연동](#백엔드-연동)
7. [모바일 앱 통합 방법](#모바일-앱-통합-방법)

---

## 개요

### 목표
- 모바일 웹뷰에서 동작하는 챗봇 UI 구현
- 백엔드 API와의 실시간 통신 (일반/스트리밍)
- 터치 친화적이고 반응형인 사용자 인터페이스
- 기존 모바일 앱에 웹뷰로 통합 가능

### 아키텍처
```
모바일 앱 (Native)
    ↓ (WebView)
React 웹 앱
    ↓ (HTTP/SSE)
FastAPI 백엔드
```

---

## 기술 스택

### 필수 패키지
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "typescript": "^5.0.0",
  "vite": "^5.0.0",
  "tailwindcss": "^3.4.0",
  "axios": "^1.6.0"
}
```

### 선택적 패키지 (권장)
```json
{
  "react-icons": "^4.12.0",
  "framer-motion": "^10.16.0"
}
```

---

## 프로젝트 구조

```
src/
├── App.tsx                 # 메인 앱 컴포넌트
├── main.tsx               # React 진입점
├── index.css              # 전역 스타일
├── components/
│   ├── ChatWindow.tsx     # 채팅창 컨테이너
│   ├── MessageBubble.tsx  # 메시지 버블 컴포넌트
│   └── InputForm.tsx      # 입력 폼 컴포넌트
├── hooks/
│   └── useChat.ts         # 채팅 로직 커스텀 훅
├── services/
│   └── api.ts             # API 통신 서비스
├── types/
│   └── chat.ts            # TypeScript 타입 정의
└── utils/
    └── constants.ts       # 상수 정의
```

---

## 단계별 구현 가이드

### 1단계: 프로젝트 초기 설정

#### 1-1. package.json 생성

**파일**: `package.json`

```json
{
  "name": "chatbot-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

#### 1-2. Vite 설정

**파일**: `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
```

#### 1-3. TypeScript 설정

**파일**: `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### 1-4. Tailwind CSS 설정

**파일**: `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
        }
      }
    },
  },
  plugins: [],
}
```

**파일**: `postcss.config.js`

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

### 2단계: 타입 정의

**파일**: `src/types/chat.ts`

```typescript
// 메시지 타입
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

// API 요청 타입
export interface ChatRequest {
  message: string;
  conversation_id?: string;
  history?: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
}

// API 응답 타입
export interface ChatResponse {
  response: string;
  sources: Source[];
  recommended_menus: RecommendedMenu[];
  conversation_id: string;
  timestamp: string;
}

// 소스 정보
export interface Source {
  content: string;
  metadata: {
    restaurant_name?: string;
    menu_name?: string;
    price?: number;
    calories?: number;
    address?: string;
    category?: string;
  };
  score?: number;
}

// 추천 메뉴
export interface RecommendedMenu {
  restaurant_name: string;
  menu_name: string;
  price: string;
  calories: string;
  address: string;
  category: string;
  score?: number;
}

// 스트리밍 청크
export interface StreamChunk {
  content: string;
  done: boolean;
  sources?: Source[];
}
```

---

### 3단계: API 서비스 구현

**파일**: `src/services/api.ts`

```typescript
import axios from 'axios';
import type { ChatRequest, ChatResponse, StreamChunk } from '../types/chat';

// API 기본 URL (환경 변수 또는 상수)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30초
});

/**
 * 일반 채팅 요청 (전체 응답 한 번에 받기)
 */
export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  try {
    const response = await apiClient.post<ChatResponse>('/chat', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        error.response?.data?.detail || '채팅 요청 중 오류가 발생했습니다.'
      );
    }
    throw error;
  }
}

/**
 * 스트리밍 채팅 요청 (SSE)
 */
export function streamChatMessage(
  request: ChatRequest,
  onChunk: (chunk: StreamChunk) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): () => void {
  // EventSource는 GET만 지원하므로, POST 요청은 fetch 사용
  const abortController = new AbortController();

  fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          if (onComplete) onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as StreamChunk;
              onChunk(data);
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError' && onError) {
        onError(error as Error);
      }
    });

  // 취소 함수 반환
  return () => {
    abortController.abort();
  };
}

/**
 * 헬스 체크
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await apiClient.get('/health');
    return response.status === 200;
  } catch {
    return false;
  }
}
```

---

### 4단계: 커스텀 훅 구현

**파일**: `src/hooks/useChat.ts`

```typescript
import { useState, useCallback, useRef } from 'react';
import type { Message, ChatRequest, StreamChunk } from '../types/chat';
import { sendChatMessage, streamChatMessage } from '../services/api';

interface UseChatOptions {
  useStreaming?: boolean; // 스트리밍 사용 여부
  onError?: (error: Error) => void;
}

export function useChat(options: UseChatOptions = {}) {
  const { useStreaming = true, onError } = options;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();
  
  const abortStreamRef = useRef<(() => void) | null>(null);

  /**
   * 메시지 전송 (일반 또는 스트리밍)
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      // 사용자 메시지 추가
      const userMessage: Message = {
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      // 이전 메시지를 history로 변환
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const request: ChatRequest = {
        message: content.trim(),
        conversation_id: conversationId,
        history,
      };

      try {
        if (useStreaming) {
          // 스트리밍 방식
          let assistantMessage: Message = {
            role: 'assistant',
            content: '',
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, assistantMessage]);

          abortStreamRef.current = streamChatMessage(
            request,
            (chunk: StreamChunk) => {
              if (chunk.content) {
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMessage = newMessages[newMessages.length - 1];
                  if (lastMessage.role === 'assistant') {
                    lastMessage.content += chunk.content;
                  }
                  return newMessages;
                });
              }

              if (chunk.done) {
                setIsLoading(false);
                if (chunk.sources) {
                  // 소스 정보는 필요시 처리
                }
              }
            },
            (err) => {
              setError(err);
              setIsLoading(false);
              if (onError) onError(err);
            },
            () => {
              setIsLoading(false);
            }
          );
        } else {
          // 일반 방식
          const response = await sendChatMessage(request);

          const assistantMessage: Message = {
            role: 'assistant',
            content: response.response,
            timestamp: new Date(response.timestamp),
          };

          setMessages((prev) => [...prev, assistantMessage]);

          if (response.conversation_id) {
            setConversationId(response.conversation_id);
          }

          setIsLoading(false);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error('알 수 없는 오류');
        setError(error);
        setIsLoading(false);
        if (onError) onError(error);
      }
    },
    [messages, conversationId, isLoading, useStreaming, onError]
  );

  /**
   * 대화 초기화
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
    setError(null);
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
    }
  }, []);

  /**
   * 스트리밍 취소
   */
  const cancelStream = useCallback(() => {
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
      setIsLoading(false);
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    conversationId,
    sendMessage,
    clearMessages,
    cancelStream,
  };
}
```

---

### 5단계: 컴포넌트 구현

#### 5-1. MessageBubble 컴포넌트

**파일**: `src/components/MessageBubble.tsx`

```typescript
import React from 'react';
import type { Message } from '../types/chat';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex w-full mb-4 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>
        {message.timestamp && (
          <p
            className={`text-xs mt-1 ${
              isUser ? 'text-blue-100' : 'text-gray-500'
            }`}
          >
            {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
    </div>
  );
};
```

#### 5-2. InputForm 컴포넌트

**파일**: `src/components/InputForm.tsx`

```typescript
import React, { useState, useRef, useEffect } from 'react';

interface InputFormProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export const InputForm: React.FC<InputFormProps> = ({
  onSend,
  isLoading = false,
  disabled = false,
  placeholder = '메시지를 입력하세요...',
}) => {
  const [inputValue, setInputValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && !disabled) {
      onSend(inputValue);
      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 p-4 bg-white border-t border-gray-200"
    >
      <textarea
        ref={textareaRef}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading || disabled}
        rows={1}
        className="flex-1 resize-none border border-gray-300 rounded-2xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed max-h-32 overflow-y-auto"
        style={{ minHeight: '44px' }}
      />
      <button
        type="submit"
        disabled={!inputValue.trim() || isLoading || disabled}
        className="bg-blue-500 text-white rounded-full p-3 disabled:bg-gray-300 disabled:cursor-not-allowed active:bg-blue-600 transition-colors"
        aria-label="전송"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </form>
  );
};
```

#### 5-3. ChatWindow 컴포넌트

**파일**: `src/components/ChatWindow.tsx`

```typescript
import React, { useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { InputForm } from './InputForm';

export const ChatWindow: React.FC = () => {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat({
    useStreaming: true,
    onError: (err) => {
      console.error('Chat error:', err);
    },
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가되면 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-gray-800">전주 음식점 챗봇</h1>
        <button
          onClick={clearMessages}
          className="text-sm text-gray-600 hover:text-gray-800"
        >
          초기화
        </button>
      </header>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>안녕하세요! 전주 음식점을 추천해드립니다. 무엇을 도와드릴까요?</p>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-red-600 text-sm">{error.message}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <InputForm
        onSend={sendMessage}
        isLoading={isLoading}
        placeholder="음식점이나 메뉴를 검색해보세요..."
      />
    </div>
  );
};
```

#### 5-4. App 컴포넌트

**파일**: `src/App.tsx`

```typescript
import React from 'react';
import { ChatWindow } from './components/ChatWindow';
import './index.css';

function App() {
  return (
    <div className="App">
      <ChatWindow />
    </div>
  );
}

export default App;
```

#### 5-5. 진입점

**파일**: `src/main.tsx`

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

#### 5-6. 전역 스타일

**파일**: `src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    box-sizing: border-box;
  }

  html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
  }

  #root {
    height: 100%;
    width: 100%;
  }

  /* 모바일 터치 최적화 */
  * {
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }

  /* 스크롤바 스타일링 (선택적) */
  ::-webkit-scrollbar {
    width: 6px;
  }

  ::-webkit-scrollbar-track {
    background: transparent;
  }

  ::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }
}

@layer utilities {
  /* 커스텀 유틸리티 클래스 */
  .safe-area-top {
    padding-top: env(safe-area-inset-top);
  }

  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
```

#### 5-7. HTML 진입점

**파일**: `index.html`

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <title>전주 음식점 챗봇</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

## 모바일 최적화

### 1. 뷰포트 설정
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
```

### 2. 터치 최적화
- `touch-action: manipulation` 적용
- `-webkit-tap-highlight-color: transparent` 적용
- 최소 터치 영역 44x44px 유지

### 3. 키보드 처리
- 입력 필드 포커스 시 자동 스크롤
- 키보드가 올라와도 입력 영역이 가려지지 않도록 처리

### 4. Safe Area 처리
- iPhone의 노치 영역 고려
- `env(safe-area-inset-*)` 사용

### 5. 성능 최적화
- 이미지 lazy loading
- 메시지 가상화 (많은 메시지가 있을 경우)
- 디바운싱/스로틀링 적용

---

## 백엔드 연동

### 환경 변수 설정

**파일**: `.env`

```env
VITE_API_URL=http://localhost:8000
```

**파일**: `.env.production`

```env
VITE_API_URL=https://your-api-domain.com
```

### CORS 설정 확인

백엔드에서 모바일 앱의 도메인을 허용하도록 설정:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-mobile-app-domain.com",
        # 모바일 앱의 실제 도메인 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 모바일 앱 통합 방법

### 방법 1: WebView 사용 (권장)

#### Android (Kotlin/Java)
```kotlin
// WebView 설정
val webView = findViewById<WebView>(R.id.webview)
webView.settings.apply {
    javaScriptEnabled = true
    domStorageEnabled = true
    loadWithOverviewMode = true
    useWideViewPort = true
}

// URL 로드
webView.loadUrl("https://your-chatbot-domain.com")
```

#### iOS (Swift)
```swift
import WebKit

let webView = WKWebView(frame: view.bounds)
webView.configuration.preferences.javaScriptEnabled = true
view.addSubview(webView)

let url = URL(string: "https://your-chatbot-domain.com")!
webView.load(URLRequest(url: url))
```

### 방법 2: React Native WebView

```bash
npm install react-native-webview
```

```tsx
import { WebView } from 'react-native-webview';

<WebView
  source={{ uri: 'https://your-chatbot-domain.com' }}
  style={{ flex: 1 }}
  javaScriptEnabled={true}
  domStorageEnabled={true}
  allowsInlineMediaPlayback={true}
/>
```

### 방법 3: 하이브리드 앱 (Cordova/PhoneGap)

```bash
npm install -g cordova
cordova create chatbot-app
cd chatbot-app
cordova platform add android ios
```

빌드된 웹 앱을 `www` 폴더에 복사

---

## 빌드 및 배포

### 개발 서버 실행
```bash
npm install
npm run dev
```

### 프로덕션 빌드
```bash
npm run build
```

빌드 결과는 `dist/` 폴더에 생성됩니다.

### 정적 호스팅
- **Netlify**: `dist` 폴더 배포
- **Vercel**: 자동 배포
- **GitHub Pages**: `dist` 폴더 배포
- **자체 서버**: Nginx/Apache로 `dist` 폴더 서빙

---

## 테스트 체크리스트

### 기능 테스트
- [ ] 메시지 전송 및 수신
- [ ] 스트리밍 응답 동작
- [ ] 대화 기록 유지
- [ ] 에러 처리
- [ ] 로딩 상태 표시

### 모바일 테스트
- [ ] 터치 반응성
- [ ] 키보드 처리
- [ ] 스크롤 동작
- [ ] 다양한 화면 크기
- [ ] Safe Area 처리

### 성능 테스트
- [ ] 초기 로딩 시간
- [ ] 메시지 렌더링 성능
- [ ] 메모리 사용량
- [ ] 네트워크 요청 최적화

---

## 문제 해결

### 1. CORS 오류
- 백엔드 CORS 설정 확인
- 프론트엔드 도메인을 허용 목록에 추가

### 2. 스트리밍이 동작하지 않음
- EventSource 대신 fetch API 사용 (POST 요청 지원)
- 네트워크 탭에서 응답 확인

### 3. 모바일에서 레이아웃 깨짐
- 뷰포트 메타 태그 확인
- Tailwind의 반응형 클래스 사용
- 실제 기기에서 테스트

### 4. 키보드가 입력 영역을 가림
- `window.scrollTo()` 사용
- CSS `position: fixed` 대신 `sticky` 사용

---

## 참고 자료

- [React 공식 문서](https://react.dev)
- [Vite 공식 문서](https://vitejs.dev)
- [Tailwind CSS 문서](https://tailwindcss.com)
- [WebView 가이드](https://developer.mozilla.org/en-US/docs/Web/API/WebView)

---

**작성일**: 2024년  
**버전**: 1.0.0

