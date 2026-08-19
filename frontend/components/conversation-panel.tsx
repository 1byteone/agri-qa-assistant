"use client"

import { MessageSquarePlus, MoreHorizontal, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ConversationSummary {
  thread_id: string
  title: string
  last_message: string | null
  updated_at: string
  message_count: number
}

interface ConversationPanelProps {
  threads: ConversationSummary[]
  activeThreadId: string
  onCreate: () => void
  onSelect: (threadId: string) => void
  onDelete: (threadId: string) => void
}

function relativeTime(value: string) {
  const diff = Date.now() - new Date(value).getTime()
  const minutes = Math.max(0, Math.floor(diff / 60_000))
  if (minutes < 1) return "刚刚"
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  return new Intl.DateTimeFormat("zh-CN", { month: "numeric", day: "numeric" }).format(new Date(value))
}

export function ConversationPanel({ threads, activeThreadId, onCreate, onSelect, onDelete }: ConversationPanelProps) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-[#263f33]">对话记录</p>
          <p className="mt-0.5 text-xs text-[#718077]">{threads.length ? `${threads.length} 个已保存会话` : "开始新的农业咨询"}</p>
        </div>
        <button onClick={onCreate} className="icon-button h-8 w-8" title="新建对话" aria-label="新建对话">
          <MessageSquarePlus className="h-4 w-4" />
        </button>
      </div>

      <div className="custom-scrollbar scroll-boundary min-h-0 flex-1 space-y-1 overflow-y-auto p-2">
        {threads.length === 0 ? (
          <div className="px-3 py-8 text-center text-sm leading-6 text-[#7a887e]">发送第一条问题后，记录会保存在这里。</div>
        ) : threads.map((thread) => (
          <div key={thread.thread_id} className={cn("group flex items-start gap-1 rounded-md", thread.thread_id === activeThreadId ? "bg-[#e9f2e8]" : "hover:bg-[#f4f7f2]")}>
            <button onClick={() => onSelect(thread.thread_id)} className="min-w-0 flex-1 px-3 py-2.5 text-left">
              <p className="truncate text-sm font-medium text-[#31483b]">{thread.title}</p>
              <p className="mt-0.5 truncate text-xs text-[#748178]">{thread.last_message || "暂无内容"}</p>
              <p className="mt-1 text-[11px] text-[#95a198]">{relativeTime(thread.updated_at)} · {thread.message_count} 条消息</p>
            </button>
            <button onClick={() => onDelete(thread.thread_id)} className="mt-2 mr-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded text-[#9aa69e] opacity-0 transition-opacity hover:bg-white hover:text-[#a6192e] group-hover:opacity-100 focus:opacity-100" title="删除会话" aria-label={`删除会话：${thread.title}`}>
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
