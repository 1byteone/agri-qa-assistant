"use client"

import { FormEvent, useMemo, useState } from "react"
import { AlertTriangle, CheckCircle2, ExternalLink, Loader2, Send, ShieldCheck } from "lucide-react"
import { MarkdownMessage } from "@/components/markdown-message"

type ServiceKind = "diagnosis" | "calendar" | "policy"

type Source = {
  title?: string
  source_url?: string
  url?: string
  evidence_level?: string
  published_at?: string
  metadata?: {
    source_url?: string
    published_at?: string
  }
}

type ServiceWorkflowProps = {
  kind: ServiceKind
}

const definitions = {
  diagnosis: {
    label: "提交诊断线索",
    intro: "系统会整理线索、给出鉴别方向和复查步骤；现场图片和植保人员复核仍是确诊依据。",
    fields: [
      ["crop", "作物与品种", "水稻"],
      ["region", "种植地区", "江西南昌"],
      ["stage", "生育期", "分蘖期"],
      ["symptom", "症状、部位与扩散范围", "如：下部叶片有褐色条斑，3 天内约 10% 植株出现"],
      ["context", "近期天气、施肥或用药情况（可选）", "如：连续阴雨；7 天前追施氮肥"],
    ],
    buildPrompt: (values: Record<string, string>) => `农业场景：作物诊断。作物与品种：${values.crop}。地区：${values.region}。生育期：${values.stage}。症状：${values.symptom}。近期田间情况：${values.context || "未提供"}。
请严格按“现场摘要、最多三个可能原因及区分线索、今天和 48 小时内的排查动作、风险边界、复查节点、需要补充的信息”回答。不要把文字描述或图片直接作为确诊依据；涉及农药时不得给出未核验的商品、剂量或混配结论，并提示以当地登记信息和植保部门意见为准。`,
    safety: "诊断结果是鉴别与排查建议，不替代田间取样、实验室检测或植保人员判断。",
  },
  calendar: {
    label: "生成农时安排",
    intro: "系统会按地区、作物、生育期和计划目标生成顺序安排，并请求天气工具给出近期风险提示。",
    fields: [
      ["crop", "作物与品种", "水稻"],
      ["region", "县市或种植地区", "江西南昌"],
      ["stage", "当前生育期或前茬情况", "备耕期"],
      ["goal", "本次农事目标", "安排播种、移栽和第一次田间管理"],
      ["date", "计划日期或时间窗口（可选）", "未来 7 天"],
    ],
    buildPrompt: (values: Record<string, string>) => `农业场景：农时查询。作物与品种：${values.crop}。地区：${values.region}。当前生育期或前茬：${values.stage}。目标：${values.goal}。计划日期或窗口：${values.date || "按当前日期"}。
请调用当前日期和农业气象工具，按“建议时间窗口、分步农事安排、天气风险与暂停条件、错过窗口后的替代方案、复查节点、官方气象预警核验入口”回答。公开天气预报仅作参考，灾害预警必须提示以气象部门最新发布为准；不要把通用农时规则说成县域强制日期。`,
    safety: "天气数据属于公共预报参考；霜冻、暴雨、高温等灾害风险须以当地气象部门预警为准。",
  },
  policy: {
    label: "核验政策线索",
    intro: "系统会优先检索已入库的官方证据，区分已核验事实、待核验事项和正式办理入口。",
    fields: [
      ["region", "办理地区", "江西省"],
      ["topic", "政策主题或项目名称", "粮食生产支持"],
      ["audience", "申请主体或适用对象", "种植主体"],
      ["period", "关注年份或有效期", "2026 年"],
      ["question", "需要核验的事项", "申报条件、材料、截止日期和官方入口"],
    ],
    buildPrompt: (values: Record<string, string>) => `农业场景：政策咨询。地区：${values.region}。政策主题或项目：${values.topic}。申请主体：${values.audience}。关注时间：${values.period}。需要核验：${values.question}。
请仅基于可追溯的官方证据回答，并分为“已核验信息、仍需核验的信息、正式办理前应确认的材料/窗口、官方来源与发布日期/有效期”。没有 A 级官方证据时，明确说明不能确认，不得编造补贴标准、申报资格、截止日期或办理结论。`,
    safety: "政策资格、补贴金额、申报截止日和受理方式以办事地政府最新公告及受理窗口答复为准。",
  },
} as const

function makeThreadId(kind: ServiceKind) {
  return `service_${kind}_${crypto.randomUUID()}`
}

export function ServiceWorkflow({ kind }: ServiceWorkflowProps) {
  const definition = definitions[kind]
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(definition.fields.map(([key, , value]) => [key, value])))
  const [threadId] = useState(() => makeThreadId(kind))
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState<Source[]>([])
  const [completionStatus, setCompletionStatus] = useState<"complete" | "fallback" | "error" | "guarded" | null>(null)
  const [error, setError] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const requiredFields = useMemo(() => definition.fields.slice(0, 4).map(([key]) => key), [definition.fields])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (requiredFields.some((field) => !values[field]?.trim())) return
    setSubmitting(true)
    setError("")
    setAnswer("")
    setSources([])
    setCompletionStatus(null)
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: definition.buildPrompt(values),
          thread_id: threadId,
          answer_mode: "professional",
          scenario_context: { service: kind, ...values },
        }),
      })
      const payload = await response.json() as { message?: string; sources?: Source[]; completion_status?: "complete" | "fallback" | "error" | "guarded"; detail?: string }
      if (!response.ok || !payload.message) throw new Error(payload.detail || "服务暂时无法完成，请稍后重试。")
      setAnswer(payload.message)
      setSources(Array.isArray(payload.sources) ? payload.sources : [])
      setCompletionStatus(payload.completion_status || "complete")
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "服务暂时无法完成，请稍后重试。")
    } finally {
      setSubmitting(false)
    }
  }

  return <>
    <section className="rounded-lg border bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#17613c]" />
        <div><h2 className="text-base font-semibold text-[#263f33]">{definition.label}</h2><p className="mt-1 text-sm leading-6 text-[#5c6c63]">{definition.intro}</p></div>
      </div>
      <form className="mt-5 grid gap-3 sm:grid-cols-2" onSubmit={submit}>
        {definition.fields.map(([key, label, placeholder], index) => {
          const multiline = index === 3 || key === "context" || key === "question"
          const required = requiredFields.includes(key)
          return <label key={key} className={`text-xs font-medium text-[#526158] ${multiline ? "sm:col-span-2" : ""}`}>{label}
            {multiline ? <textarea value={values[key] || ""} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.value }))} required={required} className="field-input mt-1 min-h-24 resize-y" placeholder={placeholder} /> : <input value={values[key] || ""} onChange={(event) => setValues((current) => ({ ...current, [key]: event.target.value }))} required={required} className="field-input mt-1" placeholder={placeholder} />}
          </label>
        })}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[#e5ebe3] pt-4 sm:col-span-2">
          <p className="max-w-xl text-xs leading-5 text-[#718077]">{definition.safety}</p>
          <button type="submit" disabled={submitting} className="primary-button inline-flex min-h-11 items-center gap-2 px-4 disabled:cursor-not-allowed disabled:opacity-60">
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}{submitting ? "正在检索与生成" : definition.label}
          </button>
        </div>
      </form>
    </section>

    {error && <section className="rounded-lg border border-[#e7b7ba] bg-[#fff8f8] p-4 text-sm text-[#8c1b28]" role="alert"><span className="flex items-center gap-2 font-medium"><AlertTriangle className="h-4 w-4" />{error}</span></section>}

    {answer && <section className="rounded-lg border bg-white p-5 shadow-sm" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e5ebe3] pb-3"><h2 className="text-base font-semibold text-[#263f33]">服务结果</h2><span className={`inline-flex items-center gap-1 text-xs font-medium ${completionStatus === "guarded" ? "text-[#a66b12]" : "text-[#17613c]"}`}><CheckCircle2 className="h-4 w-4" />{completionStatus === "guarded" ? "已启用证据安全边界" : "已完成检索"}</span></div>
      <div className="mt-4"><MarkdownMessage content={answer} /></div>
      <div className="mt-5 border-t border-[#e5ebe3] pt-4"><h3 className="text-sm font-semibold text-[#263f33]">可追溯来源</h3>
        {sources.length ? <ul className="mt-2 space-y-2">{sources.map((source, index) => {
          const sourceUrl = source.source_url || source.url || source.metadata?.source_url
          const publishedAt = source.published_at || source.metadata?.published_at
          return <li key={`${sourceUrl || source.title || "source"}-${index}`} className="flex items-start justify-between gap-3 text-sm"><span className="min-w-0 text-[#5c6c63]"><span className="font-medium text-[#33483b]">{source.title || "检索来源"}</span>{source.evidence_level ? <span className="ml-2 text-xs text-[#718077]">{source.evidence_level} 级证据</span> : null}{publishedAt ? <span className="ml-2 text-xs text-[#718077]">{publishedAt}</span> : null}</span>{sourceUrl ? <a href={sourceUrl} target="_blank" rel="noreferrer noopener" className="shrink-0 text-[#a6192e] hover:text-[#811225]" aria-label="打开来源"><ExternalLink className="h-4 w-4" /></a> : null}</li>
        })}</ul> : <p className="mt-2 text-sm text-[#718077]">本次回答未返回可展示来源；涉及政策、用药或高风险农事时请先完成官方核验。</p>}
      </div>
    </section>}
  </>
}
