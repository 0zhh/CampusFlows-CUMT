import type { SiteStatic } from './types'
import raw from './site_geolocation.json'

const geo = raw as any

function geoOf(id: string) {
  const s = geo.sites.find((x: any) => x.id === id)
  return { lat: s.approximate_wgs84.lat, lng: s.approximate_wgs84.lng, px: s.image_pixels.x_px, py: s.image_pixels.y_px }
}

export const SITES: SiteStatic[] = [
  {
    id: 'NH-TAOYUAN',
    name: '桃苑物流服务中心',
    shortName: '桃苑',
    role: 'main_hub',
    roleLabel: '主站',
    area: '桃苑',
    locationText: '桃苑 4 号楼楼下南侧',
    hours: { open: '08:30', close: '18:30' },
    services: ['普通快递代收与自取', '部分大件代收与人工查件', '人工寄件', '顺丰驿收发 / 京东小蜜蜂服务区（站内西侧）'],
    color: 'var(--tao)',
    ...geoOf('NH-TAOYUAN')
  },
  {
    id: 'NH-SONGYUAN',
    name: '松苑无人菜鸟驿站',
    shortName: '松苑',
    role: 'unmanned',
    roleLabel: '无人辅站',
    area: '松苑',
    locationText: '松苑 1 号楼南侧，面向二食堂',
    hours: { open: '07:00', close: '23:30' },
    services: ['部分中小件代收', '自助取件'],
    color: 'var(--song)',
    ...geoOf('NH-SONGYUAN')
  },
  {
    id: 'NH-MEIYUAN',
    name: '梅苑无人菜鸟驿站',
    shortName: '梅苑',
    role: 'unmanned',
    roleLabel: '无人辅站',
    area: '梅苑',
    locationText: '梅苑 1 号楼北侧，面向竹苑 4 号楼',
    hours: { open: '07:00', close: '23:30' },
    services: ['部分中小件代收', '自助取件'],
    color: 'var(--mei)',
    ...geoOf('NH-MEIYUAN')
  },
  {
    id: 'NH-LANYUAN',
    name: '兰苑无人菜鸟驿站',
    shortName: '兰苑',
    role: 'unmanned',
    roleLabel: '无人辅站',
    area: '兰苑',
    locationText: '兰苑 1 号楼南侧，面向兰苑 2 号楼',
    hours: { open: '07:00', close: '23:30' },
    services: ['部分中小件代收', '自助取件'],
    color: 'var(--lan)',
    ...geoOf('NH-LANYUAN')
  }
]

export const SITE_BY_ID = Object.fromEntries(SITES.map((s) => [s.id, s]))

export const SUPPLEMENTARY = [
  {
    id: 'NH-MAILROOM',
    name: '南湖收发室',
    locationText: '竹苑 3 号楼一层南侧、三食堂斜对面',
    note: '补充邮政服务点，不并入四站库存仿真',
    tag: '公开资料'
  }
]

export const NOT_TO_BUILD = ['竹苑无独立菜鸟驿站（指南建议可到梅苑）', '杏苑未找到独立快递站的可靠证据，不新增虚构站点']

/** 当前时刻是否在营业时间内（按常态演示时间，不含节假日） */
export function isOpenNow(site: SiteStatic, now = new Date()): boolean {
  const m = now.getHours() * 60 + now.getMinutes()
  const [oh, om] = site.hours.open.split(':').map(Number)
  const [ch, cm] = site.hours.close.split(':').map(Number)
  return m >= oh * 60 + om && m < ch * 60 + cm
}
