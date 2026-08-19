"use client"

import { AlertTriangle, BookOpenCheck, CheckCircle2, ClipboardCheck, ExternalLink, FileImage, FileText, ListChecks, Loader2, RefreshCw, Search, ShieldAlert, BrainCircuit, ChevronDown } from "lucide-react"
import { useState } from "react"

export type GeneratedUiEvent =
  | { component: "decision-card"; props: { conclusion?: string; summary: string; judgments: string[]; actions: string[]; risks: string[]; followup: string[]; complete: boolean } }
  | { component: "domain-guard"; props: { category: string; reason: string; scope: string; recommendations: string[] } }
  | { component: "knowledge-context"; props: { items: Array<{ title: string; excerpt: string; relevance?: number; eligible?: boolean; evidence_level?: string; eligibility_reason?: string }>; strategy?: string } }
  | { component: "source-list"; props: { items: Array<{ label: string; title: string; excerpt: string; relevance: number; eligible: boolean }> } }
  | { component: "tool-status"; props: { name: string; status: "running" | "complete"; ok?: boolean; errorCode?: string; durationMs?: number } }
  | { component: "time-context"; props: { date: string; localDatetime?: string; timezone?: string; source?: string; isActualNow?: boolean; notice?: string } }
  | { component: "memory-context"; props: { used: Array<{ id?: string; content: string; relevance?: number }>; skipped: Array<{ id?: string; content: string; relevance?: number; reason?: string }>; candidates?: Array<{ id?: string; type?: string; content: string; status?: string }>; organized?: { reason?: string; conflicts?: number; archived?: number }; questions?: string[] } }
  | { component: "runtime-details"; props: { persisted?: boolean; toolCount?: number; knowledgeCount?: number; citationCount?: number; memoryUsedCount?: number; memorySkippedCount?: number; hasTimeContext?: boolean } }
  | { component: "resource-results"; props: { items: Array<{ kind: "image" | "document"; title: string; url: string; source_url: string; license?: string }> } }

export function getToolStatusCopy(name: string, status: "running" | "complete") {
  const labels: Record<string, string> = {
    search_agri_resources: "查找相关图片和公开资料",
    query_crop_knowledge: "匹配农业知识库内容",
    fetch_web_content: "读取公开农业资料",
    calculate_growing_period: "整理农时信息",
    get_current_datetime: "核对当前日期",
  }
  const label = labels[name] || "整理相关信息"
  return status === "running" ? `正在${label}` : `${label}已完成`
}

function safeHttpUrl(value: string) {
  return /^https?:\/\//i.test(value) ? value : null
}

function imageProxyUrl(value: string) {
  return `/api/resource-image?url=${encodeURIComponent(value)}`
}

function DecisionText({ value }: { value: string }) {
  const parts = value.split(/(\*\*[^*]+\*\*)/g)
  return <>{parts.map((part, index) => part.startsWith("**") && part.endsWith("**") ? <strong key={index}>{part.slice(2, -2)}</strong> : part)}</>
}

function ResourcePreview({ item }: { item: { kind: "image" | "document"; title: string; url: string; source_url: string; license?: string } }) {
  const [imageFailed, setImageFailed] = useState(false)
  const resourceUrl = safeHttpUrl(item.url)
  const sourceUrl = safeHttpUrl(item.source_url)
  const [imageSrc, setImageSrc] = useState(() => resourceUrl ? imageProxyUrl(resourceUrl) : null)
  if (!resourceUrl) return null

  return (
    <a href={resourceUrl} target="_blank" rel="noreferrer noopener" className="group overflow-hidden rounded-md border bg-[#fbfcfa] transition-colors hover:border-[#9db9a6] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#17613c]/30">
      <div className="relative flex aspect-[16/9] items-center justify-center overflow-hidden bg-[#eef4ec]">
        {item.kind === "image" && !imageFailed ? (
          <img
            src={imageSrc || resourceUrl}
            alt={item.title}
            loading="lazy"
            onError={() => {
              if (imageSrc && imageSrc !== resourceUrl) setImageSrc(resourceUrl)
              else setImageFailed(true)
            }}
            className="h-full w-full object-contain p-1.5"
          />
        ) : item.kind === "image" ? (
          <div className="flex flex-col items-center gap-1 text-[#718077]"><FileImage className="h-6 w-6" /><span className="text-[10px]">图片暂时无法加载</span></div>
        ) : (
          <div className="flex flex-col items-center gap-1 text-[#17613c]"><FileText className="h-6 w-6" /><span className="text-[10px]">官方文档</span></div>
        )}
      </div>
      <div className="p-2.5">
        <p className="line-clamp-2 text-xs font-medium leading-5 text-[#334d40] group-hover:text-[#a6192e]">{item.title}</p>
        <div className="mt-1 flex items-center justify-between gap-2 text-[10px] text-[#87958b]">
          <span className="truncate">{item.license || "开放资料"}</span>
          {sourceUrl && <span className="inline-flex shrink-0 items-center gap-0.5"><ExternalLink className="h-3 w-3" />来源</span>}
        </div>
      </div>
    </a>
  )
}

export function GenerativeUi({ events }: { events: GeneratedUiEvent[] }) {
  if (events.length === 0) return null

  // The response is the primary object. Runtime traces stay available, but
  // must not compete with the answer or create a stack of peer cards.
  const decision = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "decision-card" }> => event.component === "decision-card")
  const guard = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "domain-guard" }> => event.component === "domain-guard")
  const knowledge = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "knowledge-context" }> => event.component === "knowledge-context")
  const sources = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "source-list" }> => event.component === "source-list")
  const time = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "time-context" }> => event.component === "time-context")
  const memory = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "memory-context" }> => event.component === "memory-context")
  const runtime = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "runtime-details" }> => event.component === "runtime-details")
  const resources = [...events].reverse().find((event): event is Extract<GeneratedUiEvent, { component: "resource-results" }> => event.component === "resource-results")
  const toolMap = new Map<string, Extract<GeneratedUiEvent, { component: "tool-status" }>>()
  events.forEach((event) => { if (event.component === "tool-status") toolMap.set(event.props.name, event) })
  const toolEvents = Array.from(toolMap.values())
  const hasRunningTool = toolEvents.some((event) => event.props.status === "running")
  const hasDetails = Boolean(knowledge || sources || time || memory || runtime || resources || toolEvents.length)
  const sections = decision ? [
    { title: "优先判断", icon: ClipboardCheck, items: decision.props.judgments },
    { title: "现在做什么", icon: ListChecks, items: decision.props.actions },
    { title: "风险边界", icon: ShieldAlert, items: decision.props.risks },
    { title: "复查节点", icon: RefreshCw, items: decision.props.followup },
  ] : []
  const primarySections = sections.slice(0, 2)
  const secondarySections = sections.slice(2)

  return (
    <div className="mb-3 space-y-2">
      {decision && (
        <section className="overflow-hidden rounded-lg border border-[#b9cfbd] bg-white shadow-sm" aria-label="农业回答">
          <div className="flex items-center justify-between gap-3 border-b border-[#dbe6db] bg-[#f3f8f2] px-3 py-2.5">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#17613c]"><ClipboardCheck className="h-4 w-4" /> 农业回答</div>
            <span className={decision.props.complete ? "decision-badge decision-badge-ready" : "decision-badge decision-badge-pending"}>{decision.props.complete ? "信息完整" : "待补充现场信息"}</span>
          </div>
          <div className="border-b border-[#e3ebe1] border-l-4 border-l-[#17613c] bg-[#fbfdf9] px-3 py-3.5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#587363]">结论</p>
            <p className="mt-1.5 text-[15px] font-semibold leading-6 text-[#203a2f]"><DecisionText value={decision.props.conclusion || decision.props.judgments[0] || "先补充关键现场信息，再确定具体措施。"} /></p>
          </div>
          <div className="border-b border-[#e3ebe1] px-3 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#587363]">问题概况</p>
            <p className="mt-1.5 whitespace-pre-line text-sm leading-6 text-[#334d40]"><DecisionText value={decision.props.summary} /></p>
          </div>
          <div className="divide-y divide-[#edf1ec] px-3">
            {primarySections.map(({ title, icon: Icon, items }) => (
              <div key={title} className="py-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-[#315c3d]"><Icon className="h-3.5 w-3.5" />{title}</div>
                <ul className="mt-1.5 space-y-1 text-sm leading-6 text-[#526158]">{items.slice(0, 5).map((item, itemIndex) => <li key={`${title}-${itemIndex}`} className="flex gap-2"><span className="text-[#9bb59f]" aria-hidden="true">•</span><span><DecisionText value={item} /></span></li>)}</ul>
              </div>
            ))}
            {secondarySections.length > 0 && (
              <details className="answer-more border-t border-[#edf1ec]">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 py-3 text-xs font-semibold text-[#526158]">
                  <span>查看风险边界与复查节点</span>
                  <ChevronDown className="h-3.5 w-3.5 text-[#718077]" />
                </summary>
                <div className="divide-y divide-[#edf1ec] pb-1">
                  {secondarySections.map(({ title, icon: Icon, items }) => (
                    <div key={title} className="py-3">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-[#315c3d]"><Icon className="h-3.5 w-3.5" />{title}</div>
                      <ul className="mt-1.5 space-y-1 text-sm leading-6 text-[#526158]">{items.slice(0, 5).map((item, itemIndex) => <li key={`${title}-${itemIndex}`} className="flex gap-2"><span className="text-[#9bb59f]" aria-hidden="true">•</span><span><DecisionText value={item} /></span></li>)}</ul>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        </section>
      )}

      {guard && (
        <section className="overflow-hidden rounded-md border border-[#ead6d8] bg-[#fff9f9]">
          <div className="flex items-center gap-2 border-b border-[#ead6d8] px-3 py-2 text-xs font-semibold text-[#8f2332]"><AlertTriangle className="h-3.5 w-3.5" /> 当前问题不在农业问答范围内</div>
          <div className="space-y-2 px-3 py-2.5 text-xs leading-5 text-[#6d5a5e]"><p>{guard.props.reason}</p><p><span className="font-medium text-[#334d40]">支持范围：</span>{guard.props.scope}</p><div><p className="font-medium text-[#334d40]">可以这样问：</p><ul className="mt-1 list-inside list-disc space-y-0.5">{guard.props.recommendations.slice(0, 3).map((item) => <li key={item}>{item}</li>)}</ul></div></div>
        </section>
      )}

      {hasDetails && (
        <details open={hasRunningTool || undefined} className="overflow-hidden rounded-md border border-[#dbe6db] bg-[#fbfdf9]">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2.5 text-xs font-semibold text-[#526158]"><span className="flex items-center gap-2"><BookOpenCheck className="h-3.5 w-3.5 text-[#17613c]" /> 回答依据与运行详情 <span className="font-normal text-[#87958b]">默认收起，不影响阅读</span></span><ChevronDown className="h-3.5 w-3.5 text-[#718077]" /></summary>
          <div className="space-y-3 border-t border-[#e4ece2] px-3 py-3">
            {knowledge && <div><div className="flex items-center justify-between gap-2 text-xs font-semibold text-[#17613c]"><span>知识库依据</span>{knowledge.props.strategy && <span className="rounded border border-[#cbdacb] px-1.5 py-0.5 text-[10px] font-normal text-[#718077]">{strategyLabel(knowledge.props.strategy)}</span>}</div><div className="mt-2 divide-y divide-[#e4ece2]">{knowledge.props.items.map((item, itemIndex) => <div key={`${item.title}-${itemIndex}`} className="py-2"><div className="flex items-center justify-between gap-2"><p className="text-xs font-medium text-[#334d40]">{item.title}</p>{item.eligible === false ? <span className="shrink-0 text-[10px] text-[#8f2332]">待官方核验</span> : item.eligible === true ? <span className="shrink-0 text-[10px] text-[#17613c]">可引用</span> : null}</div><p className="mt-1 line-clamp-2 text-xs leading-5 text-[#718077]">{item.excerpt || "已匹配到相关农业知识。"}</p><div className="mt-2 flex items-center gap-2 text-[10px] text-[#87958b]"><span className="h-1.5 flex-1 overflow-hidden rounded-full bg-[#e3ebe1]"><span className="block h-full rounded-full bg-[#6d9b75]" style={{ width: `${Math.max(8, Math.min(100, Math.round((item.relevance ?? 0.5) * 100)))}%` }} /></span><span>{item.relevance !== undefined ? `匹配度 ${Math.round(item.relevance * 100)}%` : "知识库依据"}</span></div></div>)}</div></div>}
            {sources && <div className="border-t border-[#edf1ec] pt-2"><p className="text-xs font-semibold text-[#17613c]">可追溯来源</p><div className="mt-2 divide-y divide-[#e4ece2]">{sources.props.items.map((item) => <div key={item.label} className="py-2"><div className="flex items-center justify-between gap-2 text-xs font-medium text-[#334d40]"><span>[{item.label}] {item.title}</span><span className={item.eligible ? "text-[#17613c]" : "text-[#8b6f35]"}>{item.eligible ? "达标引用" : "待核验"}</span></div><p className="mt-1 text-xs leading-5 text-[#718077]">{item.excerpt}</p></div>)}</div></div>}
            {time && (() => { const actual = time.props.isActualNow === true; return <div className="flex items-center justify-between gap-2 border-t border-[#edf1ec] pt-2 text-xs text-[#52705c]" role="status"><span>{actual ? "服务端当前时间" : "用户指定评估日期"}：{time.props.date}{time.props.timezone ? ` · ${time.props.timezone}` : ""}</span><span className="text-[10px] text-[#87958b]">{actual ? "系统时钟" : "不代表当前日期"}</span></div> })()}
            {runtime && <div className="border-t border-[#edf1ec] pt-2 text-xs leading-5 text-[#718077]"><p className="font-semibold text-[#526158]">历史运行摘要</p>{runtime.props.persisted === false ? <p className="mt-1">该历史消息未保存工具与检索明细，仅保留主回答。</p> : <p className="mt-1">工具 {runtime.props.toolCount || 0} 次 · 知识库片段 {runtime.props.knowledgeCount || 0} 条 · 引用 {runtime.props.citationCount || 0} 条 · 记忆采用 {runtime.props.memoryUsedCount || 0} 条{runtime.props.hasTimeContext ? " · 已核对时间" : ""}</p>}</div>}
            {memory && <MemoryContext {...memory.props} />}
            {toolEvents.length > 0 && <div className="border-t border-[#edf1ec] pt-2" role="status" aria-live="polite"><p className="text-xs font-semibold text-[#17613c]">服务运行状态</p><div className="mt-1.5 space-y-1">{toolEvents.map((event) => <div key={event.props.name} className="flex items-center gap-2 text-xs text-[#627168]">{event.props.status === "running" ? <Loader2 className="h-3.5 w-3.5 animate-spin text-[#17613c]" /> : event.props.ok === false ? <AlertTriangle className="h-3.5 w-3.5 text-[#a6192e]" /> : <CheckCircle2 className="h-3.5 w-3.5 text-[#17613c]" />}<span className="min-w-0 flex-1">{event.props.status === "running" ? getToolStatusCopy(event.props.name, "running") : event.props.ok === false ? `${getToolStatusCopy(event.props.name, "complete")}失败` : getToolStatusCopy(event.props.name, "complete")}</span>{event.props.durationMs !== undefined && <span className="text-[10px] text-[#87958b]">{Math.round(event.props.durationMs)} ms</span>}</div>)}</div></div>}
            {resources && resources.props.items.length > 0 && <div className="border-t border-[#edf1ec] pt-2"><p className="text-xs font-semibold text-[#17613c]">相关图片与资料</p><div className="mt-2 grid gap-2 sm:grid-cols-2">{resources.props.items.map((item, itemIndex) => <ResourcePreview key={`${item.url}-${itemIndex}`} item={item} />)}</div></div>}
          </div>
        </details>
      )}
    </div>
  )
}

function strategyLabel(strategy: string) {
  return ({
    hybrid: "混合检索",
    "hybrid-temporal": "混合检索 · 时间推理",
    "hybrid-metadata": "混合检索 · 元数据过滤",
    vector: "向量检索",
  } as Record<string, string>)[strategy] || strategy
}

function MemoryContext({ used, skipped, candidates = [], organized, questions = [] }: { used: Array<{ id?: string; content: string; relevance?: number }>; skipped: Array<{ id?: string; content: string; relevance?: number; reason?: string }>; candidates?: Array<{ id?: string; type?: string; content: string; status?: string }>; organized?: { reason?: string; conflicts?: number; archived?: number }; questions?: string[] }) {
  const [open, setOpen] = useState(false)
  if (used.length === 0 && skipped.length === 0 && candidates.length === 0) return null
  return (
    <section className="overflow-hidden rounded-md border border-[#dbe6db] bg-[#fbfdf9]">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-xs font-semibold text-[#315c3d]" aria-expanded={open}>
        <span className="flex items-center gap-2"><BrainCircuit className="h-3.5 w-3.5" />本轮记忆依据<span className="font-normal text-[#87958b]">相关不等于相似</span></span>
        <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="space-y-2 border-t border-[#e4ece2] px-3 py-2.5 text-xs leading-5">
        {organized && <p className="rounded border border-[#dbe6db] bg-[#f3f8f2] px-2 py-1.5 text-[#526158]">已触发记忆整理：{organized.reason === "count_or_conflict" ? "达到数量或冲突临界点" : "按需整理"}，归档 {organized.archived || 0} 条{organized.conflicts ? `，检测到 ${organized.conflicts} 个冲突维度` : ""}。</p>}
        {questions.length > 0 && <div className="rounded border border-[#f1d9a7] bg-[#fffaf0] px-2 py-1.5 text-[#765a24]"><p className="font-semibold text-[#8b6518]">主动补充关键信息</p><ul className="mt-1 space-y-1">{questions.map((question) => <li key={question}>- {question}</li>)}</ul></div>}
        {used.length > 0 && <div><p className="font-semibold text-[#17613c]">已用于本轮</p><ul className="mt-1 space-y-1 text-[#526158]">{used.map((item) => <li key={item.id || item.content}>- {item.content}{item.relevance !== undefined ? ` · 相关性 ${Math.round(item.relevance * 100)}%` : ""}</li>)}</ul></div>}
        {skipped.length > 0 && <div><p className="font-semibold text-[#718077]">相似但未使用</p><ul className="mt-1 space-y-1 text-[#87958b]">{skipped.map((item) => <li key={item.id || item.content}>- {item.content}{item.reason ? ` · ${item.reason}` : ""}</li>)}</ul></div>}
        {candidates.length > 0 && <div><p className="font-semibold text-[#8f2332]">待确认</p><ul className="mt-1 space-y-1 text-[#6d5a5e]">{candidates.map((item) => <li key={item.id || item.content}>- {item.content}</li>)}</ul></div>}
      </div>}
    </section>
  )
}
