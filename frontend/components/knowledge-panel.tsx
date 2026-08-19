"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { AnimatePresence, motion } from "framer-motion"
import { ChevronRight, ExternalLink, X } from "lucide-react"
import { useSidebar } from "@/lib/sidebar-context"
import { cn } from "@/lib/utils"

const CROP_ACHIEVEMENTS = [
  { id: "1", image: "/crops/hybrid-rice.jpg", tag: "国家重大成果", title: "籼型杂交水稻", desc: "颜龙安院士团队推动籼型杂交水稻研究与应用。" },
  { id: "2", image: "/crops/double-crop.jpg", tag: "品种选育", title: "优质晚籼稻新品种", desc: "服务长江中下游优质稻产业发展。" },
  { id: "3", image: "/crops/super-rice.jpg", tag: "高产栽培", title: "双季超级稻技术", desc: "围绕早蘖壮秆强源形成高产栽培技术。" },
  { id: "4", image: "/crops/chemical-rice.jpg", tag: "育种创新", title: "化学杀雄杂交水稻", desc: "探索水稻杂种优势利用的新路径。" },
]

export function KnowledgePanel({ mobileOpen = false, onMobileClose }: { mobileOpen?: boolean; onMobileClose?: () => void }) {
  const { rightOpen, setRightOpen } = useSidebar()
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    if (paused || !rightOpen) return
    const timer = setInterval(() => setIndex((value) => (value + 1) % CROP_ACHIEVEMENTS.length), 5000)
    return () => clearInterval(timer)
  }, [paused, rightOpen])

  const current = CROP_ACHIEVEMENTS[index]

  const content = (
    <div className="sidebar-panel custom-scrollbar scroll-boundary flex h-full min-h-0 flex-col overflow-y-auto rounded-lg p-4" onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}>
      <div className="flex items-start justify-between border-b pb-3">
        <div>
          <p className="section-kicker">科研成果</p>
          <p className="mt-1 text-xs leading-5 text-[#718077]">作物育种与栽培技术</p>
        </div>
        <button onClick={() => setRightOpen(false)} className="text-xs text-[#718077] hover:text-[#17613c]">收起</button>
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={current.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }} className="pt-4">
          <Link href={`/jxau-news/${current.id}`} className="group block w-full text-left">
            <div className="overflow-hidden rounded-md border bg-[#eef2ea]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={current.image} alt={current.title} className="h-32 w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]" />
            </div>
            <p className="mt-3 text-xs font-medium text-[#17613c]">{current.tag}</p>
            <h2 className="mt-1 text-base font-semibold text-[#263f33]">{current.title}</h2>
            <p className="mt-1.5 text-sm leading-6 text-[#66756c]">{current.desc}</p>
            <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[#a6192e]">查看详情 <ExternalLink className="h-3.5 w-3.5" /></span>
          </Link>
        </motion.div>
      </AnimatePresence>

      <div className="mt-auto flex items-center justify-between border-t pt-4">
        <div className="flex gap-1.5">
          {CROP_ACHIEVEMENTS.map((item, itemIndex) => (
            <button key={item.id} onClick={() => setIndex(itemIndex)} aria-label={`查看${item.title}`} className={cn("h-2 w-2 rounded-full transition-colors", itemIndex === index ? "bg-[#17613c]" : "bg-[#d5ded4] hover:bg-[#9db5a1]")} />
          ))}
        </div>
        <ChevronRight className="h-4 w-4 text-[#98a69e]" />
      </div>
    </div>
  )

  return (
    <>
      <AnimatePresence>
      {rightOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0, x: 12 }}
          animate={{ width: 272, opacity: 1, x: 0 }}
          exit={{ width: 0, opacity: 0, x: 12 }}
          transition={{ duration: 0.22 }}
          className="hidden min-h-0 shrink-0 overflow-hidden xl:block"
        >
          {content}
        </motion.aside>
      )}
    </AnimatePresence>
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onMobileClose} className="fixed inset-0 z-[60] bg-[#17352b]/35 xl:hidden" aria-label="关闭科研成果" />
            <motion.aside initial={{ x: 320 }} animate={{ x: 0 }} exit={{ x: 320 }} transition={{ duration: 0.22 }} className="fixed inset-y-0 right-0 z-[70] h-[100dvh] w-[min(320px,88vw)] overflow-hidden bg-white px-5 pb-5 pt-[calc(1.25rem+env(safe-area-inset-top))] shadow-xl xl:hidden">
              <div className="mb-5 flex items-center justify-between">
                <p className="text-sm font-semibold text-[#263f33]">科研成果</p>
                <button onClick={onMobileClose} className="icon-button" title="关闭科研成果" aria-label="关闭科研成果"><X className="h-4 w-4" /></button>
              </div>
              {content}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
