/**
 * 启动时探测后端：能连上就用真数据，连不上就用内置样例。
 * 无论成败都不阻塞首屏——先渲染样例，探测完成后再决定要不要换源。
 */
import { ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { fetchRemote } from '@/data/api'
import { setRemoteBundle } from './useData'

export const probing = ref(true)
/** 探测结论的人话说明，给「资料与说明」页用 */
export const probeNote = ref<string>('正在检测后端接口…')

export async function initDataSource() {
  const store = useAppStore()
  probing.value = true
  const remote = await fetchRemote()

  if (remote) {
    setRemoteBundle(remote.bundle)
    store.dataMode = 'api'
    probeNote.value = `已连接后端接口，数据来自 /api/scenarios（生成于 ${remote.bundle.generated_at}）`
  } else {
    store.dataMode = 'local'
    probeNote.value = '未检测到后端接口（/api/scenarios 不可达），当前使用内置演示样例数据'
  }
  probing.value = false
}
