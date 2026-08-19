import { ServicePage, InfoSection } from "@/components/service-page"
import { ServiceWorkflow } from "@/components/service-workflow"

export default function FarmingCalendarPage() {
  return <ServicePage eyebrow="服务入口 / 02" title="农时查询" description="根据作物、地区、当前环节和目标直接生成可执行的农事顺序，并标明近期天气风险和核验点。">
    <ServiceWorkflow kind="calendar" />
    <InfoSection title="使用边界"><ul className="list-disc space-y-1 pl-5"><li>播期、移栽期和收获期仍需结合县域积温、品种熟期和前茬进度。</li><li>页面引用的公共天气预报不等同于当地气象站实况或灾害预警。</li><li>遇到暴雨、寒潮、高温等风险时，以气象部门和当地农技部门的最新通知为准。</li></ul></InfoSection>
  </ServicePage>
}
