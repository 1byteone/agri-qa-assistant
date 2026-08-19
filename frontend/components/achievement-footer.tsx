"use client"

import { useEffect, useState } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"

const achievements = [
  { image: "/crops/hybrid-rice.jpg", label: "籼型杂交水稻", detail: "作物育种领域的重要成果" },
  { image: "/crops/double-crop.jpg", label: "优质晚籼稻", detail: "新品种选育与推广" },
  { image: "/crops/super-rice.jpg", label: "双季超级稻技术", detail: "高产栽培技术体系" },
]

export function AchievementFooter() {
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)
  const current = achievements[index]

  useEffect(() => {
    if (paused) return
    const timer = setInterval(() => setIndex((value) => (value + 1) % achievements.length), 4500)
    return () => clearInterval(timer)
  }, [paused])

  return (
    <section className="workspace-panel mx-auto flex max-w-4xl items-center gap-3 rounded-lg px-3 py-2.5 sm:px-4" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <button onClick={() => setIndex((value) => (value - 1 + achievements.length) % achievements.length)} className="icon-button h-8 w-8 shrink-0" aria-label="上一项成果"><ChevronLeft className="h-4 w-4" /></button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={current.image} alt="" className="h-12 w-16 shrink-0 rounded-md object-cover" />
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-[#17613c]">江农科研成果</p>
        <p className="truncate text-sm font-semibold text-[#263f33]">{current.label}</p>
        <p className="truncate text-xs text-[#718077]">{current.detail}</p>
      </div>
      <button onClick={() => setIndex((value) => (value + 1) % achievements.length)} className="icon-button h-8 w-8 shrink-0" aria-label="下一项成果"><ChevronRight className="h-4 w-4" /></button>
    </section>
  )
}
