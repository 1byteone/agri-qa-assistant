"use client"

import { PanelLeftClose, PanelRightClose, Menu, X } from "lucide-react"
import { useSidebar } from "@/lib/sidebar-context"

export function ToggleBtn({ type }: { type: "left" | "right" }) {
  const { leftOpen, rightOpen, setLeftOpen, setRightOpen } = useSidebar()

  if (type === "left") {
    return (
      <button
        onClick={() => setLeftOpen(!leftOpen)}
        className="hidden xl:flex p-2 rounded-xl glass-panel hover:bg-white/80 transition-colors"
        title={leftOpen ? "收起学校介绍" : "展开学校介绍"}
      >
        {leftOpen ? (
          <Menu className="w-4 h-4 text-gray-500" />
        ) : (
          <PanelLeftClose className="w-4 h-4 text-gray-500" />
        )}
      </button>
    )
  }

  return (
    <button
      onClick={() => setRightOpen(!rightOpen)}
      className="hidden xl:flex p-2 rounded-xl glass-panel hover:bg-white/80 transition-colors"
      title={rightOpen ? "收起作物成就" : "展开作物成就"}
    >
      {rightOpen ? (
        <X className="w-4 h-4 text-gray-500" />
      ) : (
        <PanelLeftClose className="w-4 h-4 text-gray-500 rotate-180" />
      )}
    </button>
  )
}

export function MobileMenuBtn({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-2 rounded-lg hover:bg-white/30 transition-colors"
      title="菜单"
    >
      <Menu className="w-5 h-5 text-gray-700" />
    </button>
  )
}