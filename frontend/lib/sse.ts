export type StreamEventType = "status" | "mode" | "answer-replace" | "guard" | "delta" | "tool" | "time-context" | "ui" | "sources" | "trace" | "resources" | "memory" | "memory-candidate" | "memory-action" | "memory-organized" | "done" | "error"

export interface StreamEvent {
  type: StreamEventType
  [key: string]: unknown
}

/**
 * Parses SSE across arbitrary ReadableStream chunk boundaries. A network chunk
 * is not an event boundary, so JSON is decoded only after a complete frame.
 */
export class SSEEventParser {
  private buffer = ""

  push(chunk: string): StreamEvent[] {
    this.buffer += chunk.replace(/\r\n/g, "\n")
    const frames = this.buffer.split("\n\n")
    this.buffer = frames.pop() ?? ""
    return frames.flatMap((frame) => this.parseFrame(frame))
  }

  flush(): StreamEvent[] {
    const frame = this.buffer.trim()
    this.buffer = ""
    return frame ? this.parseFrame(frame) : []
  }

  private parseFrame(frame: string): StreamEvent[] {
    let eventType = "message"
    const dataLines: string[] = []

    for (const line of frame.split("\n")) {
      if (!line || line.startsWith(":")) continue
      if (line.startsWith("event:")) eventType = line.slice(6).trim()
      if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart())
    }

    if (dataLines.length === 0) return []
    const parsed = JSON.parse(dataLines.join("\n")) as StreamEvent
    return [{ ...parsed, type: (parsed.type ?? eventType) as StreamEventType }]
  }
}

export async function consumeSSE(
  response: Response,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  if (!response.body) throw new Error("浏览器不支持流式响应")

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  const parser = new SSEEventParser()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      for (const event of parser.push(decoder.decode(value, { stream: true }))) onEvent(event)
    }
    for (const event of parser.push(decoder.decode())) onEvent(event)
    for (const event of parser.flush()) onEvent(event)
  } finally {
    reader.releaseLock()
  }
}
