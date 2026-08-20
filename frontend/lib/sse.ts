export type SseEvent = Record<string, unknown>

export type SseEventHandler = (event: SseEvent) => void

/** Incrementally parses JSON SSE data frames, including CRLF and an unterminated tail. */
export class SseEventParser {
  private buffer = ""
  private readonly onEvent: SseEventHandler

  constructor(onEvent: SseEventHandler) {
    this.onEvent = onEvent
  }

  push(chunk: string, flush = false): void {
    this.buffer += chunk.replace(/\r\n/g, "\n").replace(/\r/g, "\n")
    const frames = this.buffer.split("\n\n")
    const remainder = frames.pop() ?? ""
    this.buffer = flush ? "" : remainder
    if (flush && remainder.trim()) frames.push(remainder)

    for (const frame of frames) {
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n")
      if (!data) continue
      try {
        const parsed: unknown = JSON.parse(data)
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          this.onEvent(parsed as SseEvent)
        }
      } catch (error) {
        console.warn("无法解析农业 Agent 事件", error)
      }
    }
  }

  flush(): void {
    this.push("", true)
  }
}
