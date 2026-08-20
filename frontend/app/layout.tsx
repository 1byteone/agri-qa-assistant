import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "CropWise · 江西农业大学农业智能问答",
  description: "江西农业大学官方农业智能问答助手，连接农业知识库、Agent 检索与可核验来源",
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
