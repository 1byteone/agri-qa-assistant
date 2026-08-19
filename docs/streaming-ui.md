# CropWise 流式对话工程说明

## 目标与边界

本实现让农业问答的文本、工具状态和知识上下文以增量事件到达页面。模型生成的内容不直接执行 HTML 或 JSX。生成式界面仅能选择本地白名单组件，并向组件传入经过校验的 JSON 数据。

## 传输决策

| 场景 | 选择 | 原因 |
| --- | --- | --- |
| 当前单轮问答流 | `POST + SSE` | 单向服务端推送、代理兼容性好，保留 JSON 请求体并支持 `fetch` 取消。 |
| 浏览器读取 | `fetch + ReadableStream` | `EventSource` 只支持 GET，不能自然携带当前 POST 请求体和 `AbortController`。 |
| 多人协同、实时语音、客户端频繁上行 | WebSocket | 需要持久全双工通道时再启用，不为普通问答增加连接与重连复杂度。 |
| HTTP/3 | 部署层优化 | QUIC/HTTP/3 由 CDN、反向代理与 TLS 终止层协商，不改变 `/chat/stream` 的 SSE 事件协议。 |

## 事件契约

每个事件都是一个完整的 SSE 帧：

```text
event: delta
data: {"type":"delta","text":"分蘖期应注意"}

```

支持的事件类型：

- `status`：检索、生成或备用通道阶段提示。
- `delta`：可直接追加的文本增量。
- `tool`：工具的 `running` / `complete` 状态。
- `ui`：白名单生成式组件，目前为 `knowledge-context`。
- `done`：最终文本和工具调用记录。
- `error`：可展示的流错误。

`frontend/lib/sse.ts` 会先用 `TextDecoder` 保留 UTF-8 半字符状态，再按 SSE 空行分帧，最后对完整 `data` 进行 JSON 解析。网络 ReadableStream 的 chunk 不被假定为 JSON 或 SSE 边界。

## 客户端状态机

```text
idle -> connecting -> streaming -> draining -> complete
                     |                 |
                     +-> cancelled     +-> error
```

服务端收到的 `delta` 先放入队列。`requestAnimationFrame` 每帧批量追加字符，在积压时最多每帧追加 14 个字符。这让打字机视觉效果稳定，同时避免高频 `setState` 造成虚拟 DOM 和滚动布局抖动。结束帧到达后，页面会等待队列排空再标记回答完成。

停止按钮通过 `AbortController` 中断浏览器请求。FastAPI 的 async generator 接收取消后停止向模型继续消费，前端丢弃尚未渲染的排队字符并保留已显示内容。

## 生成式 UI 安全边界

后端的 `ui` 事件只包含：

```json
{
  "type": "ui",
  "component": "knowledge-context",
  "props": { "items": [{ "title": "农业知识库", "excerpt": "..." }] }
}
```

前端将 `component` 映射到固定 React 组件，并对 `props.items` 的标题与摘要逐项做运行时类型校验。不要接受模型返回的原始 HTML、动态组件名、CSS 或可执行代码。

## 运行与验证

- 后端端点：`POST /chat/stream`
- 前端代理：`/api/chat/stream`
- 取消：点击输入框右侧的停止按钮
- 回退兼容：原有 `POST /chat` 继续可用，并通过同一事件生成器收集完整回答。

## 资料依据

- [MDN: ReadableStream](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream)：流读取和浏览器字节流语义。
- [MDN: Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)：SSE 帧格式、`event` 与 `data` 字段。
- [WHATWG HTML: Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)：SSE 规范。
- [MDN: WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)：全双工连接的适用边界。
- [RFC 9114: HTTP/3](https://www.rfc-editor.org/rfc/rfc9114)：HTTP/3 的传输语义和部署层定位。
- [FastAPI: StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)：异步生成器流式响应。
- [LangChain: Streaming](https://python.langchain.com/docs/how_to/streaming/)：模型增量输出与事件流。
- [Vercel AI SDK: Stream Protocol](https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol)：结构化流事件与 UI 协议设计参考。
