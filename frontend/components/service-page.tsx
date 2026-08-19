import Link from "next/link"
import { ArrowLeft, ExternalLink, Leaf } from "lucide-react"

export function ServicePage({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string
  title: string
  description: string
  children: React.ReactNode
}) {
  return (
    <main className="app-shell min-h-[100dvh] px-4 py-6 sm:px-8 sm:py-10">
      <div className="mx-auto max-w-4xl">
        <nav className="mb-8 flex items-center justify-between">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-medium text-[#17613c] hover:text-[#10462c]"><ArrowLeft className="h-4 w-4" /> 返回 CropWise</Link>
          <div className="flex items-center gap-2 text-xs text-[#718077]"><Leaf className="h-4 w-4 text-[#17613c]" /> 江西农业大学 CropWise</div>
        </nav>
        <header className="border-b border-[#d8e0d6] pb-6">
          <p className="section-kicker">{eyebrow}</p>
          <h1 className="mt-2 text-3xl font-semibold text-[#203a2f] sm:text-4xl">{title}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#5c6c63]">{description}</p>
        </header>
        <div className="mt-6 space-y-4">{children}</div>
      </div>
    </main>
  )
}

export function InfoSection({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-lg border bg-white p-5 shadow-sm"><h2 className="text-base font-semibold text-[#263f33]">{title}</h2><div className="mt-3 text-sm leading-6 text-[#5c6c63]">{children}</div></section>
}

export function OfficialLink({ href, children }: { href: string; children: React.ReactNode }) {
  return <a href={href} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 font-medium text-[#a6192e] underline decoration-[#d99ba6] underline-offset-2 hover:text-[#811225]">{children}<ExternalLink className="h-3.5 w-3.5" /></a>
}
