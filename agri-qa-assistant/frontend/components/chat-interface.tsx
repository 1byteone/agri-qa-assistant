"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Sparkles, History, Trash2, Leaf, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
  tool_calls?: any[]
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [threadId] = useState(() => `thread_${Date.now()}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          thread_id: threadId,
        }),
      })

      if (!response.ok) throw new Error("请求失败")

      const data = await response.json()

      const assistantMessage: Message = {
        role: "assistant",
        content: data.message,
        timestamp: new Date(),
        tool_calls: data.tool_calls,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error("发送消息失败:", error)
      const errorMessage: Message = {
        role: "assistant",
        content: "抱歉，连接服务器失败，请检查网络或稍后重试。",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const clearHistory = async () => {
    try {
      await fetch(`/api/history/${threadId}`, { method: "DELETE" })
      setMessages([])
    } catch (error) {
      console.error("清空历史失败:", error)
    }
  }

  return (
    <div className="flex flex-col h-screen p-4 md:p-6 max-w-5xl mx-auto">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel rounded-2xl p-4 mb-4 flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-lg">
            <Leaf className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-lg text-gray-900">AgriQA Assistant</h1>
            <p className="text-xs text-gray-500">农业智能问答助手</p>
          </div>
        </div>
        <button
          onClick={clearHistory}
          className="p-2 rounded-xl hover:bg-white/50 transition-colors"
          title="清空对话"
        >
          <Trash2 className="w-5 h-5 text-gray-500" />
        </button>
      </motion.header>

      {/* Messages Area */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 glass-card rounded-2xl overflow-hidden relative"
      >
        <div className="h-full overflow-y-auto custom-scrollbar p-4 space-y-4">
          <AnimatePresence>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="h-full flex flex-col items-center justify-center text-center p-8"
              >
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center mb-4">
                  <Sparkles className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">有什么农业问题想问我？</h2>
                <p className="text-gray-500 text-sm max-w-md">
                  我可以帮你解答作物种植、病虫害防治、施肥灌溉、土壤管理等农业技术问题
                </p>
                <div className="mt-6 flex flex-wrap gap-2 justify-center">
                  {["水稻稻飞虱怎么防治？", "小麦什么时候追肥合适？", "玉米种植密度多少合适？"].map(
                    (suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setInput(suggestion)}
                        className="px-4 py-2 rounded-full bg-white/80 border border-gray-200 text-sm text-gray-600 hover:bg-white hover:border-blue-300 hover:text-blue-600 transition-all"
                      >
                        {suggestion}
                      </button>
                    )
                  )}
                </div>
              </motion.div>
            ) : (
              messages.map((msg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
                >
                  <div
                    className={cn(
                      "max-w-[80%] md:max-w-[70%] px-4 py-3",
                      msg.role === "user" ? "message-user" : "message-assistant"
                    )}
                  >
                    <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    {msg.tool_calls && msg.tool_calls.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-black/10">
                        <p className="text-xs opacity-70">🔧 已调用工具: {msg.tool_calls.map(tc => tc.name).join(", ")}</p>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))
            )}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="message-assistant px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span className="text-sm text-gray-500">正在思考...</span>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Input Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-4 glass-panel rounded-2xl p-2"
      >
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入农业问题..."
            className="flex-1 bg-transparent border-0 resize-none focus:outline-none focus:ring-0 px-4 py-3 text-sm md:text-base max-h-32 min-h-[48px]"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="glass-button p-3 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed mb-1"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </motion.div>
    </div>
  )
}