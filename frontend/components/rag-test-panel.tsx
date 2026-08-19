"use client"

import { useEffect, useMemo, useState } from "react"
import { Check, Clipboard, FlaskConical, Search, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface RagTestPrompt {
  id: string
  category: string
  prompt: string
  intent: string
  difficulty: "基础" | "进阶" | "边界"
  expected: string[]
}

interface RagTestPanelProps {
  open: boolean
  onClose: () => void
  onUsePrompt: (prompt: string) => void
}

export function RagTestPanel({ open, onClose, onUsePrompt }: RagTestPanelProps) {
  const [prompts, setPrompts] = useState<RagTestPrompt[]>([])
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("全部")
  const [difficulty, setDifficulty] = useState("全部")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [copiedId, setCopiedId] = useState<string | null>(null)

  useEffect(() => {
    if (!open || prompts.length > 0 || loading) return
    setLoading(true)
    fetch("/api/rag-test-prompts")
      .then(async (response) => {
        if (!response.ok) throw new Error("测试提示词文件暂不可用")
        const data = await response.json() as { prompts?: RagTestPrompt[] }
        setPrompts(Array.isArray(data.prompts) ? data.prompts : [])
      })
      .catch(() => setError("无法读取测试提示词，请检查 docs/agri-rag-test-prompts.md"))
      .finally(() => setLoading(false))
  }, [open, prompts.length, loading])

  useEffect(() => {
    if (!open) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [open, onClose])

  const categories = useMemo(() => ["全部", ...Array.from(new Set(prompts.map((item) => item.category)))], [prompts])
  const filteredPrompts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return prompts.filter((item) => {
      const matchesCategory = category === "全部" || item.category === category
      const matchesDifficulty = difficulty === "全部" || item.difficulty === difficulty
      const matchesQuery = !normalizedQuery || `${item.category} ${item.prompt} ${item.intent} ${item.expected.join(" ")}`.toLowerCase().includes(normalizedQuery)
      return matchesCategory && matchesDifficulty && matchesQuery
    })
  }, [category, difficulty, prompts, query])

  const copyPrompt = async (item: RagTestPrompt) => {
    try {
      await navigator.clipboard.writeText(item.prompt)
      setCopiedId(item.id)
      window.setTimeout(() => setCopiedId((current) => current === item.id ? null : current), 1400)
    } catch {
      setError("复制失败，请直接点击提示词内容选中复制")
    }
  }

  return (
    <>
      {open && <button className="fixed inset-0 z-[55] bg-[#17352b]/30" onClick={onClose} aria-label="关闭测试提示词面板" />}
      <aside
        aria-label="RAG 测试提示词"
        aria-hidden={!open}
        className={cn(
          "fixed inset-y-0 right-0 z-[60] flex h-[100dvh] w-full max-w-[440px] flex-col border-l bg-white pb-[env(safe-area-inset-bottom)] pt-[env(safe-area-inset-top)] shadow-2xl transition-transform duration-200",
          open ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex items-start justify-between border-b px-4 py-4 sm:px-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#e7f1e8] text-[#17613c]">
              <FlaskConical className="h-4.5 w-4.5" strokeWidth={1.8} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#263f33]">RAG 测试提示词</h2>
              <p className="mt-1 text-xs leading-5 text-[#718077]">来自农业知识库测试文档，点击即可填入输入框</p>
            </div>
          </div>
          <button onClick={onClose} className="icon-button" title="关闭测试提示词" aria-label="关闭测试提示词"><X className="h-4 w-4" /></button>
        </div>

        <div className="space-y-3 border-b bg-[#fafcf9] px-4 py-3 sm:px-5">
          <label className="flex items-center gap-2 rounded-md border bg-white px-3 py-2 text-sm text-[#718077]">
            <Search className="h-4 w-4 shrink-0" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索作物、病虫害或场景" className="min-w-0 flex-1 bg-transparent text-sm text-[#273f33] outline-none placeholder:text-[#9aa69e]" />
          </label>
          <div className="flex gap-1.5 overflow-x-auto pb-0.5 custom-scrollbar">
            {categories.map((item) => (
              <button key={item} onClick={() => setCategory(item)} className={cn("shrink-0 rounded-md border px-2.5 py-1.5 text-xs transition-colors", category === item ? "border-[#17613c] bg-[#17613c] text-white" : "bg-white text-[#5f6e65] hover:border-[#9db9a6] hover:text-[#17613c]")}>{item}</button>
            ))}
          </div>
          <div className="flex items-center gap-1.5" aria-label="按测试难度筛选">
            <span className="shrink-0 text-[11px] text-[#87938b]">难度</span>
            {["全部", "基础", "进阶", "边界"].map((item) => <button key={item} onClick={() => setDifficulty(item)} className={cn("rounded border px-2 py-1 text-[11px] transition-colors", difficulty === item ? "border-[#17613c] bg-[#e7f1e8] text-[#17613c]" : "border-[#e1e8df] bg-white text-[#718077] hover:border-[#9db9a6]")}>{item}</button>)}
          </div>
        </div>

        <div className="scroll-boundary min-h-0 flex-1 overflow-y-auto px-4 py-4 custom-scrollbar sm:px-5">
          {loading && <div className="rounded-md border border-dashed px-3 py-5 text-center text-xs text-[#718077]">正在读取测试提示词...</div>}
          {!loading && error && <div className="rounded-md border border-[#ead8dc] bg-[#fdf7f8] px-3 py-4 text-xs leading-5 text-[#8f2332]">{error}</div>}
          {!loading && !error && filteredPrompts.length === 0 && <div className="rounded-md border border-dashed px-3 py-5 text-center text-xs text-[#718077]">没有匹配的测试提示词</div>}
          <div className="space-y-2">
            {filteredPrompts.map((item) => (
              <article key={item.id} className="group rounded-md border bg-white p-3 transition-colors hover:border-[#9db9a6] hover:bg-[#fbfdfb]">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                      <span className="font-medium text-[#17613c]">{item.category}</span>
                      <span className={cn("rounded border px-1.5 py-0.5", item.difficulty === "边界" ? "border-[#ead6d8] bg-[#fff8f8] text-[#8f2332]" : item.difficulty === "进阶" ? "border-[#ead8b5] bg-[#fffaf0] text-[#89651b]" : "border-[#dbe6db] bg-[#f6faf5] text-[#587363]")}>{item.difficulty}</span>
                      <span className="text-[#9aa69e]">{item.intent}</span>
                    </div>
                    <p className="mt-1 text-sm leading-5 text-[#30473b]">{item.prompt}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {item.expected.map((check) => <span key={check} className="rounded bg-[#f4f7f2] px-1.5 py-0.5 text-[10px] text-[#718077]">验收：{check}</span>)}
                    </div>
                  </div>
                  <button onClick={() => void copyPrompt(item)} className="icon-button h-8 w-8 shrink-0 opacity-70 group-hover:opacity-100" title="复制提示词" aria-label={`复制：${item.prompt}`}>
                    {copiedId === item.id ? <Check className="h-3.5 w-3.5 text-[#17613c]" /> : <Clipboard className="h-3.5 w-3.5" />}
                  </button>
                </div>
                <button onClick={() => { onUsePrompt(item.prompt); onClose() }} className="mt-3 inline-flex min-h-8 items-center rounded-md border border-[#cfe0ce] bg-[#f3f8f2] px-2.5 text-xs font-medium text-[#17613c] transition-colors hover:border-[#17613c] hover:bg-[#e7f1e8]">填入输入框</button>
              </article>
            ))}
          </div>
        </div>

        <div className="border-t bg-[#fafcf9] px-4 py-3 text-[11px] leading-5 text-[#87938b] sm:px-5">当前显示 {filteredPrompts.length} / 共 {prompts.length} 条 · 每条模板附带测试意图和验收观察点</div>
      </aside>
    </>
  )
}
