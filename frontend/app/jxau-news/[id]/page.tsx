import Link from "next/link"
import { notFound } from "next/navigation"
import { ServicePage, InfoSection, OfficialLink } from "@/components/service-page"

const achievements: Record<string, { title: string; tag: string; description: string }> = {
  "1": { title: "籼型杂交水稻", tag: "国家重大成果", description: "江西农业大学科研团队长期开展杂交水稻育种与推广研究，相关成果服务于优质稻产业发展。" },
  "2": { title: "优质晚籼稻新品种", tag: "品种选育", description: "围绕长江中下游稻区的品质与适应性开展品种选育，具体品种信息应以学校科研或审定公告为准。" },
  "3": { title: "双季超级稻技术", tag: "高产栽培", description: "双季稻高产栽培需要结合品种、播期、群体质量和水肥管理进行综合决策。" },
  "4": { title: "化学杀雄杂交水稻", tag: "育种创新", description: "化学杀雄技术是水稻杂种优势利用研究方向之一，具体成果与论文请以学校官方发布为准。" },
}

export default function JxauNewsPage({ params }: { params: { id: string } }) {
  const { id } = params
  const item = achievements[id]
  if (!item) notFound()
  return <ServicePage eyebrow={`江农科研成果 / ${item.tag}`} title={item.title} description={item.description}>
    <InfoSection title="信息说明"><p>此页面用于展示 CropWise 工作台中的科研成果卡片详情。它不替代学校新闻稿、品种审定公告或正式科研成果证明。</p></InfoSection>
    <InfoSection title="官方核验"><p><OfficialLink href="https://www.jxau.edu.cn/">访问江西农业大学官网</OfficialLink>，在站内搜索成果名称和最新公告。</p><Link href="/" className="mt-4 inline-flex rounded-md border px-3 py-2 text-sm font-medium text-[#17613c] hover:bg-[#f3f8f2]">返回农业问答</Link></InfoSection>
  </ServicePage>
}
