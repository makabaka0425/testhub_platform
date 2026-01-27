<template>
  <div class="key-value-editor">
    <div class="header">
      <div class="column key-column">Key</div>
      <div class="column value-column">Value</div>
      <div class="column description-column">Description</div>
      <div class="column action-column"></div>
    </div>
    
    <div class="rows">
      <div
        v-for="(row, index) in rows"
        :key="index"
        class="row"
        :class="{ disabled: !row.enabled }"
      >
        <div class="column key-column">
          <el-checkbox v-model="row.enabled" @change="updateValue" />
          <el-input
            v-model="row.key"
            :placeholder="placeholderKey"
            size="small"
            @input="updateValue"
          />
        </div>
        
        <div class="column value-column">
          <el-input
            v-if="!showFile || row.type !== 'file'"
            v-model="row.value"
            :placeholder="placeholderValue"
            size="small"
            @input="updateValue"
          >
            <template #append>
              <el-button
                size="small"
                :icon="MagicStick"
                @click="openDataFactorySelector(index)"
                title="引用数据工厂"
                class="data-factory-btn"
              />
            </template>
          </el-input>
          <el-upload
            v-else
            :auto-upload="false"
            :show-file-list="false"
            @change="(file) => handleFileChange(index, file)"
          >
            <el-button size="small">选择文件</el-button>
          </el-upload>
          <el-tooltip content="插入动态变量" placement="top" v-if="!showFile || row.type !== 'file'">
            <el-button size="small" style="margin-left: 5px" @click="openVariableHelper(index)" class="variable-helper-btn">
              <el-icon><MagicStick /></el-icon>
            </el-button>
          </el-tooltip>
          <span v-if="row.file" class="file-name">{{ row.file.name }}</span>
        </div>
        
        <div class="column description-column">
          <el-input
            v-model="row.description"
            placeholder="描述"
            size="small"
            @input="updateValue"
          />
        </div>
        
        <div class="column action-column">
          <el-select
            v-if="showFile"
            v-model="row.type"
            size="small"
            style="width: 70px; margin-right: 5px;"
            @change="updateValue"
          >
            <el-option label="Text" value="text" />
            <el-option label="File" value="file" />
          </el-select>
          
          <el-button
            size="small"
            type="danger"
            :icon="Delete"
            @click="removeRow(index)"
            :disabled="rows.length <= 1"
          />
        </div>
      </div>
    </div>
    
    <div class="footer">
      <el-button size="small" @click="addRow">
        <el-icon><Plus /></el-icon>
        添加行
      </el-button>
    </div>
    
    <DataFactorySelector
      v-model="showDataFactorySelector"
      @select="handleDataFactorySelect"
    />
    
    <el-dialog
      :close-on-press-escape="false"
      :modal="true"
      :destroy-on-close="false"
      v-model="showVariableHelper"
      title="变量助手 (点击插入)"
      :close-on-click-modal="false"
      width="900px"
    >
      <el-tabs tab-position="left" style="height: 450px">
        <el-tab-pane
          v-for="(category, index) in variableCategories"
          :key="index"
          :label="category.label"
        >
          <div style="height: 450px; overflow-y: auto; padding: 10px;">
            <el-table :data="category.variables" style="width: 100%" @row-click="insertVariable" highlight-current-row>
              <el-table-column prop="name" label="函数名" width="150" show-overflow-tooltip>
                <template #default="{ row }">
                  <el-tag size="small">{{ row.name }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="desc" label="描述" min-width="150" />
              <el-table-column prop="syntax" label="语法" min-width="200" show-overflow-tooltip />
              <el-table-column prop="example" label="示例" min-width="200" show-overflow-tooltip />
              <el-table-column label="操作" width="80" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" size="small">插入</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { Plus, Delete, MagicStick } from '@element-plus/icons-vue'
import DataFactorySelector from '@/components/DataFactorySelector.vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  placeholderKey: {
    type: String,
    default: 'Key'
  },
  placeholderValue: {
    type: String,
    default: 'Value'
  },
  showFile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const rows = ref([])
const showDataFactorySelector = ref(false)
const showVariableHelper = ref(false)
const currentRowIndex = ref(0)

const variableCategories = [
  {
    label: '随机数',
    variables: [
      { name: 'random_int', syntax: '${random_int(min, max, count)}', desc: '生成随机整数', example: '${random_int(100, 999, 1)}' },
      { name: 'random_float', syntax: '${random_float(min, max, precision, count)}', desc: '生成随机浮点数', example: '${random_float(0, 1, 2, 1)}' },
      { name: 'random_boolean', syntax: '${random_boolean(count)}', desc: '生成随机布尔值', example: '${random_boolean(1)}' },
      { name: 'random_date', syntax: '${random_date(start_date, end_date, count, date_format)}', desc: '生成随机日期', example: '${random_date(2024-01-01, 2024-12-31, 1, %Y-%m-%d)}' }
    ]
  },
  {
    label: '随机字符串',
    variables: [
      { name: 'random_string', syntax: '${random_string(length, char_type, count)}', desc: '生成随机字符串', example: '${random_string(8, all, 1)}' },
      { name: 'random_uuid', syntax: '${random_uuid(version, count)}', desc: '生成UUID', example: '${random_uuid(4, 1)}' },
      { name: 'random_mac_address', syntax: '${random_mac_address(separator, count)}', desc: '生成MAC地址', example: '${random_mac_address(:, 1)}' },
      { name: 'random_ip_address', syntax: '${random_ip_address(ip_version, count)}', desc: '生成IP地址', example: '${random_ip_address(4, 1)}' },
      { name: 'random_sequence', syntax: '${random_sequence(sequence, count, unique)}', desc: '从序列中随机选择', example: '${random_sequence([a,b,c], 1, false)}' }
    ]
  },
  {
    label: '字符工具',
    variables: [
      { name: 'remove_whitespace', syntax: '${remove_whitespace(text, type)}', desc: '去除空格换行', example: '${remove_whitespace(hello world, all)}' },
      { name: 'replace_string', syntax: '${replace_string(text, old, new, count)}', desc: '字符串替换', example: '${replace_string(hello world, world, test, 1)}' },
      { name: 'word_count', syntax: '${word_count(text)}', desc: '字数统计', example: '${word_count(hello world)}' },
      { name: 'regex_test', syntax: '${regex_test(text, pattern, flags)}', desc: '正则测试', example: '${regex_test(hello123, ^[a-z]+\\d+$, gi)}' },
      { name: 'case_convert', syntax: '${case_convert(text, case_type)}', desc: '大小写转换', example: '${case_convert(hello, upper)}' }
    ]
  },
  {
    label: '测试数据',
    variables: [
      { name: 'generate_chinese_name', syntax: '${generate_chinese_name(gender, count)}', desc: '生成中文姓名', example: '${generate_chinese_name(random, 1)}' },
      { name: 'generate_chinese_phone', syntax: '${generate_chinese_phone(count)}', desc: '生成手机号', example: '${generate_chinese_phone(1)}' },
      { name: 'generate_chinese_email', syntax: '${generate_chinese_email(count)}', desc: '生成邮箱', example: '${generate_chinese_email(1)}' },
      { name: 'generate_chinese_address', syntax: '${generate_chinese_address(full_address, count)}', desc: '生成地址', example: '${generate_chinese_address(true, 1)}' },
      { name: 'generate_id_card', syntax: '${generate_id_card(count)}', desc: '生成身份证号', example: '${generate_id_card(1)}' },
      { name: 'generate_company_name', syntax: '${generate_company_name(count)}', desc: '生成公司名称', example: '${generate_company_name(1)}' },
      { name: 'generate_bank_card', syntax: '${generate_bank_card(count)}', desc: '生成银行卡号', example: '${generate_bank_card(1)}' },
      { name: 'generate_hk_id_card', syntax: '${generate_hk_id_card(count)}', desc: '生成香港身份证号', example: '${generate_hk_id_card(1)}' },
      { name: 'generate_business_license', syntax: '${generate_business_license(count)}', desc: '生成营业执照号', example: '${generate_business_license(1)}' },
      { name: 'generate_user_profile', syntax: '${generate_user_profile(count)}', desc: '生成用户档案', example: '${generate_user_profile(1)}' },
      { name: 'generate_coordinates', syntax: '${generate_coordinates(count)}', desc: '生成经纬度', example: '${generate_coordinates(1)}' }
    ]
  },
  {
    label: '时间日期',
    variables: [
      { name: 'timestamp_convert', syntax: '${timestamp_convert(timestamp, convert_type)}', desc: '时间戳转换', example: '${timestamp_convert(1234567890, to_datetime)}' },
      { name: 'random_date', syntax: '${random_date(start_date, end_date, count, date_format)}', desc: '生成随机日期', example: '${random_date(2024-01-01, 2024-12-31, 1, %Y-%m-%d)}' }
    ]
  },
  {
    label: '编码转换',
    variables: [
      { name: 'base64_encode', syntax: '${base64_encode(text, encoding)}', desc: 'Base64编码', example: '${base64_encode("123456", "utf-8")}' },
      { name: 'base64_decode', syntax: '${base64_decode(text, encoding)}', desc: 'Base64解码', example: '${base64_decode("MTIzNDU2", "utf-8")}' },
      { name: 'url_encode', syntax: '${url_encode(data, encoding)}', desc: 'URL编码', example: '${url_encode("hello world", "utf-8")}' },
      { name: 'url_decode', syntax: '${url_decode(data, encoding)}', desc: 'URL解码', example: '${url_decode("hello%20world", "utf-8")}' },
      { name: 'unicode_convert', syntax: '${unicode_convert(text, convert_type)}', desc: 'Unicode转换', example: '${unicode_convert("你好", "to_unicode")}' },
      { name: 'ascii_convert', syntax: '${ascii_convert(text, convert_type)}', desc: 'ASCII转换', example: '${ascii_convert("ABC", "to_ascii")}' },
      { name: 'color_convert', syntax: '${color_convert(color, from_type, to_type)}', desc: '颜色值转换', example: '${color_convert("#ff0000", "hex", "rgb")}' },
      { name: 'base_convert', syntax: '${base_convert(number, from_base, to_base)}', desc: '进制转换', example: '${base_convert(10, 10, 16)}' },
      { name: 'timestamp_convert', syntax: '${timestamp_convert(timestamp, convert_type)}', desc: '时间戳转换', example: '${timestamp_convert(1234567890, "to_datetime")}' },
      { name: 'generate_barcode', syntax: '${generate_barcode(data, format)}', desc: '生成条形码', example: '${generate_barcode("123456", "code128")}' },
      { name: 'generate_qrcode', syntax: '${generate_qrcode(data)}', desc: '生成二维码', example: '${generate_qrcode("https://example.com")}' },
      { name: 'decode_qrcode', syntax: '${decode_qrcode(data)}', desc: '二维码解析', example: '${decode_qrcode("/path/to/image.png")}' },
      { name: 'image_to_base64', syntax: '${image_to_base64(image_path)}', desc: '图片转Base64', example: '${image_to_base64("/path/to/image.png")}' },
      { name: 'base64_to_image', syntax: '${base64_to_image(base64_data, output_path)}', desc: 'Base64转图片', example: '${base64_to_image("data:image/png;base64,...", "/path/to/output.png")}' }
    ]
  },
  {
    label: '加密哈希',
    variables: [
      { name: 'md5_hash', syntax: '${md5_hash(text)}', desc: 'MD5加密', example: '${md5_hash("123456")}' },
      { name: 'sha1_hash', syntax: '${sha1_hash(text)}', desc: 'SHA1加密', example: '${sha1_hash("123456")}' },
      { name: 'sha256_hash', syntax: '${sha256_hash(text)}', desc: 'SHA256加密', example: '${sha256_hash("123456")}' },
      { name: 'sha512_hash', syntax: '${sha512_hash(text)}', desc: 'SHA512加密', example: '${sha512_hash("123456")}' },
      { name: 'hash_comparison', syntax: '${hash_comparison(hash1, hash2)}', desc: '哈希值比对', example: '${hash_comparison("hash1", "hash2")}' },
      { name: 'aes_encrypt', syntax: '${aes_encrypt(text, password, mode)}', desc: 'AES加密', example: '${aes_encrypt("hello", "password", "CBC")}' },
      { name: 'aes_decrypt', syntax: '${aes_decrypt(encrypted_text, password, mode)}', desc: 'AES解密', example: '${aes_decrypt("encrypted", "password", "CBC")}' }
    ]
  },
  {
    label: 'Crontab',
    variables: [
      { name: 'generate_expression', syntax: '${generate_expression(minute, hour, day, month, weekday)}', desc: '生成Crontab表达式', example: '${generate_expression("*", "*", "*", "*", "*")}' },
      { name: 'parse_expression', syntax: '${parse_expression(expression)}', desc: '解析Crontab表达式', example: '${parse_expression("0 0 * * *")}' },
      { name: 'get_next_runs', syntax: '${get_next_runs(expression, count)}', desc: '获取下次执行时间', example: '${get_next_runs("0 0 * * *", 5)}' },
      { name: 'validate_expression', syntax: '${validate_expression(expression)}', desc: '验证Crontab表达式', example: '${validate_expression("0 0 * * *")}' }
    ]
  },
  {
    label: '其他',
    variables: [
      { name: 'random_password', syntax: '${random_password(length, include_uppercase, include_lowercase, include_digits, include_special, count)}', desc: '生成随机密码', example: '${random_password(12, true, true, true, true, 1)}' },
      { name: 'random_color', syntax: '${random_color(format, count)}', desc: '生成随机颜色', example: '${random_color(hex, 1)}' },
      { name: 'jwt_decode', syntax: '${jwt_decode(token, verify, secret)}', desc: 'JWT解码', example: '${jwt_decode(token, false, secret)}' },
      { name: 'password_strength', syntax: '${password_strength(password)}', desc: '密码强度分析', example: '${password_strength(myPassword123)}' },
      { name: 'generate_salt', syntax: '${generate_salt(length)}', desc: '生成随机盐值', example: '${generate_salt(16)}' }
    ]
  }
]

const initializeRows = () => {
  const data = props.modelValue || {}
  console.log('KeyValueEditor initializeRows called with data:', data)
  const newRows = []
  
  // 检查数据是否为数组格式（来自convertObjectToKeyValueArray）
  if (Array.isArray(data)) {
    console.log('Data is array, processing...')
    // 如果是数组，直接使用
    newRows.push(...data.map(item => ({
      enabled: item.enabled !== false,
      key: item.key || '',
      value: item.value || '',
      description: item.description || '',
      type: item.type || 'text',
      file: item.file || null
    })))
  } else {
    console.log('Data is object, converting...')
    // 如果是对象，转换为行数据
    Object.keys(data).forEach(key => {
      if (key && data[key] !== undefined) {
        newRows.push({
          enabled: true,
          key,
          value: data[key],
          description: '',
          type: 'text',
          file: null
        })
      }
    })
  }
  
  // 确保至少有一个空行
  if (newRows.length === 0) {
    newRows.push({
      enabled: true,
      key: '',
      value: '',
      description: '',
      type: 'text',
      file: null
    })
  }
  
  console.log('KeyValueEditor final rows:', newRows)
  rows.value = newRows
}

const updateValue = () => {
  // 发送完整的行数据数组，而不是简化的key-value对象
  const result = rows.value.filter(row => row.key || row.value || row.description).map(row => ({
    key: row.key || '',
    value: row.value || '',
    description: row.description || '',
    enabled: row.enabled !== false,
    type: row.type || 'text'
  }))
  
  console.log('KeyValueEditor updateValue result (full format):', result)
  emit('update:modelValue', result)
  
  // 如果最后一行有内容，自动添加新行
  const lastRow = rows.value[rows.value.length - 1]
  if (lastRow.key || lastRow.value) {
    addRow()
  }
}

const addRow = () => {
  rows.value.push({
    enabled: true,
    key: '',
    value: '',
    description: '',
    type: 'text',
    file: null
  })
}

const removeRow = (index) => {
  if (rows.value.length > 1) {
    rows.value.splice(index, 1)
    updateValue()
  }
}

const handleFileChange = (index, file) => {
  rows.value[index].file = file
  rows.value[index].value = file.name
  updateValue()
}

const openDataFactorySelector = (index) => {
  currentRowIndex.value = index
  showDataFactorySelector.value = true
}

const handleDataFactorySelect = (record) => {
  const rowIndex = currentRowIndex.value
  if (record && record.output_data) {
    let valueToSet = ''
    
    if (typeof record.output_data === 'string') {
      valueToSet = record.output_data
    } else if (record.output_data.result) {
      valueToSet = record.output_data.result
    } else if (record.output_data.output_data) {
      valueToSet = record.output_data.output_data
    } else {
      valueToSet = JSON.stringify(record.output_data)
    }
    
    rows.value[rowIndex].value = valueToSet
    rows.value[rowIndex].description = `来自数据工厂: ${record.tool_name}`
    updateValue()
  }
  showDataFactorySelector.value = false
}

const openVariableHelper = (index) => {
  currentRowIndex.value = index
  showVariableHelper.value = true
}

const insertVariable = (variable) => {
  const rowIndex = currentRowIndex.value
  const example = variable.example
  
  const currentValue = rows.value[rowIndex].value || ''
  if (!currentValue) {
    rows.value[rowIndex].value = example
  } else {
    rows.value[rowIndex].value = currentValue + example
  }
  
  ElMessage.success(`已插入变量: ${variable.name}`)
  showVariableHelper.value = false
  updateValue()
}

// 监听props.modelValue变化
watch(
  () => props.modelValue,
  () => {
    initializeRows()
  },
  { immediate: true }
)

// 暴露rows供父组件访问
defineExpose({
  rows
})
</script>

<style scoped>
.key-value-editor {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: white;
}

.header {
  display: flex;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  padding: 8px;
  font-weight: 500;
  font-size: 12px;
  color: #606266;
}

.rows {
  max-height: 300px;
  overflow-y: auto;
}

.row {
  display: flex;
  border-bottom: 1px solid #f5f7fa;
  padding: 8px;
  min-height: 40px;
  align-items: center;
}

.row:hover {
  background: #fafbfc;
}

.row.disabled {
  opacity: 0.6;
}

.column {
  display: flex;
  align-items: center;
  gap: 5px;
}

.key-column {
  width: 25%;
  min-width: 150px;
}

.value-column {
  width: 25%;
  min-width: 200px;
}

.description-column {
  width: 30%;
  min-width: 120px;
}

.action-column {
  width: 20%;
  min-width: 100px;
  justify-content: flex-end;
  gap: 135px;
}

.data-factory-btn {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: white !important;
}

.data-factory-btn:hover {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
}

.variable-helper-btn {
  background-color: #67c23a;
  border-color: #67c23a;
  color: white;
}

.variable-helper-btn:hover {
  background-color: #5daf34;
  border-color: #5daf34;
}

.file-name {
  font-size: 12px;
  color: #606266;
  margin-left: 8px;
}

.footer {
  padding: 8px;
  border-top: 1px solid #f5f7fa;
  background: #fafbfc;
}

/* 变量助手弹窗样式优化 */
:deep(.el-dialog__body) {
  padding: 0;
}

:deep(.el-tabs__content) {
  height: 100%;
}

:deep(.el-tab-pane) {
  height: 100%;
}

:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

:deep(.el-table td) {
  padding: 12px 0;
}

:deep(.el-table .cell) {
  padding: 0 10px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-table__row.current-row) {
  background-color: #ecf5ff;
}
</style>