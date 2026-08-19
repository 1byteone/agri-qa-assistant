"use client"

import { ExternalLink, Info, Loader2 } from "lucide-react"
import { useEffect, useRef, useState } from "react"

export interface AgriTermDefinition {
  term: string
  title?: string
  summary: string
  source_name: string
  source_url: string
  source_label: string
}

export function TermAnnotation({ term }: { term: string }) {
  const [definition, setDefinition] = useState<AgriTermDefinition | null>(null)
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const loaded = useRef(false)

  const loadDefinition = async () => {
    if (loaded.current || loading) return
    setLoading(true)
    try {
      const response = await fetch(`/api/agri-terms/lookup?term=${encodeURIComponent(term)}`)
      if (!response.ok) return
      setDefinition(await response.json() as AgriTermDefinition)
      loaded.current = true
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (open) void loadDefinition()
  }, [open])

  return (
    <span className="term-annotation-wrap">
      <button
        type="button"
        className="term-annotation-mark"
        aria-label={`查看${term}专业词条`}
        aria-expanded={open}
        onMouseEnter={() => { setOpen(true); void loadDefinition() }}
        onFocus={() => { setOpen(true); void loadDefinition() }}
        onClick={() => { setOpen((value) => !value); void loadDefinition() }}
      >
        <Info className="h-3 w-3" aria-hidden="true" />
      </button>
      {open && (
        <span className="term-annotation-popover" role="dialog" aria-label={`${term}专业词条`}>
          <span className="flex items-start gap-2">
            <span className="min-w-0 flex-1">
              <strong className="block text-xs text-[#213a2f]">{definition?.title || term}</strong>
              {loading && !definition ? <span className="mt-1 flex items-center gap-1 text-[11px] text-[#68776d]"><Loader2 className="h-3 w-3 animate-spin" />正在读取权威资料</span> : definition ? <>
                <span className="mt-1 block text-[11px] leading-5 text-[#526158]">{definition.summary}</span>
                <a className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-[#17613c] underline underline-offset-2" href={definition.source_url} target="_blank" rel="noreferrer noopener">{definition.source_label}<ExternalLink className="h-3 w-3" /></a>
              </> : <span className="mt-1 block text-[11px] text-[#68776d]">暂无可核验的权威词条</span>}
            </span>
          </span>
        </span>
      )}
    </span>
  )
}
