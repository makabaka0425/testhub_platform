<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">{{ isEdit ? '编辑缺陷' : '新建缺陷' }}</h1>
      <el-button @click="router.back()">
        <el-icon><Back /></el-icon>
        返回
      </el-button>
    </div>

    <div class="card-container">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
        <el-row :gutter="16">
          <el-col :xs="24" :md="16">
            <el-form-item label="缺陷标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入缺陷标题" maxlength="300" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="所属项目" prop="project_id">
              <el-select
                v-model="form.project_id"
                filterable
                clearable
                placeholder="请选择项目"
                class="full-width"
                @change="handleProjectChange"
              >
                <el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :md="6">
            <el-form-item label="版本">
              <el-select
                v-model="form.version_id"
                filterable
                clearable
                :disabled="!form.project_id"
                :placeholder="form.project_id ? '请选择版本' : '请先选择项目'"
                class="full-width"
              >
                <el-option v-for="version in versions" :key="version.id" :label="version.name" :value="version.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-form-item label="模块" prop="module" required>
              <el-input v-model="form.module" placeholder="请输入模块名称" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-form-item label="严重级别" prop="severity">
              <el-select v-model="form.severity" class="full-width">
                <el-option v-for="item in severityOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="form.priority" class="full-width">
                <el-option v-for="item in priorityOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :md="8">
            <el-form-item label="缺陷类型" prop="defect_type" required>
              <el-select v-model="form.defect_type" clearable placeholder="请选择缺陷类型" class="full-width">
                <el-option v-for="item in defectTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="来源">
              <el-select v-model="form.source" class="full-width">
                <el-option v-for="item in sourceOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="处理人">
              <el-select v-model="form.assignee_id" filterable clearable placeholder="请选择处理人" class="full-width">
                <el-option v-for="user in users" :key="user.id" :label="user.username || user.name" :value="user.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="缺陷描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="描述缺陷现象、影响范围或上下文" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input v-model="form.reproduce_steps" type="textarea" :rows="4" placeholder="按步骤描述如何复现" />
        </el-form-item>

        <el-row :gutter="16">
          <el-col :xs="24" :md="12">
            <el-form-item label="预期结果">
              <el-input v-model="form.expected_result" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="实际结果">
              <el-input v-model="form.actual_result" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="期望修复时间">
          <el-date-picker
            v-model="form.due_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="请选择时间"
          />
        </el-form-item>

        <div class="form-actions">
          <el-button @click="router.back()">取消</el-button>
          <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { createDefect, getDefect, updateDefect } from '@/api/defects'
import {
  defectTypeOptions,
  priorityOptions,
  severityOptions,
  sourceOptions
} from './options'

const route = useRoute()
const router = useRouter()
const formRef = ref()
const submitting = ref(false)
const projects = ref([])
const versions = ref([])
const users = ref([])
const isEdit = computed(() => Boolean(route.params.id))

const nullableFields = ['project_id', 'version_id', 'assignee_id', 'due_at']

const form = reactive({
  title: '',
  description: '',
  reproduce_steps: '',
  expected_result: '',
  actual_result: '',
  project_id: '',
  version_id: '',
  module: '',
  severity: 'major',
  priority: 'p2',
  defect_type: '',
  source: 'manual',
  assignee_id: '',
  due_at: ''
})

const rules = {
  title: [{ required: true, message: '请输入缺陷标题', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  module: [{ required: true, message: '请输入模块名称', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择严重级别', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  defect_type: [{ required: true, message: '请选择缺陷类型', trigger: 'change' }]
}

const normalizeList = (data) => data?.results || data || []

const fetchProjects = async () => {
  try {
    const response = await api.get('/projects/')
    projects.value = normalizeList(response.data)
  } catch (error) {
    projects.value = []
  }
}

const fetchVersions = async (projectId = form.project_id) => {
  if (!projectId) {
    versions.value = []
    return
  }

  try {
    const response = await api.get(`/versions/projects/${projectId}/versions/`)
    versions.value = normalizeList(response.data)
  } catch (error) {
    versions.value = []
  }
}

const fetchUsers = async () => {
  try {
    const response = await api.get('/users/')
    users.value = normalizeList(response.data)
  } catch (error) {
    users.value = []
  }
}

const handleProjectChange = async () => {
  form.version_id = ''
  await fetchVersions()
}

const loadDefect = async () => {
  if (!isEdit.value) return

  try {
    const response = await getDefect(route.params.id)
    const data = response.data || {}
    form.title = data.title || ''
    form.description = data.description || ''
    form.reproduce_steps = data.reproduce_steps || ''
    form.expected_result = data.expected_result || ''
    form.actual_result = data.actual_result || ''
    form.project_id = data.project?.id || ''
    form.version_id = data.version?.id || ''
    form.module = data.module || ''
    form.severity = data.severity || 'major'
    form.priority = data.priority || 'p2'
    form.defect_type = data.defect_type || ''
    form.source = data.source || 'manual'
    form.assignee_id = data.assignee?.id || ''
    form.due_at = data.due_at || ''
    await fetchVersions(data.project?.id || '')
  } catch (error) {
    ElMessage.error('加载缺陷详情失败')
  }
}

const buildPayload = () => {
  const payload = { ...form }

  nullableFields.forEach((field) => {
    if (payload[field] === '') {
      payload[field] = null
    }
  })

  return payload
}

const extractErrorMessage = (errorData) => {
  if (!errorData) return ''
  if (typeof errorData === 'string') return errorData
  if (Array.isArray(errorData)) return errorData[0] || ''

  const firstValue = Object.values(errorData)[0]
  if (Array.isArray(firstValue)) return firstValue[0] || ''
  if (typeof firstValue === 'string') return firstValue
  return ''
}

const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true
    const payload = buildPayload()

    if (isEdit.value) {
      await updateDefect(route.params.id, payload)
      ElMessage.success('缺陷已更新')
      router.push(`/defects/${route.params.id}`)
    } else {
      const response = await createDefect(payload)
      ElMessage.success('缺陷已创建')
      router.push(`/defects/${response.data?.id || 'list'}`)
    }
  } catch (error) {
    if (error?.response) {
      const message = extractErrorMessage(error.response.data) || '保存缺陷失败'
      ElMessage.error(message)
    }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchProjects(), fetchUsers()])
  await loadDefect()
})
</script>

<style lang="scss" scoped>
.full-width {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 12px;
}
</style>
