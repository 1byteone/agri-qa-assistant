"use client"

import type { Components } from "react-markdown"
import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { TermAnnotation } from "@/components/term-annotation"

const TERM_PATTERN = /稻飞虱|条锈病|分蘖期|双季稻|赣南脐橙|红壤|鄱阳湖|植保无人机/g

function annotateText(value: string, enabled: boolean) {
  if (!enabled) return value
  const parts = value.split(TERM_PATTERN)
  const terms = value.match(TERM_PATTERN) || []
  return parts.flatMap((part, index) => index < terms.length ? [part, <span key={`${terms[index]}-${index}`} className="term-annotated">{terms[index]}<TermAnnotation term={terms[index]} /></span>] : [part])
}

const markdownComponents: Components = {
  h1: ({ children }) => <h1 className="mb-3 mt-1 text-lg font-semibold text-[#203a2f]">{children}</h1>,
  h2: ({ children }) => <h2 className="mb-2 mt-4 text-base font-semibold text-[#203a2f]">{children}</h2>,
  h3: ({ children }) => <h3 className="mb-1.5 mt-3 text-sm font-semibold text-[#29513e]">{children}</h3>,
  p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  blockquote: ({ children }) => <blockquote className="my-3 border-l-2 border-[#86a68f] bg-[#f4f8f3] px-3 py-2 text-[#5e7064]">{children}</blockquote>,
  code: ({ className, children, ...props }) => {
    const isBlock = Boolean(className)
    return isBlock ? (
      <code className="block overflow-x-auto rounded-md bg-[#17352b] px-3 py-2.5 font-mono text-xs leading-5 text-[#e8f4e8]" {...props}>{children}</code>
    ) : (
      <code className="rounded bg-[#eef3ec] px-1 py-0.5 font-mono text-[0.9em] text-[#17613c]" {...props}>{children}</code>
    )
  },
  pre: ({ children }) => <pre className="mb-3 overflow-hidden rounded-md last:mb-0">{children}</pre>,
  table: ({ children }) => <div className="mb-3 overflow-x-auto last:mb-0"><table className="min-w-full border-collapse text-left text-xs">{children}</table></div>,
  th: ({ children }) => <th className="border bg-[#eef4ec] px-2.5 py-2 font-semibold text-[#31503f]">{children}</th>,
  td: ({ children }) => <td className="border px-2.5 py-2 align-top">{children}</td>,
  a: ({ href, children }) => {
    const safeHref = href && /^(https?:|mailto:)/i.test(href) ? href : undefined
    return <a href={safeHref} target="_blank" rel="noreferrer noopener" className="font-medium text-[#a6192e] underline decoration-[#d99ba6] underline-offset-2 hover:text-[#811225]">{children}</a>
  },
  img: ({ src, alt }) => {
    const safeSrc = src && /^(https?:|data:image\/)/i.test(src) ? src : undefined
    if (!safeSrc) return null
    return <img src={safeSrc} alt={alt || "农业相关图片"} loading="lazy" className="my-3 max-h-72 max-w-full rounded-md border object-contain" />
  },
  hr: () => <hr className="my-4 border-[#dbe5d9]" />,
}

export function stripToolCallMarkers(content: string) {
  return content
    .replace(/<tool_calls?\b[^>]*>[\s\S]*?(?:<\/tool_calls?>|$)/gi, "")
    .replace(/<\/?tool_call(?:s)?\b[^>]*>/gi, "")
    .replace(/^\s*(?:我来为您|我将为您|我会为您|我将调用工具|我会调用工具)(?:搜索|查找|检索)[^\n]*$/gim, "")
    .replace(/^\s*\*{0,2}图片资源查找\*{0,2}\s*[:：]?\s*$/gim, "")
    .replace(/^\s*(?:正在调用|已调用|已完成)\s*[:：]?\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather)(?:\s*[,、]\s*(?:search_agri_resources|query_crop_knowledge|fetch_web_content|get_current_datetime|calculate_growing_period|get_agri_weather))*\s*$/gim, "")
    .replace(/^[ \t]*\*([^*\r\n]+)\*\*(?=[ \t]*(?:[:：。！？]|$))/gm, "**$1**")
    .replace(/^\s*[-*]\s*$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
}

export function MarkdownMessage({ content, terminologyEnabled = false }: { content: string; terminologyEnabled?: boolean }) {
  const cleanContent = stripToolCallMarkers(content)
  if (!cleanContent) return null

  return (
    <div className="markdown-message text-[15px] leading-6 text-[#243b31] sm:text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={terminologyEnabled ? {
        ...markdownComponents,
        p: ({ children }) => <p className="mb-3 last:mb-0">{React.Children.map(children, (child) => typeof child === "string" ? annotateText(child, true) : child)}</p>,
        li: ({ children }) => <li className="pl-1">{React.Children.map(children, (child) => typeof child === "string" ? annotateText(child, true) : child)}</li>,
        td: ({ children }) => <td className="border px-2.5 py-2 align-top">{React.Children.map(children, (child) => typeof child === "string" ? annotateText(child, true) : child)}</td>,
      } : markdownComponents} skipHtml>
        {cleanContent}
      </ReactMarkdown>
    </div>
  )
}
