import { SseEventParser } from "./sse.ts"

type TestCase = { name: string; run: () => void }
const tests: TestCase[] = []
const test = (name: string, run: () => void) => tests.push({ name, run })
const equal = (actual: unknown, expected: unknown) => {
  const a = JSON.stringify(actual)
  const e = JSON.stringify(expected)
  if (a !== e) throw new Error(`Expected ${e}, received ${a}`)
}

test("parses frames split across chunks and CRLF", () => {
  const events: Record<string, unknown>[] = []
  const parser = new SseEventParser((event) => events.push(event))
  parser.push('event: delta\r\ndata: {"type":"delta","text":"水"}\r\n\r\n')
  parser.push('data: {"type":"delta","text":"稻"}')
  parser.flush()
  equal(events, [{ type: "delta", text: "水" }, { type: "delta", text: "稻" }])
})

test("joins multiline data fields", () => {
  const events: Record<string, unknown>[] = []
  const parser = new SseEventParser((event) => events.push(event))
  parser.push('data: {"type":"status",\ndata: "message":"ready"}\n\n')
  equal(events, [{ type: "status", message: "ready" }])
})

test("flushes an unterminated frame and ignores malformed/non-object data", () => {
  const events: Record<string, unknown>[] = []
  const parser = new SseEventParser((event) => events.push(event))
  parser.push('data: {bad}\n\ndata: [1,2]\n\ndata: {"type":"done"}')
  parser.flush()
  equal(events, [{ type: "done" }])
})

for (const { name, run } of tests) {
  run()
  console.log(`PASS ${name}`)
}
console.log(`SSE contract tests passed: ${tests.length}`)
