"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { ArrowLeft, CheckCircle2, ChevronLeft, ChevronRight, ClipboardCheck, Download, Loader2, RefreshCw, ShieldCheck } from "lucide-react"

type Scenario = "diagnosis" | "fertilizer" | "weather" | "policy" | "safety"

interface EvalItem {
  id: string
  question: string
  scenario: Scenario
  crop: string | null
  region: string | null
  stage: string | null
  expected_sources: string[]
  forbidden_claims: string[]
  review_status: "pending" | "expert_approved"
  reviewer: string | null
  gold_evidence_ids: string[]
  retrieval_relevant: boolean | null
  citation_covered: boolean | null
  faithful: boolean | null
  safety_ok: boolean | null
}

interface Candidate {
  evidenceId: string
  title: string
  excerpt: string
  sourceUrl?: string
  evidenceLevel: string
  evidenceScope: string
  eligible: boolean
}

interface Metrics {
  expert_labeled_items: number
  candidate_retrieval_rate: number
  traceable_candidate_retrieval_rate: number
  official_candidate_retrieval_rate: number
  scenario_coverage: Partial<Record<Scenario, {
    items: number
    traceable_candidate_retrieval_rate: number
    official_candidate_retrieval_rate: number
  }>>
  recall_at_k: number | null
  citation_coverage: number | null
  faithfulness_rate: number | null
  safety_coverage: number | null
  quality_status: string
}

const scenarioLabels: Record<Scenario, string> = {
  diagnosis: "病虫害诊断",
  fertilizer: "施肥灌溉",
  weather: "农时天气",
  policy: "政策核验",
  safety: "安全边界",
}

function metric(value: number | null) {
  return value === null ? "待专家标注" : `${Math.round(value * 100)}%`
}

export default function EvaluationsPage() {
  const [items, setItems] = useState<EvalItem[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [scenario, setScenario] = useState<Scenario | "all">("all")
  const [index, setIndex] = useState(0)
  const [reviewer, setReviewer] = useState("")
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [selectedEvidence, setSelectedEvidence] = useState<string[]>([])
  const [retrievalRelevant, setRetrievalRelevant] = useState(true)
  const [citationCovered, setCitationCovered] = useState(true)
  const [faithful, setFaithful] = useState(true)
  const [safetyOk, setSafetyOk] = useState(true)
  const [busy, setBusy] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState("")

  const filtered = useMemo(() => scenario === "all" ? items : items.filter((item) => item.scenario === scenario), [items, scenario])
  const current = filtered[Math.min(index, Math.max(0, filtered.length - 1))]

  const refreshMetrics = useCallback(async () => {
    const response = await fetch("/api/evaluations/retrieval?limit=120")
    if (response.ok) setMetrics(await response.json() as Metrics)
  }, [])

  const loadItems = useCallback(async () => {
    setBusy(true)
    try {
      const response = await fetch("/api/evaluations/items?limit=120")
      if (!response.ok) throw new Error("无法读取评测队列")
      const payload = await response.json() as { items: EvalItem[] }
      setItems(payload.items)
      await refreshMetrics()
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "读取评测队列失败")
    } finally {
      setBusy(false)
    }
  }, [refreshMetrics])

  useEffect(() => { void loadItems() }, [loadItems])
  useEffect(() => { setIndex(0) }, [scenario])

  useEffect(() => {
    if (!current) return
    setCandidates([])
    setSelectedEvidence(current.gold_evidence_ids || [])
    setRetrievalRelevant(current.retrieval_relevant ?? true)
    setCitationCovered(current.citation_covered ?? true)
    setFaithful(current.faithful ?? true)
    setSafetyOk(current.safety_ok ?? true)
    setNotice("")
    const controller = new AbortController()
    void fetch(`/api/knowledge-base/search?query=${encodeURIComponent(current.question)}&limit=5`, { signal: controller.signal })
      .then(async (response) => response.ok ? response.json() : Promise.reject(new Error("无法获取候选证据")))
      .then((payload: { results?: Array<{ content?: string; metadata?: Record<string, unknown>; relevance?: number }>; citations?: Array<{ eligible?: boolean }> }) => {
        const rows = payload.results || []
        setCandidates(rows.flatMap((row, rowIndex) => {
          const metadata = row.metadata || {}
          const evidenceId = typeof metadata.evidence_id === "string" ? metadata.evidence_id : ""
          if (!evidenceId) return []
          return [{
            evidenceId,
            title: typeof metadata.title === "string" ? metadata.title : typeof metadata.source === "string" ? metadata.source : "农业知识库",
            excerpt: typeof row.content === "string" ? row.content.slice(0, 220) : "",
            sourceUrl: typeof metadata.source_url === "string" ? metadata.source_url : undefined,
            evidenceLevel: typeof metadata.evidence_level === "string" ? metadata.evidence_level : "C",
            evidenceScope: typeof metadata.evidence_scope === "string" ? metadata.evidence_scope : "未声明",
            eligible: payload.citations?.[rowIndex]?.eligible === true,
          }]
        }))
      })
      .catch((error: Error) => { if (error.name !== "AbortError") setNotice(error.message) })
    return () => controller.abort()
  }, [current])

  const toggleEvidence = (evidenceId: string) => setSelectedEvidence((currentIds) => currentIds.includes(evidenceId) ? currentIds.filter((id) => id !== evidenceId) : [...currentIds, evidenceId])

  const submit = async () => {
    if (!current || !reviewer.trim() || selectedEvidence.length === 0) {
      setNotice("请填写审核人并选择至少一条真实证据")
      return
    }
    setSaving(true)
    setNotice("")
    try {
      const response = await fetch(`/api/evaluations/items/${encodeURIComponent(current.id)}/annotation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer: reviewer.trim(), gold_evidence_ids: selectedEvidence, retrieval_relevant: retrievalRelevant, citation_covered: citationCovered, faithful, safety_ok: safetyOk }),
      })
      if (!response.ok) throw new Error((await response.json() as { detail?: string }).detail || "保存审核失败")
      const payload = await response.json() as { item: EvalItem }
      setItems((currentItems) => currentItems.map((item) => item.id === payload.item.id ? payload.item : item))
      await refreshMetrics()
      setNotice("已保存专家审核")
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "保存审核失败")
    } finally {
      setSaving(false)
    }
  }

  const exportReviewQueue = async () => {
    setNotice("")
    try {
      const suffix = scenario === "all" ? "" : `?scenario=${encodeURIComponent(scenario)}`
      const response = await fetch(`/api/evaluations/review-queue${suffix}`)
      if (!response.ok) throw new Error("无法导出审核包")
      const payload = await response.json()
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = `cropwise-agriir-review-queue-${scenario}.json`
      link.click()
      URL.revokeObjectURL(url)
      setNotice("已导出只读审核包，导出内容不包含金标准标签")
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "无法导出审核包")
    }
  }

  if (busy) return <main className="app-shell flex min-h-[100dvh] items-center justify-center"><Loader2 className="h-6 w-6 animate-spin text-[#17613c]" /></main>

  return (
    <main className="app-shell min-h-[100dvh] px-4 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto max-w-6xl">
        <nav className="mb-7 flex items-center justify-between gap-3"><Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-[#17613c] hover:text-[#10462c]"><ArrowLeft className="h-4 w-4" />返回 CropWise</Link><span className="flex items-center gap-2 text-xs text-[#718077]"><ShieldCheck className="h-4 w-4 text-[#17613c]" />专家审核工作台</span></nav>
        <header className="border-b border-[#d8e0d6] pb-5"><p className="section-kicker">证据评测 / P0</p><h1 className="mt-2 text-3xl font-semibold text-[#203a2f]">AgriIR 证据审核</h1><p className="mt-2 text-sm leading-6 text-[#5c6c63]">只有已审核通过的真实证据进入质量指标。</p></header>

        <section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
          {[['专家已审', metrics?.expert_labeled_items ?? 0], ['可溯源候选', metric(metrics?.traceable_candidate_retrieval_rate ?? null)], ['A 级候选', metric(metrics?.official_candidate_retrieval_rate ?? null)], ['Recall@K', metric(metrics?.recall_at_k ?? null)], ['引用覆盖率', metric(metrics?.citation_coverage ?? null)], ['忠实度', metric(metrics?.faithfulness_rate ?? null)], ['安全覆盖率', metric(metrics?.safety_coverage ?? null)]].map(([label, value]) => <div key={String(label)} className="rounded-md border border-[#dbe6db] bg-white px-3 py-3"><p className="text-xs text-[#718077]">{label}</p><p className="mt-1 text-lg font-semibold text-[#203a2f]">{value}</p></div>)}
        </section>

        {metrics?.scenario_coverage && <section className="mt-5 overflow-x-auto border-y border-[#d8e4d8] py-4">
          <p className="text-xs font-semibold text-[#315c3d]">场景证据覆盖</p>
          <table className="mt-2 w-full min-w-[520px] text-left text-xs text-[#526158]">
            <thead className="text-[#718077]"><tr><th className="pb-2 font-medium">场景</th><th className="pb-2 font-medium">条目</th><th className="pb-2 font-medium">可溯源候选</th><th className="pb-2 font-medium">A 级候选</th></tr></thead>
            <tbody>{(Object.entries(metrics.scenario_coverage) as Array<[Scenario, NonNullable<Metrics["scenario_coverage"][Scenario]>]>).map(([key, coverage]) => <tr key={key} className="border-t border-[#edf2ec]"><td className="py-2 font-medium text-[#405248]">{scenarioLabels[key]}</td><td className="py-2">{coverage.items}</td><td className="py-2">{metric(coverage.traceable_candidate_retrieval_rate)}</td><td className="py-2">{metric(coverage.official_candidate_retrieval_rate)}</td></tr>)}</tbody>
          </table>
        </section>}

        <div className="mt-5 flex flex-wrap items-center gap-2" role="tablist" aria-label="评测场景筛选">
          {(["all", "diagnosis", "fertilizer", "weather", "policy", "safety"] as const).map((value) => <button key={value} type="button" onClick={() => setScenario(value)} className={scenario === value ? "rounded-md bg-[#17613c] px-3 py-2 text-xs font-medium text-white" : "rounded-md border border-[#d8e4d8] bg-white px-3 py-2 text-xs font-medium text-[#526158] hover:border-[#9db9a6]"}>{value === "all" ? "全部" : scenarioLabels[value]}</button>)}
          <button type="button" onClick={() => void exportReviewQueue()} className="ml-auto inline-flex items-center gap-1.5 rounded-md border border-[#d8e4d8] bg-white px-3 py-2 text-xs font-medium text-[#17613c] hover:border-[#9db9a6]"><Download className="h-3.5 w-3.5" />导出审核包</button>
        </div>

        {current && <div className="mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
          <section className="rounded-lg border border-[#dbe6db] bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3"><div><p className="text-xs font-medium text-[#587363]">{scenarioLabels[current.scenario]} · {current.id}</p><h2 className="mt-2 text-lg font-semibold leading-7 text-[#203a2f]">{current.question}</h2></div><span className={current.review_status === "expert_approved" ? "shrink-0 rounded border border-[#b7d4bd] bg-[#f3faf4] px-2 py-1 text-xs text-[#17613c]" : "shrink-0 rounded border border-[#ead8aa] bg-[#fffcf0] px-2 py-1 text-xs text-[#7d6425]"}>{current.review_status === "expert_approved" ? "已审核" : "待审核"}</span></div>
            <div className="mt-4 grid gap-2 text-xs text-[#5c6c63] sm:grid-cols-3"><p>作物：{current.crop || "待补充"}</p><p>地区：{current.region || "待补充"}</p><p>时期：{current.stage || "待补充"}</p></div>
            <div className="mt-5 border-t border-[#e5ece3] pt-4">
              <p className="text-xs font-semibold text-[#315c3d]">候选证据</p>
              {candidates.length === 0 ? <p className="mt-2 text-sm text-[#718077]">本次检索未返回带 evidence_id 的候选材料。</p> : (
                <div className="mt-3 space-y-2">
                  {candidates.map((candidate) => <label key={candidate.evidenceId} className="block cursor-pointer rounded-md border border-[#dbe6db] p-3 hover:border-[#9db9a6]">
                    <span className="flex gap-3">
                      <input type="checkbox" checked={selectedEvidence.includes(candidate.evidenceId)} onChange={() => toggleEvidence(candidate.evidenceId)} className="mt-0.5 h-4 w-4 accent-[#17613c]" />
                      <span className="min-w-0">
                        <span className="flex flex-wrap items-center gap-2 text-xs font-semibold text-[#334d40]">{candidate.title}<span className={candidate.evidenceLevel === "A" ? "text-[#17613c]" : "text-[#8b6f35]"}>{candidate.evidenceLevel} 级</span>{candidate.eligible && <CheckCircle2 className="h-3.5 w-3.5 text-[#17613c]" />}</span>
                        <span className="mt-1 block text-xs leading-5 text-[#718077]">{candidate.excerpt}</span>
                        <span className="mt-2 block font-mono text-[10px] text-[#87958b]">{candidate.evidenceId} · {candidate.evidenceScope}</span>
                        {candidate.sourceUrl && <a href={candidate.sourceUrl} target="_blank" rel="noreferrer noopener" onClick={(event) => event.stopPropagation()} className="mt-1 inline-block text-xs font-medium text-[#a6192e] hover:text-[#811225]">查看原文</a>}
                      </span>
                    </span>
                  </label>)}
                </div>
              )}
            </div>
          </section>

          <aside className="rounded-lg border border-[#dbe6db] bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 text-base font-semibold text-[#203a2f]"><ClipboardCheck className="h-4 w-4 text-[#17613c]" />审核结论</h2><label className="mt-4 block text-xs font-medium text-[#526158]">审核人<input value={reviewer} onChange={(event) => setReviewer(event.target.value)} className="mt-1.5 w-full rounded-md border border-[#cfdccf] px-3 py-2 text-sm text-[#203a2f] outline-none focus:border-[#17613c]" placeholder="姓名或专家编号" /></label><div className="mt-4 space-y-3">{([['retrieval', '检索结果命中金标准', retrievalRelevant, setRetrievalRelevant], ['citation', '关键结论有引用', citationCovered, setCitationCovered], ['faithful', '回答忠实于证据', faithful, setFaithful], ['safety', '安全边界充分', safetyOk, setSafetyOk]] as const).map(([key, label, value, setValue]) => <label key={key} className="flex cursor-pointer items-center justify-between gap-3 text-sm text-[#405248]"><span>{label}</span><input type="checkbox" checked={value} onChange={(event) => setValue(event.target.checked)} className="h-4 w-4 accent-[#17613c]" /></label>)}</div><button type="button" onClick={() => void submit()} disabled={saving} className="mt-6 flex w-full items-center justify-center gap-2 rounded-md bg-[#17613c] px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[#10462c] disabled:cursor-not-allowed disabled:bg-[#97aa9a]">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}{saving ? "保存中" : "提交专家审核"}</button>{notice && <p className="mt-3 text-xs leading-5 text-[#6b5640]" role="status">{notice}</p>}<div className="mt-6 flex items-center justify-between border-t border-[#e5ece3] pt-4"><button type="button" onClick={() => setIndex((value) => Math.max(0, value - 1))} disabled={index === 0} className="rounded-md border p-2 text-[#526158] disabled:opacity-40" aria-label="上一题"><ChevronLeft className="h-4 w-4" /></button><span className="text-xs text-[#718077]">{index + 1} / {filtered.length}</span><button type="button" onClick={() => setIndex((value) => Math.min(filtered.length - 1, value + 1))} disabled={index >= filtered.length - 1} className="rounded-md border p-2 text-[#526158] disabled:opacity-40" aria-label="下一题"><ChevronRight className="h-4 w-4" /></button></div><button type="button" onClick={() => void loadItems()} className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[#17613c]"><RefreshCw className="h-3.5 w-3.5" />刷新队列</button></aside>
        </div>}
      </div>
    </main>
  )
}
