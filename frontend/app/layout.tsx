import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "江西农业大学 CropWise · 智慧农业问答",
  description: "江西农业大学智能问答助手，传承「厚德博学、抱朴守真」江农精神，覆盖作物种植、病虫害防治、施肥灌溉等农业技术问答",
  icons: {
    icon: "/jxau-favicon.png",
    shortcut: "/jxau-favicon.png",
    apple: "/jxau-favicon.png",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}
