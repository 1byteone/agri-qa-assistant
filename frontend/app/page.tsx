"use client"

import { ChatInterface } from "@/components/chat-interface"

export default function Home() {
  return (
    <main className="app-shell min-h-[100dvh] overflow-x-hidden">
      <ChatInterface />
    </main>
  )
}
