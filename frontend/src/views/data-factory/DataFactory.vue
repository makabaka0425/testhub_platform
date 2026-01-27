<template>
  <div class="data-factory-container">
    <el-card class="header-card">
      <div class="header-content">
        <h1 class="page-title" @click="goToHome">
          <el-icon class="title-icon"><DataLine /></el-icon>
          数据工厂
        </h1>
        <p class="page-subtitle">智能数据生成工具箱 - 为测试提供高质量测试数据</p>
        <div class="header-actions">
          <el-button-group>
            <el-button
              :type="viewMode === 'category' ? 'primary' : ''"
              @click="viewMode = 'category'"
            >
              <el-icon><Menu /></el-icon>
              按工具分类
            </el-button>
            <el-button
              :type="viewMode === 'scenario' ? 'primary' : ''"
              @click="viewMode = 'scenario'"
            >
              <el-icon><Grid /></el-icon>
              按使用场景
            </el-button>
          </el-button-group>
          <el-button type="info" @click="showHistory = true">
            <el-icon><Clock /></el-icon>
            使用历史
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 工具分类视图 -->
    <div v-if="viewMode === 'category'" class="category-view">
      <div
        v-for="category in filteredCategories()"
        :key="category.category"
        class="category-section"
      >
        <el-card class="category-card">
          <template #header>
            <div class="category-header">
              <el-icon :class="`category-icon ${category.icon}`">
                <component :is="getIcon(category.icon)" />
              </el-icon>
              <span class="category-title">{{ category.name }}</span>
              <el-tag size="small">{{ category.tools.length }}个工具</el-tag>
              <el-button
                v-if="currentScenario"
                size="small"
                @click.stop="clearScenario"
                style="margin-left: auto;"
              >
                清除筛选
              </el-button>
            </div>
          </template>
          <div class="tools-grid">
            <div
              v-for="tool in category.tools"
              :key="tool.name"
              class="tool-item"
              @click="openTool(tool, category.category)"
            >
              <div class="tool-icon">
                <el-icon><component :is="getIcon(tool.icon || 'operation')" /></el-icon>
              </div>
              <div class="tool-info">
                <h4 class="tool-name">{{ tool.display_name }}</h4>
                <p class="tool-desc">{{ tool.description }}</p>
              </div>
              <el-icon class="tool-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 场景视图 -->
    <div v-else class="scenario-view">
      <el-row :gutter="20">
        <el-col :span="8" v-for="scenario in scenarios" :key="scenario.scenario">
          <el-card class="scenario-card" @click="filterByScenario(scenario)">
            <div class="scenario-content">
              <el-icon class="scenario-icon">
                <component :is="getScenarioIcon(scenario.scenario)" />
              </el-icon>
              <h3 class="scenario-title">{{ scenario.name }}</h3>
              <p class="scenario-desc">{{ scenario.description }}</p>
              <div class="scenario-stats">
                <el-tag size="small">{{ scenario.tool_count }}个工具</el-tag>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 工具执行对话框 -->
    <el-dialog
      v-model="toolDialogVisible"
      :title="currentTool?.display_name"
      width="1200px"
      :close-on-click-modal="false"
      @close="resetToolForm"
    >
      <div v-if="currentTool" class="tool-execution">
        <el-alert
          :title="currentTool.description"
          type="info"
          :closable="false"
          show-icon
          class="tool-alert"
        />

        <!-- 测试数据工具 - 无需输入参数 -->
        <div v-if="currentCategory === 'test_data'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item label="生成数量">
              <el-input-number v-model="toolForm.count" :min="1" :max="100" />
              <span class="form-tip">生成数据的数量</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_chinese_phone'" label="运营商">
              <el-select v-model="toolForm.region" placeholder="请选择运营商">
                <el-option label="全部" value="all" />
                <el-option label="移动" value="mobile" />
                <el-option label="联通" value="unicom" />
                <el-option label="电信" value="telecom" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_chinese_email'" label="邮箱域名">
              <el-select v-model="toolForm.domain" placeholder="请选择邮箱域名">
                <el-option label="随机" value="random" />
                <el-option label="QQ邮箱" value="qq.com" />
                <el-option label="163邮箱" value="163.com" />
                <el-option label="126邮箱" value="126.com" />
                <el-option label="Gmail" value="gmail.com" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_chinese_address'" label="地址类型">
              <el-switch v-model="toolForm.full_address" active-text="完整地址" inactive-text="简短地址" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 字符工具 -->
        <div v-else-if="currentCategory === 'string'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item v-if="currentTool.name !== 'text_diff'" label="输入文本">
              <el-input
                v-model="toolForm.text"
                type="textarea"
                :rows="4"
                placeholder="请输入文本..."
              />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'replace_string'" label="查找内容">
              <el-input v-model="toolForm.old_str" placeholder="要替换的内容" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'replace_string'" label="替换内容">
              <el-input v-model="toolForm.new_str" placeholder="替换后的内容" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'replace_string'" label="正则表达式">
              <el-switch v-model="toolForm.is_regex" />
              <span class="form-tip">使用正则表达式替换</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'escape_string'" label="转义类型">
              <el-select v-model="toolForm.escape_type" placeholder="请选择转义类型">
                <el-option label="JSON" value="json" />
                <el-option label="HTML" value="html" />
                <el-option label="URL" value="url" />
                <el-option label="XML" value="xml" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'unescape_string'" label="反转义类型">
              <el-select v-model="toolForm.unescape_type" placeholder="请选择反转义类型">
                <el-option label="JSON" value="json" />
                <el-option label="HTML" value="html" />
                <el-option label="URL" value="url" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'regex_test'" label="正则表达式">
              <el-input v-model="toolForm.pattern" placeholder="请输入正则表达式" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'regex_test'" label="标志">
              <el-checkbox-group v-model="toolForm.flags">
                <el-checkbox label="i">忽略大小写</el-checkbox>
                <el-checkbox label="m">多行模式</el-checkbox>
                <el-checkbox label="s">单行模式</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'case_convert'" label="转换类型">
              <el-select v-model="toolForm.convert_type" placeholder="请选择转换类型">
                <el-option label="大写" value="upper" />
                <el-option label="小写" value="lower" />
                <el-option label="首字母大写" value="capitalize" />
                <el-option label="标题格式" value="title" />
                <el-option label="大小写互换" value="swapcase" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'string_format'" label="格式化类型">
              <el-select v-model="toolForm.format_type" placeholder="请选择格式化类型">
                <el-option label="去除首尾空格" value="trim" />
                <el-option label="反转字符串" value="reverse" />
                <el-option label="分割字符串" value="split" />
                <el-option label="合并字符串" value="join" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'text_diff'" label="文本1">
              <el-input
                v-model="toolForm.text1"
                type="textarea"
                :rows="6"
                placeholder="请输入第一个文本..."
              />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'text_diff'" label="文本2">
              <el-input
                v-model="toolForm.text2"
                type="textarea"
                :rows="6"
                placeholder="请输入第二个文本..."
              />
            </el-form-item>
          </el-form>
        </div>

        <!-- 随机工具 -->
        <div v-else-if="currentCategory === 'random'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item v-if="currentTool.name === 'random_int'" label="最小值">
              <el-input-number v-model="toolForm.min_val" :min="-999999" :max="999999" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_int'" label="最大值">
              <el-input-number v-model="toolForm.max_val" :min="-999999" :max="999999" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_float'" label="最小值">
              <el-input-number v-model="toolForm.min_val" :step="0.1" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_float'" label="最大值">
              <el-input-number v-model="toolForm.max_val" :step="0.1" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_float'" label="精度">
              <el-input-number v-model="toolForm.precision" :min="0" :max="10" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_string'" label="长度">
              <el-input-number v-model="toolForm.length" :min="1" :max="1000" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_string'" label="字符类型">
              <el-select v-model="toolForm.char_type" placeholder="请选择字符类型">
                <el-option label="全部" value="all" />
                <el-option label="字母" value="letters" />
                <el-option label="小写字母" value="lowercase" />
                <el-option label="大写字母" value="uppercase" />
                <el-option label="数字" value="digits" />
                <el-option label="字母数字" value="alphanumeric" />
                <el-option label="十六进制" value="hex" />
                <el-option label="中文" value="chinese" />
                <el-option label="特殊字符" value="special" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_uuid'" label="UUID版本">
              <el-select v-model="toolForm.version" placeholder="请选择UUID版本">
                <el-option label="UUID v1" :value="1" />
                <el-option label="UUID v4" :value="4" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_mac_address'" label="分隔符">
              <el-select v-model="toolForm.separator" placeholder="请选择分隔符">
                <el-option label="冒号 (:)" value=":" />
                <el-option label="连字符 (-)" value="-" />
                <el-option label="无" value="" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_ip_address'" label="IP版本">
              <el-select v-model="toolForm.ip_version" placeholder="请选择IP版本">
                <el-option label="IPv4" :value="4" />
                <el-option label="IPv6" :value="6" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_date'" label="开始日期">
              <el-date-picker v-model="toolForm.start_date" type="date" placeholder="选择开始日期" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_date'" label="结束日期">
              <el-date-picker v-model="toolForm.end_date" type="date" placeholder="选择结束日期" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_date'" label="日期格式">
              <el-input v-model="toolForm.date_format" placeholder="%Y-%m-%d" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_color'" label="颜色格式">
              <el-select v-model="toolForm.format" placeholder="请选择颜色格式">
                <el-option label="十六进制" value="hex" />
                <el-option label="RGB" value="rgb" />
                <el-option label="RGBA" value="rgba" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_password'" label="密码长度">
              <el-input-number v-model="toolForm.length" :min="4" :max="50" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_password'" label="字符选项">
              <el-checkbox-group v-model="toolForm.char_options">
                <el-checkbox label="include_uppercase">大写字母</el-checkbox>
                <el-checkbox label="include_lowercase">小写字母</el-checkbox>
                <el-checkbox label="include_digits">数字</el-checkbox>
                <el-checkbox label="include_special">特殊字符</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item v-if="['random_int', 'random_float', 'random_string', 'random_uuid', 'random_mac_address', 'random_ip_address', 'random_date', 'random_boolean', 'random_color', 'random_password', 'random_sequence'].includes(currentTool.name)" label="生成数量">
              <el-input-number v-model="toolForm.count" :min="1" :max="100" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_sequence'" label="序列数据">
              <el-input v-model="toolForm.sequence" type="textarea" :rows="4" placeholder="请输入序列数据，用逗号分隔，例如：apple,banana,orange" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'random_sequence'" label="唯一性">
              <el-switch v-model="toolForm.unique" />
              <span class="form-tip">开启后不会重复选择</span>
            </el-form-item>
          </el-form>
        </div>

        <!-- 编码工具 -->
        <div v-else-if="currentCategory === 'encoding'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item v-if="['generate_barcode', 'generate_qrcode'].includes(currentTool.name)" label="数据">
              <el-input v-model="toolForm.data" placeholder="请输入要编码的数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_barcode'" label="条形码类型">
              <el-select v-model="toolForm.barcode_type" placeholder="请选择条形码类型">
                <el-option label="Code128" value="code128" />
                <el-option label="Code39" value="code39" />
                <el-option label="EAN13" value="ean13" />
                <el-option label="EAN8" value="ean8" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_qrcode'" label="图片大小">
              <el-input-number v-model="toolForm.image_size" :min="100" :max="1000" :step="50" />
              <span class="form-tip">像素值，建议200-500</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'decode_qrcode'" label="上传二维码">
              <el-upload
                class="qr-code-upload"
                :show-file-list="false"
                :before-upload="handleQrCodeUpload"
                accept="image/*"
                drag
              >
                <div v-if="!qrCodeImage" class="upload-placeholder">
                  <el-icon class="upload-icon"><Upload /></el-icon>
                  <div class="upload-text">点击或拖拽上传二维码图片</div>
                  <div class="upload-tip">支持 PNG、JPG、JPEG 等格式</div>
                </div>
                <div v-else class="upload-preview">
                  <img :src="qrCodeImage" alt="二维码预览" />
                  <div class="upload-mask" @click="clearQrCodeImage">
                    <el-icon><Delete /></el-icon>
                    <span>点击删除</span>
                  </div>
                </div>
              </el-upload>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'timestamp_convert'" label="时间戳/日期">
              <el-input v-model="toolForm.timestamp" placeholder="请输入时间戳" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'timestamp_convert'" label="转换类型">
              <el-select v-model="toolForm.timestamp_convert_type" placeholder="请选择转换类型">
                <el-option label="时间戳转日期" value="to_datetime" />
                <el-option label="日期转时间戳" value="to_timestamp" />
                <el-option label="当前时间戳" value="current_timestamp" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'timestamp_convert' && toolForm.timestamp_convert_type === 'to_datetime'" label="时间戳单位">
              <el-select v-model="toolForm.timestamp_unit" placeholder="请选择时间戳单位">
                <el-option label="自动检测" value="auto" />
                <el-option label="秒" value="second" />
                <el-option label="毫秒" value="millisecond" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'base_convert'" label="数值">
              <el-input v-model="toolForm.number" placeholder="请输入数值" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'base_convert'" label="源进制">
              <el-input-number v-model="toolForm.from_base" :min="2" :max="36" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'base_convert'" label="目标进制">
              <el-input-number v-model="toolForm.to_base" :min="2" :max="36" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'unicode_convert'" label="文本">
              <el-input v-model="toolForm.text" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'unicode_convert'" label="转换类型">
              <el-select v-model="toolForm.unicode_convert_type" placeholder="请选择转换类型">
                <el-option label="中文转Unicode" value="to_unicode" />
                <el-option label="Unicode转中文" value="from_unicode" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'ascii_convert'" label="文本">
              <el-input v-model="toolForm.text" placeholder="请输入文本或ASCII码" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'ascii_convert'" label="转换类型">
              <el-select v-model="toolForm.convert_type" placeholder="请选择转换类型">
                <el-option label="字符转ASCII" value="to_ascii" />
                <el-option label="ASCII转字符" value="from_ascii" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'color_convert'" label="颜色值">
              <el-input v-model="toolForm.color" placeholder="请输入颜色值，如 #FF0000" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'color_convert'" label="源格式">
              <el-select v-model="toolForm.from_type" placeholder="请选择源格式">
                <el-option label="十六进制" value="hex" />
                <el-option label="RGB" value="rgb" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'color_convert'" label="目标格式">
              <el-select v-model="toolForm.to_type" placeholder="请选择目标格式">
                <el-option label="十六进制" value="hex" />
                <el-option label="RGB" value="rgb" />
                <el-option label="RGBA" value="rgba" />
                <el-option label="HSL" value="hsl" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="['base64_encode', 'base64_decode'].includes(currentTool.name)" label="文本">
              <el-input v-model="toolForm.text" type="textarea" :rows="4" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="['base64_encode', 'base64_decode'].includes(currentTool.name)" label="编码">
              <el-input v-model="toolForm.encoding" placeholder="utf-8" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'url_encode'" label="数据">
              <el-input v-model="toolForm.data" type="textarea" :rows="4" placeholder="请输入要编码的URL数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'url_encode'" label="编码方式">
              <el-select v-model="toolForm.plus" placeholder="请选择编码方式">
                <el-option label="标准编码" :value="false" />
                <el-option label="Plus编码" :value="true" />
              </el-select>
              <span class="form-tip">Plus编码会将空格转为+号</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'url_decode'" label="数据">
              <el-input v-model="toolForm.data" type="textarea" :rows="4" placeholder="请输入要解码的URL数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'url_decode'" label="解码方式">
              <el-select v-model="toolForm.plus" placeholder="请选择解码方式">
                <el-option label="标准解码" :value="false" />
                <el-option label="Plus解码" :value="true" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'jwt_decode'" label="JWT令牌">
              <el-input v-model="toolForm.token" type="textarea" :rows="6" placeholder="请输入JWT令牌" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'jwt_decode'" label="验证签名">
              <el-switch v-model="toolForm.verify" />
              <span class="form-tip">开启验证需要提供密钥</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'jwt_decode' && toolForm.verify" label="密钥">
              <el-input v-model="toolForm.secret" type="password" placeholder="请输入密钥" show-password />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'image_to_base64'" label="上传图片">
              <el-upload
                ref="uploadRef"
                class="image-upload"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
                accept="image/*"
              >
                <el-button type="primary">选择图片</el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 JPG、PNG、GIF、WebP 等格式，最大 10MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'image_to_base64' && imagePreview" label="图片预览">
              <div class="image-preview">
                <img :src="imagePreview" alt="预览" />
              </div>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'image_to_base64'" label="图片格式">
              <el-select v-model="toolForm.image_format" placeholder="选择图片格式">
                <el-option label="PNG" value="png" />
                <el-option label="JPEG" value="jpeg" />
                <el-option label="GIF" value="gif" />
                <el-option label="WebP" value="webp" />
                <el-option label="BMP" value="bmp" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'image_to_base64'" label="包含前缀">
              <el-switch v-model="toolForm.include_prefix" />
              <span class="form-tip">是否包含 data:image/png;base64, 前缀</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'base64_to_image'" label="Base64编码">
              <el-input v-model="toolForm.base64_str" type="textarea" :rows="10" placeholder="请输入Base64编码" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 加密工具 -->
        <div v-else-if="currentCategory === 'encryption'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item v-if="['md5_hash', 'sha1_hash', 'sha256_hash', 'sha512_hash', 'password_strength'].includes(currentTool.name)" label="文本">
              <el-input v-model="toolForm.text" type="textarea" :rows="4" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'hash_comparison'" label="文本">
              <el-input v-model="toolForm.text" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'hash_comparison'" label="哈希值">
              <el-input v-model="toolForm.hash_value" placeholder="请输入哈希值" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'hash_comparison'" label="算法">
              <el-select v-model="toolForm.algorithm" placeholder="请选择算法">
                <el-option label="MD5" value="md5" />
                <el-option label="SHA1" value="sha1" />
                <el-option label="SHA256" value="sha256" />
                <el-option label="SHA512" value="sha512" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="['aes_encrypt', 'aes_decrypt'].includes(currentTool.name)" label="文本">
              <el-input v-model="toolForm.text" type="textarea" :rows="4" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="['aes_encrypt', 'aes_decrypt'].includes(currentTool.name)" label="密码">
              <el-input v-model="toolForm.password" type="password" placeholder="请输入密码" />
            </el-form-item>
            <el-form-item v-if="['aes_encrypt', 'aes_decrypt'].includes(currentTool.name)" label="模式">
              <el-select v-model="toolForm.mode" placeholder="请选择模式">
                <el-option label="CBC" value="CBC" />
                <el-option label="ECB" value="ECB" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_salt'" label="长度">
              <el-input-number v-model="toolForm.length" :min="8" :max="64" />
            </el-form-item>
            <el-form-item v-if="['base64_encode', 'base64_decode'].includes(currentTool.name)" label="文本">
              <el-input v-model="toolForm.text" type="textarea" :rows="4" placeholder="请输入文本" />
            </el-form-item>
            <el-form-item v-if="['base64_encode', 'base64_decode'].includes(currentTool.name)" label="编码">
              <el-input v-model="toolForm.encoding" placeholder="utf-8" />
            </el-form-item>
          </el-form>
        </div>

        <!-- JSONPath查询工具 - 上下布局 -->
        <div v-else-if="currentCategory === 'json' && ['jsonpath_query'].includes(currentTool.name)" class="tool-form json-path-tool">
          <el-row :gutter="20">
            <el-col :span="24">
              <div class="path-input-panel">
                <h4>JSONPath表达式</h4>
                <el-input 
                  v-model="toolForm.jsonpath_expr" 
                  placeholder="例如: $.store.book[*].author" 
                  @input="handleJsonPathInput"
                />
                <div class="form-tip">
                  <a href="https://goessner.net/articles/JsonPath/" target="_blank">JSONPath语法参考</a>
                </div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="json-input-panel">
                <h4>JSON数据输入</h4>
                <el-input 
                  v-model="toolForm.json_str" 
                  type="textarea" 
                  :rows="15" 
                  placeholder="请输入JSON数据" 
                  @input="handleJsonPathInput"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="json-input-panel">
                <h4>查询结果</h4>
                <div v-if="toolResult" class="result-display">
                  <pre>{{ JSON.stringify(toolResult.result || toolResult, null, 2) }}</pre>
                </div>
                <div v-else class="result-empty">
                  <el-empty description="输入JSON数据和JSONPath表达式后，右侧将实时显示查询结果" :image-size="60" />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- JSON对比工具 - 左右分栏布局 -->
        <div v-else-if="currentCategory === 'json' && ['json_diff_enhanced'].includes(currentTool.name)" class="tool-form json-diff-tool">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="json-input-panel">
                <h4>JSON数据1</h4>
                <el-input 
                  v-model="toolForm.json_str1" 
                  type="textarea" 
                  :rows="15" 
                  placeholder="请输入第一个JSON数据" 
                  @input="handleJsonDiffInput"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="json-input-panel">
                <h4>JSON数据2</h4>
                <el-input 
                  v-model="toolForm.json_str2" 
                  type="textarea" 
                  :rows="15" 
                  placeholder="请输入第二个JSON数据" 
                  @input="handleJsonDiffInput"
                />
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="diff-options">
            <el-col :span="24">
              <el-form label-width="120px">
                <el-form-item label="忽略空格">
                  <el-switch v-model="toolForm.ignore_whitespace" @change="handleJsonDiffInput" />
                </el-form-item>
                <el-form-item label="仅显示差异">
                  <el-switch v-model="toolForm.show_only_diff" @change="handleJsonDiffInput" />
                </el-form-item>
              </el-form>
            </el-col>
          </el-row>
        </div>

        <!-- JSON格式化工具 - 左右分栏布局 -->
        <div v-else-if="currentCategory === 'json' && currentTool.name === 'format_json'" class="tool-form json-format-tool">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="json-input-panel">
                <div class="panel-header">
                  <h4>输入</h4>
                  <div class="input-stats">
                    <span>字符: {{ getInputStats().chars }}</span>
                    <span>行数: {{ getInputStats().lines }}</span>
                  </div>
                </div>
                <el-input 
                  v-model="toolForm.json_str" 
                  type="textarea" 
                  :rows="20" 
                  placeholder="请输入JSON数据"
                  @input="handleJsonInput"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="json-input-panel">
                <div class="panel-header">
                  <h4>输出</h4>
                  <!-- <div class="output-stats">
                    <span>字符: {{ getOutputStats().chars }}</span>
                    <span>行数: {{ getOutputStats().lines }}</span>
                  </div> -->
                </div>
                <div v-if="jsonTreeData" class="result-display json-tree-view">
                  <div class="json-tree-actions">
                    <el-button size="small" @click="expandAllJson">
                      <el-icon><Operation /></el-icon>
                      全部展开
                    </el-button>
                    <el-button size="small" @click="collapseAllJson">
                      <el-icon><Operation /></el-icon>
                      全部收缩
                    </el-button>
                  </div>
                  <el-tree
                    :data="[jsonTreeData]"
                    :props="{ label: 'label', children: 'children' }"
                    :expand-on-click-node="false"
                    :default-expand-all="false"
                    :default-expanded-keys="jsonExpandedKeys"
                    @node-expand="handleNodeExpand"
                    @node-collapse="handleNodeCollapse"
                    node-key="key"
                    class="json-tree"
                  >
                    <template #default="{ node, data }">
                      <span class="json-tree-node" :class="`json-type-${data.type}`">
                        <span class="json-node-label">{{ data.label }}</span>
                      </span>
                    </template>
                  </el-tree>
                </div>
                <div v-else-if="toolResult && toolResult.result" class="result-display">
                  <pre>{{ toolResult.result }}</pre>
                </div>
                <div v-else class="result-empty">
                  <el-empty description="输入JSON数据后，右侧将显示格式化结果" :image-size="60" />
                </div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" class="format-options">
            <el-col :span="24">
              <div class="options-bar">
                <div class="option-group">
                  <span class="option-label">缩进:</span>
                  <el-radio-group v-model="toolForm.indent" @change="handleJsonInput">
                    <el-radio-button :value="2">2空格</el-radio-button>
                    <el-radio-button :value="4">4空格</el-radio-button>
                  </el-radio-group>
                </div>
                <div class="option-group">
                  <el-switch v-model="toolForm.sort_keys" @change="handleJsonInput" />
                  <span class="option-label">排序键</span>
                </div>
                <div class="option-group">
                  <el-switch v-model="toolForm.compress" @change="handleJsonInput" />
                  <span class="option-label">压缩</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 其他JSON工具 -->
        <div v-else-if="currentCategory === 'json' && !['format_json', 'jsonpath_query', 'json_diff_enhanced'].includes(currentTool.name)" class="tool-form json-tool">
          <el-form label-width="120px">
            <el-form-item v-if="['format_json', 'validate_json', 'json_to_xml', 'json_to_yaml', 'json_to_csv', 'json_path_list', 'json_flatten'].includes(currentTool.name)" label="JSON数据">
              <el-input 
                v-model="toolForm.json_str" 
                type="textarea" 
                :rows="8" 
                placeholder="请输入JSON数据"
                @input="handleJsonInput"
              />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'format_json'" label="缩进">
              <el-input-number v-model="toolForm.indent" :min="0" :max="8" @change="handleJsonInput" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'format_json'" label="排序键">
              <el-switch v-model="toolForm.sort_keys" @change="handleJsonInput" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'format_json'" label="压缩">
              <el-switch v-model="toolForm.compress" @change="handleJsonInput" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'xml_to_json'" label="XML数据">
              <el-input v-model="toolForm.xml_str" type="textarea" :rows="8" placeholder="请输入XML数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'yaml_to_json'" label="YAML数据">
              <el-input v-model="toolForm.yaml_str" type="textarea" :rows="8" placeholder="请输入YAML数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'csv_to_json'" label="CSV数据">
              <el-input v-model="toolForm.csv_str" type="textarea" :rows="8" placeholder="请输入CSV数据" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'csv_to_json'" label="分隔符">
              <el-input v-model="toolForm.separator" placeholder="默认为逗号" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'csv_to_json'" label="包含表头">
              <el-switch v-model="toolForm.has_header" />
            </el-form-item>
          </el-form>
        </div>

        <!-- Mock数据工具 -->
        <div v-else-if="currentCategory === 'mock'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item label="生成数量">
              <el-input-number v-model="toolForm.count" :min="1" :max="100" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_string'" label="长度">
              <el-input-number v-model="toolForm.length" :min="1" :max="100" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_string'" label="字符类型">
              <el-select v-model="toolForm.char_type" placeholder="选择字符类型">
                <el-option label="全部" value="all" />
                <el-option label="字母" value="letters" />
                <el-option label="数字" value="digits" />
                <el-option label="字母数字" value="alphanumeric" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_number'" label="最小值">
              <el-input-number v-model="toolForm.min_val" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_number'" label="最大值">
              <el-input-number v-model="toolForm.max_val" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_number'" label="小数位数">
              <el-input-number v-model="toolForm.decimals" :min="0" :max="10" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_date'" label="开始日期">
              <el-date-picker v-model="toolForm.start_date" type="date" placeholder="选择开始日期" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_date'" label="结束日期">
              <el-date-picker v-model="toolForm.end_date" type="date" placeholder="选择结束日期" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_datetime'" label="开始日期">
              <el-date-picker v-model="toolForm.start_date" type="datetime" placeholder="选择开始日期时间" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'mock_datetime'" label="结束日期">
              <el-date-picker v-model="toolForm.end_date" type="datetime" placeholder="选择结束日期时间" />
            </el-form-item>
          </el-form>
        </div>

        <!-- Crontab工具 -->
        <div v-else-if="currentCategory === 'crontab'" class="tool-form">
          <el-form label-width="120px">
            <el-form-item v-if="currentTool.name === 'generate_expression'" label="分钟">
              <el-input v-model="toolForm.minute" placeholder="0-59, *, */5, 1,3,5, 1-10" />
              <span class="form-tip">范围: 0-59</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_expression'" label="小时">
              <el-input v-model="toolForm.hour" placeholder="0-23, *, */2, 9,18, 8-18" />
              <span class="form-tip">范围: 0-23</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_expression'" label="日">
              <el-input v-model="toolForm.day" placeholder="1-31, *, */7, 1,15, 1-10" />
              <span class="form-tip">范围: 1-31</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_expression'" label="月">
              <el-input v-model="toolForm.month" placeholder="1-12, *, */3, 1,4,7,10, 6-9" />
              <span class="form-tip">范围: 1-12</span>
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'generate_expression'" label="星期">
              <el-input v-model="toolForm.weekday" placeholder="0-6, *, */2, 1-5, 1,3,5" />
              <span class="form-tip">范围: 0-6 (0是周日)</span>
            </el-form-item>
            <el-form-item v-if="['parse_expression', 'get_next_runs', 'validate_expression'].includes(currentTool.name)" label="Crontab表达式">
              <el-input v-model="toolForm.expression" type="textarea" :rows="3" placeholder="例如: */5 * * * *" />
            </el-form-item>
            <el-form-item v-if="currentTool.name === 'get_next_runs'" label="执行次数">
              <el-input-number v-model="toolForm.count" :min="1" :max="20" />
            </el-form-item>
          </el-form>
        </div>

        <el-form label-width="120px" class="tool-options">
          <el-form-item label="保存结果">
            <el-switch v-model="toolForm.isSaved" />
            <span class="form-tip">保存后可在历史记录中查看</span>
          </el-form-item>
          <el-form-item label="标签">
            <el-input
              v-model="toolForm.tags"
              placeholder="输入标签，多个标签用逗号分隔"
            />
          </el-form-item>
        </el-form>

        <div v-if="toolResult && currentTool?.name !== 'jsonpath_query' && currentTool?.name !== 'format_json'" class="tool-result">
          <div class="result-header">
            <h4>执行结果</h4>
            <el-button 
              v-if="['json_to_xml', 'json_to_yaml', 'json_to_csv', 'xml_to_json', 'yaml_to_json', 'csv_to_json'].includes(currentTool?.name)"
              type="primary" 
              size="small"
              @click="downloadResult"
            >
              <el-icon><Download /></el-icon>
              下载结果
            </el-button>
          </div>
          <div v-if="['generate_barcode', 'generate_qrcode', 'base64_to_image'].includes(currentTool?.name)" class="image-result">
            <div class="image-preview">
              <img v-if="toolResult.url" :src="getImageUrl(toolResult.url)" :alt="currentTool.display_name" />
              <div v-else class="no-image">图片生成失败</div>
            </div>
            <div class="image-actions">
              <el-button type="primary" @click="downloadImage(toolResult)">
                <el-icon><Download /></el-icon>
                下载图片
              </el-button>
              <el-tag v-if="toolResult.filename" type="info">{{ toolResult.filename }}</el-tag>
            </div>
          </div>
          <el-input
            v-else-if="typeof toolResult === 'string'"
            v-model="toolResult"
            type="textarea"
            :rows="6"
            readonly
          />
          <pre v-else>{{ JSON.stringify(toolResult, null, 2) }}</pre>
        </div>
      </div>
      <template #footer>
        <el-button @click="toolDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="executing" @click="executeTool">
          执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 历史记录对话框 -->
    <el-dialog
      v-model="showHistory"
      title="使用历史"
      width="1200px"
    >
      <el-tabs v-model="historyTab">
        <el-tab-pane label="所有记录" name="all">
          <div class="history-content">
            <el-table :data="historyRecords" stripe class="history-table">
              <el-table-column label="工具名称" min-width="180">
                <template #default="{ row }">
                  <span>{{ getToolDisplayName(row.tool_name) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="tool_category_display" label="分类" min-width="120" />
              <el-table-column prop="tool_scenario_display" label="场景" min-width="120" />
              <el-table-column label="使用时间" min-width="180">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="danger" @click="deleteRecord(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-model:current-page="historyCurrentPage"
              v-model:page-size="historyPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="historyTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleHistorySizeChange"
              @current-change="handleHistoryPageChange"
              class="history-pagination"
            />
          </div>
        </el-tab-pane>
        <el-tab-pane label="统计信息" name="stats">
          <div class="stats-container">
            <el-row :gutter="20">
              <el-col :span="24">
                <el-card class="total-stats-card">
                  <div class="total-stats">
                    <div class="total-stat-item">
                      <div class="total-stat-value">{{ statistics.total_records || 0 }}</div>
                      <div class="total-stat-label">总记录数</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <span class="card-header-title">分类统计</span>
                  </template>
                  <div v-if="statistics.category_stats && Object.keys(statistics.category_stats).length > 0">
                    <div v-for="(count, category) in statistics.category_stats" :key="category" class="stat-item">
                      <div class="stat-item-content">
                        <span class="stat-label">{{ category }}</span>
                        <el-progress 
                          :percentage="calculatePercentage(count, statistics.total_records)" 
                          :stroke-width="12"
                          :show-text="false"
                        />
                        <span class="stat-count">{{ count }}</span>
                      </div>
                    </div>
                  </div>
                  <el-empty v-else description="暂无数据" :image-size="80" />
                </el-card>
              </el-col>
              <el-col :span="12">
                <el-card>
                  <template #header>
                    <span class="card-header-title">场景统计</span>
                  </template>
                  <div v-if="statistics.scenario_stats && Object.keys(statistics.scenario_stats).length > 0">
                    <div v-for="(count, scenario) in statistics.scenario_stats" :key="scenario" class="stat-item">
                      <div class="stat-item-content">
                        <span class="stat-label">{{ scenario }}</span>
                        <el-progress 
                          :percentage="calculatePercentage(count, statistics.total_records)" 
                          :stroke-width="12"
                          :show-text="false"
                        />
                        <span class="stat-count">{{ count }}</span>
                      </div>
                    </div>
                  </div>
                  <el-empty v-else description="暂无数据" :image-size="80" />
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataLine, Menu, Grid, Clock, Operation, ArrowRight,
  Document, List, Lock, User, MagicStick, VideoPlay, ChatDotSquare, Picture, Connection,
  Phone, Message, Location, Ticket, OfficeBuilding, CreditCard, CircleCheck, DocumentCopy, Search, Delete, Edit, Unlock, DataLine as DataLineIcon, Sort, Share, View, Upload
} from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

const viewMode = ref('category')
const categories = ref([])
const scenarios = ref([])
const currentScenario = ref(null)
const toolDialogVisible = ref(false)
const currentTool = ref(null)
const currentCategory = ref('')
const toolForm = ref({
  count: 1,
  text: '',
  isSaved: false,
  tags: '',
  gender: 'random',
  region: 'all',
  domain: 'random',
  full_address: true,
  company_type: 'all',
  old_str: '',
  new_str: '',
  is_regex: false,
  escape_type: 'json',
  unescape_type: 'json',
  pattern: '',
  flags: [],
  text1: '',
  text2: '',
  convert_type: 'to_ascii',
  format_type: 'trim',
  min_val: 1,
  max_val: 100,
  precision: 2,
  length: 8,
  char_type: 'all',
  version: 4,
  separator: ':',
  ip_version: 4,
  start_date: '2025-01-01',
  end_date: '2025-12-31',
  date_format: '%Y-%m-%d',
  format: 'hex',
  char_options: ['include_uppercase', 'include_lowercase', 'include_digits', 'include_special'],
  data: '',
  barcode_type: 'code128',
  timestamp: '',
  timestamp_convert_type: 'to_datetime',
  timestamp_unit: 'auto',
  number: '',
  from_base: 10,
  to_base: 16,
  from_type: 'hex',
  to_type: 'rgb',
  encoding: 'utf-8',
  unicode_convert_type: 'to_unicode',
  hash_value: '',
  algorithm: 'md5',
  password: '',
  mode: 'CBC',
  json_str: '',
  json_str1: '',
  json_str2: '',
  xml_str: '',
  yaml_str: '',
  csv_str: '',
  jsonpath_expr: '',
  root_tag: 'root',
  indent: 2,
  sort_keys: false,
  compress: false,
  ignore_whitespace: true,
  has_header: true,
  show_only_diff: false,
  array_length: 5,
  item_type: 'string',
  keys: '',
  value_type: 'string',
  plus: false,
  token: '',
  verify: false,
  secret: '',
  minute: '*',
  hour: '*',
  day: '*',
  month: '*',
  weekday: '*',
  expression: '',
  image_data: '',
  image_format: 'png',
  include_prefix: true,
  base64_str: ''
})
const toolResult = ref(null)
const imagePreview = ref('')
const qrCodeImage = ref('')
const uploadRef = ref(null)
const executing = ref(false)
const showHistory = ref(false)
const historyTab = ref('all')
const historyRecords = ref([])
const historyTotal = ref(0)
const historyCurrentPage = ref(1)
const historyPageSize = ref(10)
const statistics = ref({})
const jsonTreeData = ref(null)
const jsonExpandedKeys = ref([])
const jsonCollapseState = ref({})

const iconMap = {
  'document': Document,
  'code': List,
  'distribute': Grid,
  'lock': Lock,
  'user': User,
  'magic': MagicStick,
  'video': VideoPlay,
  'chat': ChatDotSquare,
  'clock': Clock,
  'picture': Picture,
  'phone': Phone,
  'message': Message,
  'location': Location,
  'ticket': Ticket,
  'office': OfficeBuilding,
  'credit-card': CreditCard,
  'circle-check': CircleCheck,
  'document-copy': DocumentCopy,
  'search': Search,
  'delete': Delete,
  'edit': Edit,
  'unlock': Unlock,
  'data-line': DataLineIcon,
  'sort': Sort,
  'share': Share,
  'view': View
}

const getIcon = (iconName) => {
  return iconMap[iconName] || Operation
}

const getScenarioIcon = (scenario) => {
  const iconMapping = {
    'test_data': User,
    'json': List,
    'string': Document,
    'encoding': Connection,
    'random': MagicStick,
    'encryption': Lock,
    'crontab': Clock
  }
  return iconMapping[scenario] || Operation
}

const fetchCategories = async () => {
  try {
    const response = await axios.get('/api/data-factory/categories/')
    categories.value = response.data.categories
  } catch (error) {
    ElMessage.error('获取工具分类失败')
  }
}

const fetchScenarios = async () => {
  try {
    const response = await axios.get('/api/data-factory/categories/')
    const scenarioMap = {}
    response.data.categories.forEach(category => {
      category.tools.forEach(tool => {
        const scenario = tool.scenario || 'other'
        if (!scenarioMap[scenario]) {
          scenarioMap[scenario] = {
            scenario: scenario,
            name: getScenarioName(scenario),
            description: getScenarioDesc(scenario),
            tool_count: 0
          }
        }
        scenarioMap[scenario].tool_count++
      })
    })
    scenarios.value = Object.values(scenarioMap)
  } catch (error) {
    ElMessage.error('获取场景列表失败')
  }
}

const getScenarioName = (scenario) => {
  const names = {
    'test_data': '测试数据',
    'json': 'JSON工具',
    'string': '字符工具',
    'encoding': '编码工具',
    'random': '随机工具',
    'encryption': '加密工具',
    'crontab': 'Crontab工具'
  }
  return names[scenario] || '其他'
}

const getScenarioDesc = (scenario) => {
  const descs = {
    'test_data': '生成各种类型的测试数据',
    'json': 'JSON数据的格式化、验证和转换',
    'string': '字符串的处理和转换',
    'encoding': '各种编码格式的转换',
    'random': '生成随机数据',
    'encryption': '加密和解密敏感数据',
    'crontab': '生成和解析Crontab命令'
  }
  return descs[scenario] || '其他工具'
}

const getToolDisplayName = (toolName) => {
  const toolNames = {
    'generate_chinese_name': '生成中文姓名',
    'generate_chinese_phone': '生成手机号',
    'generate_chinese_email': '生成邮箱',
    'generate_chinese_address': '生成地址',
    'generate_id_card': '生成身份证号',
    'generate_company_name': '生成公司名称',
    'generate_bank_card': '生成银行卡号',
    'generate_user_profile': '生成用户档案',
    'generate_hk_id_card': '生成香港身份证号',
    'generate_business_license': '生成营业执照号',
    'generate_coordinates': '生成经纬度',
    'remove_whitespace': '去除空格换行',
    'replace_string': '字符串替换',
    'escape_string': '字符串转义',
    'unescape_string': '字符串反转义',
    'word_count': '字数统计',
    'text_diff': '文本对比',
    'regex_test': '正则测试',
    'case_convert': '大小写转换',
    'string_format': '字符串格式化',
    'generate_barcode': '生成条形码',
    'generate_qrcode': '生成二维码',
    'decode_qrcode':'二维码解析',
    'timestamp_convert': '时间戳转换',
    'base_convert': '进制转换',
    'unicode_convert': 'Unicode转换',
    'ascii_convert': 'ASCII转换',
    'color_convert': '颜色值转换',
    'base64_encode': 'Base64编码',
    'base64_decode': 'Base64解码',
    'random_int': '随机整数',
    'random_float': '随机浮点数',
    'random_string': '随机字符串',
    'random_uuid': '随机UUID',
    'random_mac_address': '随机MAC地址',
    'random_ip_address': '随机IP地址',
    'random_date': '随机日期',
    'random_boolean': '随机布尔值',
    'random_color': '随机颜色',
    'random_password': '随机密码',
    'random_sequence': '随机序列',
    'md5_hash': 'MD5加密',
    'sha1_hash': 'SHA1加密',
    'sha256_hash': 'SHA256加密',
    'sha512_hash': 'SHA512加密',
    'hash_comparison': '哈希值比对',
    'aes_encrypt': 'AES加密',
    'aes_decrypt': 'AES解密',
    'password_strength': '密码强度分析',
    'generate_salt': '生成盐值',
    'format_json': 'JSON格式化',
    'validate_json': 'JSON校验',
    'json_to_xml': 'JSON转XML',
    'xml_to_json': 'XML转JSON',
    'json_to_yaml': 'JSON转YAML',
    'yaml_to_json': 'YAML转JSON',
    'json_diff': 'JSON对比',
    'jsonpath_query': 'JSONPath查询',
    'json_path_list': '列出JSON路径',
    'json_flatten': '扁平化JSON',
    'json_diff_enhanced': 'JSON增强对比',
    'mock_string': 'Mock字符串',
    'mock_number': 'Mock数字',
    'mock_boolean': 'Mock布尔值',
    'mock_email': 'Mock邮箱',
    'mock_phone': 'Mock手机号',
    'mock_date': 'Mock日期',
    'mock_datetime': 'Mock日期时间',
    'mock_name': 'Mock姓名',
    'mock_address': 'Mock地址',
    'mock_url': 'Mock URL',
    'mock_uuid': 'Mock UUID',
    'mock_ip': 'Mock IP地址',
    'generate_expression': '生成Crontab表达式',
    'parse_expression': '解析Crontab表达式',
    'get_next_runs': '获取下次执行时间',
    'validate_expression': '验证Crontab表达式',
    'image_to_base64': '图片转Base64',
    'base64_to_image': 'Base64转图片'
  }
  return toolNames[toolName] || toolName
}

const goToHome = () => {
  router.push('/')
}

const openTool = (tool, category) => {
  currentTool.value = tool
  currentCategory.value = category
  toolDialogVisible.value = true
  resetToolForm()
}

const buildInputData = () => {
  const toolName = currentTool.value.name
  const category = currentCategory.value
  const form = toolForm.value

  if (category === 'test_data') {
    const data = { count: form.count }
    if (toolName === 'generate_chinese_name') data.gender = form.gender
    if (toolName === 'generate_chinese_phone') data.region = form.region
    if (toolName === 'generate_chinese_email') data.domain = form.domain
    if (toolName === 'generate_chinese_address') data.full_address = form.full_address
    if (toolName === 'generate_company_name') data.company_type = form.company_type
    return data
  }

  if (category === 'string') {
    if (toolName === 'remove_whitespace') return { text: form.text }
    if (toolName === 'replace_string') return { text: form.text, old_str: form.old_str, new_str: form.new_str, is_regex: form.is_regex }
    if (toolName === 'escape_string') return { text: form.text, escape_type: form.escape_type }
    if (toolName === 'unescape_string') return { text: form.text, unescape_type: form.unescape_type }
    if (toolName === 'word_count') return { text: form.text }
    if (toolName === 'text_diff') return { text1: form.text1, text2: form.text2 }
    if (toolName === 'regex_test') return { pattern: form.pattern, text: form.text, flags: form.flags.join('') }
    if (toolName === 'case_convert') return { text: form.text, convert_type: form.convert_type }
    if (toolName === 'string_format') return { text: form.text, format_type: form.format_type }
  }

  if (category === 'random') {
    if (toolName === 'random_int') return { min_val: form.min_val, max_val: form.max_val, count: form.count }
    if (toolName === 'random_float') return { min_val: form.min_val, max_val: form.max_val, precision: form.precision, count: form.count }
    if (toolName === 'random_string') return { length: form.length, char_type: form.char_type, count: form.count }
    if (toolName === 'random_uuid') return { version: form.version, count: form.count }
    if (toolName === 'random_mac_address') return { separator: form.separator, count: form.count }
    if (toolName === 'random_ip_address') return { ip_version: form.ip_version, count: form.count }
    if (toolName === 'random_date') {
      const formatDate = (date) => {
        if (!date) return ''
        const d = new Date(date)
        const year = d.getFullYear()
        const month = String(d.getMonth() + 1).padStart(2, '0')
        const day = String(d.getDate()).padStart(2, '0')
        return `${year}-${month}-${day}`
      }
      return { start_date: formatDate(form.start_date), end_date: formatDate(form.end_date), count: form.count, date_format: form.date_format }
    }
    if (toolName === 'random_boolean') return { count: form.count }
    if (toolName === 'random_color') return { format: form.format, count: form.count }
    if (toolName === 'random_password') {
      return {
        length: form.length,
        include_uppercase: form.char_options.includes('include_uppercase'),
        include_lowercase: form.char_options.includes('include_lowercase'),
        include_digits: form.char_options.includes('include_digits'),
        include_special: form.char_options.includes('include_special'),
        count: form.count
      }
    }
    if (toolName === 'random_sequence') {
      const sequence = form.sequence ? form.sequence.split(',').map(s => s.trim()) : []
      return { sequence: sequence, count: form.count, unique: form.unique }
    }
  }

  if (category === 'encoding') {
    if (toolName === 'generate_barcode') return { data: form.data, barcode_type: form.barcode_type }
    if (toolName === 'generate_qrcode') return { data: form.data, image_size: form.image_size, border: 4 }
    if (toolName === 'decode_qrcode') return { image_data: form.image_data || '', image_format: 'png' }
    if (toolName === 'timestamp_convert') return { timestamp: form.timestamp, convert_type: form.timestamp_convert_type, timestamp_unit: form.timestamp_unit }
    if (toolName === 'base_convert') return { number: form.number, from_base: form.from_base, to_base: form.to_base }
    if (toolName === 'unicode_convert') return { text: form.text, convert_type: form.unicode_convert_type }
    if (toolName === 'ascii_convert') return { text: form.text, convert_type: form.convert_type }
    if (toolName === 'color_convert') return { color: form.color, from_type: form.from_type, to_type: form.to_type }
    if (toolName === 'url_encode') return { data: form.data, encoding: form.encoding, plus: form.plus }
    if (toolName === 'url_decode') return { data: form.data, encoding: form.encoding, plus: form.plus }
    if (toolName === 'jwt_decode') return { token: form.token, verify: form.verify, secret: form.secret }
    if (toolName === 'image_to_base64') return { image_data: form.image_data || '', image_format: form.image_format || 'png', include_prefix: form.include_prefix !== false }
    if (toolName === 'base64_to_image') return { base64_str: form.base64_str || '' }
    if (toolName === 'base64_encode') return { text: form.text, encoding: form.encoding }
    if (toolName === 'base64_decode') return { text: form.text, encoding: form.encoding }
  }

  if (category === 'encryption') {
    if (toolName === 'md5_hash') return { text: form.text }
    if (toolName === 'sha1_hash') return { text: form.text }
    if (toolName === 'sha256_hash') return { text: form.text }
    if (toolName === 'sha512_hash') return { text: form.text }
    if (toolName === 'hash_comparison') return { text: form.text, hash_value: form.hash_value, algorithm: form.algorithm }
    if (toolName === 'aes_encrypt') return { text: form.text, password: form.password, mode: form.mode }
    if (toolName === 'aes_decrypt') return { encrypted_text: form.text, password: form.password, mode: form.mode }
    if (toolName === 'password_strength') return { password: form.text }
    if (toolName === 'generate_salt') return { length: form.length }
  }

  if (category === 'json') {
    if (toolName === 'format_json') return { json_str: form.json_str, indent: form.indent, sort_keys: form.sort_keys, compress: form.compress }
    if (toolName === 'validate_json') return { json_str: form.json_str }
    if (toolName === 'json_to_xml') return { json_str: form.json_str, root_tag: form.root_tag || 'root' }
    if (toolName === 'xml_to_json') return { xml_str: form.xml_str }
    if (toolName === 'json_to_yaml') return { json_str: form.json_str }
    if (toolName === 'yaml_to_json') return { yaml_str: form.yaml_str }
    if (toolName === 'json_diff_enhanced') return { json_str1: form.json_str1, json_str2: form.json_str2, ignore_whitespace: form.ignore_whitespace, show_only_diff: form.show_only_diff }
    if (toolName === 'jsonpath_query') return { json_str: form.json_str, jsonpath_expr: form.jsonpath_expr }
    if (toolName === 'json_path_list') return { json_str: form.json_str }
    if (toolName === 'json_flatten') return { json_str: form.json_str, separator: form.separator || '.' }
  }

  if (category === 'crontab') {
    if (toolName === 'generate_expression') return { minute: form.minute || '*', hour: form.hour || '*', day: form.day || '*', month: form.month || '*', weekday: form.weekday || '*' }
    if (toolName === 'parse_expression') return { expression: form.expression || '' }
    if (toolName === 'get_next_runs') return { expression: form.expression || '', count: form.count || 10 }
    if (toolName === 'validate_expression') return { expression: form.expression || '' }
  }

  if (category === 'mock') {
    const data = { count: form.count }
    if (toolName === 'mock_string') {
      data.length = form.length
      data.char_type = form.char_type
    }
    if (toolName === 'mock_number') {
      data.min_val = form.min_val
      data.max_val = form.max_val
      data.decimals = form.decimals
    }
    if (toolName === 'mock_date' || toolName === 'mock_datetime') {
      data.start_date = form.start_date
      data.end_date = form.end_date
    }
    if (toolName === 'mock_array') {
      data.array_length = form.array_length
      data.item_type = form.item_type
    }
    if (toolName === 'mock_object') {
      data.keys = form.keys ? form.keys.split(',').map(k => k.trim()) : ['id', 'name', 'value']
      data.value_type = form.value_type
    }
    return data
  }

  return {}
}

const executeTool = async () => {
  if (!currentTool.value) return

  executing.value = true
  try {
    const input_data = buildInputData()
    const response = await axios.post('/api/data-factory/', {
      tool_name: currentTool.value.name,
      tool_category: currentCategory.value,
      tool_scenario: currentTool.value.scenario || 'other',
      input_data: input_data,
      is_saved: toolForm.value.isSaved,
      tags: toolForm.value.tags ? toolForm.value.tags.split(',') : []
    })

    toolResult.value = response.data
    ElMessage.success('执行成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '执行失败')
  } finally {
    executing.value = false
  }
}

const resetToolForm = () => {
  toolForm.value = {
    count: 1,
    text: '',
    isSaved: false,
    tags: '',
    gender: 'random',
    region: 'all',
    domain: 'random',
    full_address: true,
    company_type: 'all',
    old_str: '',
    new_str: '',
    is_regex: false,
    escape_type: 'json',
    unescape_type: 'json',
    pattern: '',
    flags: [],
    text1: '',
    text2: '',
    convert_type: 'to_ascii',
    format_type: 'trim',
    min_val: 1,
    max_val: 100,
    precision: 2,
    length: 8,
    char_type: 'all',
    image_size: 300,
    separator: ':',
    ip_version: 4,
    start_date: '2025-01-01',
    end_date: '2025-12-31',
    date_format: '%Y-%m-%d',
    format: 'hex',
    char_options: ['include_uppercase', 'include_lowercase', 'include_digits', 'include_special'],
    data: '',
    barcode_type: 'code128',
    timestamp: '',
    timestamp_convert_type: 'to_datetime',
    timestamp_unit: 'auto',
    number: '',
    from_base: 10,
    to_base: 16,
    from_type: 'hex',
    to_type: 'rgb',
    encoding: 'utf-8',
    unicode_convert_type: 'to_unicode',
    hash_value: '',
    algorithm: 'md5',
    password: '',
    mode: 'CBC',
    json_str: '',
    json_str1: '',
    json_str2: '',
    xml_str: '',
    yaml_str: '',
    csv_str: '',
    jsonpath_expr: '',
    root_tag: 'root',
    indent: 2,
    sort_keys: false,
    compress: false,
    ignore_whitespace: true,
    has_header: true,
    show_only_diff: false,
    array_length: 5,
    item_type: 'string',
    keys: '',
    value_type: 'string',
    minute: '*',
    hour: '*',
    day: '*',
    month: '*',
    weekday: '*',
    expression: '',
    image_data: '',
    image_format: 'png',
    include_prefix: true,
    base64_str: '',
    sequence: '',
    unique: false
  }
  toolResult.value = null
  imagePreview.value = ''
  jsonTreeData.value = null
  jsonExpandedKeys.value = []
  jsonCollapseState.value = {}
}

let debounceTimer = null
const handleJsonInput = async () => {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  debounceTimer = setTimeout(async () => {
    if (currentTool.value?.name === 'format_json' && toolForm.value.json_str) {
      try {
        const response = await axios.post('/api/data-factory/', {
          tool_name: 'format_json',
          tool_category: 'json',
          tool_scenario: 'data_validation',
          input_data: {
            json_str: toolForm.value.json_str,
            indent: toolForm.value.indent,
            sort_keys: toolForm.value.sort_keys,
            compress: toolForm.value.compress
          },
          is_saved: false
        })
        toolResult.value = response.data
        jsonTreeData.value = parseJsonToTree(response.data.result)
        saveJsonCollapseState()
      } catch (error) {
        toolResult.value = null
        jsonTreeData.value = null
      }
    }
  }, 300)
}

const parseJsonToTree = (jsonStr) => {
  try {
    const obj = JSON.parse(jsonStr)
    return convertObjectToTree(obj)
  } catch (e) {
    return null
  }
}

const convertObjectToTree = (obj, key = 'root', path = '') => {
  const currentPath = path ? `${path}.${key}` : key
  
  if (obj === null) {
    return {
      key: currentPath,
      label: `${key}: null`,
      value: null,
      type: 'null',
      children: []
    }
  }
  
  if (typeof obj === 'object') {
    const isArray = Array.isArray(obj)
    const children = Object.keys(obj).map(k => convertObjectToTree(obj[k], k, currentPath))
    
    return {
      key: currentPath,
      label: `${key}${isArray ? ` [${obj.length}]` : ''}`,
      value: isArray ? `Array(${obj.length})` : `Object{${Object.keys(obj).length}}`,
      type: isArray ? 'array' : 'object',
      children: children
    }
  }
  
  const type = typeof obj
  return {
    key: currentPath,
    label: `${key}: ${String(obj)}`,
    value: String(obj),
    type: type,
    children: []
  }
}

const expandAllJson = () => {
  const getAllKeys = (nodes) => {
    let keys = []
    nodes.forEach(node => {
      keys.push(node.key)
      if (node.children && node.children.length > 0) {
        keys = keys.concat(getAllKeys(node.children))
      }
    })
    return keys
  }
  
  if (jsonTreeData.value) {
    jsonExpandedKeys.value = getAllKeys([jsonTreeData.value])
    saveJsonCollapseState()
  }
}

const collapseAllJson = () => {
  jsonExpandedKeys.value = []
  saveJsonCollapseState()
}

const saveJsonCollapseState = () => {
  if (currentTool.value?.name === 'format_json') {
    const state = {
      expandedKeys: jsonExpandedKeys.value,
      timestamp: Date.now()
    }
    localStorage.setItem('json_format_collapse_state', JSON.stringify(state))
  }
}

const loadJsonCollapseState = () => {
  try {
    const state = localStorage.getItem('json_format_collapse_state')
    if (state) {
      const parsed = JSON.parse(state)
      jsonExpandedKeys.value = parsed.expandedKeys || []
    }
  } catch (e) {
    jsonExpandedKeys.value = []
  }
}

watch(() => currentTool.value, (newTool) => {
  if (newTool?.name === 'format_json') {
    loadJsonCollapseState()
  }
  if (newTool?.name !== 'decode_qrcode') {
    qrCodeImage.value = ''
    toolForm.value.image_data = ''
  }
})

const handleNodeExpand = (data, node) => {
  if (!jsonExpandedKeys.value.includes(data.key)) {
    jsonExpandedKeys.value.push(data.key)
    saveJsonCollapseState()
  }
}

const handleNodeCollapse = (data, node) => {
  const index = jsonExpandedKeys.value.indexOf(data.key)
  if (index > -1) {
    jsonExpandedKeys.value.splice(index, 1)
    saveJsonCollapseState()
  }
}

const handleQrCodeUpload = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64Data = e.target.result
      qrCodeImage.value = base64Data
      toolForm.value.image_data = base64Data
      resolve(false)
    }
    reader.onerror = () => {
      ElMessage.error('图片读取失败')
      reject(false)
    }
    reader.readAsDataURL(file)
  })
}

const clearQrCodeImage = () => {
  qrCodeImage.value = ''
  toolForm.value.image_data = ''
}

const getInputStats = () => {
  const text = toolForm.value.json_str || ''
  return {
    chars: text.length,
    lines: text.split('\n').length
  }
}

const getOutputStats = () => {
  if (!toolResult.value || !toolResult.value.result) {
    return { chars: 0, lines: 0 }
  }
  const text = toolResult.value.result
  return {
    chars: text.length,
    lines: text.split('\n').length
  }
}

const handleJsonDiffInput = async () => {
  if (currentTool.value?.name === 'json_diff_enhanced') {
    if (!toolForm.value.json_str1 || !toolForm.value.json_str2) {
      toolResult.value = null
      return
    }
    try {
      const response = await axios.post('/api/data-factory/', {
        tool_name: 'json_diff_enhanced',
        tool_category: 'json',
        tool_scenario: 'data_validation',
        input_data: {
          json_str1: toolForm.value.json_str1,
          json_str2: toolForm.value.json_str2,
          ignore_whitespace: toolForm.value.ignore_whitespace,
          show_only_diff: toolForm.value.show_only_diff
        },
        is_saved: false
      })
      toolResult.value = response.data
    } catch (error) {
      toolResult.value = null
    }
  }
}

const handleJsonPathInput = async () => {
  if (currentTool.value?.name === 'jsonpath_query' && toolForm.value.json_str && toolForm.value.jsonpath_expr) {
    try {
      const response = await axios.post('/api/data-factory/', {
        tool_name: 'jsonpath_query',
        tool_category: 'json',
        tool_scenario: 'data_validation',
        input_data: {
          json_str: toolForm.value.json_str,
          jsonpath_expr: toolForm.value.jsonpath_expr
        },
        is_saved: false
      })
      toolResult.value = response.data
    } catch (error) {
      toolResult.value = null
    }
  }
}

const handleImageChange = (file) => {
  if (file.raw.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过10MB')
    return false
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    imagePreview.value = e.target.result
  }
  reader.readAsDataURL(file.raw)

  const fileReader = new FileReader()
  fileReader.onload = (e) => {
    const result = e.target.result
    if (result.startsWith('data:image')) {
      toolForm.value.image_data = result.split(',')[1]
    } else {
      toolForm.value.image_data = result
    }
  }
  fileReader.readAsDataURL(file.raw)
}

const downloadResult = () => {
  if (!toolResult.value) return

  let content = ''
  let filename = ''
  let mimeType = 'text/plain'

  const toolName = currentTool.value?.name

  if (toolName === 'json_to_xml') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.xml`
    mimeType = 'application/xml'
  } else if (toolName === 'xml_to_json') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.json`
    mimeType = 'application/json'
  } else if (toolName === 'json_to_yaml') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.yaml`
    mimeType = 'text/yaml'
  } else if (toolName === 'yaml_to_json') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.json`
    mimeType = 'application/json'
  } else if (toolName === 'json_to_csv') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.csv`
    mimeType = 'text/csv;charset=utf-8'
    content = '\ufeff' + content
  } else if (toolName === 'csv_to_json') {
    content = toolResult.value.result || toolResult.value
    filename = `${toolName}_${Date.now()}.csv`
    mimeType = 'text/csv;charset=utf-8'
    content = '\ufeff' + content
  } else {
    content = typeof toolResult.value === 'string' ? toolResult.value : JSON.stringify(toolResult.value, null, 2)
    filename = `${toolName}_${Date.now()}.json`
    mimeType = 'application/json'
  }

  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const filterByScenario = (scenario) => {
  currentScenario.value = scenario
  viewMode.value = 'category'
  ElMessage.success(`已筛选: ${scenario.name}`)
}

const clearScenario = () => {
  currentScenario.value = null
}

const filteredCategories = () => {
  if (!currentScenario.value) return categories.value
  return categories.value.map(category => ({
    ...category,
    tools: category.tools.filter(tool => tool.scenario === currentScenario.value.scenario)
  })).filter(category => category.tools.length > 0)
}

const fetchHistory = async () => {
  try {
    const response = await axios.get('/api/data-factory/', {
      params: {
        page: historyCurrentPage.value,
        page_size: historyPageSize.value
      }
    })
    historyRecords.value = response.data.results
    historyTotal.value = response.data.count
  } catch (error) {
    ElMessage.error('获取历史记录失败')
  }
}

const handleHistoryPageChange = (page) => {
  historyCurrentPage.value = page
  fetchHistory()
}

const handleHistorySizeChange = (size) => {
  historyPageSize.value = size
  historyCurrentPage.value = 1
  fetchHistory()
}

const fetchStatistics = async () => {
  try {
    const response = await axios.get('/api/data-factory/statistics/')
    statistics.value = response.data
  } catch (error) {
    ElMessage.error('获取统计信息失败')
  }
}

const deleteRecord = async (record) => {
  try {
    await axios.delete(`/api/data-factory/${record.id}/`)
    ElMessage.success('删除成功')
    fetchHistory()
    fetchStatistics()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const calculatePercentage = (value, total) => {
  if (!total) return 0
  return Math.round((value / total) * 100)
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const getImageUrl = (url) => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return `/api/data-factory/download_static_file/?filename=${url.split('/').pop()}`
}

const downloadImage = (result) => {
  if (!result || !result.url) {
    ElMessage.error('图片URL不存在')
    return
  }
  
  const link = document.createElement('a')
  const filename = result.url.split('/').pop()
  const downloadUrl = `/api/data-factory/download_static_file/?filename=${filename}`
  link.href = downloadUrl
  link.download = result.filename || 'image.png'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('下载已开始')
}

watch(showHistory, (newVal) => {
  if (newVal) {
    fetchHistory()
    fetchStatistics()
  }
})

watch(historyTab, (newVal) => {
  if (newVal === 'stats') {
    fetchStatistics()
  }
})

onMounted(() => {
  fetchCategories()
  fetchScenarios()
})
</script>

<style scoped lang="scss">
.data-factory-container {
  padding: 20px;
  min-height: calc(100vh - 60px);
  background: #f5f7fa;
}

.header-card {
  margin-bottom: 20px;

  .header-content {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .page-title {
    font-size: 28px;
    font-weight: 600;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0;
    cursor: pointer;
    transition: color 0.3s;

    &:hover {
      color: #409eff;
    }

    .title-icon {
      font-size: 32px;
      color: #409eff;
    }
  }

  .page-subtitle {
    font-size: 16px;
    color: #7f8c8d;
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }
}

.category-view {
  display: flex;
  flex-direction: column;
  gap: 20px;

  .category-section {
    .category-card {
      .category-header {
        display: flex;
        align-items: center;
        gap: 10px;

        .category-icon {
          font-size: 24px;
        }

        .category-title {
          flex: 1;
          font-size: 18px;
          font-weight: 600;
        }
      }

      .tools-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 15px;
        margin-top: 15px;
      }

      .tool-item {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        gap: 12px;

        &:hover {
          background: #fff;
          border-color: #409eff;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
          transform: translateY(-2px);
        }

        .tool-icon {
          width: 40px;
          height: 40px;
          background: #e6f7ff;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #409eff;
          font-size: 20px;
        }

        .tool-info {
          flex: 1;

          .tool-name {
            font-size: 14px;
            font-weight: 600;
            margin: 0 0 5px 0;
            color: #2c3e50;
          }

          .tool-desc {
            font-size: 12px;
            color: #7f8c8d;
            margin: 0;
            line-height: 1.4;
          }
        }

        .tool-arrow {
          color: #c0c4cc;
          transition: transform 0.3s;
        }

        &:hover .tool-arrow {
          transform: translateX(5px);
          color: #409eff;
        }
      }
    }
  }
}

.scenario-view {
  .scenario-card {
    margin-bottom: 20px;
    cursor: pointer;
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      transform: translateY(-5px);
    }

    .scenario-content {
      text-align: center;
      padding: 20px;

      .scenario-icon {
        font-size: 48px;
        color: #409eff;
        margin-bottom: 15px;
      }

      .scenario-title {
        font-size: 18px;
        font-weight: 600;
        margin: 0 0 10px 0;
        color: #2c3e50;
      }

      .scenario-desc {
        font-size: 14px;
        color: #7f8c8d;
        margin: 0 0 15px 0;
        line-height: 1.5;
      }

      .scenario-stats {
        display: flex;
        justify-content: center;
      }
    }
  }
}

.tool-execution {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding-right: 10px;

  .tool-alert {
    margin-bottom: 20px;
  }

  .tool-form {
    margin-bottom: 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;

    .form-tip {
      margin-left: 10px;
      font-size: 12px;
      color: #909399;
    }
  }

  .tool-options {
    margin-bottom: 20px;

    .form-tip {
      margin-left: 10px;
      font-size: 12px;
      color: #909399;
    }
  }

  .tool-result {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;

    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }

    pre {
      margin: 0;
      padding: 10px;
      background: #fff;
      border-radius: 4px;
      overflow-x: auto;
      max-height: 400px;
      overflow-y: auto;
    }

    .image-result {
      display: flex;
      flex-direction: column;
      gap: 15px;

      .image-preview {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 20px;
        background: #fff;
        border-radius: 8px;
        border: 2px dashed #dcdfe6;
        min-height: 200px;

        img {
          max-width: 100%;
          max-height: 400px;
          border-radius: 4px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .no-image {
          color: #909399;
          font-size: 14px;
        }
      }

      .image-actions {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        padding: 10px;
        background: #fff;
        border-radius: 8px;
      }
    }
  }
}

.history-table {
  :deep(.el-table) {
    .el-table__cell {
      text-align: center;
    }
    
    .el-table__header-wrapper {
      .el-table__header {
        th {
          text-align: center;
          background-color: #f5f7fa;
        }
      }
    }
  }
}

.history-content {
  max-height: calc(100vh - 300px);
  display: flex;
  flex-direction: column;

  .history-table {
    flex: 1;
    overflow-y: auto;

    :deep(.el-table) {
      overflow: visible;
    }
  }

  .history-pagination {
    margin-top: 20px;
    display: flex;
    justify-content: center;
    padding: 10px 0;
    flex-shrink: 0;
  }
}

.stats-container {
  .total-stats-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    
    :deep(.el-card__body) {
      padding: 30px;
    }
    
    .total-stats {
      display: flex;
      justify-content: center;
      align-items: center;
      
      .total-stat-item {
        text-align: center;
        color: white;
        
        .total-stat-value {
          font-size: 48px;
          font-weight: 700;
          margin-bottom: 10px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .total-stat-label {
          font-size: 18px;
          opacity: 0.9;
        }
      }
    }
  }
  
  .card-header-title {
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
  }
  
  .stat-item {
    margin-bottom: 20px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .stat-item-content {
      display: flex;
      align-items: center;
      gap: 15px;

      .stat-label {
        width: 100px;
        font-size: 14px;
        color: #2c3e50;
        font-weight: 500;
        flex-shrink: 0;
      }

      .stat-count {
        width: 50px;
        text-align: right;
        font-size: 14px;
        color: #409eff;
        font-weight: 600;
        flex-shrink: 0;
      }
    }
  }
}

.json-path-tool {
  .path-input-panel {
    margin-bottom: 15px;
    
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .json-input-panel {
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
}

.json-format-tool {
  .json-input-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      padding: 10px;
      background: #f5f7fa;
      border-radius: 6px;
      
      h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #2c3e50;
      }
      
      .input-stats,
      .output-stats {
        display: flex;
        gap: 15px;
        font-size: 12px;
        color: #606266;
        
        span {
          padding: 2px 8px;
          background: #fff;
          border-radius: 4px;
          border: 1px solid #dcdfe6;
        }
      }
    }
    
    .result-display {
      flex: 1;
      overflow: auto;
      overflow-x: auto;
      padding: 10px;
      background: #f5f7fa;
      border-radius: 6px;
      border: 1px solid #dcdfe6;
      display: flex;
      flex-direction: column;
      min-width: 0;
      
      pre {
        margin: 0;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.5;
        color: #2c3e50;
        white-space: pre;
        word-wrap: normal;
        min-width: fit-content;
        overflow-x: auto;
      }
    }
    
    .result-empty {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 200px;
      background: #f5f7fa;
      border-radius: 6px;
      border: 1px solid #dcdfe6;
    }
  }
  
  .json-tree-view {
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    .json-tree-actions {
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e9ecef;
    }
    
    .json-tree {
      flex: 1;
      overflow: auto;
      overflow-x: auto;
      background: #fff;
      border-radius: 4px;
      padding: 10px;
      max-height: 280px;
      min-width: fit-content;
      
      :deep(.el-tree-node) {
        min-width: fit-content;
      }
      
      :deep(.el-tree-node__content) {
        padding: 4px 0;
        height: auto;
        min-width: fit-content;
      }
      
      :deep(.el-tree-node__label) {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        white-space: nowrap;
      }
    }
    
    .json-tree-node {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      
      .json-node-label {
        white-space: nowrap;
      }
      
      &.json-type-object {
        color: #e91e63;
      }
      
      &.json-type-array {
        color: #9c27b0;
      }
      
      &.json-type-string {
        color: #4caf50;
      }
      
      &.json-type-number {
        color: #2196f3;
      }
      
      &.json-type-boolean {
        color: #ff9800;
      }
      
      &.json-type-null {
        color: #9e9e9e;
      }
    }
  }
  
  .format-options {
    margin-top: 15px;
    padding: 15px;
    background: #f0f2f5;
    border-radius: 8px;
    
    .options-bar {
      display: flex;
      align-items: center;
      gap: 30px;
      flex-wrap: wrap;
      
      .option-group {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .option-label {
          font-size: 14px;
          color: #606266;
          font-weight: 500;
        }
      }
    }
  }
}

.json-diff-tool {
  .json-input-panel {
    margin-bottom: 15px;
    
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .diff-options {
    margin-top: 15px;
    padding: 15px;
    background: #f0f2f5;
    border-radius: 8px;
  }
}

.image-upload {
  width: 100%;
  
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d9d9d9;
    border-radius: 8px;
    background: #fafafa;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409eff;
      background: #f0f9ff;
    }
  }
  
  .el-upload__tip {
    margin-top: 10px;
    color: #909399;
    font-size: 12px;
  }
}

.qr-code-upload {
  width: 100%;
  
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 200px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d9d9d9;
    border-radius: 8px;
    background: #fafafa;
    transition: all 0.3s;
    
    &:hover {
      border-color: #409eff;
      background: #f0f9ff;
    }
  }
  
  .upload-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    
    .upload-icon {
      font-size: 48px;
      color: #c0c4cc;
    }
    
    .upload-text {
      font-size: 14px;
      color: #606266;
      font-weight: 500;
    }
    
    .upload-tip {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .upload-preview {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    
    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    
    .upload-mask {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: #fff;
      opacity: 0;
      transition: opacity 0.3s;
      cursor: pointer;
      
      &:hover {
        opacity: 1;
      }
      
      .el-icon {
        font-size: 24px;
      }
      
      span {
        font-size: 14px;
      }
    }
  }
}

.image-preview {
  width: 100%;
  max-width: 400px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 10px;
  
  img {
    width: 100%;
    height: auto;
    display: block;
  }
}

.json-path-tool {
  .path-input-panel {
    margin-bottom: 15px;
    
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .json-input-panel {
    margin-bottom: 15px;
    
    h4 {
      margin: 0 0 10px 0;
      font-size: 14px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .result-display {
    height: 100%;
    min-height: 300px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    overflow: auto;
    overflow-x: auto;
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    pre {
      margin: 0;
      padding: 10px;
      background: #fff;
      border-radius: 4px;
      max-height: 280px;
      font-size: 13px;
      line-height: 1.4;
      white-space: pre;
      word-wrap: normal;
      min-width: fit-content;
      overflow-x: auto;
    }
  }
  
  .result-empty {
    height: 100%;
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .json-tree-view {
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    .json-tree-actions {
      display: flex;
      gap: 10px;
      margin-bottom: 10px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e9ecef;
    }
    
    .json-tree {
      flex: 1;
      overflow: auto;
      overflow-x: auto;
      background: #fff;
      border-radius: 4px;
      padding: 10px;
      max-height: 280px;
      min-width: fit-content;
      
      :deep(.el-tree-node) {
        min-width: fit-content;
      }
      
      :deep(.el-tree-node__content) {
        padding: 4px 0;
        height: auto;
        min-width: fit-content;
      }
      
      :deep(.el-tree-node__label) {
        font-family: 'Courier New', monospace;
        font-size: 13px;
        white-space: nowrap;
      }
    }
    
    .json-tree-node {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      
      .json-node-label {
        white-space: nowrap;
      }
      
      &.json-type-object {
        color: #e91e63;
      }
      
      &.json-type-array {
        color: #9c27b0;
      }
      
      &.json-type-string {
        color: #4caf50;
      }
      
      &.json-type-number {
        color: #2196f3;
      }
      
      &.json-type-boolean {
        color: #ff9800;
      }
      
      &.json-type-null {
        color: #9e9e9e;
      }
    }
  }
}
</style>
