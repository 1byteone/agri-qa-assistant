import { ServicePage, InfoSection, OfficialLink } from "@/components/service-page"
import { ServiceWorkflow } from "@/components/service-workflow"

export default function PolicyPage() {
  return <ServicePage eyebrow="服务入口 / 03" title="政策咨询" description="围绕地区、项目、主体和时间直接检索政策证据，呈现已核验信息与办理前仍需确认的事项。">
    <ServiceWorkflow kind="policy" />
    <InfoSection title="官方核验入口"><p>农业农村部公开信息、江西省农业农村厅公告和办事地政府通知是办理前核验的优先来源。</p><div className="mt-3 flex flex-wrap gap-x-5 gap-y-2"><OfficialLink href="https://www.moa.gov.cn/">农业农村部官网</OfficialLink><OfficialLink href="https://nync.jiangxi.gov.cn/">江西省农业农村厅</OfficialLink></div></InfoSection>
  </ServicePage>
}
