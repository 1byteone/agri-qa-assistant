import os
from openai import OpenAI

key = os.getenv("AGNES_API_KEY") or os.getenv("AGNES_AI_API_KEY")
print("当前使用的 key 前缀:", key[:8] + "..." if key else "未设置")

client = OpenAI(
    api_key=key,
    base_url="https://api.agnes-ai.cn/v1",
)

try:
    r = client.chat.completions.create(
        model="agnes-2.0-flash",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=10,
    )
    print("成功:", r.choices[0].message.content)
except Exception as e:
    print("失败:", e)