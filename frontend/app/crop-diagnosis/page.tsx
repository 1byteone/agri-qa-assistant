import { ServicePage, InfoSection } from "@/components/service-page"
import { ServiceWorkflow } from "@/components/service-workflow"

export default function CropDiagnosisPage() {
  return <ServicePage eyebrow="服务入口 / 01" title="作物诊断" description="录入田间症状后直接发起受证据约束的诊断咨询，输出鉴别思路、排查动作和复查节点。">
    <ServiceWorkflow kind="diagnosis" />
    <InfoSection title="田间复核重点"><ol className="list-decimal space-y-1 pl-5"><li>补充病斑正反面、根系和全株照片，并记录取样位置。</li><li>记录发病时间、扩散比例、近期天气和施肥用药史。</li><li>出现快速扩散、疑似检疫性病虫害或药害时，及时联系当地植保或农技部门。</li></ol></InfoSection>
  </ServicePage>
}
