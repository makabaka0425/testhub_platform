/**
 * APP自动化测试模块 - 公共工具函数
 */

// ========== 状态映射 ==========

const EXECUTION_STATUS_MAP = {
  'pending':   { type: 'info',    text: '等待中' },
  'running':   { type: 'warning', text: '执行中' },
  'success':   { type: 'success', text: '成功' },
  'completed': { type: 'success', text: '已完成' },
  'failed':    { type: 'danger',  text: '失败' },
  'stopped':   { type: 'info',    text: '已停止' },
}

const DEVICE_STATUS_MAP = {
  'available': { type: 'success', text: '可用' },
  'locked':    { type: 'warning', text: '已锁定' },
  'online':    { type: 'success', text: '在线' },
  'offline':   { type: 'danger',  text: '离线' },
}

/**
 * 获取执行状态的 Element Plus Tag 类型
 * @param {string} status - 状态值
 * @returns {string} - 'info' | 'warning' | 'success' | 'danger'
 */
export function getExecutionStatusType(status) {
  return EXECUTION_STATUS_MAP[status]?.type || 'info'
}

/**
 * 获取执行状态的中文文本
 * @param {string} status - 状态值
 * @returns {string}
 */
export function getExecutionStatusText(status) {
  return EXECUTION_STATUS_MAP[status]?.text || status
}

/**
 * 获取设备状态的 Element Plus Tag 类型
 * @param {string} status - 状态值
 * @returns {string}
 */
export function getDeviceStatusType(status) {
  return DEVICE_STATUS_MAP[status]?.type || 'info'
}

/**
 * 获取设备状态的中文文本
 * @param {string} status - 状态值
 * @returns {string}
 */
export function getDeviceStatusText(status) {
  return DEVICE_STATUS_MAP[status]?.text || status
}

// ========== 日期格式化 ==========

/**
 * 格式化日期时间（完整格式）
 * @param {string} timeStr - ISO 时间字符串
 * @returns {string}
 */
export function formatDateTime(timeStr) {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 格式化为相对时间（如"3分钟前"）
 * @param {string} timeStr - ISO 时间字符串
 * @returns {string}
 */
export function formatRelativeTime(timeStr) {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前'
  return Math.floor(diff / 86400000) + ' 天前'
}
