"use client"

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Activity, AlertTriangle, Archive, ArrowUpRight, BookOpen, Bot, CheckCircle2, ChevronDown, Command, HelpCircle, CloudSun, Database, FileText, History, Leaf, Loader2, MapPin, Menu, PanelLeft, PanelRight, Plus, RefreshCw, Search, Send, Settings2, ShieldCheck, Sprout, Trash2, X, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { SseEventParser } from "@/lib/sse"

interface Source { label?: string; title?: string; publisher?: string; evidence_level?: string; excerpt?: string; source_url?: string; eligible?: boolean; relevance?: number; evidence_id?: string }
interface ToolCall { name?: string; status?: string; duration_ms?: number }
interface AgentEvent { type: string; label: string; status?: string; name?: string; stage?: string }
interface NewsItem { title: string; tag?: string }
interface Message { role: "user" | "assistant"; content: string; timestamp: Date; sources?: Source[]; tool_calls?: ToolCall[]; completion_status?: string; activity?: AgentEvent[]; decisionCard?: Record<string, unknown> }
interface CropOption { name: string; stage: string; region: string; health: string; tone: "green" | "amber" | "blue" }
interface ThreadSummary { thread_id?: string; title?: string; updated_at?: string; message_count?: number }
interface WeatherDay { date?: string; temperature_max_c?: number; temperature_min_c?: number; precipitation_mm?: number; wind_speed_max_kmh?: number; weather_code?: number }
interface WeatherData { ok?: boolean; location?: string; resolved_name?: string; source?: string; publisher?: string; notice?: string; daily?: WeatherDay[]; message?: string }
interface KnowledgeHit { content?: string; metadata?: Record<string, unknown>; relevance?: number }
interface KnowledgeSearchData { query?: string; strategy?: string; results?: KnowledgeHit[]; citations?: Source[] }
interface GraphData { status?: string; error?: string; query?: string; results?: Array<Record<string, unknown>> }

const suggestions = [
  { label: "诊断病害", text: "水稻叶片出现黄褐色斑点，田间湿度较高，可能是什么病？" },
  { label: "制定施肥", text: "赣南脐橙膨果期如何制定施肥方案？" },
  { label: "查看农时", text: "江西早稻当前田间管理有哪些关键节点？" },
]
const navItems = [
  { label: "工作台", icon: Activity }, { label: "知识检索", icon: Search }, { label: "作物档案", icon: Sprout }, { label: "病虫害诊断", icon: ShieldCheck }, { label: "农情图谱", icon: MapPin },
]
const cropOptions: CropOption[] = [
  { name: "水稻", stage: "分蘖期", region: "赣州", health: "良好", tone: "green" }, { name: "脐橙", stage: "膨果期", region: "安远", health: "关注", tone: "amber" }, { name: "油茶", stage: "幼果期", region: "吉安", health: "稳定", tone: "blue" },
]
function formatTime(date: Date) { return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }) }
function formatSessionMeta(updatedAt?: string, messageCount?: number) {
  const count = typeof messageCount === "number" ? `${messageCount} 条消息` : "已保存会话"
  if (!updatedAt) return count
  const date = new Date(updatedAt)
  return Number.isNaN(date.getTime()) ? count : `${count} · ${formatTime(date)}`
}

function formatKnowledgeText(value: unknown) {
  return typeof value === "string" ? value : value == null ? "" : JSON.stringify(value, null, 2)
}

function formatRelevance(value: unknown) {
  if (typeof value !== "number" || Number.isNaN(value)) return "已匹配"
  return value >= 0 && value <= 1 ? `${Math.round(value * 100)}%` : value.toFixed(2)
}

function WorkspaceToolView({
  activeNav,
  selectedCrop,
  knowledgeQuery,
  setKnowledgeQuery,
  knowledgeData,
  knowledgeLoading,
  knowledgeError,
  onKnowledgeSearch,
  graphQuery,
  setGraphQuery,
  graphData,
  graphLoading,
  graphError,
  onGraphSearch,
  onStartDiagnosis,
}: {
  activeNav: string
  selectedCrop: CropOption
  knowledgeQuery: string
  setKnowledgeQuery: (value: string) => void
  knowledgeData: KnowledgeSearchData | null
  knowledgeLoading: boolean
  knowledgeError: string
  onKnowledgeSearch: () => void
  graphQuery: string
  setGraphQuery: (value: string) => void
  graphData: GraphData | null
  graphLoading: boolean
  graphError: string
  onGraphSearch: () => void
  onStartDiagnosis: () => void
}) {
  if (activeNav === "病虫害诊断") {
    return <section className="tool-view diagnosis-view" aria-label="病虫害诊断工作区">
      <div className="tool-view-kicker"><ShieldCheck size={14} /> REAL AGENT WORKFLOW</div>
      <h2>病虫害诊断</h2>
      <p>诊断通过真实农业 Agent 流式问答完成，当前作物、生育期和区域会作为结构化上下文发送到后端。</p>
      <div className="tool-context-grid"><div><span>作物</span><strong>{selectedCrop.name}</strong></div><div><span>生育期</span><strong>{selectedCrop.stage}</strong></div><div><span>区域</span><strong>{selectedCrop.region}</strong></div></div>
      <button type="button" className="tool-primary" onClick={onStartDiagnosis}><ShieldCheck size={15} /> 开始真实诊断</button>
      <p className="tool-note"><CheckCircle2 size={13} /> 点击后进入工作台输入区，发送内容将调用 `/api/chat/stream`。</p>
    </section>
  }

  if (activeNav === "农情图谱") {
    return <section className="tool-view" aria-label="农情图谱工作区">
      <div className="tool-view-kicker"><MapPin size={14} /> KNOWLEDGE GRAPH API</div>
      <h2>农情图谱</h2>
      <p>这里连接后端 Neo4j 知识图谱搜索接口。图谱服务不可用时明确显示服务状态，不使用静态节点冒充结果。</p>
      <form className="tool-search" onSubmit={(event) => { event.preventDefault(); onGraphSearch() }}><Search size={16} /><input value={graphQuery} onChange={(event) => setGraphQuery(event.target.value)} placeholder="搜索作物、病害或管理关系…" aria-label="搜索农情图谱" /><button type="submit" disabled={graphLoading || !graphQuery.trim()}>{graphLoading ? <Loader2 size={15} className="spin" /> : <Search size={15} />} 搜索</button></form>
      {graphError && <div className="tool-error"><AlertTriangle size={15} /> {graphError}</div>}
      {graphData?.status && graphData.status !== "ok" && <div className="tool-warning"><AlertTriangle size={15} /> 图谱服务未连接（状态：{graphData.status}）。请先启动 Neo4j 或检查后端图谱连接。</div>}
      {graphData?.results && graphData.results.length > 0 ? <div className="tool-results">{graphData.results.map((result, index) => <article className="tool-result" key={`${String(result.id ?? result.name ?? index)}`}><div className="tool-result-meta">实体 {index + 1} · {String(result.label ?? result.type ?? "农业实体")}</div><strong>{String(result.name ?? result.entity ?? result.id ?? "未命名实体")}</strong><pre>{JSON.stringify(result, null, 2)}</pre></article>)}</div> : <div className="tool-empty"><MapPin size={18} /><span>输入作物、病害或管理关键词，查询知识图谱实体与关系。</span></div>}
    </section>
  }

  const isProfile = activeNav === "作物档案"
  return <section className="tool-view" aria-label={isProfile ? "作物档案工作区" : "知识检索工作区"}>
    <div className="tool-view-kicker"><Search size={14} /> KNOWLEDGE BASE API</div>
    <h2>{isProfile ? `${selectedCrop.name} · 作物档案` : "知识检索"}</h2>
    <p>{isProfile ? "档案内容来自当前农业知识库检索结果，随作物和关键词变化，不使用固定示例文本。" : "检索直接调用后端混合检索接口，返回可核验的知识片段与引用信息。"}</p>
    <form className="tool-search" onSubmit={(event) => { event.preventDefault(); onKnowledgeSearch() }}><Search size={16} /><input value={knowledgeQuery} onChange={(event) => setKnowledgeQuery(event.target.value)} placeholder={isProfile ? "补充档案主题，如病虫害、施肥…" : "搜索农业知识…"} aria-label={isProfile ? "搜索作物档案" : "搜索农业知识"} /><button type="submit" disabled={knowledgeLoading || !knowledgeQuery.trim()}>{knowledgeLoading ? <Loader2 size={15} className="spin" /> : <Search size={15} />} 检索</button></form>
    {knowledgeError && <div className="tool-error"><AlertTriangle size={15} /> {knowledgeError}</div>}
    {knowledgeData?.results && knowledgeData.results.length > 0 ? <div className="tool-results">{knowledgeData.results.map((result, index) => <article className="tool-result" key={`${String(result.metadata?.evidence_id ?? result.metadata?.title ?? index)}`}><div className="tool-result-meta">证据 {index + 1} · 相关度 {formatRelevance(result.relevance)}</div><strong>{String(result.metadata?.title ?? result.metadata?.source ?? "农业知识库片段")}</strong><p>{formatKnowledgeText(result.content)}</p></article>)}</div> : <div className="tool-empty"><BookOpen size={18} /><span>输入农业关键词，检索知识库中的相关证据与来源。</span></div>}
  </section>
}

function DecisionCard({ card }: { card: Record<string, unknown> }) {
  const items = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : []
  const sections = [
    ["优先判断", items(card.judgments)],
    ["现在做什么", items(card.actions)],
    ["风险边界", items(card.risks)],
    ["复查节点", items(card.followup)],
  ] as const
  return <section className="decision-card" aria-label="农业决策卡">
    <div className="decision-card-header"><div><span className="section-label">ACTION BRIEF</span><strong>{typeof card.conclusion === "string" ? card.conclusion : "基于当前证据的农业行动建议"}</strong></div><span className={cn("decision-status", card.complete === false && "is-incomplete")}>{card.complete === false ? "待补充信息" : "可执行建议"}</span></div>
    {typeof card.summary === "string" && card.summary.trim() && <p className="decision-summary">{card.summary}</p>}
    <div className="decision-sections">{sections.map(([label, values]) => values.length > 0 && <div className="decision-section" key={label}><span>{label}</span><ul>{values.map((value, index) => <li key={`${label}-${index}`}>{value}</li>)}</ul></div>)}</div>
  </section>
}

function AssistantAnswer({ content }: { content: string }) {
  const [detailOpen, setDetailOpen] = useState(false)
  const detailMarker = content.match(/(?:^|\n)(?=(?:#{0,3}\s*)?\d+[.、]\s+)/m)

  if (!detailMarker || detailMarker.index === undefined) {
    return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
  }

  const detailStart = detailMarker.index + detailMarker[0].length
  const summary = content.slice(0, detailMarker.index).trim()
  const details = content.slice(detailStart).trim()

  return <>
    {summary && <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary}</ReactMarkdown>}
    <details className="answer-details" open={detailOpen} onToggle={(event) => setDetailOpen(event.currentTarget.open)}>
      <summary>详细分析与管理建议</summary>
      <div className="answer-details-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{details}</ReactMarkdown></div>
    </details>
  </>
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [threadId, setThreadId] = useState(() => `thread_${Date.now()}`)
  const [activeNav, setActiveNav] = useState("工作台")
  const [selectedCrop, setSelectedCrop] = useState(cropOptions[0])
  const [selectedRegion, setSelectedRegion] = useState(cropOptions[0].region)
  const [activeSource, setActiveSource] = useState<Source | null>(null)
  const [showMobileContext, setShowMobileContext] = useState(false)
  const [showMobileSidebar, setShowMobileSidebar] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const [showContext, setShowContext] = useState(true)
  const [showHistory, setShowHistory] = useState(false)
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [commandQuery, setCommandQuery] = useState("")
  const [showSettings, setShowSettings] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [serviceStatus, setServiceStatus] = useState<"checking" | "online" | "offline">("checking")
  const [jxauNews, setJxauNews] = useState<NewsItem[]>([])
  const [threadSummaries, setThreadSummaries] = useState<ThreadSummary[]>([])
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null)
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState("")
  const [knowledgeQuery, setKnowledgeQuery] = useState("")
  const [knowledgeData, setKnowledgeData] = useState<KnowledgeSearchData | null>(null)
  const [knowledgeLoading, setKnowledgeLoading] = useState(false)
  const [knowledgeError, setKnowledgeError] = useState("")
  const [graphQuery, setGraphQuery] = useState("")
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [graphLoading, setGraphLoading] = useState(false)
  const [graphError, setGraphError] = useState("")
  const [systemInfo, setSystemInfo] = useState<Record<string, unknown> | null>(null)
  const [systemInfoLoading, setSystemInfoLoading] = useState(false)
  const [agentActivity, setAgentActivity] = useState<AgentEvent[]>([])
  const [activityExpanded, setActivityExpanded] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const latestSources = useMemo(() => { for (let i = messages.length - 1; i >= 0; i -= 1) if (messages[i].sources?.length) return messages[i].sources ?? []; return [] }, [messages])

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages, isLoading])
  const refreshThreads = async () => {
    try {
      const response = await fetch("/api/threads?limit=8")
      if (!response.ok) throw new Error("threads request failed")
      const data = await response.json()
      setThreadSummaries(Array.isArray(data.threads) ? data.threads : [])
    } catch (error) {
      console.error("加载会话列表失败:", error)
    }
  }

  useEffect(() => {
    const loadWorkspaceData = async () => {
      const [healthResult, newsResult] = await Promise.allSettled([fetch("/api/health"), fetch("/api/news")])
      if (healthResult.status === "fulfilled" && healthResult.value.ok) setServiceStatus("online")
      else setServiceStatus("offline")
      if (newsResult.status === "fulfilled" && newsResult.value.ok) {
        const news = await newsResult.value.json()
        setJxauNews(Array.isArray(news.news) ? news.news.slice(0, 3) : [])
      }
      void refreshThreads()
    }
    void loadWorkspaceData()
  }, [])

  useEffect(() => {
    const loadWeather = async () => {
      setWeatherLoading(true)
      setWeatherError("")
      try {
        const response = await fetch(`/api/weather?location=${encodeURIComponent(selectedRegion)}&days=3`)
        const data = await response.json()
        if (!response.ok || data.ok === false) throw new Error(data.message ?? "天气服务暂不可用")
        setWeatherData(data)
      } catch (error) {
        setWeatherData(null)
        setWeatherError(error instanceof Error ? error.message : "天气服务暂不可用")
      } finally {
        setWeatherLoading(false)
      }
    }
    void loadWeather()
  }, [selectedRegion])
  useEffect(() => {
    const handleCommandShortcut = (event: globalThis.KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setShowCommandPalette((current) => !current)
      }
      if (event.key === "Escape") {
        setShowCommandPalette(false)
        setShowMobileContext(false)
        setActiveSource(null)
        setShowHistory(false)
      }
    }
    window.addEventListener("keydown", handleCommandShortcut)
    return () => window.removeEventListener("keydown", handleCommandShortcut)
  }, [])

  const sendMessage = async (content: string) => {
    const trimmed = content.trim()
    if (!trimmed || isLoading) return
    setActiveNav("工作台")
    const assistantIndex = messages.length + 1
    setMessages((prev) => [...prev, { role: "user", content: trimmed, timestamp: new Date() }, { role: "assistant", content: "", timestamp: new Date(), activity: [] }])
    setAgentActivity([])
    setActivityExpanded(true)
    setInput("")
    setIsLoading(true)
    try {
      const response = await fetch("/api/chat/stream", { method: "POST", headers: { "Content-Type": "application/json", Accept: "text/event-stream" }, body: JSON.stringify({ message: trimmed, thread_id: threadId, answer_mode: "professional", scenario_context: { crop: selectedCrop.name, growth_stage: selectedCrop.stage, region: selectedRegion } }) })
      if (!response.ok) {
        const payload = await response.json().catch(() => null)
        throw new Error(payload?.detail ?? payload?.message ?? "农业服务请求失败")
      }
      if (!response.body) throw new Error("农业服务未返回流式响应")
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let answer = ""
      const sources: Source[] = []
      const toolCalls: ToolCall[] = []
      const activity: AgentEvent[] = []
      const addActivity = (event: AgentEvent) => {
        const key = `${event.type}:${event.name ?? event.stage ?? event.label}`
        if (!activity.some((item) => `${item.type}:${item.name ?? item.stage ?? item.label}` === key)) {
          activity.push(event)
          setAgentActivity([...activity])
        }
      }
      const updateAssistant = (patch: Partial<Message>) => setMessages((prev) => prev.map((item, index) => index === assistantIndex ? { ...item, ...patch } : item))
      const handleEvent = (event: Record<string, any>) => {
        if (event.type === "delta") answer += String(event.text ?? "")
        if (event.type === "answer-replace") answer = String(event.text ?? answer)
        if (event.type === "done" && typeof event.message === "string") answer = event.message
        if (event.type === "sources" && Array.isArray(event.items)) sources.splice(0, sources.length, ...event.items)
        if (event.type === "tool") { toolCalls.push({ name: event.name, status: event.status, duration_ms: event.duration_ms }); addActivity({ type: "tool", label: `${event.status === "running" ? "正在调用" : "已完成"} ${event.name ?? "农业工具"}`, status: event.status, name: event.name }) }
        if (event.type === "trace") addActivity({ type: "trace", label: event.stage === "routing" ? "已完成问题路由" : "已完成知识库检索", stage: event.stage })
        if (event.type === "status") addActivity({ type: "status", label: String(event.message ?? "Agent 正在处理") })
        if (event.type === "guard") addActivity({ type: "guard", label: "已启用农业领域安全边界" })
        const patch: Partial<Message> = { content: answer, sources: [...sources], tool_calls: [...toolCalls], activity: [...activity] }
        if (event.type === "ui" && event.component === "decision-card" && event.props && typeof event.props === "object") patch.decisionCard = event.props
        if (event.type === "done") patch.completion_status = event.completion_status ?? "complete"
        if (event.type === "error") { patch.completion_status = "error"; patch.content = answer || String(event.message ?? "农业服务暂时不可用") }
        updateAssistant(patch)
      }
      const parser = new SseEventParser((event) => handleEvent(event))
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        parser.push(decoder.decode(value, { stream: true }))
      }
      parser.push(decoder.decode(), true)
      await refreshThreads()
    } catch (error) {
      console.error("发送消息失败:", error)
      const errorActivity = [{ type: "error", label: "农业服务连接失败" }]
      setAgentActivity(errorActivity)
      setMessages((prev) => prev.map((item, index) => index === assistantIndex ? { ...item, content: error instanceof Error && error.message ? error.message : "当前无法连接农业知识服务。请检查后端服务是否运行，稍后再试。", completion_status: "error", activity: errorActivity } : item))
    } finally { setIsLoading(false); setActivityExpanded(false); inputRef.current?.focus() }
  }
  const handleSubmit = (event: FormEvent) => { event.preventDefault(); void sendMessage(input) }
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void sendMessage(input) } }
  const searchKnowledge = async (query = knowledgeQuery) => {
    const normalizedQuery = query.trim()
    if (!normalizedQuery || knowledgeLoading) return
    setKnowledgeLoading(true)
    setKnowledgeError("")
    try {
      const response = await fetch(`/api/knowledge-base/search?query=${encodeURIComponent(normalizedQuery)}&limit=6`)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail ?? "知识库检索失败")
      setKnowledgeData(data)
    } catch (error) {
      setKnowledgeData(null)
      setKnowledgeError(error instanceof Error ? error.message : "知识库检索失败")
    } finally {
      setKnowledgeLoading(false)
    }
  }
  const searchGraph = async (query = graphQuery) => {
    const normalizedQuery = query.trim()
    if (!normalizedQuery || graphLoading) return
    setGraphLoading(true)
    setGraphError("")
    try {
      const [statusResponse, response] = await Promise.all([
        fetch("/api/knowledge-graph/status"),
        fetch(`/api/knowledge-graph/search?q=${encodeURIComponent(normalizedQuery)}&limit=10`),
      ])
      const statusData = await statusResponse.json()
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail ?? data.error ?? "知识图谱检索失败")
      setGraphData({ ...data, status: statusData.status, error: statusData.error })
    } catch (error) {
      setGraphData(null)
      setGraphError(error instanceof Error ? error.message : "知识图谱检索失败")
    } finally {
      setGraphLoading(false)
    }
  }
  const setActiveWorkspace = (label: string) => {
    setActiveNav(label)
    setShowMobileSidebar(false)
    setShowMobileContext(false)
    if (label === "知识检索") {
      setKnowledgeQuery("")
      setKnowledgeData(null)
      setKnowledgeError("")
    }
    if (label === "作物档案") {
      const query = `${selectedCrop.name} ${selectedCrop.stage} 管理 病虫害 施肥`
      setKnowledgeQuery(query)
      void searchKnowledge(query)
    }
    if (label === "农情图谱") {
      setGraphQuery(selectedCrop.name)
      setGraphData(null)
      void searchGraph(selectedCrop.name)
    }
    if (label === "病虫害诊断") setInput(`${selectedCrop.name} 在${selectedRegion}出现病斑或异常，请描述症状、发生部位和田间环境。`)
  }
  const startDiagnosis = () => {
    setActiveNav("工作台")
    setInput(`${selectedCrop.name} 在${selectedRegion}出现病斑或异常，请描述症状、发生部位和田间环境。`)
    window.setTimeout(() => inputRef.current?.focus(), 0)
  }
  const selectCrop = (crop: CropOption) => {
    setSelectedCrop(crop)
    setSelectedRegion(crop.region)
    if (activeNav === "作物档案") {
      const query = `${crop.name} ${crop.stage} 管理 病虫害 施肥`
      setKnowledgeQuery(query)
      void searchKnowledge(query)
    }
  }
  const changeRegion = (region: string) => {
    setSelectedRegion(region)
    setSelectedCrop((current) => ({ ...current, region }))
  }
  const startNewSession = () => { setThreadId(`thread_${Date.now()}`); setMessages([]); setInput(""); setAgentActivity([]); setActivityExpanded(false); setActiveSource(null); setShowHistory(false); setActiveNav("工作台") }
  const clearHistory = async () => {
    try {
      const response = await fetch(`/api/history/${threadId}`, { method: "DELETE" })
      if (!response.ok) throw new Error("clear history request failed")
      await refreshThreads()
    } catch (error) { console.error("清空历史失败:", error) }
    setMessages([]); setAgentActivity([]); setActivityExpanded(false); setActiveSource(null); setShowHistory(false)
  }
  const openThread = async (nextThreadId: string) => {
    setShowHistory(false)
    setAgentActivity([])
    setActivityExpanded(false)
    if (nextThreadId === threadId) return
    try {
      const response = await fetch(`/api/history/${nextThreadId}?limit=20`)
      if (!response.ok) throw new Error("history request failed")
      const data = await response.json()
      setThreadId(nextThreadId)
      setActiveNav("工作台")
      setMessages((data.history ?? []).map((item: { role: "user" | "assistant"; content: string; timestamp?: string; extra?: { completion_status?: string; tool_count?: number; decision_card?: Record<string, unknown> } }) => ({ role: item.role, content: item.content, timestamp: item.timestamp ? new Date(item.timestamp) : new Date(), completion_status: item.extra?.completion_status, decisionCard: item.extra?.decision_card })))
    } catch (error) { console.error("加载会话失败:", error) }
  }
  const loadSystemInfo = async () => {
    setSystemInfoLoading(true)
    try {
      const response = await fetch("/api/system/info")
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail ?? "系统信息获取失败")
      setSystemInfo(data)
    } catch (error) {
      setSystemInfo({ error: error instanceof Error ? error.message : "系统信息获取失败" })
    } finally {
      setSystemInfoLoading(false)
    }
  }
  const todayWeather = weatherData?.daily?.[0]
  const rainAmount = typeof todayWeather?.precipitation_mm === "number" ? todayWeather.precipitation_mm : null
  const weatherHeadline = weatherLoading ? "加载中" : typeof todayWeather?.temperature_max_c === "number" ? `${Math.round(todayWeather.temperature_max_c)}°C` : "暂无数据"
  const weatherRisk = rainAmount !== null && rainAmount >= 10 ? "降雨与排水关注" : rainAmount !== null ? "暂无高降雨提醒" : "等待天气数据"
  const weatherRiskDetail = rainAmount !== null ? `今日降水 ${rainAmount.toFixed(1)} mm` : weatherError || "公共天气接口未返回数据"
  const commandFilter = commandQuery.trim().toLowerCase()

  return <div className={cn("app-shell", !showSidebar && "is-sidebar-hidden", !showContext && "is-context-hidden")}>
    <aside className={cn("sidebar", showMobileSidebar && "mobile-open", !showSidebar && "is-collapsed")} aria-label="主导航">
      <div className="brand-lockup"><div className="brand-mark" aria-hidden="true"><Leaf size={18} strokeWidth={2.5} /></div><div><p className="brand-name">CropWise</p><p className="brand-subtitle">JXAU AGRICULTURE AI</p></div><button type="button" className="icon-button sidebar-close" onClick={() => setShowMobileSidebar(false)} aria-label="关闭主导航"><X size={17} /></button></div>
      <div className="agent-status"><span className={cn("status-dot", serviceStatus === "offline" && "is-offline")} /> {serviceStatus === "online" ? "农业智能体在线" : serviceStatus === "checking" ? "正在连接农业服务" : "农业服务离线"}</div>
      <a className="university-card" href="https://www.jxau.edu.cn" target="_blank" rel="noreferrer" aria-label="访问江西农业大学官网"><div className="university-card-top"><div><strong>江西农业大学</strong><small>官方农业智能问答助手</small></div><ShieldCheck size={15} /></div><div className="university-brand-bar" aria-label="江西农业大学官方校名标识"><img src="/branding/jxau-logo.png" alt="江西农业大学" /></div></a>
      <div className="university-news"><div className="news-label"><span>江农动态</span><small>{serviceStatus === "online" ? "已同步" : "等待服务"}</small></div>{jxauNews.length > 0 ? <p>{jxauNews[0].title}</p> : <p>连接后显示江西农业大学官方动态</p>}</div>
      <nav className="nav-group"><p className="nav-label">工作空间</p>{navItems.map((item) => { const Icon = item.icon; return <button key={item.label} type="button" className={cn("nav-item", activeNav === item.label && "is-active")} onClick={() => setActiveWorkspace(item.label)}><Icon size={17} strokeWidth={1.8} /><span>{item.label}</span>{item.label === "知识检索" && <span className="nav-count">KB</span>}</button> })}</nav>
      <div className="sidebar-divider" />
      <nav className="nav-group"><p className="nav-label">最近会话 {threadSummaries.length > 0 && <span className="nav-count">{threadSummaries.length}</span>}</p>{threadSummaries.length > 0 ? threadSummaries.slice(0, 2).map((thread) => <button type="button" className="session-item" key={thread.thread_id} onClick={() => thread.thread_id && void openThread(thread.thread_id)}><History size={15} /><span className="session-copy"><strong>{thread.title || "农业问答会话"}</strong><small>{formatSessionMeta(thread.updated_at, thread.message_count)}</small></span></button>) : <><button type="button" className="session-item is-current" onClick={() => setShowHistory(false)}><span className="session-indicator" /><span className="session-copy"><strong>当前农业问答</strong><small>本地新会话</small></span></button><button type="button" className="session-item" onClick={() => setShowHistory(true)}><History size={15} /><span className="session-copy"><strong>查看历史会话</strong><small>等待服务连接</small></span></button></>}</nav>
      <div className="sidebar-footer"><button type="button" className="footer-action" onClick={() => setShowHistory(true)}><Archive size={16} /> 会话记录</button><button type="button" className="footer-action" onClick={() => { setShowSettings(true); void loadSystemInfo() }}><Settings2 size={16} /> 工作台设置</button><div className="user-profile"><div className="avatar">研</div><div><strong>研究员</strong><small>农业知识项目组</small></div><ChevronDown size={15} /></div></div>
    </aside>

    {showMobileSidebar && <button type="button" className="mobile-sidebar-backdrop" onClick={() => setShowMobileSidebar(false)} aria-label="关闭主导航" />}
    <main className="workspace">
      <header className="topbar"><div className="topbar-leading"><button type="button" className="icon-button desktop-panel-toggle" onClick={() => setShowSidebar((current) => !current)} aria-label={showSidebar ? "隐藏主导航" : "显示主导航"} aria-pressed={!showSidebar} title={showSidebar ? "隐藏主导航" : "显示主导航"}><PanelLeft size={18} /></button><div className="mobile-brand"><button type="button" className="icon-button" onClick={() => setShowMobileSidebar(true)} aria-label="打开导航"><Menu size={19} /></button><img className="mobile-jxau-logo" src="/branding/jxau-favicon.png" alt="江西农业大学校徽" /><span>CropWise</span></div><div className="breadcrumbs"><span>工作台</span><span>/</span><strong>{activeNav}</strong></div></div><div className="topbar-actions"><button type="button" className="icon-button desktop-panel-toggle" onClick={() => setShowContext((current) => !current)} aria-label={showContext ? "隐藏当前农情" : "显示当前农情"} aria-pressed={!showContext} title={showContext ? "隐藏当前农情" : "显示当前农情"}><PanelRight size={18} /></button><button type="button" className="command-trigger" onClick={() => { setCommandQuery(""); setShowCommandPalette(true) }} aria-label="打开命令面板"><Search size={15} /><span>搜索农业知识</span><kbd><Command size={11} /> K</kbd></button><button type="button" className="icon-button" title="帮助" aria-label="帮助" onClick={() => setShowHelp(true)}><HelpCircle size={18} /></button><button type="button" className="new-session" onClick={startNewSession}><Plus size={16} /> 新建会话</button></div></header>
      <div className="workspace-body">
        <section className="conversation" aria-label="农业问答对话">
          <div className="conversation-heading"><div><p className="eyebrow">AI AGRICULTURE WORKSPACE</p><h1>农业知识工作台</h1></div><div className="heading-meta"><span><Database size={14} /> 私有知识库</span><span className="meta-divider" /><span>专业模式</span></div></div>
          <div className="retrieval-route" aria-label="当前检索上下文"><span className="route-label"><Activity size={13} /> 检索路径</span><span className="route-node">{selectedCrop.name}</span><span className="route-arrow">/</span><span className="route-node">{selectedCrop.stage}</span><span className="route-arrow">/</span><span className="route-node">{selectedRegion}</span><span className="route-spacer" /><span className="route-status"><span className="status-dot" /> {serviceStatus === "online" ? "已就绪" : "等待服务"}</span></div>
          <div className="message-list custom-scrollbar">
            {activeNav !== "工作台" ? <WorkspaceToolView activeNav={activeNav} selectedCrop={selectedCrop} knowledgeQuery={knowledgeQuery} setKnowledgeQuery={setKnowledgeQuery} knowledgeData={knowledgeData} knowledgeLoading={knowledgeLoading} knowledgeError={knowledgeError} onKnowledgeSearch={() => void searchKnowledge()} graphQuery={graphQuery} setGraphQuery={setGraphQuery} graphData={graphData} graphLoading={graphLoading} graphError={graphError} onGraphSearch={() => void searchGraph()} onStartDiagnosis={startDiagnosis} /> : messages.length === 0 ? <div className="empty-state"><div className="empty-kicker"><span className="signal-line" /> CONTEXT-AWARE ASSISTANT</div><h2>从现场问题开始，<br /><em>把知识变成行动。</em></h2><p>结合当前作物、生育期与区域背景，检索农业知识库并给出可核验的管理建议。</p><div className="suggestion-grid">{suggestions.map((suggestion) => <button key={suggestion.label} type="button" className="suggestion-card" onClick={() => { setInput(suggestion.text); inputRef.current?.focus() }}><span>{suggestion.label}</span><ArrowUpRight size={16} /><strong>{suggestion.text}</strong></button>)}</div></div> : <div className="messages-stack">{messages.map((message, index) => <article key={`${message.timestamp.toISOString()}-${index}`} className={cn("message-row", message.role === "user" ? "user-row" : "assistant-row")}>{message.role === "assistant" && <div className="assistant-avatar"><Bot size={17} /></div>}<div className={cn("message-content", message.role === "user" && "user-message-content")}><div className="message-meta"><strong>{message.role === "user" ? "你" : "AgriQA Agent"}</strong><time>{formatTime(message.timestamp)}</time>{message.completion_status === "guarded" && <span className="guarded-tag"><ShieldCheck size={12} /> 证据保护</span>}</div><div className={cn("message-bubble", message.role === "user" ? "user-bubble" : "assistant-bubble")}>{message.role === "assistant" ? <AssistantAnswer content={message.content} /> : <p>{message.content}</p>}</div>{message.role === "assistant" && message.decisionCard && <DecisionCard card={message.decisionCard} />}{activityExpanded && message.tool_calls && message.tool_calls.length > 0 && <div className="tool-trace"><Zap size={13} /><span>已完成 {message.tool_calls.length} 项检索动作</span>{message.tool_calls.map((tool, toolIndex) => <code key={`${tool.name}-${toolIndex}`}>{tool.name ?? "knowledge_search"}</code>)}</div>}{message.sources && message.sources.length > 0 && <div className="inline-sources"><span className="source-caption"><BookOpen size={13} /> 支撑来源</span>{message.sources.slice(0, 3).map((source, sourceIndex) => <button type="button" key={`${source.evidence_id ?? source.title}-${sourceIndex}`} onClick={() => setActiveSource(source)}>{source.label ?? source.title ?? `证据 ${sourceIndex + 1}`}</button>)}</div>}</div></article>)}{isLoading && <div className="message-row assistant-row"><div className="assistant-avatar"><Bot size={17} /></div><div className="message-content"><div className="message-meta"><strong>AgriQA Agent</strong><span className="live-label"><span className="status-dot" /> 正在工作</span></div><div className="message-bubble assistant-bubble loading-bubble"><Loader2 size={16} className="spin" /><span>正在检索作物知识与区域依据…</span></div></div></div>}<div ref={messagesEndRef} /></div>}
          </div>
          {agentActivity.length > 0 && <div className={cn("agent-activity-panel", activityExpanded && "is-open")}><button type="button" className="activity-toggle" onClick={() => setActivityExpanded((current) => !current)} aria-expanded={activityExpanded} aria-controls="agent-activity-list"><span className="activity-heading"><Activity size={13} /> Agent 工作记录 <span>{agentActivity.length} 项实时事件</span><ChevronDown size={13} className="activity-chevron" /></span></button><div className="activity-list" id="agent-activity-list">{agentActivity.slice(-6).map((event, index) => <div className="activity-row" key={`${event.type}-${event.name ?? event.stage ?? index}`}><span className={cn("activity-dot", event.status === "running" && "is-running")} /><span>{event.label}</span></div>)}</div></div>}
          <div className="composer-wrap"><form className="composer" onSubmit={handleSubmit}><textarea ref={inputRef} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={handleKeyDown} placeholder="描述你的农业问题…" rows={1} disabled={isLoading} aria-label="输入农业问题" /><div className="composer-footer"><span><span className="context-chip"><Sprout size={13} /> {selectedCrop.name} · {selectedRegion}</span><span className="composer-hint">Enter 发送 · Shift + Enter 换行</span></span><button type="submit" className="send-button" disabled={!input.trim() || isLoading} aria-label="发送问题">{isLoading ? <Loader2 size={17} className="spin" /> : <Send size={17} />}</button></div></form><p className="disclaimer"><ShieldCheck size={12} /> AI 建议仅供农业生产辅助决策，请结合当地技术人员意见与官方标签核验。</p></div>
        </section>
        <aside className={cn("context-panel", showMobileContext && "mobile-open", !showContext && "is-hidden")} aria-label="当前农情上下文"><div className="context-header"><div><p className="eyebrow">FIELD CONTEXT</p><h2>当前农情</h2></div><button type="button" className="icon-button context-close" onClick={() => setShowMobileContext(false)} aria-label="关闭农情面板"><X size={17} /></button></div><div className="location-row"><MapPin size={15} /><select value={selectedRegion} onChange={(event) => changeRegion(event.target.value)} aria-label="切换区域"><option value="赣州">江西省 · 赣州</option><option value="南昌">江西省 · 南昌</option><option value="吉安">江西省 · 吉安</option><option value="九江">江西省 · 九江</option></select><RefreshCw size={13} className={cn(weatherLoading && "spin")} aria-hidden="true" /></div><div className="crop-selector"><p className="section-label">关注作物</p>{cropOptions.map((crop) => <button key={crop.name} type="button" className={cn("crop-row", selectedCrop.name === crop.name && "is-selected")} onClick={() => selectCrop(crop)}><span className={cn("crop-icon", `crop-${crop.tone}`)}><Leaf size={15} /></span><span className="crop-copy"><strong>{crop.name}</strong><small>{crop.stage} · {crop.region}</small></span><span className={cn("crop-health", `health-${crop.tone}`)}>{crop.health}</span></button>)}</div><div className="weather-block"><div className="weather-top"><span className="section-label">今日气象 · {weatherData?.resolved_name ?? selectedRegion}</span><CloudSun size={25} /></div><div className="weather-value">{weatherHeadline}</div><div className="weather-details"><span>最低 {typeof todayWeather?.temperature_min_c === "number" ? `${Math.round(todayWeather.temperature_min_c)}°C` : "--"}</span><span>降水 {rainAmount !== null ? `${rainAmount.toFixed(1)} mm` : "--"}</span><span>风速 {typeof todayWeather?.wind_speed_max_kmh === "number" ? `${Math.round(todayWeather.wind_speed_max_kmh)} km/h` : "--"}</span></div><small className="weather-source">{weatherData?.publisher ?? "Open-Meteo 公共预报"} · {(weatherData?.notice ?? weatherError) || "等待接口返回"}</small></div><div className="risk-block"><div className="panel-section-heading"><span className="section-label">农情提醒</span><span className="risk-count">接口推导</span></div><div className="risk-item"><span className="risk-icon amber"><AlertTriangle size={14} /></span><span><strong>{weatherRisk}</strong><small>{weatherRiskDetail}</small></span></div><div className="risk-item"><span className="risk-icon blue"><CloudSun size={14} /></span><span><strong>风险不替代官方预警</strong><small>农药与灾害决策需核验当地技术意见</small></span></div></div><div className="sources-block"><div className="panel-section-heading"><span className="section-label">回答依据</span><span className="source-count">{latestSources.length || 0} 条</span></div>{latestSources.length === 0 ? <div className="sources-empty"><FileText size={17} /><span>提出问题后，这里会显示可核验来源。</span></div> : latestSources.slice(0, 4).map((source, index) => <button type="button" className="source-row" key={`${source.evidence_id ?? source.title}-${index}`} onClick={() => setActiveSource(source)}><span className="source-index">0{index + 1}</span><span><strong>{source.title ?? source.label ?? "农业知识库"}</strong><small>{source.publisher ?? "已登记来源"} · {source.evidence_level ?? "C"} 级</small></span><ArrowUpRight size={14} /></button>)}</div><div className="context-footer"><button type="button" onClick={() => setShowHistory(true)}><History size={15} /> 查看会话记录</button><button type="button" onClick={clearHistory}><Trash2 size={16} /> 清空当前会话</button></div></aside>
      </div>
    </main>
    {showCommandPalette && <div className="command-backdrop" role="presentation" onClick={() => setShowCommandPalette(false)}><section className="command-palette" role="dialog" aria-modal="true" aria-label="农业知识命令面板" onClick={(event) => event.stopPropagation()}><div className="command-search"><Search size={17} /><input autoFocus value={commandQuery} onChange={(event) => setCommandQuery(event.target.value)} placeholder="搜索动作或农业知识…" aria-label="搜索动作或农业知识" /><kbd>ESC</kbd></div><div className="command-section-label">快捷操作</div>{(!commandFilter || "开始新的农业提问 聚焦输入".includes(commandFilter)) && <button type="button" className="command-row" onClick={() => { setShowCommandPalette(false); setActiveNav("工作台"); window.setTimeout(() => inputRef.current?.focus(), 0) }}><span className="command-icon"><Search size={15} /></span><span><strong>开始新的农业提问</strong><small>聚焦到问题输入框</small></span><kbd>↵</kbd></button>}{(!commandFilter || "查看当前农情 天气风险上下文".includes(commandFilter)) && <button type="button" className="command-row" onClick={() => { setShowCommandPalette(false); setShowContext(true); setShowMobileContext(true) }}><span className="command-icon"><PanelRight size={15} /></span><span><strong>查看当前农情</strong><small>打开实时天气与风险上下文</small></span><kbd>→</kbd></button>}{(!commandFilter || "打开会话记录 历史问题".includes(commandFilter)) && <button type="button" className="command-row" onClick={() => { setShowCommandPalette(false); setShowHistory(true) }}><span className="command-icon"><History size={15} /></span><span><strong>打开会话记录</strong><small>继续最近的农业问题</small></span><kbd>→</kbd></button>}{(!commandFilter || "知识检索 知识库".includes(commandFilter)) && <button type="button" className="command-row" onClick={() => { setShowCommandPalette(false); setActiveWorkspace("知识检索") }}><span className="command-icon"><BookOpen size={15} /></span><span><strong>检索农业知识</strong><small>打开真实知识库检索</small></span><kbd>↵</kbd></button>}<div className="command-footer"><span><Command size={12} /> 命令面板</span><span>{commandFilter ? "按关键词筛选" : "真实工作区入口"}</span></div></section></div>}
    <button type="button" className="mobile-context-toggle" onClick={() => { setShowContext(true); setShowMobileContext(true) }} aria-label="打开当前农情"><PanelRight size={17} /><span>农情</span></button>
    {activeSource && <div className="source-modal-backdrop" role="presentation" onClick={() => setActiveSource(null)}><section className="source-modal" role="dialog" aria-modal="true" aria-label="来源详情" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><p className="eyebrow">SOURCE DETAIL</p><h2>{activeSource.title ?? activeSource.label ?? "农业知识来源"}</h2></div><button type="button" className="icon-button" onClick={() => setActiveSource(null)} aria-label="关闭来源详情"><X size={17} /></button></div><div className="source-detail-grid"><div><span>发布机构</span><strong>{activeSource.publisher ?? "农业知识库"}</strong></div><div><span>证据等级</span><strong>{activeSource.evidence_level ?? "C"} 级 · {activeSource.eligible ? "可引用" : "待核验"}</strong></div><div><span>相关度</span><strong>{typeof activeSource.relevance === "number" ? `${Math.round(activeSource.relevance * 100)}%` : "已匹配"}</strong></div></div><div className="excerpt-box"><FileText size={16} /><p>{activeSource.excerpt ?? "该来源已被检索并参与当前回答。打开原文查看完整上下文。"}</p></div>{activeSource.source_url && <a className="source-link" href={activeSource.source_url} target="_blank" rel="noreferrer">打开原始来源 <ArrowUpRight size={14} /></a>}</section></div>}
    {showHistory && <div className="source-modal-backdrop" role="presentation" onClick={() => setShowHistory(false)}><section className="source-modal history-modal" role="dialog" aria-modal="true" aria-label="会话记录" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><p className="eyebrow">SESSION ARCHIVE</p><h2>会话记录</h2></div><button type="button" className="icon-button" onClick={() => setShowHistory(false)} aria-label="关闭会话记录"><X size={17} /></button></div>{threadSummaries.length > 0 ? <div className="history-list">{threadSummaries.map((thread) => <button type="button" className={cn("history-row", thread.thread_id === threadId && "is-current")} key={thread.thread_id} onClick={() => thread.thread_id && void openThread(thread.thread_id)}><History size={15} /><span><strong>{thread.title || "农业问答会话"}</strong><small>{formatSessionMeta(thread.updated_at, thread.message_count)}</small></span><ArrowUpRight size={14} /></button>)}</div> : <div className="tool-empty"><History size={18} /><span>后端会话接口暂无已保存记录。</span></div>}</section></div>}
    {showSettings && <div className="source-modal-backdrop" role="presentation" onClick={() => setShowSettings(false)}><section className="source-modal workspace-modal" role="dialog" aria-modal="true" aria-label="工作台设置" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><p className="eyebrow">WORKSPACE STATUS</p><h2>工作台设置</h2></div><button type="button" className="icon-button" onClick={() => setShowSettings(false)} aria-label="关闭工作台设置"><X size={17} /></button></div><p className="modal-description">这里展示当前后端实际返回的系统配置，用于确认检索、重排、知识图谱和知识包能力是否已接入。</p>{systemInfoLoading ? <div className="tool-empty"><Loader2 size={18} className="spin" /><span>正在读取系统信息…</span></div> : <pre className="system-info">{JSON.stringify(systemInfo ?? { error: "暂无系统信息" }, null, 2)}</pre>}</section></div>}
    {showHelp && <div className="source-modal-backdrop" role="presentation" onClick={() => setShowHelp(false)}><section className="source-modal workspace-modal" role="dialog" aria-modal="true" aria-label="帮助" onClick={(event) => event.stopPropagation()}><div className="modal-header"><div><p className="eyebrow">SUPPORT</p><h2>使用帮助</h2></div><button type="button" className="icon-button" onClick={() => setShowHelp(false)} aria-label="关闭帮助"><X size={17} /></button></div><div className="help-list"><div><strong>真实问答</strong><span>发送问题后调用 `/api/chat/stream`，回答、检索事件和来源由后端返回。</span></div><div><strong>知识工作区</strong><span>知识检索、作物档案和农情图谱分别调用后端检索接口；服务不可用时页面会显示实际错误。</span></div><div><strong>官方归属</strong><span>江西农业大学官方入口：<a href="https://www.jxau.edu.cn" target="_blank" rel="noreferrer">访问官网</a>。</span></div></div></section></div>}
  </div>
}
