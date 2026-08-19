import { access, readFile } from "node:fs/promises"
import path from "node:path"
import { NextResponse } from "next/server"

interface RagTestPrompt {
  id: string
  category: string
  prompt: string
  intent: string
  difficulty: "基础" | "进阶" | "边界"
  expected: string[]
}

function getTestMeta(category: string, prompt: string): Pick<RagTestPrompt, "intent" | "difficulty" | "expected"> {
  const boundary = /不能|是否应该|只凭|编造|越界|无关|冲突|不确定|无法|外部/.test(prompt)
  const temporal = /当前|最近|上周|去年|日期|农时|生育期|播期|时效/.test(prompt)
  const memory = /记忆|上一轮|之前|偏好|多轮|冲突|历史/.test(prompt)
  const intent = memory ? "记忆门控" : temporal ? "时间与时效" : boundary ? "边界与证据" : category.includes("文档") ? "入库判定" : category.includes("资源") ? "资源检索" : "知识检索"
  const difficulty = boundary ? "边界" : (memory || temporal || category.includes("江西")) ? "进阶" : "基础"
  const expected = memory
    ? ["区分相关与相似", "不误用旧记忆", "说明冲突处理"]
    : temporal
      ? ["识别时间条件", "结合地区/生育期", "说明时效边界"]
      : boundary
        ? ["诚实说明证据", "不编造来源", "给出复核建议"]
        : ["命中相关知识", "引用适用条件", "给出可执行步骤"]
  return { intent, difficulty, expected }
}

function parsePrompts(markdown: string): RagTestPrompt[] {
  let category = "未分类"
  const prompts: RagTestPrompt[] = []

  for (const line of markdown.split(/\r?\n/)) {
    const heading = line.match(/^##\s+(.+)$/)
    if (heading) {
      category = heading[1].trim()
      continue
    }

    const item = line.match(/^\s*\d+[.、]\s+(.+?)\s*$/)
    if (item) {
      prompts.push({
        id: `rag-prompt-${prompts.length + 1}`,
        category,
        prompt: item[1],
        ...getTestMeta(category, item[1]),
      })
    }
  }

  return prompts
}

export async function GET() {
  try {
    const candidatePaths = [
      path.join(process.cwd(), "..", "docs", "agri-rag-test-prompts.md"),
      path.join(process.cwd(), "docs", "agri-rag-test-prompts.md"),
    ]
    let filePath = candidatePaths[0]
    for (const candidate of candidatePaths) {
      try {
        await access(candidate)
        filePath = candidate
        break
      } catch {
        // Try the next workspace layout.
      }
    }
    const markdown = await readFile(filePath, "utf8")
    const prompts = parsePrompts(markdown)
    return NextResponse.json({ prompts, source: "docs/agri-rag-test-prompts.md" }, {
      headers: { "Cache-Control": "no-store" },
    })
  } catch (error) {
    console.error("读取 RAG 测试提示词失败", error)
    return NextResponse.json({ error: "测试提示词文件暂不可用" }, { status: 500 })
  }
}
