"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { AnimatePresence, motion } from "framer-motion"
import {
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ClipboardList,
  AlertCircle,
  FileText,
  FlaskConical,
  Leaf,
  Loader2,
  Menu,
  MessageCircleQuestion,
  MessageSquareMore,
  MessageSquarePlus,
  PanelLeftClose,
  PanelRightClose,
  Paperclip,
  Send,
  Square,
  Sparkles,
  StopCircle,
  Trash2,
  X,
} from "lucide-react"
import { AchievementFooter } from "@/components/achievement-footer"
import { ConversationPanel, type ConversationSummary } from "@/components/conversation-panel"
import { GenerativeUi, getToolStatusCopy, type GeneratedUiEvent } from "@/components/generative-ui"
import { MarkdownMessage, stripToolCallMarkers } from "@/components/markdown-message"
import { KnowledgePanel } from "@/components/knowledge-panel"
import { RagTestPanel } from "@/components/rag-test-panel"
import { SidebarContext, useSidebar } from "@/lib/sidebar-context"
import { consumeSSE, type StreamEvent } from "@/lib/sse"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  completedAt?: Date
  status?: "streaming" | "complete" | "cancelled" | "error"
  completionStatus?: "complete" | "fallback" | "error" | "guarded"
  answerMode?: AnswerMode
  toolCalls?: Array<{ name: string; args?: Record<string, unknown> }>
  generatedUi?: GeneratedUiEvent[]
}

type AnswerMode = "professional" | "brief"

interface AttachmentAnalysis {
  filename: string
  extension: string
  content_type: string
  bytes: number
  characters: number
  estimated_chunks: number
  content_hash: string
  preview: string
  eligible: boolean
  confidence: number
  matched_terms: string[]
  non_agriculture_terms: string[]
  reason: string
  ingested?: boolean
  duplicate?: boolean
  added_chunks?: number
  requires_confirmation?: boolean
}

const slogans = [
  "面向作物种植、病虫害与农事管理的知识服务",
  "厚德博学，抱朴守真",
  "以科技兴农强农",
]

const QUICK_QUESTIONS = [
  "水稻稻飞虱怎么防治？",
  "小麦什么时候追肥？",
  "玉米种植密度多少？",
]

const RAG_FILE_EXTENSIONS = new Set([".txt", ".md", ".markdown", ".csv", ".html", ".htm", ".json", ".docx", ".pdf"])
const RAG_MAX_FILE_BYTES = 15 * 1024 * 1024

const cropHighlights = [
  {
    tag: "水稻育种",
    title: "籼型杂交水稻",
    desc: "江农科研团队在杂交水稻育种与推广领域持续深耕。",
    image: "/crops/hybrid-rice.jpg",
  },
  {
    tag: "高产栽培",
    title: "双季超级稻技术",
    desc: "围绕高产稳产，形成适宜本地的栽培技术体系。",
    image: "/crops/super-rice.jpg",
  },
]

function PanelHeading({ children }: { children: React.ReactNode }) {
  return <p className="section-kicker mb-3">{children}</p>
}

function formatMessageTime(timestamp: Date) {
  return new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit" }).format(timestamp)
}

function MessageStatus({ status, detail, timestamp, completionStatus }: { status: Message["status"]; detail?: string; timestamp: Date; completionStatus?: Message["completionStatus"] }) {
  if (!status) return null

  const config = {
    streaming: {
      label: "回答中",
      icon: Loader2,
      className: "message-status-streaming",
      live: "polite" as const,
      detail: detail || "正在生成农技建议",
    },
    complete: {
      label: "回答完成",
      icon: CheckCircle2,
      className: "message-status-complete",
      live: "polite" as const,
      detail: `${completionStatus === "fallback" ? "已完成 · 备用回答通道 · " : "已完成 · "}${formatMessageTime(timestamp)}`,
    },
    cancelled: {
      label: "已停止生成",
      icon: StopCircle,
      className: "message-status-cancelled",
      live: "polite" as const,
      detail: "本次回答未继续生成",
    },
    error: {
      label: "回答未完整返回",
      icon: AlertCircle,
      className: "message-status-error",
      live: "assertive" as const,
      detail: "请检查服务后重试",
    },
  }[status]
  const Icon = config.icon

  return (
    <div className={`message-status ${config.className}`} role="status" aria-live={config.live}>
      <span className="flex min-w-0 items-center gap-2">
        <Icon className={cn("h-4 w-4 shrink-0", status === "streaming" && "animate-spin")} aria-hidden="true" />
        <span className="font-semibold">{config.label}</span>
        <span className="message-status-detail truncate">{config.detail}</span>
      </span>
      {status === "streaming" && <span className="message-status-track" aria-hidden="true"><span /></span>}
    </div>
  )
}

function LeftPanel({ mobile = false }: { mobile?: boolean }) {
  const { leftOpen, setLeftOpen } = useSidebar()
  const shouldRender = mobile || leftOpen
  const panelContent = (
    <>
      <div className="border-b pb-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <div className="overflow-hidden rounded-md bg-[#17613c] px-3 py-2">
          <img src="/jxau-official-logo.png" alt="江西农业大学" className="h-auto w-full" />
        </div>
      </div>

      <div className="border-l-2 border-[#a6192e] bg-[#fdf7f8] px-3 py-2.5">
        <p className="text-sm font-semibold text-[#273f33]">团结 · 勤奋 · 求实 · 创新</p>
        <p className="mt-1 text-xs leading-5 text-[#6c766f]">江西农业大学 CropWise 农业知识问答平台</p>
      </div>

      <div>
        <PanelHeading>学校简介</PanelHeading>
        <p className="text-sm leading-6 text-[#5c6c63]">
          溯源于1905年江西农林学堂，学校以农为优势、以生物技术为特色，服务乡村全面振兴。
        </p>
      </div>

      <div>
        <PanelHeading>江农特色知识域</PanelHeading>
        <div className="flex flex-wrap gap-1.5" aria-label="江西农业大学特色知识域">
          {[
            "水稻与南方粮油",
            "家猪育种与动物健康",
            "鄱阳湖生态",
            "果蔬采后与脐橙",
            "农业资源环境",
            "现代农业装备",
          ].map((item) => <span key={item} className="rounded-md border border-[#d8e4d8] bg-[#f6faf5] px-2 py-1 text-[11px] text-[#587363]">{item}</span>)}
        </div>
      </div>

      <div>
        <PanelHeading>服务入口</PanelHeading>
        <div className="space-y-1.5">
          {[
            { label: "作物诊断", href: "/crop-diagnosis", icon: MessageCircleQuestion },
            { label: "农时查询", href: "/farming-calendar", icon: CalendarDays },
            { label: "政策咨询", href: "/policy", icon: FileText },
            { label: "证据评测", href: "/evaluations", icon: FlaskConical },
          ].map(({ label, href, icon: Icon }) => (
            <Link
              key={label}
              href={href}
              className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-left text-sm text-[#415249] transition-colors hover:bg-[#f0f5ee] hover:text-[#17613c]"
            >
              <Icon className="h-4 w-4" strokeWidth={1.8} />
              {label}
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-auto border-t pt-4">
        <p className="text-xs leading-5 text-[#718077]">农业技术建议仅供生产决策参考，请结合当地植保与农技部门指导。</p>
      </div>
    </>
  )

  if (!shouldRender) return null

  if (mobile) {
    return <div className="flex h-full flex-col gap-5">{panelContent}</div>
  }

  return (
    <AnimatePresence>
      {leftOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0, x: -12 }}
          animate={{ width: 272, opacity: 1, x: 0 }}
          exit={{ width: 0, opacity: 0, x: -12 }}
          transition={{ duration: 0.22 }}
          className="hidden min-h-0 shrink-0 overflow-hidden xl:block"
        >
          <div className="sidebar-panel scroll-boundary flex h-full flex-col gap-5 overflow-y-auto rounded-lg p-4 custom-scrollbar">
            {panelContent}
            <button onClick={() => setLeftOpen(false)} className="flex items-center gap-1 text-left text-xs text-[#718077] hover:text-[#17613c]">
              <ChevronLeft className="h-3.5 w-3.5" /> 收起侧栏
            </button>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}

function EmptyCropCard() {
  const [index, setIndex] = useState(0)
  const current = cropHighlights[index]

  return (
    <section className="mt-6 w-full max-w-xl border-t pt-5 text-left">
      <div className="mb-3 flex items-center justify-between">
        <p className="section-kicker">江农作物科技</p>
        <div className="flex gap-1">
          {cropHighlights.map((item, itemIndex) => (
            <button
              key={item.title}
              onClick={() => setIndex(itemIndex)}
              aria-label={`查看${item.title}`}
              className={cn("h-2 w-2 rounded-full transition-colors", itemIndex === index ? "bg-[#17613c]" : "bg-[#d3ddd1] hover:bg-[#9bb39f]")}
            />
          ))}
        </div>
      </div>
      <div className="grid overflow-hidden rounded-lg border bg-white sm:grid-cols-[176px_1fr]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={current.image} alt="水稻试验田" className="h-28 w-full object-cover sm:h-full" />
        <div className="p-4">
          <p className="text-xs font-medium text-[#17613c]">{current.tag}</p>
          <h3 className="mt-1 text-base font-semibold text-[#243b31]">{current.title}</h3>
          <p className="mt-1 text-sm leading-5 text-[#66756c]">{current.desc}</p>
        </div>
      </div>
    </section>
  )
}

function FieldBrief({ onUsePrompt }: { onUsePrompt: (prompt: string) => void }) {
  const [open, setOpen] = useState(false)
  const [scenario, setScenario] = useState<"diagnosis" | "nutrition" | "calendar" | "policy">("diagnosis")
  const [crop, setCrop] = useState("水稻")
  const [region, setRegion] = useState("江西")
  const [stage, setStage] = useState("分蘖期")
  const [detail, setDetail] = useState("")

  const scenarios = [
    { id: "diagnosis" as const, label: "病虫害诊断", icon: MessageCircleQuestion, stageLabel: "生育期", detailLabel: "症状与扩散", detailPlaceholder: "如：叶尖发黄，近三天扩散到约一成植株" },
    { id: "nutrition" as const, label: "施肥灌溉", icon: Leaf, stageLabel: "生育期", detailLabel: "目标或异常", detailPlaceholder: "如：叶色偏淡，想制定追肥和灌溉安排" },
    { id: "calendar" as const, label: "农时计划", icon: CalendarDays, stageLabel: "当前农时", detailLabel: "计划目标", detailPlaceholder: "如：安排早稻播种、移栽和第一次追肥" },
    { id: "policy" as const, label: "政策核验", icon: FileText, stageLabel: "政策主题", detailLabel: "需要核验的事项", detailPlaceholder: "如：江西稻谷绿色高产项目的申报条件和官方入口" },
  ]
  const currentScenario = scenarios.find((item) => item.id === scenario) ?? scenarios[0]

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!detail.trim()) return
    const scenarioInstruction = {
      diagnosis: "请优先区分可能原因，给出现场排查、处理建议、用药安全边界和复查指标，不要直接下确诊结论。",
      nutrition: "请给出施肥/灌溉决策依据、建议时机和复查指标；涉及用量时说明需要结合测土、品种和当地登记信息。",
      calendar: "请按时间顺序给出农事安排、关键前置条件、天气风险和错过窗口后的替代方案。",
      policy: "请优先引用官方政策或资料入口，区分已核验信息和待确认事项，不要编造申报条件或截止日期。",
    }[scenario]
    onUsePrompt(`农业场景：${currentScenario.label}。地区：${region}。涉及作物或项目：${crop}。${currentScenario.stageLabel}：${stage}。${currentScenario.detailLabel}：${detail.trim()}。${scenarioInstruction}请按现场摘要、优先判断、现在做什么、风险边界、复查节点五段式回答，并列出需要我补充的信息。`)
    setOpen(false)
  }

  return (
    <section className="mt-7 border-y border-[#d8e0d6] py-4">
      <button onClick={() => setOpen((value) => !value)} className="flex min-h-11 w-full items-center justify-between text-left" aria-expanded={open}>
        <span className="flex items-center gap-2.5">
          <span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#e7f1e8] text-[#17613c]"><ClipboardList className="h-4 w-4" /></span>
          <span><span className="block text-sm font-semibold text-[#263f33]">选择农业场景</span><span className="mt-0.5 block text-xs text-[#718077]">用场景化信息生成更可执行、可复查的问题</span></span>
        </span>
        <ChevronLeft className={cn("h-4 w-4 text-[#718077] transition-transform", open ? "-rotate-90" : "rotate-180")} />
      </button>
      {open && (
        <form onSubmit={submit} className="mt-4 grid gap-3 border-t border-[#e5ebe3] pt-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <p className="text-xs font-medium text-[#526158]">问题场景</p>
            <div className="mt-1.5 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
              {scenarios.map((item) => {
                const Icon = item.icon
                return <button key={item.id} type="button" onClick={() => setScenario(item.id)} aria-pressed={scenario === item.id} className={cn("flex min-h-11 items-center justify-center gap-1.5 rounded-md border px-2 text-xs font-medium transition-colors", scenario === item.id ? "border-[#17613c] bg-[#eef6ed] text-[#17613c]" : "bg-white text-[#66756c] hover:border-[#9db9a6] hover:text-[#17613c]")}><Icon className="h-3.5 w-3.5" />{item.label}</button>
              })}
            </div>
          </div>
          <label className="text-xs font-medium text-[#526158]">作物<input value={crop} onChange={(event) => setCrop(event.target.value)} className="field-input" placeholder="如：水稻" /></label>
          <label className="text-xs font-medium text-[#526158]">地区<input value={region} onChange={(event) => setRegion(event.target.value)} className="field-input" placeholder="如：江西南昌" /></label>
          <label className="text-xs font-medium text-[#526158]">{currentScenario.stageLabel}<input value={stage} onChange={(event) => setStage(event.target.value)} className="field-input" placeholder={currentScenario.stageLabel === "生育期" ? "如：分蘖期" : "如：2026 年申报"} /></label>
          <label className="text-xs font-medium text-[#526158] sm:col-span-2">{currentScenario.detailLabel}<textarea value={detail} onChange={(event) => setDetail(event.target.value)} className="field-input min-h-20 resize-y" placeholder={currentScenario.detailPlaceholder} required /></label>
          <div className="flex items-center justify-between gap-3 sm:col-span-2"><p className="text-xs leading-5 text-[#87938b]">系统会把这些信息整理成一条可追踪的农业问题。</p><button type="submit" className="primary-button min-h-11 px-4">生成田间问题</button></div>
        </form>
      )}
    </section>
  )
}

export function ChatInterface() {
  const [leftOpen, setLeftOpen] = useState(false)
  const [rightOpen, setRightOpen] = useState(false)
  const [mobileLeftOpen, setMobileLeftOpen] = useState(false)
  const [sessionsOpen, setSessionsOpen] = useState(false)
  const [mobileSessionsOpen, setMobileSessionsOpen] = useState(false)
  const [mobileRightOpen, setMobileRightOpen] = useState(false)
  const [ragTestOpen, setRagTestOpen] = useState(false)
  const [threads, setThreads] = useState<ConversationSummary[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const messagesRef = useRef<Message[]>([])
  const [input, setInput] = useState("")
  const [answerMode, setAnswerMode] = useState<AnswerMode>("professional")
  const [isLoading, setIsLoading] = useState(false)
  const [streamStatus, setStreamStatus] = useState("")
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)
  const [threadId, setThreadId] = useState(() => `thread_${crypto.randomUUID()}`)
  const [knowledgeStatus, setKnowledgeStatus] = useState<{ total_documents: number; embedding_mode?: string } | null>(null)
  const [attachment, setAttachment] = useState<File | null>(null)
  const [attachmentAnalysis, setAttachmentAnalysis] = useState<AttachmentAnalysis | null>(null)
  const [attachmentBusy, setAttachmentBusy] = useState(false)
  const [attachmentError, setAttachmentError] = useState("")
  const [dragActive, setDragActive] = useState(false)
  const [sloganIndex, setSloganIndex] = useState(0)
  const [titleMood, setTitleMood] = useState<"idle" | "loading" | "done" | "guard" | "error">("idle")
  const [terminologyEnabled, setTerminologyEnabled] = useState(false)
  const restoredThreadRef = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messageScrollRef = useRef<HTMLDivElement>(null)
  const shouldFollowMessagesRef = useRef(true)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dragDepthRef = useRef(0)
  const abortControllerRef = useRef<AbortController | null>(null)
  const activeAssistantIdRef = useRef<string | null>(null)
  const typewriterQueueRef = useRef("")
  const typewriterFrameRef = useRef<number | null>(null)
  const typewriterResolversRef = useRef<Array<() => void>>([])
  const cancelledRef = useRef(false)

  const resizeInput = useCallback(() => {
    const textarea = inputRef.current
    if (!textarea) return
    textarea.style.height = "auto"
    const maxHeight = 144
    textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 46), maxHeight)}px`
  }, [])

  useEffect(() => {
    resizeInput()
  }, [input, resizeInput])

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  useEffect(() => {
    if (messages.length > 0) setRightOpen(true)
  }, [messages.length])

  useEffect(() => {
    if (!shouldFollowMessagesRef.current) return
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages])

  useEffect(() => {
    const timer = setInterval(() => setSloganIndex((value) => (value + 1) % slogans.length), 4200)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // A dropped file must never navigate the SPA to the browser's file viewer.
    const preventFileNavigation = (event: DragEvent) => {
      if (event.dataTransfer?.types.includes("Files")) event.preventDefault()
    }
    window.addEventListener("dragover", preventFileNavigation)
    window.addEventListener("drop", preventFileNavigation)
    return () => {
      window.removeEventListener("dragover", preventFileNavigation)
      window.removeEventListener("drop", preventFileNavigation)
    }
  }, [])

  useEffect(() => {
    const titles = {
      idle: "CropWise · 江西农业大学农业问答",
      loading: "(•̀ᴗ•́)و CropWise 正在处理",
      done: "(^_^) CropWise · 已完成",
      guard: "(￣▽￣) CropWise · 农业范围提示",
      error: "(｡•́︿•̀｡) CropWise · 请求中断",
    }
    document.title = titles[titleMood]
    if (titleMood === "idle") return
    const timer = window.setTimeout(() => setTitleMood("idle"), titleMood === "loading" ? 1200 : 2600)
    return () => window.clearTimeout(timer)
  }, [titleMood])

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return
      setMobileSessionsOpen(false)
      setMobileLeftOpen(false)
      setMobileRightOpen(false)
      setRagTestOpen(false)
    }
    window.addEventListener("keydown", handleEscape)
    return () => window.removeEventListener("keydown", handleEscape)
  }, [])

  const refreshThreads = useCallback(async () => {
    try {
      const response = await fetch("/api/threads")
      if (!response.ok) throw new Error("无法读取会话列表")
      const data = await response.json() as { threads?: ConversationSummary[] }
      setThreads(Array.isArray(data.threads) ? data.threads : [])
    } catch {
      // The chat itself remains usable when the history service is temporarily unavailable.
    }
  }, [])

  useEffect(() => {
    const savedThreadId = window.localStorage.getItem("cropwise-active-thread")
    if (savedThreadId) setThreadId(savedThreadId)
    const savedAnswerMode = window.localStorage.getItem("cropwise-answer-mode")
    if (savedAnswerMode === "professional" || savedAnswerMode === "brief") setAnswerMode(savedAnswerMode)
    const prompt = new URLSearchParams(window.location.search).get("prompt")
    if (prompt) setInput(prompt)
    void refreshThreads()
    void fetch("/api/knowledge-base/status")
      .then((response) => response.ok ? response.json() : null)
      .then((status) => setKnowledgeStatus(status))
      .catch(() => setKnowledgeStatus(null))
  }, [refreshThreads])

  const changeAnswerMode = useCallback((mode: AnswerMode) => {
    setAnswerMode(mode)
    window.localStorage.setItem("cropwise-answer-mode", mode)
  }, [])

  useEffect(() => {
    window.localStorage.setItem("cropwise-active-thread", threadId)
  }, [threadId])

  const settleTypewriter = useCallback(() => {
    const resolvers = typewriterResolversRef.current.splice(0)
    resolvers.forEach((resolve) => resolve())
  }, [])

  const drainTypewriter = useCallback(() => {
    if (typewriterFrameRef.current !== null) return

    const tick = () => {
      const assistantId = activeAssistantIdRef.current
      const queue = typewriterQueueRef.current
      if (!assistantId || !queue) {
        typewriterFrameRef.current = null
        settleTypewriter()
        return
      }

      // Keep the animation tactile at normal speed, but catch up when the network outruns the UI.
      const characters = Math.min(14, Math.max(1, Math.ceil(queue.length / 24)))
      const nextText = queue.slice(0, characters)
      typewriterQueueRef.current = queue.slice(characters)
      setMessages((current) => current.map((message) => (
        message.id === assistantId ? { ...message, content: message.content + nextText } : message
      )))
      typewriterFrameRef.current = requestAnimationFrame(tick)
    }

    typewriterFrameRef.current = requestAnimationFrame(tick)
  }, [settleTypewriter])

  const waitForTypewriter = useCallback(() => new Promise<void>((resolve) => {
    if (!typewriterQueueRef.current && typewriterFrameRef.current === null) {
      resolve()
      return
    }
    typewriterResolversRef.current.push(resolve)
  }), [])

  const clearTypewriter = useCallback(() => {
    typewriterQueueRef.current = ""
    if (typewriterFrameRef.current !== null) cancelAnimationFrame(typewriterFrameRef.current)
    typewriterFrameRef.current = null
    settleTypewriter()
  }, [settleTypewriter])

  useEffect(() => () => {
    abortControllerRef.current?.abort()
    clearTypewriter()
  }, [clearTypewriter])

  const addGeneratedUi = useCallback((assistantId: string, generatedUi: GeneratedUiEvent) => {
    setMessages((current) => current.map((message) => (
      message.id === assistantId
        ? {
            ...message,
            generatedUi: (() => {
              const currentUi = message.generatedUi ?? []
              // These events describe one evolving state, so replace the
              // previous snapshot instead of creating duplicate peer cards.
              const sameEvent = (item: GeneratedUiEvent) => generatedUi.component === "tool-status"
                ? item.component === "tool-status" && item.props.name === generatedUi.props.name
                : item.component === generatedUi.component
              const existingIndex = currentUi.findIndex(sameEvent)
              if (existingIndex === -1) return [...currentUi, generatedUi]
              return currentUi.map((item, index) => index === existingIndex ? generatedUi : item)
            })(),
          }
        : message
    )))
  }, [])

  const readUploadError = async (response: Response) => {
    try {
      const payload = await response.json() as { detail?: unknown }
      if (typeof payload.detail === "string") return payload.detail
      if (payload.detail && typeof payload.detail === "object" && typeof (payload.detail as { reason?: unknown }).reason === "string") return (payload.detail as { reason: string }).reason
    } catch {
      // Fall through to a stable user-facing message.
    }
    return `文档处理失败（${response.status}）`
  }

  const analyzeAttachment = async (file: File, notice?: string) => {
    setAttachmentBusy(true)
    setAttachmentError("")
    setAttachmentAnalysis(null)
    const formData = new FormData()
    formData.append("file", file)
    try {
      const response = await fetch("/api/knowledge-base/documents/analyze", { method: "POST", body: formData })
      if (!response.ok) throw new Error(await readUploadError(response))
      setAttachmentAnalysis(await response.json() as AttachmentAnalysis)
      if (notice) setAttachmentError(notice)
    } catch (error) {
      setAttachmentError(error instanceof Error ? error.message : "文档解析失败，请重试")
    } finally {
      setAttachmentBusy(false)
    }
  }

  const prepareAttachment = (file: File, notice?: string) => {
    const extension = `.${file.name.split(".").pop()?.toLowerCase() || ""}`
    if (!RAG_FILE_EXTENSIONS.has(extension)) {
      setAttachment(file)
      setAttachmentAnalysis(null)
      setAttachmentError(notice ? `${notice} 暂不支持该文件格式，请拖入 TXT、Markdown、CSV、HTML、JSON、DOCX 或 PDF。` : "暂不支持该文件格式，请拖入 TXT、Markdown、CSV、HTML、JSON、DOCX 或 PDF。")
      return
    }
    if (file.size > RAG_MAX_FILE_BYTES) {
      setAttachment(file)
      setAttachmentAnalysis(null)
      setAttachmentError(notice ? `${notice} 文件超过 15MB 大小限制，请压缩后重试。` : "文件超过 15MB 大小限制，请压缩后重试。")
      return
    }
    setAttachment(file)
    if (notice) setAttachmentError(notice)
    void analyzeAttachment(file, notice)
  }

  const handleAttachmentChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return
    prepareAttachment(file)
  }

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.dataTransfer.types.includes("Files")) return
    event.preventDefault()
    dragDepthRef.current += 1
    setDragActive(true)
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.dataTransfer.types.includes("Files")) return
    event.preventDefault()
    event.dataTransfer.dropEffect = "copy"
  }

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.dataTransfer.types.includes("Files")) return
    event.preventDefault()
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1)
    if (dragDepthRef.current === 0) setDragActive(false)
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    if (!event.dataTransfer.types.includes("Files")) return
    event.preventDefault()
    dragDepthRef.current = 0
    setDragActive(false)
    const files = Array.from(event.dataTransfer.files)
    if (files.length === 0) return
    const hasExtraFiles = files.length > 1
    prepareAttachment(files[0], hasExtraFiles ? "一次只处理一个文档，已选择第一个文件进行解析。" : undefined)
  }

  const ingestAttachment = async () => {
    if (!attachment || !attachmentAnalysis?.eligible || attachmentBusy) return
    setAttachmentBusy(true)
    setAttachmentError("")
    const formData = new FormData()
    formData.append("file", attachment)
    formData.append("confirm", "true")
    try {
      const response = await fetch("/api/knowledge-base/documents", { method: "POST", body: formData })
      if (!response.ok) throw new Error(await readUploadError(response))
      const result = await response.json() as AttachmentAnalysis
      setAttachmentAnalysis(result)
      void fetch("/api/knowledge-base/status").then((statusResponse) => statusResponse.ok ? statusResponse.json() : null).then((status) => status && setKnowledgeStatus(status)).catch(() => undefined)
    } catch (error) {
      setAttachmentError(error instanceof Error ? error.message : "文档入库失败，请重试")
    } finally {
      setAttachmentBusy(false)
    }
  }

  const clearAttachment = () => {
    setAttachment(null)
    setAttachmentAnalysis(null)
    setAttachmentError("")
  }

  const handleStreamEvent = useCallback((assistantId: string, event: StreamEvent) => {
    if (event.type === "guard") {
      setTitleMood("guard")
      const recommendations = Array.isArray(event.recommendations)
        ? event.recommendations.filter((item): item is string => typeof item === "string")
        : []
      addGeneratedUi(assistantId, {
        component: "domain-guard",
        props: {
          category: typeof event.category === "string" ? event.category : "out-of-scope",
          reason: typeof event.reason === "string" ? event.reason : "当前问题暂不在农业知识服务范围内",
          scope: typeof event.scope === "string" ? event.scope : "农业知识与农业生产服务",
          recommendations,
        },
      })
      setStreamStatus("已按农业领域边界拦截")
      return
    }

    if (event.type === "status" && typeof event.message === "string") {
      setStreamStatus(event.message)
      return
    }

    if (event.type === "mode") {
      if (event.mode === "professional" || event.mode === "brief") {
        setAnswerMode(event.mode)
        setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, answerMode: event.mode as AnswerMode } : message))
      }
      return
    }

    if (event.type === "answer-replace" && typeof event.text === "string") {
      clearTypewriter()
      setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, content: event.text as string } : message))
      return
    }

    if (event.type === "delta" && typeof event.text === "string") {
      typewriterQueueRef.current += event.text
      drainTypewriter()
      return
    }

    if (event.type === "tool" && typeof event.name === "string" && (event.status === "running" || event.status === "complete")) {
      addGeneratedUi(assistantId, { component: "tool-status", props: {
        name: event.name,
        status: event.status,
        ok: typeof event.ok === "boolean" ? event.ok : undefined,
        errorCode: typeof event.error_code === "string" ? event.error_code : undefined,
        durationMs: typeof event.duration_ms === "number" ? event.duration_ms : undefined,
      } })
      if (event.status === "running") setStreamStatus(getToolStatusCopy(event.name, event.status))
      return
    }

    if (event.type === "time-context" && typeof event.context === "object" && event.context !== null) {
      const context = event.context as Record<string, unknown>
      if (typeof context.date === "string") {
        addGeneratedUi(assistantId, { component: "time-context", props: {
          date: context.date,
          localDatetime: typeof context.local_datetime === "string" ? context.local_datetime : undefined,
          timezone: typeof context.timezone === "string" ? context.timezone : undefined,
          source: typeof context.source === "string" ? context.source : undefined,
          isActualNow: context.is_actual_now === true,
          notice: typeof context.notice === "string" ? context.notice : undefined,
        } })
      }
      return
    }

    if (event.type === "memory" || event.type === "memory-candidate" || event.type === "memory-action" || event.type === "memory-organized") {
      const existing = messagesRef.current.find((message) => message.id === assistantId)?.generatedUi?.find((item) => item.component === "memory-context")
      if (event.type === "memory") {
        const used = Array.isArray(event.used) ? event.used.flatMap((item) => typeof item === "object" && item !== null && typeof (item as { content?: unknown }).content === "string" ? [{ id: typeof (item as { id?: unknown }).id === "string" ? (item as { id: string }).id : undefined, content: (item as { content: string }).content, relevance: typeof (item as { relevance?: unknown }).relevance === "number" ? (item as { relevance: number }).relevance : undefined }] : []) : []
        const skipped = Array.isArray(event.skipped) ? event.skipped.flatMap((item) => typeof item === "object" && item !== null && typeof (item as { content?: unknown }).content === "string" ? [{ id: typeof (item as { id?: unknown }).id === "string" ? (item as { id: string }).id : undefined, content: (item as { content: string }).content, relevance: typeof (item as { relevance?: unknown }).relevance === "number" ? (item as { relevance: number }).relevance : undefined, reason: typeof (item as { reason?: unknown }).reason === "string" ? (item as { reason: string }).reason : undefined }] : []) : []
        addGeneratedUi(assistantId, { component: "memory-context", props: { used, skipped, candidates: existing?.component === "memory-context" ? existing.props.candidates : [] } })
      } else if (event.type === "memory-candidate") {
        const candidate = event.memory as Record<string, unknown> | undefined
        if (candidate && typeof candidate.content === "string") {
          const prior = existing?.component === "memory-context" ? existing.props : { used: [], skipped: [], candidates: [] }
          addGeneratedUi(assistantId, { component: "memory-context", props: { ...prior, candidates: [...(prior.candidates || []), { id: typeof candidate.id === "string" ? candidate.id : undefined, type: typeof candidate.type === "string" ? candidate.type : undefined, content: candidate.content, status: typeof candidate.status === "string" ? candidate.status : undefined }] } })
        }
      } else if (event.type === "memory-action") {
        const prior = existing?.component === "memory-context" ? existing.props : { used: [], skipped: [], candidates: [] }
        const questions = Array.isArray(event.questions) ? event.questions.filter((item): item is string => typeof item === "string").slice(0, 3) : []
        addGeneratedUi(assistantId, { component: "memory-context", props: { ...prior, questions } })
      } else {
        const prior = existing?.component === "memory-context" ? existing.props : { used: [], skipped: [], candidates: [] }
        addGeneratedUi(assistantId, { component: "memory-context", props: { ...prior, organized: { reason: typeof event.reason === "string" ? event.reason : undefined, conflicts: Array.isArray(event.conflicts) ? event.conflicts.length : 0, archived: typeof event.archived === "number" ? event.archived : 0 } } })
      }
      return
    }

    if (event.type === "ui" && event.component === "knowledge-context" && typeof event.props === "object" && event.props !== null) {
      const items = (event.props as { items?: unknown }).items
      if (Array.isArray(items)) {
        addGeneratedUi(assistantId, {
          component: "knowledge-context",
          props: {
            items: items.flatMap((item) => (
              typeof item === "object" && item !== null && typeof (item as { title?: unknown }).title === "string"
                ? [{
                    title: (item as { title: string }).title,
                    excerpt: typeof (item as { excerpt?: unknown }).excerpt === "string" ? (item as { excerpt: string }).excerpt : "",
                    relevance: typeof (item as { relevance?: unknown }).relevance === "number" ? (item as { relevance: number }).relevance : undefined,
                    eligible: typeof (item as { eligible?: unknown }).eligible === "boolean" ? (item as { eligible: boolean }).eligible : undefined,
                    evidence_level: typeof (item as { evidence_level?: unknown }).evidence_level === "string" ? (item as { evidence_level: string }).evidence_level : undefined,
                    eligibility_reason: typeof (item as { eligibility_reason?: unknown }).eligibility_reason === "string" ? (item as { eligibility_reason: string }).eligibility_reason : undefined,
                  }]
              : []
            )),
            strategy: typeof (event.props as { strategy?: unknown }).strategy === "string" ? (event.props as { strategy: string }).strategy : undefined,
          },
        })
      }
      return
    }

    if (event.type === "sources" && Array.isArray(event.items)) {
      const items = event.items.flatMap((item) => {
        if (typeof item !== "object" || item === null) return []
        const candidate = item as Record<string, unknown>
        if (typeof candidate.label !== "string" || typeof candidate.title !== "string" || typeof candidate.excerpt !== "string") return []
        return [{ label: candidate.label, title: candidate.title, excerpt: candidate.excerpt, relevance: typeof candidate.relevance === "number" ? candidate.relevance : 0, eligible: candidate.eligible === true }]
      })
      if (items.length > 0) addGeneratedUi(assistantId, { component: "source-list", props: { items } })
      return
    }

    if (event.type === "ui" && event.component === "decision-card" && typeof event.props === "object" && event.props !== null) {
      const props = event.props as Record<string, unknown>
      const toStringList = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string").slice(0, 5) : []
      addGeneratedUi(assistantId, {
        component: "decision-card",
        props: {
          conclusion: typeof props.conclusion === "string" ? props.conclusion : undefined,
          summary: typeof props.summary === "string" ? props.summary : "待补充现场信息。",
          judgments: toStringList(props.judgments),
          actions: toStringList(props.actions),
          risks: toStringList(props.risks),
          followup: toStringList(props.followup),
          complete: props.complete === true,
        },
      })
      return
    }

    if (event.type === "resources" && Array.isArray(event.items)) {
      const items: Array<{ kind: "image" | "document"; title: string; url: string; source_url: string; license?: string }> = event.items.flatMap((item) => {
        if (typeof item !== "object" || item === null) return []
        const candidate = item as Record<string, unknown>
        const kind = candidate.kind === "image" || candidate.kind === "document" ? candidate.kind : null
        if (!kind || typeof candidate.title !== "string" || typeof candidate.url !== "string" || typeof candidate.source_url !== "string") return []
        return [{
          kind,
          title: candidate.title,
          url: candidate.url,
          source_url: candidate.source_url,
          license: typeof candidate.license === "string" ? candidate.license : undefined,
        }]
      })
      if (items.length > 0) addGeneratedUi(assistantId, { component: "resource-results", props: { items } })
      return
    }

    if (event.type === "done") {
      const completionStatus = event.completion_status === "fallback" || event.completion_status === "error" || event.completion_status === "guarded" ? event.completion_status : "complete"
      setTitleMood(completionStatus === "error" ? "error" : event.guarded === true || completionStatus === "guarded" ? "guard" : "done")
      const toolCalls = Array.isArray(event.tool_calls)
        ? event.tool_calls.flatMap((tool) => (
            typeof tool === "object" && tool !== null && typeof (tool as { name?: unknown }).name === "string"
              ? [{
                  name: (tool as { name: string }).name,
                  args: typeof (tool as { args?: unknown }).args === "object" && (tool as { args?: unknown }).args !== null
                    ? (tool as { args: Record<string, unknown> }).args
                    : undefined,
                }]
              : []
          ))
        : []
      setMessages((current) => current.map((message) => (
        message.id === assistantId
          ? { ...message, status: completionStatus === "error" ? "error" : "complete", completedAt: new Date(), completionStatus, toolCalls, answerMode: event.answer_mode === "brief" || event.answer_mode === "professional" ? event.answer_mode : message.answerMode }
          : message
      )))
      return
    }

    if (event.type === "error") {
      setTitleMood("error")
      throw new Error(typeof event.message === "string" ? event.message : "流式服务返回错误")
    }
  }, [addGeneratedUi, clearTypewriter, drainTypewriter, messages])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { id: `user_${crypto.randomUUID()}`, role: "user", content: input.trim(), timestamp: new Date(), status: "complete" }
    const assistantId = `assistant_${crypto.randomUUID()}`
    const controller = new AbortController()
    abortControllerRef.current = controller
    activeAssistantIdRef.current = assistantId
    cancelledRef.current = false
    setMessages((current) => [...current, userMessage, {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      status: "streaming",
      answerMode,
      generatedUi: [],
    }])
    setInput("")
    setIsLoading(true)
    setTitleMood("loading")
    setStreamStatus("正在连接流式农技服务")

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content, thread_id: threadId, answer_mode: answerMode }),
        signal: controller.signal,
      })
      if (!response.ok) throw new Error(`流式请求失败 (${response.status})`)
      await consumeSSE(response, (streamEvent) => handleStreamEvent(assistantId, streamEvent))
      await waitForTypewriter()
      if (!cancelledRef.current) {
        setMessages((current) => current.map((message) => (
          message.id === assistantId ? { ...message, status: "complete", completedAt: new Date() } : message
        )))
        setStreamStatus("")
        await refreshThreads()
      }
    } catch (error) {
      const aborted = cancelledRef.current || (error instanceof DOMException && error.name === "AbortError")
      setMessages((current) => current.map((message) => {
        if (message.id !== assistantId) return message
        return aborted
          ? { ...message, content: message.content || "已停止生成。", status: "cancelled", completedAt: new Date() }
          : { ...message, content: message.content || "抱歉，流式连接中断，请检查服务后重试。", status: "error", completedAt: new Date() }
      }))
      setStreamStatus(aborted ? "已停止生成" : "流式连接中断")
      setTitleMood(aborted ? "done" : "error")
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
      activeAssistantIdRef.current = null
      inputRef.current?.focus()
    }
  }

  const stopStreaming = () => {
    if (!abortControllerRef.current) return
    cancelledRef.current = true
    abortControllerRef.current.abort()
    clearTypewriter()
  }

  const createNewThread = () => {
    stopStreaming()
    const nextThreadId = `thread_${crypto.randomUUID()}`
    setThreadId(nextThreadId)
    setMessages([])
    setStreamStatus("")
    setMobileSessionsOpen(false)
  }

  const selectThread = async (nextThreadId: string) => {
    if (nextThreadId === threadId && messages.length > 0) return
    stopStreaming()
    setThreadId(nextThreadId)
    setMessages([])
    setStreamStatus("正在恢复历史记录")
    try {
      const response = await fetch(`/api/history/${nextThreadId}`)
      if (!response.ok) throw new Error("无法恢复会话")
      const data = await response.json() as { history?: Array<{ role: "user" | "assistant"; content: string; timestamp?: string; extra?: Record<string, unknown> | null }> }
      const historyMessages: Message[] = (data.history ?? []).map((message, index) => {
        const extra = message.extra && typeof message.extra === "object" ? message.extra : {}
        const rawCard = extra.decision_card && typeof extra.decision_card === "object" ? extra.decision_card as Record<string, unknown> : null
        const rawRuntime = extra.runtime_details && typeof extra.runtime_details === "object" ? extra.runtime_details as Record<string, unknown> : null
        const toStringList = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string").slice(0, 5) : []
        const historyCard: GeneratedUiEvent | undefined = rawCard ? {
          component: "decision-card",
          props: {
            conclusion: typeof rawCard.conclusion === "string" ? rawCard.conclusion : undefined,
            summary: typeof rawCard.summary === "string" ? rawCard.summary : "待补充现场信息。",
            judgments: toStringList(rawCard.judgments),
            actions: toStringList(rawCard.actions),
            risks: toStringList(rawCard.risks),
            followup: toStringList(rawCard.followup),
            complete: rawCard.complete === true,
          },
        } : undefined
        const historyRuntime: GeneratedUiEvent | undefined = message.role === "assistant" ? {
          component: "runtime-details",
          props: {
            persisted: rawRuntime ? rawRuntime.persisted !== false : false,
            toolCount: typeof rawRuntime?.tool_count === "number" ? rawRuntime.tool_count : undefined,
            knowledgeCount: typeof rawRuntime?.knowledge_count === "number" ? rawRuntime.knowledge_count : undefined,
            citationCount: typeof rawRuntime?.citation_count === "number" ? rawRuntime.citation_count : undefined,
            memoryUsedCount: typeof rawRuntime?.memory_used_count === "number" ? rawRuntime.memory_used_count : undefined,
            memorySkippedCount: typeof rawRuntime?.memory_skipped_count === "number" ? rawRuntime.memory_skipped_count : undefined,
            hasTimeContext: rawRuntime?.has_time_context === true,
          },
        } : undefined
        const restoredMode = extra.answer_mode === "brief" || extra.answer_mode === "professional" ? extra.answer_mode : (historyCard ? "professional" : undefined)
        const restoredStatus = extra.completion_status === "error" ? "error" : "complete"
        const restoredCompletionStatus: Message["completionStatus"] = extra.completion_status === "fallback" || extra.completion_status === "error" || extra.completion_status === "guarded" ? extra.completion_status : "complete"
        return {
          id: `history_${nextThreadId}_${index}`,
          role: message.role,
          content: message.content,
          timestamp: message.timestamp ? new Date(message.timestamp) : new Date(),
          status: restoredStatus as Message["status"],
          completionStatus: restoredCompletionStatus,
          answerMode: restoredMode as AnswerMode | undefined,
          generatedUi: historyCard && historyRuntime
            ? [historyCard, historyRuntime]
            : historyCard
              ? [historyCard]
              : historyRuntime
                ? [historyRuntime]
                : [],
        }
      })
      const restoredMode = historyMessages.find((item) => item.role === "assistant" && item.answerMode)?.answerMode
      if (restoredMode) setAnswerMode(restoredMode)
      setMessages(historyMessages)
      setStreamStatus("")
      setMobileSessionsOpen(false)
    } catch {
      setMessages([{
        id: `history_error_${nextThreadId}`,
        role: "assistant",
        content: "无法恢复这段会话，请稍后重试。",
        timestamp: new Date(),
        status: "error",
      }])
      setStreamStatus("历史记录暂不可用")
    }
  }

  useEffect(() => {
    if (restoredThreadRef.current || threads.length === 0) return
    const savedThreadId = window.localStorage.getItem("cropwise-active-thread")
    const savedThread = savedThreadId && threads.some((thread) => thread.thread_id === savedThreadId)
      ? savedThreadId
      : threads[0]?.thread_id
    if (!savedThread) return
    restoredThreadRef.current = true
    void selectThread(savedThread)
  }, [threads, threadId, messages.length])

  const deleteThread = async (targetThreadId: string) => {
    stopStreaming()
    try {
      await fetch(`/api/threads/${targetThreadId}`, { method: "DELETE" })
    } catch {
      return
    }
    const remaining = threads.filter((thread) => thread.thread_id !== targetThreadId)
    setThreads(remaining)
    if (targetThreadId === threadId) {
      if (remaining[0]) await selectThread(remaining[0].thread_id)
      else createNewThread()
    }
    await refreshThreads()
  }

  const clearHistory = async () => {
    await deleteThread(threadId)
  }

  const handleMessageScroll = () => {
    const element = messageScrollRef.current
    if (!element) return
    const distanceFromBottom = element.scrollHeight - element.scrollTop - element.clientHeight
    shouldFollowMessagesRef.current = distanceFromBottom < 96
    setShowScrollToBottom(distanceFromBottom >= 160)
  }

  const scrollMessagesToBottom = () => {
    shouldFollowMessagesRef.current = true
    setShowScrollToBottom(false)
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }

  return (
    <SidebarContext.Provider value={{ leftOpen, rightOpen, setLeftOpen, setRightOpen }}>
      <div className="relative flex min-h-[100dvh] flex-col" onDragEnter={handleDragEnter} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}>
        <a href="#main-content" className="skip-link">跳到主要内容</a>
        {dragActive && (
          <div className="drag-drop-overlay" role="status" aria-live="polite">
            <div className="drag-drop-panel">
              <Paperclip className="h-7 w-7 text-[#17613c]" aria-hidden="true" />
              <p className="mt-2 text-sm font-semibold text-[#17352b]">松开以解析农业文档</p>
              <p className="mt-1 text-xs text-[#66756c]">确认后才会写入农业知识库</p>
            </div>
          </div>
        )}
        <header className="workspace-header border-t-2 border-t-[#a6192e]">
          <div className="flex h-16 items-center justify-between px-3 sm:px-5">
            <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
              <button onClick={() => setMobileLeftOpen(true)} className="icon-button xl:hidden" title="打开学校信息" aria-label="打开学校信息">
                <Menu className="h-4 w-4" />
              </button>
              <button onClick={() => setLeftOpen(!leftOpen)} className="icon-button hidden xl:inline-flex" title={leftOpen ? "收起学校信息" : "打开学校信息"} aria-label={leftOpen ? "收起学校信息" : "打开学校信息"}>
                <PanelLeftClose className="h-4 w-4" />
              </button>
              <button onClick={() => setMobileSessionsOpen(true)} className="icon-button touch-target lg:hidden" title="打开对话记录" aria-label="打开对话记录">
                <MessageSquareMore className="h-4 w-4" />
              </button>
              <button onClick={() => setSessionsOpen(!sessionsOpen)} className="icon-button hidden touch-target lg:inline-flex" title={sessionsOpen ? "收起对话记录" : "打开对话记录"} aria-label={sessionsOpen ? "收起对话记录" : "打开对话记录"} aria-pressed={sessionsOpen}>
                <MessageSquareMore className="h-4 w-4" />
              </button>
              <div className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-md border border-[#d8e0d6] bg-white">
                <img src="/jxau-official-emblem.svg" alt="江西农业大学校徽" className="h-8 w-8 object-contain" />
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-[15px] font-semibold text-[#203a2f]">CropWise</h1>
                <AnimatePresence mode="wait">
                  <motion.p key={sloganIndex} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="hidden truncate text-xs text-[#6b796f] sm:block">
                    {slogans[sloganIndex]}
                  </motion.p>
                </AnimatePresence>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {knowledgeStatus && (
                <span className={cn("hidden rounded-md border px-2 py-1 text-xs font-medium sm:inline-flex", knowledgeStatus.total_documents > 0 ? "border-[#cfe0ce] bg-[#f2f8f1] text-[#17613c]" : "border-[#ead8dc] bg-[#fdf7f8] text-[#a6192e]") }>
                  {knowledgeStatus.total_documents > 0 ? `知识库 ${knowledgeStatus.total_documents}` : "知识库未就绪"}
                </span>
              )}
              <button
                onClick={() => setTerminologyEnabled((value) => !value)}
                className={cn("hidden h-9 items-center gap-1.5 rounded-md border px-2.5 text-xs font-medium transition-colors sm:inline-flex", terminologyEnabled ? "border-[#17613c] bg-[#eef6ed] text-[#17613c]" : "border-[#d8e0d6] bg-white text-[#66756c] hover:border-[#9db9a6] hover:text-[#17613c]")}
                title={terminologyEnabled ? "关闭专业名称词条" : "开启专业名称词条"}
                aria-label={terminologyEnabled ? "关闭专业名称词条" : "开启专业名称词条"}
                aria-pressed={terminologyEnabled}
              >
                专业词条 {terminologyEnabled ? "开" : "关"}
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="hidden h-9 items-center gap-1.5 rounded-md border border-[#cbdacb] bg-white px-3 text-xs font-medium text-[#17613c] transition-colors hover:bg-[#f3f8f2] sm:inline-flex"
                title="解析并上传 RAG 文档"
                aria-label="解析并上传 RAG 文档"
              >
                <Paperclip className="h-3.5 w-3.5" />
                上传 RAG 文档
              </button>
              <button
                onClick={createNewThread}
                className="hidden h-9 items-center gap-1.5 rounded-md border border-[#17613c] bg-[#f3f8f2] px-3 text-xs font-medium text-[#17613c] transition-colors hover:bg-[#e7f1e8] sm:inline-flex"
                title="新建消息会话"
                aria-label="新建消息会话"
              >
                <MessageSquarePlus className="h-3.5 w-3.5" />
                新建消息
              </button>
              <button
                onClick={createNewThread}
                className="icon-button touch-target sm:hidden"
                title="新建消息会话"
                aria-label="新建消息会话"
              >
                <MessageSquarePlus className="h-4 w-4" />
              </button>
              <button onClick={() => setRagTestOpen(true)} className="icon-button touch-target mobile-deprioritize" title="打开 RAG 测试提示词" aria-label="打开 RAG 测试提示词" aria-pressed={ragTestOpen}>
                <FlaskConical className="h-4 w-4" />
              </button>
              <button onClick={() => setMobileRightOpen(true)} className="icon-button touch-target xl:hidden" title="打开科研成果" aria-label="打开科研成果" aria-pressed={mobileRightOpen}>
                <BookOpen className="h-4 w-4" />
              </button>
              <button onClick={() => setRightOpen(!rightOpen)} className="icon-button hidden touch-target xl:inline-flex" title={rightOpen ? "收起科研成果" : "打开科研成果"} aria-label={rightOpen ? "收起科研成果" : "打开科研成果"} aria-pressed={rightOpen}>
                <PanelRightClose className="h-4 w-4" />
              </button>
              <button onClick={clearHistory} className="icon-button touch-target mobile-deprioritize" title="删除当前会话" aria-label="删除当前会话">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>

        <input ref={fileInputRef} type="file" className="sr-only" accept=".txt,.md,.markdown,.csv,.html,.htm,.json,.docx,.pdf" onChange={handleAttachmentChange} aria-label="选择 RAG 文档" />

        <div className="app-content flex min-h-0 gap-3 overflow-hidden px-3 py-3 sm:px-5">
          <AnimatePresence>
            {sessionsOpen && (
              <motion.aside
                initial={{ width: 0, opacity: 0, x: -12 }}
                animate={{ width: 288, opacity: 1, x: 0 }}
                exit={{ width: 0, opacity: 0, x: -12 }}
                transition={{ duration: 0.22 }}
                className="hidden min-h-0 shrink-0 overflow-hidden lg:block"
              >
                <div className="sidebar-panel h-full overflow-hidden rounded-lg">
                  <ConversationPanel threads={threads} activeThreadId={threadId} onCreate={createNewThread} onSelect={selectThread} onDelete={deleteThread} />
                </div>
              </motion.aside>
            )}
          </AnimatePresence>
          <LeftPanel />

          <section id="main-content" className="workspace-panel flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg" aria-label="农业问答工作区" tabIndex={-1}>
            <div className="flex items-center justify-between border-b px-4 py-3 sm:px-5">
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-[#263f33]">农业问答</p>
                  <span className="status-dot" aria-hidden="true" />
                  <span className="text-[11px] font-medium text-[#587363]">知识服务在线</span>
                </div>
                <p className="mt-0.5 text-xs text-[#718077]">聚焦作物种植、病虫害防治与农事管理</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="inline-flex items-center rounded-md border border-[#d8e0d6] bg-[#f8fbf7] p-0.5" role="group" aria-label="回答模式">
                  <button type="button" onClick={() => changeAnswerMode("professional")} disabled={isLoading} className={cn("h-8 rounded px-2 text-[11px] font-medium transition-colors sm:px-2.5 sm:text-xs", answerMode === "professional" ? "bg-white text-[#17613c] shadow-sm" : "text-[#718077] hover:text-[#17613c]")} aria-pressed={answerMode === "professional"} title="专业回答：完整决策卡与知识依据">
                    <span className="sm:hidden">专业</span><span className="hidden sm:inline">专业回答</span>
                  </button>
                  <button type="button" onClick={() => changeAnswerMode("brief")} disabled={isLoading} className={cn("h-8 rounded px-2 text-[11px] font-medium transition-colors sm:px-2.5 sm:text-xs", answerMode === "brief" ? "bg-white text-[#17613c] shadow-sm" : "text-[#718077] hover:text-[#17613c]")} aria-pressed={answerMode === "brief"} title="简要回答：结论、建议与风险提醒">
                    <span className="sm:hidden">简要</span><span className="hidden sm:inline">简要回答</span>
                  </button>
                </div>
                <BookOpen className="hidden h-5 w-5 text-[#17613c] sm:block" strokeWidth={1.6} />
              </div>
            </div>

            <div ref={messageScrollRef} onScroll={handleMessageScroll} className="relative scroll-boundary min-h-0 flex-1 overflow-y-auto px-4 py-5 custom-scrollbar sm:px-6">
              <AnimatePresence mode="wait">
                {messages.length === 0 ? (
                  <motion.div key="empty" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mx-auto flex min-h-full w-full max-w-2xl flex-col justify-center pb-8">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[#e7f1e8] text-[#17613c]">
                      <Sparkles className="h-6 w-6" strokeWidth={1.7} />
                    </div>
                    <h2 className="mt-5 text-2xl font-semibold text-[#213a2f]">今天想处理什么田间问题？</h2>
                    <p className="mt-2 max-w-xl text-sm leading-6 text-[#66756c]">输入作物、症状、地区或生长阶段，获得更有针对性的农技知识建议。</p>
                    <div className="mt-5 grid gap-2 sm:grid-cols-3">
                      {QUICK_QUESTIONS.map((question) => (
                        <button key={question} onClick={() => { setInput(question); inputRef.current?.focus() }} className="quick-question">
                          {question}
                        </button>
                      ))}
                    </div>
                    <FieldBrief onUsePrompt={(prompt) => { setInput(prompt); inputRef.current?.focus() }} />
                    <EmptyCropCard />
                  </motion.div>
                ) : (
                  <div className="mx-auto max-w-3xl space-y-4">
                    {messages.map((message) => (
                      <motion.div key={message.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}>
                        {(() => {
                          const hasDecisionCard = message.role === "assistant" && (message.generatedUi ?? []).some((item) => item.component === "decision-card")
                          return <div className={cn("max-w-[94%] text-[15px] leading-6 sm:max-w-[78%] sm:text-sm", message.role === "user" ? "message-user px-4 py-3" : hasDecisionCard ? "assistant-response-frame" : "message-assistant px-4 py-3")}>
                          {(() => {
                            const visibleContent = stripToolCallMarkers(message.content)
                            const showAssistantText = message.role === "user" || message.answerMode === "brief" || message.status === "streaming" || !hasDecisionCard
                            return <>
                          {message.role === "assistant" && (
                            <MessageStatus
                              status={message.status}
                              detail={message.id === activeAssistantIdRef.current ? streamStatus : undefined}
                              timestamp={message.completedAt ?? message.timestamp}
                              completionStatus={message.completionStatus}
                            />
                          )}
                          {message.role === "assistant" && <GenerativeUi events={message.generatedUi ?? []} />}
                          {visibleContent && showAssistantText ? (message.role === "user" ? <p className="user-message-copy">{visibleContent}</p> : <MarkdownMessage content={visibleContent} terminologyEnabled={terminologyEnabled} />) : message.status === "streaming" ? (
                            <div className="flex items-center gap-2 text-sm text-[#68776d]">
                              <Loader2 className="h-4 w-4 animate-spin text-[#17613c]" /> {streamStatus || "正在生成农技建议"}
                            </div>
                          ) : null}
                            </>
                          })()}
                          {message.status === "streaming" && message.content && <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-[#17613c] align-[-2px]" aria-label="正在输入" />}
                          </div>
                        })()}
                      </motion.div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </AnimatePresence>
              <AnimatePresence>
                {showScrollToBottom && (
                  <motion.button
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 8 }}
                    onClick={scrollMessagesToBottom}
                    className="sticky bottom-2 left-1/2 z-10 mx-auto flex min-h-10 -translate-x-1/2 items-center gap-2 rounded-full border border-[#c8d8c9] bg-white px-3 py-2 text-xs font-medium text-[#17613c] shadow-md hover:bg-[#f3f8f2]"
                    aria-label="回到最新消息"
                  >
                    <ChevronLeft className="h-3.5 w-3.5 -rotate-90" /> 回到最新消息
                  </motion.button>
                )}
              </AnimatePresence>
            </div>

            <div className="composer-shell relative z-20 shrink-0 isolate overflow-visible border-t p-3 sm:p-4">
              {(attachment || attachmentBusy || attachmentError) && (
                <div className="mx-auto mb-2 max-w-3xl rounded-md border border-[#dbe6db] bg-[#f7fbf6] px-3 py-2 text-xs text-[#526158]" role="status" aria-live="polite">
                  <div className="flex items-start gap-2">
                    <Paperclip className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#17613c]" />
                    <div className="min-w-0 flex-1">
                      {attachment && <p className="truncate font-medium text-[#334d40]">{attachment.name}</p>}
                      {attachmentBusy && <p className="mt-1 text-[#587363]">正在解析文档并检查农业知识范围…</p>}
                      {attachmentError && <p className="mt-1 text-[#a6192e]">{attachmentError}</p>}
                      {attachmentAnalysis && !attachmentBusy && (
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1">
                          <span className={attachmentAnalysis.eligible ? "font-medium text-[#17613c]" : "font-medium text-[#a6192e]"}>{attachmentAnalysis.eligible ? "可进入农业知识库" : "不建议入库"}</span>
                          <span>置信度 {Math.round(attachmentAnalysis.confidence * 100)}%</span>
                          <span>{attachmentAnalysis.estimated_chunks} 个预计分块</span>
                          {attachmentAnalysis.ingested && <span className="font-medium text-[#17613c]">{attachmentAnalysis.duplicate ? "已存在，未重复写入" : `已向量化入库 ${attachmentAnalysis.added_chunks ?? 0} 个分块`}</span>}
                        </div>
                      )}
                      {attachmentAnalysis && !attachmentBusy && <p className="mt-1 leading-5 text-[#718077]">{attachmentAnalysis.reason}</p>}
                      {attachmentAnalysis?.eligible && !attachmentAnalysis.ingested && !attachmentBusy && <button type="button" onClick={() => void ingestAttachment()} className="mt-2 rounded-md border border-[#17613c] bg-white px-2.5 py-1.5 text-xs font-medium text-[#17613c] hover:bg-[#eef6ed]">确认加入知识库</button>}
                    </div>
                    <button type="button" onClick={clearAttachment} className="icon-button h-7 w-7 shrink-0" title="移除附件" aria-label="移除附件"><X className="h-3.5 w-3.5" /></button>
                  </div>
                </div>
              )}
              <form onSubmit={handleSubmit} aria-label="农业问题输入区" className={cn("mx-auto flex min-h-[59px] max-w-3xl items-end gap-2 overflow-visible rounded-lg border bg-white p-1.5 shadow-sm transition-colors", isLoading ? "border-[#9db9a6]" : "focus-within:border-[#86a68f] focus-within:ring-2 focus-within:ring-[#17613c]/10")}>
                <button type="button" onClick={() => fileInputRef.current?.click()} className="icon-button mb-0.5 h-10 w-10 shrink-0" title="解析并上传 RAG 文档" aria-label="解析并上传 RAG 文档"><Paperclip className="h-4 w-4" /></button>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); handleSubmit(event) }
                  }}
                  placeholder="例如：早稻分蘖期叶尖发黄，该如何判断？"
                  aria-label="输入农业问题"
                  maxLength={2000}
                  aria-describedby="composer-help"
                  className="min-h-[46px] max-h-36 flex-1 resize-none overflow-y-auto break-words whitespace-pre-wrap border-0 bg-transparent px-3 py-2.5 text-base leading-6 text-[#273f33] placeholder:text-[#94a097] focus:outline-none sm:text-sm sm:leading-5"
                  rows={1}
                  disabled={isLoading}
                />
                <button
                  type={isLoading ? "button" : "submit"}
                  onClick={isLoading ? stopStreaming : undefined}
                  disabled={!isLoading && !input.trim()}
                  className="primary-button mb-0.5 h-10 w-10 px-0"
                  title={isLoading ? "停止生成" : "发送问题"}
                  aria-label={isLoading ? "停止生成" : "发送问题"}
                >
                  {isLoading ? <Square className="h-3.5 w-3.5 fill-current" /> : <Send className="h-4 w-4" />}
                </button>
              </form>
              <div id="composer-help" className="mx-auto mt-2 flex min-h-5 max-w-3xl items-start justify-between gap-3 px-1 text-xs leading-5 text-[#87938b]">
                <p aria-live="polite" className="min-w-0 flex-1 whitespace-normal">{isLoading ? `${streamStatus || "正在生成"}，可点击停止按钮中断。` : "按 Enter 发送，Shift + Enter 换行"}</p>
                <span className={cn("shrink-0 tabular-nums", input.length > 1800 && "text-[#a6192e]")}>{input.length}/2000</span>
              </div>
            </div>
          </section>

          <KnowledgePanel mobileOpen={mobileRightOpen} onMobileClose={() => setMobileRightOpen(false)} />
        </div>

        <div className={cn("px-3 pb-3 sm:px-5", messages.length > 0 ? "hidden" : "block")}>
          <AchievementFooter />
        </div>

        <AnimatePresence>
          {mobileSessionsOpen && (
            <>
              <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setMobileSessionsOpen(false)} className="fixed inset-0 z-[60] bg-[#17352b]/35 lg:hidden" aria-label="关闭对话记录" />
              <motion.aside initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }} transition={{ duration: 0.22 }} className="fixed inset-y-0 left-0 z-[70] flex h-[100dvh] w-[min(320px,88vw)] flex-col overflow-hidden bg-white pt-[env(safe-area-inset-top)] shadow-xl lg:hidden">
                <ConversationPanel threads={threads} activeThreadId={threadId} onCreate={createNewThread} onSelect={selectThread} onDelete={deleteThread} />
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {mobileLeftOpen && (
            <>
              <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setMobileLeftOpen(false)} className="fixed inset-0 z-[60] bg-[#17352b]/35 xl:hidden" aria-label="关闭学校信息" />
              <motion.aside initial={{ x: -320 }} animate={{ x: 0 }} exit={{ x: -320 }} transition={{ duration: 0.22 }} className="scroll-boundary fixed inset-y-0 left-0 z-[70] h-[100dvh] w-[min(320px,88vw)] overflow-y-auto bg-white px-5 pb-5 pt-[calc(1.25rem+env(safe-area-inset-top))] shadow-xl xl:hidden">
                <div className="mb-5 flex items-center justify-between">
                  <p className="text-sm font-semibold text-[#263f33]">学校信息</p>
                  <button onClick={() => setMobileLeftOpen(false)} className="icon-button" title="关闭学校信息" aria-label="关闭学校信息"><X className="h-4 w-4" /></button>
                </div>
                <LeftPanel mobile />
              </motion.aside>
            </>
          )}
        </AnimatePresence>

      </div>
      <RagTestPanel open={ragTestOpen} onClose={() => setRagTestOpen(false)} onUsePrompt={(prompt) => { setInput(prompt); inputRef.current?.focus() }} />
    </SidebarContext.Provider>
  )
}
