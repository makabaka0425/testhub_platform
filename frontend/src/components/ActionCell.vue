<template>
  <div class="action-cell">
    <!-- 直接显示的按钮 -->
    <el-button
      v-for="action in visibleActions"
      :key="action.key"
      class="action-btn"
      :class="{ 'action-btn--danger': action.danger }"
      :type="action.type || 'primary'"
      link
      size="small"
      :loading="action.loading"
      :disabled="action.disabled"
      @click="handleClick(action)"
    >
      <el-icon v-if="action.icon"><component :is="action.icon" /></el-icon>
      <span v-if="action.label">{{ action.label }}</span>
    </el-button>

    <!-- 更多下拉 -->
    <el-dropdown
      v-if="overflowActions.length > 0"
      trigger="hover"
      @command="handleDropdownCommand"
    >
      <el-button class="action-btn action-btn--more" link size="small">
        <el-icon><MoreFilled /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="action in overflowActions"
            :key="action.key"
            :command="action.key"
            :divided="action.divided"
            :disabled="action.disabled"
          >
            <el-icon v-if="action.icon"><component :is="action.icon" /></el-icon>
            <span :style="{ color: action.danger ? '#f56c6c' : '' }">{{ action.label }}</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  /**
   * 操作列表，每项格式：
   * { key, label, type, danger, icon, disabled, divided, loading, onClick }
   * - key:      唯一标识（必须）
   * - label:    按钮文字（图标按钮可省略）
   * - type:     按钮类型，默认 primary
   * - danger:   是否为危险操作（红色文字）
   * - icon:     图标组件
   * - disabled: 是否禁用
   * - divided:  下拉菜单中是否显示分隔线
   * - loading:  是否加载中
   * - onClick:  点击回调函数，参数为 row
   * - hidden:   是否隐藏此项
   */
  actions: {
    type: Array,
    default: () => []
  },
  /** 当前行数据，会传给 onClick */
  row: {
    type: Object,
    default: () => ({})
  },
  /** 直接显示的按钮数量阈值，超出部分收纳到"更多" */
  maxVisible: {
    type: Number,
    default: 3
  }
})

// 过滤掉 hidden 的操作
const filteredActions = computed(() =>
  props.actions.filter(a => !a.hidden)
)

// 直接显示的按钮
const visibleActions = computed(() =>
  filteredActions.value.slice(0, props.maxVisible)
)

// 收纳到"更多"的按钮
const overflowActions = computed(() =>
  filteredActions.value.slice(props.maxVisible)
)

// 点击直接显示的按钮
const handleClick = (action) => {
  if (action.disabled || action.loading) return
  action.onClick?.(props.row)
}

// 点击下拉菜单项
const handleDropdownCommand = (key) => {
  const action = filteredActions.value.find(a => a.key === key)
  if (action && !action.disabled) {
    action.onClick?.(props.row)
  }
}
</script>

<style scoped>
.action-cell {
  display: flex;
  align-items: center;
  gap: 0;
  padding-right: 8px;
}

.action-btn {
  --el-button-text-color: var(--brand-500, #4f8cff);
  padding: 2px 6px !important;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}

.action-btn--danger {
  --el-button-text-color: #f56c6c;
}

.action-btn--more {
  --el-button-text-color: var(--gray-500, #64748b);
  padding: 2px 4px !important;
}

.action-btn .el-icon + span {
  margin-left: 2px;
}

/* 下拉菜单项样式 */
:deep(.el-dropdown-menu__item) {
  font-size: 13px;
  padding: 6px 16px;
}

:deep(.el-dropdown-menu__item .el-icon) {
  margin-right: 4px;
}
</style>
