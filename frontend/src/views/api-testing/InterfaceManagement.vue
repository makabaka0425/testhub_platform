<template>
	<div class="interface-management">
		<div class="interface-layout">
			<!-- 左侧集合树 -->
			<div class="sidebar">
				<div class="sidebar-header">
					<el-select v-model="selectedProject" :placeholder="$t('apiTesting.common.selectProject')"
						@change="onProjectChange" style="width: 100%;">
						<el-option v-for="project in projects" :key="project.id" :label="project.name"
							:value="project.id" />
					</el-select>
					<div class="header-actions">
						<el-input v-model="searchKeyword" placeholder="搜索接口..." size="small" clearable
							@input="onSearchDebounced" @keyup.enter="onSearch(searchKeyword)"
							style="flex: 1; min-width: 0;">
							<template #prefix>
								<el-icon>
									<Search />
								</el-icon>
							</template>
						</el-input>
						<el-button type="primary" size="small" @click="showCreateCollectionDialog = true"
							:title="$t('apiTesting.interface.createCollection')">
							<el-icon>
								<Folder />
							</el-icon>
						</el-button>
						<el-button type="success" size="small" @click="createEmptyRequest"
							:title="$t('apiTesting.interface.addInterface')">
							<el-icon>
								<Plus />
							</el-icon>
						</el-button>
					</div>
				</div>

				<div class="collection-tree" v-show="!searchKeyword || searchKeyword.trim() === ''">
					<el-tree ref="treeRef" :data="collections" :props="treeProps" node-key="id"
						:expand-on-click-node="false" :default-expanded-keys="expandedKeys" @node-click="onNodeClick"
						@node-contextmenu="onNodeRightClick" @node-expand="onNodeExpand"
						@node-collapse="onNodeCollapse">
						<template #default="{ node, data }">
							<div class="tree-node">
								<el-icon v-if="data.type === 'collection'">
									<Folder />
								</el-icon>
								<el-icon v-else>
									<Document />
								</el-icon>

								<!-- 集合名称编辑 -->
								<div v-if="data.type === 'collection' && editingNodeId === data.id" class="node-edit">
									<el-input v-model="editingNodeName" size="small" @blur="saveCollectionName"
										@keyup.enter="saveCollectionName" @keyup.esc="cancelEdit" ref="editInputRef" />
								</div>

								<!-- 普通显示模式 -->
								<span v-else class="node-label">{{ node.label }}</span>

								<span v-if="data.type === 'request' && data.request_type !== 'WEBSOCKET'"
									class="method-tag" :class="data.method?.toLowerCase()">
									{{ data.method }}
								</span>
							</div>
						</template>
					</el-tree>

					<!-- 搜索结果 -->
					<div v-if="filteredCollections.length > 0" class="search-results">
						<div class="search-results-header">
							<span>搜索结果 ({{ filteredCollections.length }})</span>
							<el-button size="small" text @click="searchKeyword = ''; filteredCollections = []">
								<el-icon>
									<Close />
								</el-icon>
							</el-button>
						</div>
						<div class="search-results-list">
							<div v-for="item in filteredCollections" :key="item.id" class="search-result-item"
								@click="selectSearchResult(item)">
								<el-icon>
									<Document />
								</el-icon>
								<div class="search-result-content">
									<div class="search-result-name">{{ item.name }}</div>
									<div class="search-result-url">{{ item.url }}</div>
								</div>
								<el-tag v-if="item.matchType === 'name'" type="primary" size="small">名称</el-tag>
								<el-tag v-else-if="item.matchType === 'method'" type="warning" size="small">方法</el-tag>
								<el-tag v-else type="success" size="small">URL</el-tag>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- 右侧请求详情 -->
			<div class="main-content">
				<div v-if="!selectedRequest" class="empty-state">
					<el-empty :description="$t('apiTesting.interface.selectInterface')">
						<el-button type="primary"
							@click="createEmptyRequest">{{ $t('apiTesting.interface.createNewInterface') }}</el-button>
					</el-empty>
				</div>

				<div v-else class="request-detail">
					<!-- 请求基本信息 -->
					<div class="request-header">
						<div class="request-line">
							<!-- HTTP接口显示方法选择器 -->
							<el-select v-if="!selectedRequest || selectedRequest.request_type !== 'WEBSOCKET'"
								v-model="selectedRequest.method" class="method-select">
								<el-option v-for="method in availableMethods" :key="method" :label="method"
									:value="method" />
							</el-select>

							<el-input v-model="selectedRequest.url"
								:placeholder="$t('apiTesting.interface.inputRequestUrl')" class="url-input"
								:class="{ 'websocket-url': selectedRequest && selectedRequest.request_type === 'WEBSOCKET' }">
								<template #prepend>
									<el-select v-model="selectedEnvironment" placeholder="环境" class="env-select">
										<el-option label="无环境" :value="null" />
										<el-option v-for="env in environments" :key="env.id" :label="env.name"
											:value="env.id" />
									</el-select>
								</template>
							</el-input>

							<!-- WebSocket连接按钮 -->
							<el-button v-if="selectedRequest && selectedRequest.request_type === 'WEBSOCKET'"
								:type="websocketConnectionStatus === 'disconnected' ? 'primary' : 'info'"
								:loading="websocketConnectionStatus === 'connecting'" @click="toggleWebSocketConnection"
								class="send-button">
								<span
									v-if="websocketConnectionStatus === 'disconnected'">{{ $t('apiTesting.interface.connect') }}</span>
								<span
									v-else-if="websocketConnectionStatus === 'connecting'">{{ $t('apiTesting.interface.connecting') }}</span>
								<span v-else>{{ $t('apiTesting.interface.disconnect') }}</span>
							</el-button>

							<!-- HTTP发送按钮 -->
							<el-button v-else type="primary" @click="sendRequest" :loading="sending"
								class="send-button">
								{{ $t('apiTesting.interface.send') }}
							</el-button>
						</div>

						<div class="request-meta">
							<el-input v-model="selectedRequest.name"
								:placeholder="$t('apiTesting.interface.requestName')" size="small" class="name-input" />
							<div class="action-buttons">
								<el-button size="small" @click="saveRequest" :loading="saving" ref="saveButtonRef">
									保存
								</el-button>
								<el-dropdown split-button type="default" size="small" @click="importCurl">
									导入
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item @click="importCurl">导入CURL</el-dropdown-item>
											<el-dropdown-item @click="exportRequest">导出为CURL</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
								<el-dropdown split-button type="default" size="small"
									@click="generateCode('javascript')">
									生成代码
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item
												@click="generateCode('javascript')">JavaScript</el-dropdown-item>
											<el-dropdown-item @click="generateCode('python')">Python</el-dropdown-item>
											<el-dropdown-item @click="generateCode('java')">Java</el-dropdown-item>
											<el-dropdown-item @click="generateCode('curl')">cURL</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
							</div>
						</div>
					</div>

					<!-- 请求配置 -->
					<el-tabs v-model="activeTab" class="request-tabs">
						<el-tab-pane label="Params" name="params">
							<KeyValueEditor v-model="selectedRequest.params"
								:placeholder-key="$t('apiTesting.interface.paramName')"
								:placeholder-value="$t('apiTesting.interface.paramValue')" />
						</el-tab-pane>

						<el-tab-pane label="Headers" name="headers">
							<KeyValueEditor ref="headersEditorRef" v-model="selectedRequest.headers"
								:placeholder-key="$t('apiTesting.interface.headerName')"
								:placeholder-value="$t('apiTesting.interface.headerValue')"
								@update:modelValue="onHeadersUpdate" />
						</el-tab-pane>

						<el-tab-pane label="Body" name="body" v-if="hasBody">
							<div class="body-container">
								<el-radio-group v-model="bodyType" @change="onBodyTypeChange">
									<el-radio value="none">none</el-radio>
									<el-radio value="form-data">form-data</el-radio>
									<el-radio value="x-www-form-urlencoded">x-www-form-urlencoded</el-radio>
									<el-radio value="raw">raw</el-radio>
									<el-radio value="binary">binary</el-radio>
								</el-radio-group>

								<div v-if="bodyType === 'form-data'" class="body-content">
									<KeyValueEditor v-model="formData" :placeholder-key="$t('apiTesting.interface.key')"
										:placeholder-value="$t('apiTesting.interface.value')" :show-file="true" />
								</div>

								<div v-else-if="bodyType === 'x-www-form-urlencoded'" class="body-content">
									<KeyValueEditor v-model="formUrlEncoded"
										:placeholder-key="$t('apiTesting.interface.key')"
										:placeholder-value="$t('apiTesting.interface.value')" />
								</div>

								<div v-else-if="bodyType === 'raw'" class="body-content">
									<div class="raw-options">
										<el-select v-model="rawType" style="width: 150px;">
											<el-option label="Text" value="text" />
											<el-option label="JSON" value="json" />
											<el-option label="HTML" value="html" />
											<el-option label="XML" value="xml" />
										</el-select>

										<el-button size="small" :icon="MagicStick"
											@click="openDataFactorySelectorForBody('rawBody')" title="引用数据工厂"
											class="data-factory-btn">
											引用数据工厂
										</el-button>
										<el-button size="small" :icon="MagicStick"
											@click="openVariableHelper('rawBody')" title="变量助手"
											class="variable-helper-btn">
											变量助手
										</el-button>
									</div>
									<el-input v-model="rawBody" type="textarea" :rows="10"
										:placeholder="$t('apiTesting.interface.inputRequestBody')" class="raw-body" />
								</div>
							</div>
						</el-tab-pane>

						<!-- HTTP接口专用标签页 -->
						<template v-if="!selectedRequest || selectedRequest.request_type !== 'WEBSOCKET'">
							<el-tab-pane label="Pre-request Script" name="pre-script">
								<div class="script-editor-container">
									<el-input v-model="selectedRequest.pre_request_script" type="textarea" :rows="10"
										placeholder="// 请求前脚本，使用JavaScript语法" />
									<div class="script-buttons">
										<el-button size="small" :icon="MagicStick"
											@click="openDataFactorySelectorForScript('pre_request_script')"
											title="引用数据工厂" class="script-factory-btn">
											引用数据工厂
										</el-button>
										<el-button size="small" :icon="MagicStick"
											@click="openVariableHelper('pre_request_script')" title="变量助手"
											class="script-variable-btn">
											变量助手
										</el-button>
									</div>
								</div>
							</el-tab-pane>

							<el-tab-pane label="Tests" name="tests">
								<div class="script-editor-container">
									<el-input v-model="selectedRequest.post_request_script" type="textarea" :rows="10"
										placeholder="// 请求后脚本和测试，使用JavaScript语法" />
									<div class="script-buttons">
										<el-button size="small" :icon="MagicStick"
											@click="openDataFactorySelectorForScript('post_request_script')"
											title="引用数据工厂" class="script-factory-btn">
											引用数据工厂
										</el-button>
										<el-button size="small" :icon="MagicStick"
											@click="openVariableHelper('post_request_script')" title="变量助手"
											class="script-variable-btn">
											变量助手
										</el-button>
									</div>
								</div>
							</el-tab-pane>

							<el-tab-pane :label="$t('apiTesting.interface.assertions')" name="assertions">
								<div class="assertions-editor">
									<div class="assertions-header">
										<el-button size="small" type="primary" @click="addAssertion">
											<el-icon>
												<Plus />
											</el-icon>
											{{ $t('apiTesting.interface.addAssertion') }}
										</el-button>
									</div>

									<div class="assertions-list">
										<div v-for="(assertion, index) in selectedRequest.assertions" :key="index"
											class="assertion-item">
											<div class="assertion-header">
												<el-input v-model="assertion.name"
													:placeholder="$t('apiTesting.interface.assertionName')" size="small"
													class="assertion-name" />
												<el-button size="small" type="danger" @click="removeAssertion(index)"
													circle>
													<el-icon>
														<Delete />
													</el-icon>
												</el-button>
											</div>

											<div class="assertion-config">
												<el-select v-model="assertion.type"
													:placeholder="$t('apiTesting.interface.selectAssertionType')"
													size="small" @change="onAssertionTypeChange(assertion)">
													<el-option
														:label="$t('apiTesting.interface.assertionTypes.statusCode')"
														value="status_code" />
													<el-option
														:label="$t('apiTesting.interface.assertionTypes.responseTime')"
														value="response_time" />
													<el-option
														:label="$t('apiTesting.interface.assertionTypes.contains')"
														value="contains" />
													<el-option
														:label="$t('apiTesting.interface.assertionTypes.jsonPath')"
														value="json_path" />
													<el-option :label="$t('apiTesting.interface.assertionTypes.header')"
														value="header" />
													<el-option :label="$t('apiTesting.interface.assertionTypes.equals')"
														value="equals" />
												</el-select>

												<div class="assertion-params" v-if="assertion.type">
													<!-- 状态码断言 -->
													<div v-if="assertion.type === 'status_code'">
														<el-input-number v-model="assertion.expected" :min="100"
															:max="599" size="small"
															:placeholder="$t('apiTesting.interface.expectedStatusCode')" />
													</div>

													<!-- 响应时间断言 -->
													<div v-else-if="assertion.type === 'response_time'">
														<el-input-number v-model="assertion.expected" :min="1"
															size="small"
															:placeholder="$t('apiTesting.interface.maxResponseTime')" />
													</div>

													<!-- 包含文本断言 -->
													<div v-else-if="assertion.type === 'contains'">
														<div style="display: flex; align-items: center; width: 100%">
															<el-input v-model="assertion.expected" placeholder="期望包含的文本"
																size="small" style="flex: 1">
																<template #append>
																	<el-button size="small" :icon="MagicStick"
																		@click="openDataFactorySelector(assertion, 'expected', index)"
																		title="引用数据工厂" class="data-factory-btn" />
																</template>
															</el-input>
															<el-tooltip content="插入动态变量" placement="top">
																<el-button size="small" style="margin-left: 5px"
																	@click="openVariableHelperForAssertion(assertion, 'expected', index)"
																	class="variable-helper-btn">
																	<el-icon>
																		<MagicStick />
																	</el-icon>
																</el-button>
															</el-tooltip>
														</div>
													</div>

													<!-- JSON路径断言 -->
													<div v-else-if="assertion.type === 'json_path'">
														<el-input v-model="assertion.json_path"
															:placeholder="$t('apiTesting.interface.jsonPathExpression')"
															size="small" class="assertion-input" />
														<div style="display: flex; align-items: center; width: 100%">
															<el-input v-model="assertion.expected" placeholder="期望值"
																size="small" style="flex: 1">
																<template #append>
																	<el-button size="small" :icon="MagicStick"
																		@click="openDataFactorySelector(assertion, 'expected', index)"
																		title="引用数据工厂" class="data-factory-btn" />
																</template>
															</el-input>
															<el-tooltip content="插入动态变量" placement="top">
																<el-button size="small" style="margin-left: 5px"
																	@click="openVariableHelperForAssertion(assertion, 'expected', index)"
																	class="variable-helper-btn">
																	<el-icon>
																		<MagicStick />
																	</el-icon>
																</el-button>
															</el-tooltip>
														</div>
													</div>

													<!-- 响应头断言 -->
													<div v-else-if="assertion.type === 'header'">
														<el-input v-model="assertion.header_name"
															:placeholder="$t('apiTesting.interface.headerNameLabel')"
															size="small" class="assertion-input" />
														<div style="display: flex; align-items: center; width: 100%">
															<el-input v-model="assertion.expected_value"
																placeholder="期望值" size="small" style="flex: 1">
																<template #append>
																	<el-button size="small" :icon="MagicStick"
																		@click="openDataFactorySelector(assertion, 'expected_value', index)"
																		title="引用数据工厂" class="data-factory-btn" />
																</template>
															</el-input>
															<el-tooltip content="插入动态变量" placement="top">
																<el-button size="small" style="margin-left: 5px"
																	@click="openVariableHelperForAssertion(assertion, 'expected_value', index)"
																	class="variable-helper-btn">
																	<el-icon>
																		<MagicStick />
																	</el-icon>
																</el-button>
															</el-tooltip>
														</div>
													</div>

													<!-- 完全匹配断言 -->
													<div v-else-if="assertion.type === 'equals'">
														<div style="display: flex; align-items: center; width: 100%">
															<el-input v-model="assertion.expected"
																placeholder="期望完全匹配的文本" size="small" style="flex: 1">
																<template #append>
																	<el-button size="small" :icon="MagicStick"
																		@click="openDataFactorySelector(assertion, 'expected', index)"
																		title="引用数据工厂" class="data-factory-btn" />
																</template>
															</el-input>
															<el-tooltip content="插入动态变量" placement="top">
																<el-button size="small" style="margin-left: 5px"
																	@click="openVariableHelperForAssertion(assertion, 'expected', index)"
																	class="variable-helper-btn">
																	<el-icon>
																		<MagicStick />
																	</el-icon>
																</el-button>
															</el-tooltip>
														</div>
													</div>
												</div>
											</div>
										</div>

										<div v-if="!selectedRequest.assertions || selectedRequest.assertions.length === 0"
											class="no-assertions">
											<p>{{ $t('apiTesting.interface.noAssertions') }}</p>
											<el-button size="small" type="primary" @click="addAssertion">
												<el-icon>
													<Plus />
												</el-icon>
												{{ $t('apiTesting.interface.addFirstAssertion') }}
											</el-button>
										</div>
									</div>
								</div>
							</el-tab-pane>
						</template>

						<!-- WebSocket接口专用标签页 -->
						<template v-else-if="selectedRequest && selectedRequest.request_type === 'WEBSOCKET'">
							<el-tab-pane label="Message" name="message">
								<div class="message-container">
									<div class="message-input-section">
										<el-select v-model="websocketMessageType"
											:placeholder="$t('apiTesting.interface.messageType')"
											style="width: 150px; margin-bottom: 15px;">
											<el-option label="Text" value="text" />
											<el-option label="JSON" value="json" />
											<el-option label="Binary" value="binary" />
										</el-select>

										<div v-if="websocketMessageType === 'text' || websocketMessageType === 'json'">
											<el-input v-model="websocketMessageContent" type="textarea" :rows="6"
												:placeholder="$t('apiTesting.interface.inputWebSocketMessage')" />
										</div>

										<div v-else-if="websocketMessageType === 'binary'">
											<el-upload drag action="#" :auto-upload="false" :show-file-list="false"
												:on-change="handleWebSocketFileUpload">
												<el-icon class="el-icon--upload"><upload-filled /></el-icon>
												<div class="el-upload__text">
													{{ $t('apiTesting.interface.dragBinaryFile') }}<em>{{ $t('apiTesting.interface.clickUpload') }}</em>
												</div>
											</el-upload>
											<div v-if="websocketBinaryFile" class="uploaded-file">
												<span>{{ websocketBinaryFile.name }}</span>
												<el-button size="small" type="danger"
													@click="clearWebSocketBinaryFile">{{ $t('apiTesting.interface.clear') }}</el-button>
											</div>
										</div>

										<div class="message-actions" style="margin-top: 15px;">
											<el-button type="primary" @click="sendWebSocketMessage">
												{{ $t('apiTesting.interface.sendMessage') }}
											</el-button>
											<el-button @click="clearWebSocketMessage">
												{{ $t('apiTesting.interface.clearMessage') }}
											</el-button>
										</div>
									</div>

									<!-- WebSocket消息历史记录 -->
									<div class="websocket-response-section" v-if="websocketMessages.length > 0">
										<h3>{{ $t('apiTesting.interface.messageHistory') }}</h3>
										<div class="websocket-messages">
											<div v-for="(msg, index) in websocketMessages.slice().reverse()"
												:key="index" class="websocket-message-item" :class="msg.type">
												<div class="message-header">
													<span class="message-type" :class="msg.type">
														{{ msg.type === 'sent' ? $t('apiTesting.interface.messageSent') :
                               msg.type === 'connected' ? $t('apiTesting.interface.messageConnected') :
                               msg.type === 'info' ? $t('apiTesting.interface.messageInfo') :
                               msg.type === 'error' ? $t('apiTesting.interface.messageError') : $t('apiTesting.interface.messageReceived') }}
													</span>
													<span class="message-time">{{ msg.timestamp }}</span>
												</div>
												<div class="message-content">
													<pre
														v-if="msg.type === 'received' && isJsonString(msg.content)">{{ formatJson(msg.content) }}
													</pre>
													<pre v-else>{{ msg.content }}</pre>
												</div>
											</div>
										</div>
										<div class="message-actions">
											<el-button size="small"
												@click="clearWebSocketMessages">{{ $t('apiTesting.interface.clearHistory') }}</el-button>
										</div>
									</div>
								</div>
							</el-tab-pane>
						</template>
					</el-tabs>

					<!-- 响应区域 -->
					<div v-if="response" class="response-section">
						<div class="response-header">
							<h3>{{ $t('apiTesting.interface.response') }}</h3>
							<div class="response-info">
								<el-tag :type="getStatusType(response.status_code)">
									{{ response.status_code }}
								</el-tag>
								<span class="response-time">{{ response.response_time?.toFixed(0) }}ms</span>
							</div>
						</div>

						<el-tabs v-model="responseActiveTab">
							<el-tab-pane :label="$t('apiTesting.interface.responseBody')" name="body">
								<div class="response-body">
									<div class="response-actions">
										<el-button-group>
											<el-button size="small" @click="formatResponse">格式化</el-button>
											<el-button size="small" @click="copyResponse">复制</el-button>
											<el-button size="small"
												@click="showJsonPathExtractor = !showJsonPathExtractor">
												JSONPath提取
											</el-button>
										</el-button-group>
									</div>
									<div v-if="showJsonPathExtractor" class="jsonpath-extractor">
										<div class="jsonpath-input">
											<el-input v-model="jsonPathExpression"
												placeholder="输入JSONPath表达式，例如：$.data.users[0].name" size="small"
												@input="evaluateJsonPath">
												<template #append>
													<el-button size="small" @click="copyJsonPathResult">复制结果</el-button>
												</template>
											</el-input>
										</div>
										<div v-if="jsonPathResult !== null" class="jsonpath-result">
											<strong>提取结果：</strong>
											<pre>{{ jsonPathResult }}</pre>
										</div>
									</div>
									<div class="response-content" v-html="highlightedResponseBody"></div>
								</div>
							</el-tab-pane>

							<el-tab-pane :label="$t('apiTesting.interface.responseHeaders')" name="headers">
								<div class="response-headers">
									<div v-for="(value, key) in response?.response_data?.headers" :key="key"
										class="header-row">
										<strong>{{ key }}:</strong> {{ value }}
									</div>
								</div>
							</el-tab-pane>

							<el-tab-pane :label="$t('apiTesting.interface.assertionResults')" name="assertions"
								v-if="response?.assertions_results && response.assertions_results.length > 0">
								<div class="assertions-results">
									<div v-for="(result, index) in response.assertions_results" :key="index"
										class="assertion-result-item"
										:class="{ 'passed': result.passed, 'failed': !result.passed }">
										<div class="assertion-result-header">
											<el-tag :type="result.passed ? 'success' : 'danger'" size="small">
												{{ result.passed ? $t('apiTesting.interface.passed') : $t('apiTesting.interface.failed') }}
											</el-tag>
											<span class="assertion-name">{{ result.name }}</span>
										</div>
										<div class="assertion-result-details">
											<div class="result-row">
												<span class="label">期望:</span>
												<span class="value">{{ formatAssertionValue(result.expected) }}</span>
											</div>
											<div class="result-row">
												<span class="label">实际:</span>
												<span class="value">{{ formatAssertionValue(result.actual) }}</span>
											</div>
											<div class="result-row" v-if="result.error">
												<span class="label">{{ $t('apiTesting.interface.error') }}</span>
												<span class="value error">{{ result.error }}</span>
											</div>
										</div>
									</div>
								</div>
							</el-tab-pane>
						</el-tabs>
					</div>
				</div>
			</div>
		</div>

		<!-- 创建集合对话框 -->
		<el-dialog v-model="showCreateCollectionDialog" title="创建集合" :close-on-click-modal="false"
			:close-on-press-escape="false" :modal="true" :destroy-on-close="false" width="500px">
			<el-form ref="collectionFormRef" :model="collectionForm" :rules="collectionRules" label-width="100px">
				<el-form-item label="集合名称" prop="name">
					<el-input v-model="collectionForm.name" placeholder="请输入集合名称" />
				</el-form-item>
				<el-form-item :label="$t('apiTesting.common.description')" prop="description">
					<el-input v-model="collectionForm.description" type="textarea" :rows="3"
						:placeholder="$t('apiTesting.common.pleaseInput')" />
				</el-form-item>
				<el-form-item :label="$t('apiTesting.interface.parentCollection')" prop="parent">
					<el-select v-model="collectionForm.parent"
						:placeholder="$t('apiTesting.interface.selectParentCollection')" clearable>
						<el-option v-for="collection in flatCollections" :key="collection.id" :label="collection.name"
							:value="collection.id" />
					</el-select>
				</el-form-item>
			</el-form>

			<template #footer>
				<el-button @click="showCreateCollectionDialog = false">{{ $t('apiTesting.common.cancel') }}</el-button>
				<el-button type="primary" @click="createCollection">{{ $t('apiTesting.common.create') }}</el-button>
			</template>
		</el-dialog>

		<!-- 编辑集合对话框 -->
		<el-dialog v-model="showEditCollectionDialog" title="编辑集合" :close-on-click-modal="false" width="500px">
			<el-form ref="editCollectionFormRef" :model="editCollectionForm" :rules="collectionRules"
				label-width="100px">
				<el-form-item label="集合名称" prop="name">
					<el-input v-model="editCollectionForm.name" placeholder="请输入集合名称" />
				</el-form-item>
				<el-form-item :label="$t('apiTesting.common.description')" prop="description">
					<el-input v-model="editCollectionForm.description" type="textarea" :rows="3"
						:placeholder="$t('apiTesting.common.pleaseInput')" />
				</el-form-item>
				<el-form-item :label="$t('apiTesting.interface.parentCollection')" prop="parent">
					<el-select v-model="editCollectionForm.parent"
						:placeholder="$t('apiTesting.interface.selectParentCollection')" clearable>
						<el-option v-for="collection in flatCollections.filter(c => c.id !== editCollectionForm.id)"
							:key="collection.id" :label="collection.name" :value="collection.id" />
					</el-select>
				</el-form-item>
			</el-form>

			<template #footer>
				<el-button @click="showEditCollectionDialog = false">{{ $t('apiTesting.common.cancel') }}</el-button>
				<el-button type="primary" @click="updateCollection">{{ $t('apiTesting.common.save') }}</el-button>
			</template>
		</el-dialog>

		<!-- 右键菜单 -->
		<ul v-show="showContextMenu" class="context-menu"
			:style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }">
			<li @click="addRequest">{{ $t('apiTesting.interface.contextMenu.addRequest') }}</li>
			<li @click="addCollection">{{ $t('apiTesting.interface.contextMenu.addSubCollection') }}</li>
			<li @click="editNode">{{ $t('apiTesting.interface.contextMenu.edit') }}</li>
			<li @click="deleteNode">{{ $t('apiTesting.interface.contextMenu.delete') }}</li>
		</ul>

		<!-- 数据工厂选择器 -->
		<DataFactorySelector v-model="showDataFactorySelector" @select="handleDataFactorySelect" />

		<!-- 变量助手对话框 -->
		<el-dialog :close-on-press-escape="false" :modal="true" :destroy-on-close="false" v-model="showVariableHelper"
			title="变量助手 (点击插入)" :close-on-click-modal="false" width="900px">
			<el-tabs tab-position="left" style="height: 450px">
				<el-tab-pane v-for="(category, index) in variableCategories" :key="index" :label="category.label">
					<div style="height: 450px; overflow-y: auto; padding: 10px;">
						<el-table :data="category.variables" style="width: 100%" @row-click="insertVariable"
							highlight-current-row>
							<el-table-column prop="name" label="函数名" width="150" show-overflow-tooltip >
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

		<!-- CURL导入对话框 -->
		<el-dialog v-model="showCurlImportDialog" title="导入CURL命令" width="800px" :close-on-click-modal="false">
			<el-input v-model="curlCommand" type="textarea" :rows="15"
				placeholder="请粘贴CURL命令，例如：curl -X POST https://api.example.com/users -H 'Content-Type: application/json' -d &apos;{&quot;name&quot;:&quot;test&quot;}&apos;" />
			<template #footer>
				<el-button @click="showCurlImportDialog = false">取消</el-button>
				<el-button type="primary" @click="parseAndImportCurl">解析并导入</el-button>
			</template>
		</el-dialog>

		<!-- 代码生成对话框 -->
		<el-dialog v-model="showCodeGenerateDialog" title="生成代码" width="900px" :close-on-click-modal="false">
			<el-select v-model="codeLanguage" placeholder="选择语言" style="width: 150px; margin-bottom: 10px"
				@change="generateCode(codeLanguage)">
				<el-option label="JavaScript" value="javascript" />
				<el-option label="Python" value="python" />
				<el-option label="Java" value="java" />
				<el-option label="Node.js" value="node" />
				<el-option label="cURL" value="curl" />
				<el-option label="PHP" value="php" />
				<el-option label="Go" value="go" />
				<el-option label="C#" value="csharp" />
				<el-option label="Ruby" value="ruby" />
				<el-option label="Swift" value="swift" />
				<el-option label="Kotlin" value="kotlin" />
				<el-option label="Rust" value="rust" />
				<el-option label="Dart" value="dart" />
				<el-option label="Objective-C" value="objective_c" />
				<el-option label="Shell" value="shell" />
				<el-option label="PowerShell" value="powershell" />
				<el-option label="MATLAB" value="matlab" />
				<el-option label="R" value="r" />
				<el-option label="Ansible" value="ansible" />
				<el-option label="C" value="c" />
				<el-option label="CFML" value="cfml" />
				<el-option label="Clojure" value="clojure" />
				<el-option label="Elixir" value="elixir" />
				<el-option label="HTTP" value="http" />
				<el-option label="HTTPie" value="httpie" />
				<el-option label="Julia" value="julia" />
				<el-option label="Lua" value="lua" />
				<el-option label="OCaml" value="ocaml" />
				<el-option label="Perl" value="perl" />
				<el-option label="Wget" value="wget" />
			</el-select>
			<el-input v-model="generatedCode" type="textarea" :rows="20" readonly placeholder="生成的代码将显示在这里" />
			<template #footer>
				<el-button @click="showCodeGenerateDialog = false">关闭</el-button>
				<el-button type="primary" @click="copyGeneratedCode">复制代码</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup>
	import {
		ref,
		reactive,
		computed,
		onMounted,
		onBeforeUnmount,
		nextTick
	} from 'vue'
	import {
		useI18n
	} from 'vue-i18n'
	import {
		ElMessage,
		ElMessageBox
	} from 'element-plus'
	import {
		Plus,
		Folder,
		Document,
		MagicStick,
		Search,
		Close
	} from '@element-plus/icons-vue'
	import api from '@/utils/api'
	import KeyValueEditor from './components/KeyValueEditor.vue'
	import DataFactorySelector from '@/components/DataFactorySelector.vue'
	import {
		RequestModelParser
	} from '@/utils/requestModel'
	import {
		CodeGenerator
	} from '@/utils/codeGenerator'
	import {
		debounce
	} from 'lodash-es'

	const {
		t
	} = useI18n()

	const treeRef = ref(null)
	const expandedKeys = ref([])
	const projects = ref([])
	const selectedProject = ref(null)
	const collections = ref([])
	const flatCollections = ref([])
	const environments = ref([])
	const selectedEnvironment = ref(null)
	const selectedRequest = ref(null)
	const response = ref(null)
	const sending = ref(false)
	const saving = ref(false)
	const activeTab = ref('params')
	const responseActiveTab = ref('body')
	const showCreateCollectionDialog = ref(false)
	const showEditCollectionDialog = ref(false)
	const showContextMenu = ref(false)
	const contextMenuX = ref(0)
	const contextMenuY = ref(0)
	const rightClickedNode = ref(null)
	const headersEditorRef = ref(null)
	const editingNodeId = ref(null)
	const editingNodeName = ref('')
	const editInputRef = ref(null)
	const saveButtonRef = ref(null)
	const collectionFormRef = ref(null)
	const editCollectionFormRef = ref(null)

	const searchKeyword = ref('')
	const filteredCollections = ref([])

	const onSearch = async (value) => {
		if (!value || value.trim() === '') {
			filteredCollections.value = []
			return
		}

		const keyword = value.toLowerCase().trim()
		const results = []

		try {
			const res = await api.get('/api-testing/requests/', {
				params: {
					search: keyword,
					project: selectedProject.value,
					page_size: 1000
				}
			})

			console.log('搜索结果:', res.data)
			const requests = res.data.results || res.data
			console.log('请求数据:', requests)

			requests.forEach(request => {
				const nameMatch = request.name && request.name.toLowerCase().includes(keyword)
				const urlMatch = request.url && request.url.toLowerCase().includes(keyword)
				const methodMatch = request.method && request.method.toLowerCase().includes(keyword)

				let matchType = 'name'
				if (methodMatch) {
					matchType = 'method'
				} else if (urlMatch) {
					matchType = 'url'
				}

				results.push({
					...request,
					type: 'request',
					matchType: matchType
				})
			})

			console.log('过滤后结果:', results)
			filteredCollections.value = results
		} catch (error) {
			console.error('搜索失败:', error)
			ElMessage.error('搜索失败')
		}
	}

	const onSearchDebounced = debounce(onSearch, 300)

	const selectSearchResult = async (item) => {
		try {
			const res = await api.get(`/api-testing/requests/${item.id}/`)
			const request = res.data

			const convertedHeaders = convertObjectToKeyValueArray(request.headers || {})
			currentHeaders.value = request.headers || {}

			selectedRequest.value = {
				...request,
				params: convertObjectToKeyValueArray(request.params || {}),
				headers: convertedHeaders,
				body: request.body || {},
				auth: request.auth || {}
			}

			if (request.body && request.body.type) {
				if (request.body.type === 'json' && request.body.data) {
					rawBody.value = JSON.stringify(request.body.data, null, 2)
				} else if (request.body.type === 'raw' && request.body.data) {
					rawBody.value = request.body.data
				} else if (request.body.type === 'formdata' && request.body.data) {
					formData.value = convertObjectToKeyValueArray(request.body.data)
				} else if (request.body.type === 'urlencoded' && request.body.data) {
					formUrlEncoded.value = convertObjectToKeyValueArray(request.body.data)
				}
			}

			searchKeyword.value = ''
			filteredCollections.value = []
		} catch (error) {
			console.error('加载请求失败:', error)
			ElMessage.error('加载请求失败')
		}
	}

	const showJsonPathExtractor = ref(false)
	const jsonPathExpression = ref('')
	const jsonPathResult = ref(null)

	const evaluateJsonPath = () => {
		if (!jsonPathExpression.value || !response.value) {
			jsonPathResult.value = null
			return
		}

		try {
			const responseData = response.value.response_data
			if (!responseData) {
				jsonPathResult.value = null
				return
			}

			let data = responseData.json
			if (!data && responseData.body) {
				try {
					data = typeof responseData.body === 'string' ? JSON.parse(responseData.body) : responseData.body
				} catch (e) {
					data = responseData.body
				}
			}

			if (!data) {
				jsonPathResult.value = null
				return
			}

			const result = simpleJsonPath(data, jsonPathExpression.value)
			jsonPathResult.value = JSON.stringify(result, null, 2)
		} catch (error) {
			console.error('JSONPath evaluation error:', error)
			jsonPathResult.value = '表达式错误: ' + error.message
		}
	}

	const formatAssertionValue = (value) => {
		if (value === null || value === undefined) {
			return '未获取到'
		}

		if (typeof value === 'object') {
			try {
				return JSON.stringify(value, null, 2)
			} catch (e) {
				return String(value)
			}
		}

		return String(value)
	}

	const simpleJsonPath = (obj, path) => {
		if (!path) return obj

		let cleanPath = path.replace(/^\$/, '')

		const parts = cleanPath.split('.')
		const keys = []

		for (let i = 0; i < parts.length; i++) {
			const part = parts[i]

			if (part === '') {
				if (i + 1 < parts.length && parts[i + 1] === '') {
					keys.push('..')
					i++
				}
			} else {
				keys.push(part)
			}
		}

		let result = obj

		for (let i = 0; i < keys.length; i++) {
			const key = keys[i]

			if (key === '..') {
				const nextKey = keys[i + 1]
				const remainingPath = keys.slice(i + 2).join('.')

				if (nextKey) {
					const recursiveFind = (current, targetKey, remainingPath) => {
						if (!current || typeof current !== 'object') return null

						if (targetKey in current) {
							const remainingKeys = remainingPath.split('.')
							let value = current[targetKey]

							if (remainingPath) {
								for (const remainingKey of remainingKeys) {
									if (value && typeof value === 'object') {
										if (remainingKey in value) {
											value = value[remainingKey]
										} else {
											return null
										}
									} else {
										return null
									}
								}
							}

							return value
						}

						for (const prop in current) {
							if (typeof current[prop] === 'object' && current[prop] !== null) {
								const found = recursiveFind(current[prop], targetKey, remainingPath)
								if (found !== null) return found
							}
						}

						return null
					}

					result = recursiveFind(result, nextKey, remainingPath)
				} else {
					const findAll = (current) => {
						if (!current || typeof current !== 'object') return null

						const results = []
						for (const prop in current) {
							if (typeof current[prop] === 'object' && current[prop] !== null) {
								results.push(current[prop])
								results.push(...findAll(current[prop]))
							}
						}
						return results
					}
					result = findAll(result)
				}

				if (result === null || (Array.isArray(result) && result.length === 0)) {
					return null
				}

				return result
			}

			const arrayMatch = key.match(/^(\w+)\[(\d+)\]$/)
			if (arrayMatch) {
				const arrayKey = arrayMatch[1]
				const index = parseInt(arrayMatch[2])
				if (result && result[arrayKey] && Array.isArray(result[arrayKey])) {
					result = result[arrayKey][index]
				} else {
					return null
				}
			} else {
				if (result && result[key] !== undefined) {
					result = result[key]
				} else {
					return null
				}
			}
		}

		return result
	}

	const copyJsonPathResult = () => {
		if (jsonPathResult.value) {
			navigator.clipboard.writeText(jsonPathResult.value).then(() => {
				ElMessage.success('结果已复制到剪贴板')
			}).catch(() => {
				ElMessage.error('复制失败')
			})
		}
	}

	const highlightedResponseBody = computed(() => {
		if (!response.value || !response.value.response_data) return ''

		const body = response.value.response_data.body || response.value.response_data
		if (!body) return ''

		try {
			const jsonStr = typeof body === 'string' ? body : JSON.stringify(body, null, 2)
			return highlightJson(jsonStr)
		} catch (error) {
			return body
		}
	})

	const highlightJson = (jsonStr) => {
		return jsonStr
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"([^"\\]|\\.)*"/g, '<span style="color: #e06c75;">$&</span>')
			.replace(/:\s*<span[^>]*>([^<]*)<\/span>/g, ': <span style="color: #98c379;">$1</span>')
			.replace(/\b(true|false|null)\b/g, '<span style="color: #d19a66;">$1</span>')
			.replace(/\b(-?\d+\.?\d*)\b/g, '<span style="color: #d19a66;">$1</span>')
	}

	// 辅助函数：将对象或数组转换为键值对数组（用于KeyValueEditor组件）
	const convertObjectToKeyValueArray = (obj) => {
		if (!obj) return []

		// 如果已经是数组格式（新的完整格式），直接返回
		if (Array.isArray(obj)) {
			console.log('Input is already array format:', obj)
			return obj.map(item => ({
				key: item.key || '',
				value: item.value || '',
				type: item.type || 'text',
				enabled: item.enabled !== false
			}))
		}

		// 如果是对象格式（旧的简单key-value格式），转换为数组
		if (typeof obj === 'object') {
			console.log('Converting object to array:', obj)
			return Object.entries(obj).map(([key, value]) => ({
				key,
				value: String(value),
				type: 'text',
				enabled: true
			}))
		}

		return []
	}

	// 辅助函数：将键值对数组转换为对象（保存时使用）
	const convertKeyValueArrayToObject = (input) => {
		console.log('convertKeyValueArrayToObject input:', input)

		// 如果输入已经是普通对象，直接返回
		if (input && typeof input === 'object' && !Array.isArray(input)) {
			console.log('Input is already an object, returning as-is')
			return input
		}

		// 如果输入是数组，转换为对象
		if (!Array.isArray(input)) return {}

		const obj = {}
		input.forEach(item => {
			console.log('Processing item:', item, 'enabled:', item.enabled)
			if (item.enabled !== false && item.key) {
				obj[item.key] = item.value || ''
				console.log('Added to obj:', item.key, '=', item.value)
			}
		})
		console.log('convertKeyValueArrayToObject output:', obj)
		return obj
	}

	const httpMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
	const websocketMethods = ['CONNECT', 'SUBSCRIBE', 'UNSUBSCRIBE', 'SEND', 'PING', 'PONG']

	const availableMethods = computed(() => {
		if (!selectedRequest.value) return httpMethods
		return selectedRequest.value.request_type === 'WEBSOCKET' ?
			websocketMethods :
			httpMethods
	})

	// WebSocket消息相关数据
	const websocketMessageType = ref('text')
	const websocketMessageContent = ref('')
	const websocketBinaryFile = ref(null)
	const websocketConnectionStatus = ref('disconnected') // disconnected, connecting, connected
	const websocketConnection = ref(null)
	const websocketMessages = ref([]) // WebSocket消息历史记录

	// 数据工厂选择器相关
	const showDataFactorySelector = ref(false)
	const showVariableHelper = ref(false)
	const currentEditingField = ref('')
	const currentBodyField = ref('')
	const currentAssertion = ref(null)
	const currentAssertionField = ref('')
	const currentAssertionIndex = ref(-1)
	const currentScriptField = ref('')

	// CURL导入相关
	const showCurlImportDialog = ref(false)
	const curlCommand = ref('')

	// 代码生成相关
	const showCodeGenerateDialog = ref(false)
	const codeLanguage = ref('javascript')
	const generatedCode = ref('')

	const rawType = ref('json')
	const bodyType = ref('none')
	const formData = ref([])
	const formUrlEncoded = ref([])
	const rawBody = ref('')

	const treeProps = {
		children: 'children',
		label: 'name'
	}

	const variableCategories = [{
			label: '随机数',
			variables: [{
					name: 'random_int',
					syntax: '${random_int(min, max, count)}',
					desc: '生成随机整数',
					example: '${random_int(100, 999, 1)}'
				},
				{
					name: 'random_float',
					syntax: '${random_float(min, max, precision, count)}',
					desc: '生成随机浮点数',
					example: '${random_float(0, 1, 2, 1)}'
				},
				{
					name: 'random_boolean',
					syntax: '${random_boolean(count)}',
					desc: '生成随机布尔值',
					example: '${random_boolean(1)}'
				},
				{
					name: 'random_date',
					syntax: '${random_date(start_date, end_date, count, date_format)}',
					desc: '生成随机日期',
					example: '${random_date(2024-01-01, 2024-12-31, 1, %Y-%m-%d)}'
				}
			]
		},
		{
			label: '随机字符串',
			variables: [{
					name: 'random_string',
					syntax: '${random_string(length, char_type, count)}',
					desc: '生成随机字符串',
					example: '${random_string(8, all, 1)}'
				},
				{
					name: 'random_uuid',
					syntax: '${random_uuid(version, count)}',
					desc: '生成UUID',
					example: '${random_uuid(4, 1)}'
				},
				{
					name: 'random_mac_address',
					syntax: '${random_mac_address(separator, count)}',
					desc: '生成MAC地址',
					example: '${random_mac_address(:, 1)}'
				},
				{
					name: 'random_ip_address',
					syntax: '${random_ip_address(ip_version, count)}',
					desc: '生成IP地址',
					example: '${random_ip_address(4, 1)}'
				},
				{
					name: 'random_sequence',
					syntax: '${random_sequence(sequence, count, unique)}',
					desc: '从序列中随机选择',
					example: '${random_sequence([a,b,c], 1, false)}'
				}
			]
		},
		{
			label: '字符工具',
			variables: [{
					name: 'remove_whitespace',
					syntax: '${remove_whitespace(text, type)}',
					desc: '去除空格换行',
					example: '${remove_whitespace(hello world, all)}'
				},
				{
					name: 'replace_string',
					syntax: '${replace_string(text, old, new, count)}',
					desc: '字符串替换',
					example: '${replace_string(hello world, world, test, 1)}'
				},
				{
					name: 'word_count',
					syntax: '${word_count(text)}',
					desc: '字数统计',
					example: '${word_count(hello world)}'
				},
				{
					name: 'regex_test',
					syntax: '${regex_test(text, pattern, flags)}',
					desc: '正则测试',
					example: '${regex_test(hello123, ^[a-z]+\\d+$, gi)}'
				},
				{
					name: 'case_convert',
					syntax: '${case_convert(text, case_type)}',
					desc: '大小写转换',
					example: '${case_convert(hello, upper)}'
				}
			]
		},
		{
			label: '测试数据',
			variables: [{
					name: 'generate_chinese_name',
					syntax: '${generate_chinese_name(gender, count)}',
					desc: '生成中文姓名',
					example: '${generate_chinese_name(random, 1)}'
				},
				{
					name: 'generate_chinese_phone',
					syntax: '${generate_chinese_phone(count)}',
					desc: '生成手机号',
					example: '${generate_chinese_phone(1)}'
				},
				{
					name: 'generate_chinese_email',
					syntax: '${generate_chinese_email(count)}',
					desc: '生成邮箱',
					example: '${generate_chinese_email(1)}'
				},
				{
					name: 'generate_chinese_address',
					syntax: '${generate_chinese_address(full_address, count)}',
					desc: '生成地址',
					example: '${generate_chinese_address(true, 1)}'
				},
				{
					name: 'generate_id_card',
					syntax: '${generate_id_card(count)}',
					desc: '生成身份证号',
					example: '${generate_id_card(1)}'
				},
				{
					name: 'generate_company_name',
					syntax: '${generate_company_name(count)}',
					desc: '生成公司名称',
					example: '${generate_company_name(1)}'
				},
				{
					name: 'generate_bank_card',
					syntax: '${generate_bank_card(count)}',
					desc: '生成银行卡号',
					example: '${generate_bank_card(1)}'
				},
				{
					name: 'generate_hk_id_card',
					syntax: '${generate_hk_id_card(count)}',
					desc: '生成香港身份证号',
					example: '${generate_hk_id_card(1)}'
				},
				{
					name: 'generate_business_license',
					syntax: '${generate_business_license(count)}',
					desc: '生成营业执照号',
					example: '${generate_business_license(1)}'
				},
				{
					name: 'generate_user_profile',
					syntax: '${generate_user_profile(count)}',
					desc: '生成用户档案',
					example: '${generate_user_profile(1)}'
				},
				{
					name: 'generate_coordinates',
					syntax: '${generate_coordinates(count)}',
					desc: '生成经纬度',
					example: '${generate_coordinates(1)}'
				}
			]
		},
		{
			label: '时间日期',
			variables: [{
					name: 'timestamp_convert',
					syntax: '${timestamp_convert(timestamp, convert_type)}',
					desc: '时间戳转换',
					example: '${timestamp_convert(1234567890, to_datetime)}'
				},
				{
					name: 'random_date',
					syntax: '${random_date(start_date, end_date, count, date_format)}',
					desc: '生成随机日期',
					example: '${random_date(2024-01-01, 2024-12-31, 1, %Y-%m-%d)}'
				}
			]
		},
		{
			label: '编码转换',
			variables: [{
					name: 'base64_encode',
					syntax: '${base64_encode(text, encoding)}',
					desc: 'Base64编码',
					example: '${base64_encode("123456", "utf-8")}'
				},
				{
					name: 'base64_decode',
					syntax: '${base64_decode(text, encoding)}',
					desc: 'Base64解码',
					example: '${base64_decode("MTIzNDU2", "utf-8")}'
				},
				{
					name: 'url_encode',
					syntax: '${url_encode(data, encoding)}',
					desc: 'URL编码',
					example: '${url_encode("hello world", "utf-8")}'
				},
				{
					name: 'url_decode',
					syntax: '${url_decode(data, encoding)}',
					desc: 'URL解码',
					example: '${url_decode("hello%20world", "utf-8")}'
				},
				{
					name: 'unicode_convert',
					syntax: '${unicode_convert(text, convert_type)}',
					desc: 'Unicode转换',
					example: '${unicode_convert("你好", "to_unicode")}'
				},
				{
					name: 'ascii_convert',
					syntax: '${ascii_convert(text, convert_type)}',
					desc: 'ASCII转换',
					example: '${ascii_convert("ABC", "to_ascii")}'
				},
				{
					name: 'color_convert',
					syntax: '${color_convert(color, from_type, to_type)}',
					desc: '颜色值转换',
					example: '${color_convert("#ff0000", "hex", "rgb")}'
				},
				{
					name: 'base_convert',
					syntax: '${base_convert(number, from_base, to_base)}',
					desc: '进制转换',
					example: '${base_convert(10, 10, 16)}'
				},
				{
					name: 'timestamp_convert',
					syntax: '${timestamp_convert(timestamp, convert_type)}',
					desc: '时间戳转换',
					example: '${timestamp_convert(1234567890, "to_datetime")}'
				},
				{
					name: 'generate_barcode',
					syntax: '${generate_barcode(data, format)}',
					desc: '生成条形码',
					example: '${generate_barcode("123456", "code128")}'
				},
				{
					name: 'generate_qrcode',
					syntax: '${generate_qrcode(data)}',
					desc: '生成二维码',
					example: '${generate_qrcode("https://example.com")}'
				},
				{
					name: 'decode_qrcode',
					syntax: '${decode_qrcode(data)}',
					desc: '二维码解析',
					example: '${decode_qrcode("/path/to/image.png")}'
				},
				{
					name: 'image_to_base64',
					syntax: '${image_to_base64(image_path)}',
					desc: '图片转Base64',
					example: '${image_to_base64("/path/to/image.png")}'
				},
				{
					name: 'base64_to_image',
					syntax: '${base64_to_image(base64_data, output_path)}',
					desc: 'Base64转图片',
					example: '${base64_to_image("data:image/png;base64,...", "/path/to/output.png")}'
				}
			]
		},
		{
			label: '加密哈希',
			variables: [{
					name: 'md5_hash',
					syntax: '${md5_hash(text)}',
					desc: 'MD5加密',
					example: '${md5_hash("123456")}'
				},
				{
					name: 'sha1_hash',
					syntax: '${sha1_hash(text)}',
					desc: 'SHA1加密',
					example: '${sha1_hash("123456")}'
				},
				{
					name: 'sha256_hash',
					syntax: '${sha256_hash(text)}',
					desc: 'SHA256加密',
					example: '${sha256_hash("123456")}'
				},
				{
					name: 'sha512_hash',
					syntax: '${sha512_hash(text)}',
					desc: 'SHA512加密',
					example: '${sha512_hash("123456")}'
				},
				{
					name: 'hash_comparison',
					syntax: '${hash_comparison(hash1, hash2)}',
					desc: '哈希值比对',
					example: '${hash_comparison("hash1", "hash2")}'
				},
				{
					name: 'aes_encrypt',
					syntax: '${aes_encrypt(text, password, mode)}',
					desc: 'AES加密',
					example: '${aes_encrypt("hello", "password", "CBC")}'
				},
				{
					name: 'aes_decrypt',
					syntax: '${aes_decrypt(encrypted_text, password, mode)}',
					desc: 'AES解密',
					example: '${aes_decrypt("encrypted", "password", "CBC")}'
				}
			]
		},
		{
			label: 'Crontab',
			variables: [{
					name: 'generate_expression',
					syntax: '${generate_expression(minute, hour, day, month, weekday)}',
					desc: '生成Crontab表达式',
					example: '${generate_expression("*", "*", "*", "*", "*")}'
				},
				{
					name: 'parse_expression',
					syntax: '${parse_expression(expression)}',
					desc: '解析Crontab表达式',
					example: '${parse_expression("0 0 * * *")}'
				},
				{
					name: 'get_next_runs',
					syntax: '${get_next_runs(expression, count)}',
					desc: '获取下次执行时间',
					example: '${get_next_runs("0 0 * * *", 5)}'
				},
				{
					name: 'validate_expression',
					syntax: '${validate_expression(expression)}',
					desc: '验证Crontab表达式',
					example: '${validate_expression("0 0 * * *")}'
				}
			]
		},
		{
			label: '其他',
			variables: [{
					name: 'random_password',
					syntax: '${random_password(length, include_uppercase, include_lowercase, include_digits, include_special, count)}',
					desc: '生成随机密码',
					example: '${random_password(12, true, true, true, true, 1)}'
				},
				{
					name: 'random_color',
					syntax: '${random_color(format, count)}',
					desc: '生成随机颜色',
					example: '${random_color(hex, 1)}'
				},
				{
					name: 'jwt_decode',
					syntax: '${jwt_decode(token, verify, secret)}',
					desc: 'JWT解码',
					example: '${jwt_decode(token, false, secret)}'
				},
				{
					name: 'password_strength',
					syntax: '${password_strength(password)}',
					desc: '密码强度分析',
					example: '${password_strength(myPassword123)}'
				},
				{
					name: 'generate_salt',
					syntax: '${generate_salt(length)}',
					desc: '生成随机盐值',
					example: '${generate_salt(16)}'
				}
			]
		}
	]

	const collectionForm = reactive({
		name: '',
		description: '',
		parent: null
	})

	const editCollectionForm = reactive({
		id: null,
		name: '',
		description: '',
		parent: null
	})

	const collectionRules = computed(() => ({
		name: [{
			required: true,
			message: t('apiTesting.interface.inputCollectionName'),
			trigger: 'blur'
		}]
	}))

	const hasBody = computed(() => {
		return selectedRequest.value && selectedRequest.value.method && ['POST', 'PUT', 'PATCH'].includes(
			selectedRequest.value.method)
	})

	const responseBody = computed(() => {
		if (!response.value?.response_data) return ''

		try {
			if (response.value?.response_data?.json) {
				return JSON.stringify(response.value.response_data.json, null, 2)
			} else {
				return response.value?.response_data?.body || ''
			}
		} catch (e) {
			return response.value?.response_data?.body || ''
		}
	})

	const getStatusType = (status) => {
		if (status >= 200 && status < 300) return 'success'
		if (status >= 300 && status < 400) return 'warning'
		if (status >= 400) return 'danger'
		return 'info'
	}

	const loadProjects = async () => {
		try {
			const res = await api.get('/api-testing/projects/')
			projects.value = res.data.results || res.data
			if (projects.value.length > 0 && !selectedProject.value) {
				selectedProject.value = projects.value[0].id
				await onProjectChange()
			}
		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.loadProjects'))
		}
	}

	const loadCollections = async (preserveExpandState = true) => {
		if (!selectedProject.value) return

		try {
			const res = await api.get('/api-testing/collections/', {
				params: {
					project: selectedProject.value
				}
			})
			const collectionsData = res.data.results || res.data

			// 检查组件是否仍然存在
			if (!selectedProject.value) return

			// 构建树形结构
			collections.value = buildTree(collectionsData)
			flatCollections.value = collectionsData

			// 加载每个集合的请求
			await loadRequests()

			// 如果不保留展开状态，清空展开键
			if (!preserveExpandState) {
				expandedKeys.value = []
			}

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.loadCollections'))
		}
	}

	const loadRequests = async () => {
		if (!selectedProject.value) return

		try {
			const res = await api.get('/api-testing/requests/')
			const requests = res.data.results || res.data

			// 清空所有集合的子节点（请求）
			collections.value.forEach(collection => {
				clearCollectionChildren(collection)
			})

			// 将请求添加到对应集合中
			requests.forEach(request => {
				const collection = findCollectionById(collections.value, request.collection)
				if (collection) {
					if (!collection.children) collection.children = []
					collection.children.push({
						...request,
						type: 'request',
						name: request.name
					})
				}
			})
		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.loadRequests'))
		}
	}

	const clearCollectionChildren = (collection) => {
		if (collection.children) {
			collection.children = collection.children.filter(child => child.type === 'collection')
			collection.children.forEach(child => clearCollectionChildren(child))
		}
	}

	const loadEnvironments = async () => {
		try {
			// 获取全局环境 + 当前项目环境，不传递project参数
			const res = await api.get('/api-testing/environments/')
			const allEnvironments = res.data.results || res.data

			// 过滤全局环境和当前项目环境
			environments.value = allEnvironments.filter(env =>
				env.scope === 'GLOBAL' ||
				(env.scope === 'LOCAL' && (!selectedProject.value || env.project === selectedProject.value))
			)
		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.loadEnvironments'))
		}
	}

	const buildTree = (items) => {
		const map = {}
		const roots = []

		items.forEach(item => {
			map[item.id] = {
				...item,
				type: 'collection',
				children: []
			}
		})

		items.forEach(item => {
			if (item.parent) {
				if (map[item.parent]) {
					map[item.parent].children.push(map[item.id])
				}
			} else {
				roots.push(map[item.id])
			}
		})

		return roots
	}

	const findCollectionById = (collections, id) => {
		for (const collection of collections) {
			if (collection.id === id) return collection
			if (collection.children) {
				const found = findCollectionById(collection.children, id)
				if (found) return found
			}
		}
		return null
	}

	const onProjectChange = async () => {
		await Promise.all([loadCollections(false), loadEnvironments()])
	}

	const onNodeClick = (data) => {
		if (!data) return

		if (data.type === 'request') {
			console.log('onNodeClick - original data.headers:', data.headers)
			const convertedHeaders = convertObjectToKeyValueArray(data.headers || {})
			console.log('onNodeClick - converted headers:', convertedHeaders)

			// 初始化currentHeaders
			currentHeaders.value = data.headers || {}
			console.log('onNodeClick - initialized currentHeaders:', currentHeaders.value)

			selectedRequest.value = {
				...data,
				params: convertObjectToKeyValueArray(data.params || {}),
				headers: convertedHeaders,
				body: data.body || {},
				auth: data.auth || {}
			}

			console.log('onNodeClick - selectedRequest.value.headers:', selectedRequest.value.headers)

			// 解析body数据
			if (data.body && data.body.type) {
				if (data.body.type === 'json' && data.body.data) {
					bodyType.value = 'raw'
					rawType.value = 'json'
					rawBody.value = JSON.stringify(data.body.data, null, 2)
				} else if (data.body.type === 'raw' && data.body.data) {
					bodyType.value = 'raw'
					rawType.value = 'text'
					rawBody.value = data.body.data
				} else if (data.body.type === 'form-data') {
					bodyType.value = 'form-data'
					formData.value = data.body.data || []
				} else if (data.body.type === 'x-www-form-urlencoded') {
					bodyType.value = 'x-www-form-urlencoded'
					formUrlEncoded.value = data.body.data || []
				} else if (data.body.type === 'binary') {
					bodyType.value = 'binary'
				} else {
					bodyType.value = 'none'
					rawBody.value = ''
				}
			} else {
				bodyType.value = 'none'
				rawBody.value = ''
			}

			response.value = null
		}
	}

	const onNodeRightClick = (event, data) => {
		event.preventDefault()
		if (!data) return

		rightClickedNode.value = data
		contextMenuX.value = event.clientX
		contextMenuY.value = event.clientY
		showContextMenu.value = true

		nextTick(() => {
			document.addEventListener('click', hideContextMenu)
		})
	}

	const hideContextMenu = () => {
		showContextMenu.value = false
		document.removeEventListener('click', hideContextMenu)
	}

	const startEditCollection = (collection) => {
		editingNodeId.value = collection.id
		editingNodeName.value = collection.name
		nextTick(() => {
			if (editInputRef.value) {
				editInputRef.value.focus()
			}
		})
	}

	const saveCollectionName = async () => {
		if (!editingNodeId.value || !editingNodeName.value.trim()) {
			cancelEdit()
			return
		}

		try {
			const collection = flatCollections.value.find(c => c.id === editingNodeId.value)
			if (!collection) {
				ElMessage.error(t('apiTesting.messages.error.operationFailed'))
				cancelEdit()
				return
			}

			const data = {
				name: editingNodeName.value.trim(),
				description: collection.description,
				parent: collection.parent,
				project: selectedProject.value
			}

			await api.put(`/api-testing/collections/${editingNodeId.value}/`, data)

			// 直接更新本地数据，避免重新加载
			const updateCollectionName = (collections, id, newName) => {
				for (const collection of collections) {
					// 只更新集合类型的节点，跳过接口类型的节点
					if (collection.type === 'collection' && collection.id === id) {
						collection.name = newName
						return true
					}
					if (collection.children && updateCollectionName(collection.children, id, newName)) {
						return true
					}
				}
				return false
			}

			// 更新树中的集合名称
			updateCollectionName(collections.value, editingNodeId.value, editingNodeName.value.trim())

			// 更新平均集合列表
			const flatCollection = flatCollections.value.find(c => c.id === editingNodeId.value)
			if (flatCollection) {
				flatCollection.name = editingNodeName.value.trim()
			}

			ElMessage.success(t('apiTesting.messages.success.collectionNameUpdated'))
			cancelEdit()
		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.updateFailed'))
			cancelEdit()
		}
	}

	const cancelEdit = () => {
		editingNodeId.value = null
		editingNodeName.value = ''
	}

	const onNodeExpand = (data) => {
		if (!expandedKeys.value.includes(data.id)) {
			expandedKeys.value.push(data.id)
		}
	}

	const onNodeCollapse = (data) => {
		const index = expandedKeys.value.indexOf(data.id)
		if (index > -1) {
			expandedKeys.value.splice(index, 1)
		}
	}

	const addRequest = () => {
		// 创建新请求
		const newRequest = {
			name: t('apiTesting.interface.newRequest'),
			method: 'GET',
			url: '',
			headers: {},
			params: {},
			body: {},
			collection: rightClickedNode.value.type === 'collection' ? rightClickedNode.value.id : rightClickedNode
				.value.collection,
			type: 'request'
		}
		selectedRequest.value = newRequest
		hideContextMenu()
	}

	const addCollection = () => {
		collectionForm.parent = rightClickedNode.value.type === 'collection' ? rightClickedNode.value.id : null
		showCreateCollectionDialog.value = true
		hideContextMenu()
	}

	const editNode = () => {
		if (rightClickedNode.value.type === 'request') {
			// 使用与onNodeClick相同的逻辑来正确设置selectedRequest
			const data = rightClickedNode.value
			console.log('editNode - original data.headers:', data.headers)
			const convertedHeaders = convertObjectToKeyValueArray(data.headers || {})
			console.log('editNode - converted headers:', convertedHeaders)

			// 初始化currentHeaders
			currentHeaders.value = data.headers || {}
			console.log('editNode - initialized currentHeaders:', currentHeaders.value)

			selectedRequest.value = {
				...data,
				params: convertObjectToKeyValueArray(data.params || {}),
				headers: convertedHeaders,
				body: data.body || {},
				auth: data.auth || {}
			}

			console.log('editNode - selectedRequest.value.headers:', selectedRequest.value.headers)

			// 解析body数据
			if (data.body && data.body.type) {
				if (data.body.type === 'json' && data.body.data) {
					bodyType.value = 'raw'
					rawType.value = 'json'
					rawBody.value = JSON.stringify(data.body.data, null, 2)
				} else if (data.body.type === 'raw' && data.body.data) {
					bodyType.value = 'raw'
					rawType.value = 'text'
					rawBody.value = data.body.data
				} else if (data.body.type === 'form-data') {
					bodyType.value = 'form-data'
					formData.value = data.body.data || []
				} else if (data.body.type === 'x-www-form-urlencoded') {
					bodyType.value = 'x-www-form-urlencoded'
					formUrlEncoded.value = data.body.data || []
				} else if (data.body.type === 'binary') {
					bodyType.value = 'binary'
				} else {
					bodyType.value = 'none'
					rawBody.value = ''
				}
			} else {
				bodyType.value = 'none'
				rawBody.value = ''
			}

			response.value = null
		} else if (rightClickedNode.value.type === 'collection') {
			// 启动集合内联编辑
			startEditCollection(rightClickedNode.value)
		}
		hideContextMenu()
	}

	const deleteNode = async () => {
		if (!rightClickedNode.value) {
			hideContextMenu()
			return
		}

		const nodeType = rightClickedNode.value.type
		const nodeName = rightClickedNode.value.name

		// 显示确认对话框
		try {
			const typeText = nodeType === 'collection' ? t('apiTesting.interface.collection') : t(
				'apiTesting.interface.request')
			const extra = nodeType === 'collection' ? t('apiTesting.interface.deleteCollectionExtra') : ''
			await ElMessageBox.confirm(
				t('apiTesting.interface.confirmDeleteNode', {
					type: typeText,
					name: nodeName,
					extra: extra
				}),
				t('apiTesting.messages.confirm.deleteTitle'), {
					confirmButtonText: t('apiTesting.interface.confirmDeleteBtn'),
					cancelButtonText: t('apiTesting.common.cancel'),
					type: 'warning',
					confirmButtonClass: 'el-button--danger'
				}
			)

			// 用户确认删除，执行删除操作
			if (nodeType === 'collection') {
				await deleteCollection(rightClickedNode.value.id)
			} else if (nodeType === 'request') {
				await deleteRequest(rightClickedNode.value.id)
			}
		} catch (error) {
			// 用户取消删除或删除失败，不做任何处理
			console.log('删除操作被取消或失败:', error)
		}

		hideContextMenu()
	}

	const deleteCollection = async (collectionId) => {
		try {
			await api.delete(`/api-testing/collections/${collectionId}/`)
			ElMessage.success(t('apiTesting.messages.success.collectionDeleted'))

			// 如果当前选中的请求属于被删除的集合，清空选中状态
			if (selectedRequest.value && selectedRequest.value.collection === collectionId) {
				selectedRequest.value = null
				response.value = null
			}

			// 直接从树中移除集合，而不是重新加载
			const removeCollectionFromTree = (collections, id) => {
				for (let i = 0; i < collections.length; i++) {
					if (collections[i].id === id) {
						collections.splice(i, 1)
						return true
					}
					if (collections[i].children && removeCollectionFromTree(collections[i].children, id)) {
						return true
					}
				}
				return false
			}

			removeCollectionFromTree(collections.value, collectionId)

			// 从平集合列表中移除
			const index = flatCollections.value.findIndex(c => c.id === collectionId)
			if (index > -1) {
				flatCollections.value.splice(index, 1)
			}

			// 从展开键中移除
			const expandedIndex = expandedKeys.value.indexOf(collectionId)
			if (expandedIndex > -1) {
				expandedKeys.value.splice(expandedIndex, 1)
			}

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.deleteFailed'))
			console.error('Delete collection error:', error)
		}
	}

	const deleteRequest = async (requestId) => {
		try {
			await api.delete(`/api-testing/requests/${requestId}/`)
			ElMessage.success(t('apiTesting.messages.success.interfaceDeleted'))

			// 如果当前选中的是被删除的请求，清空选中状态
			if (selectedRequest.value && selectedRequest.value.id === requestId) {
				selectedRequest.value = null
				response.value = null
			}

			// 直接从树中移除请求，而不是重新加载
			const removeRequestFromTree = (collections, requestId) => {
				for (const collection of collections) {
					if (collection.children) {
						const requestIndex = collection.children.findIndex(child => child.type === 'request' &&
							child.id === requestId)
						if (requestIndex > -1) {
							collection.children.splice(requestIndex, 1)
							return true
						}
					}
					if (collection.children && removeRequestFromTree(collection.children, requestId)) {
						return true
					}
				}
				return false
			}

			removeRequestFromTree(collections.value, requestId)

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.deleteFailed'))
			console.error('Delete request error:', error)
		}
	}

	const createCollection = async () => {
		try {
			const data = {
				...collectionForm,
				project: selectedProject.value
			}
			const res = await api.post('/api-testing/collections/', data)
			const newCollection = res.data

			ElMessage.success(t('apiTesting.messages.success.collectionCreated'))
			showCreateCollectionDialog.value = false
			Object.assign(collectionForm, {
				name: '',
				description: '',
				parent: null
			})

			// 直接添加到本地数据，避免重新加载
			const newTreeNode = {
				...newCollection,
				type: 'collection',
				children: []
			}

			// 添加到平集合列表
			flatCollections.value.push(newCollection)

			// 添加到树结构
			if (newCollection.parent) {
				// 找到父节点并添加
				const findAndAddToParent = (collections, parentId, newNode) => {
					for (const collection of collections) {
						if (collection.id === parentId) {
							if (!collection.children) collection.children = []
							collection.children.push(newNode)
							return true
						}
						if (collection.children && findAndAddToParent(collection.children, parentId,
							newNode)) {
							return true
						}
					}
					return false
				}

				findAndAddToParent(collections.value, newCollection.parent, newTreeNode)

				// 自动展开父节点
				if (!expandedKeys.value.includes(newCollection.parent)) {
					expandedKeys.value.push(newCollection.parent)
				}
			} else {
				// 添加到根级
				collections.value.push(newTreeNode)
			}

			// 自动展开新创建的集合
			if (!expandedKeys.value.includes(newCollection.id)) {
				expandedKeys.value.push(newCollection.id)
			}

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.createFailed'))
		}
	}

	const updateCollection = async () => {
		try {
			const data = {
				...editCollectionForm,
				project: selectedProject.value
			}
			const res = await api.put(`/api-testing/collections/${editCollectionForm.id}/`, data)
			const updatedCollection = res.data

			ElMessage.success(t('apiTesting.messages.success.collectionUpdated'))
			showEditCollectionDialog.value = false

			// 更新本地数据
			const updateCollectionInTree = (collections, id, updatedData) => {
				for (const collection of collections) {
					if (collection.id === id) {
						Object.assign(collection, updatedData)
						return true
					}
					if (collection.children && updateCollectionInTree(collection.children, id, updatedData)) {
						return true
					}
				}
				return false
			}

			updateCollectionInTree(collections.value, editCollectionForm.id, updatedCollection)

			// 更新平集合列表
			const flatIndex = flatCollections.value.findIndex(c => c.id === editCollectionForm.id)
			if (flatIndex !== -1) {
				Object.assign(flatCollections.value[flatIndex], updatedCollection)
			}

			// 重置表单
			Object.assign(editCollectionForm, {
				name: '',
				description: '',
				parent: null
			})

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.updateFailed'))
		}
	}

	// 断言相关方法
	const addAssertion = () => {
		if (!selectedRequest.value.assertions) {
			selectedRequest.value.assertions = []
		}

		selectedRequest.value.assertions.push({
			name: `${t('apiTesting.interface.assertion')}${selectedRequest.value.assertions.length + 1}`,
			type: '',
			expected: null,
			json_path: '',
			header_name: ''
		})
	}

	const removeAssertion = (index) => {
		if (selectedRequest.value.assertions) {
			selectedRequest.value.assertions.splice(index, 1)
		}
	}

	const onAssertionTypeChange = (assertion) => {
		// 重置断言参数
		assertion.expected = null
		assertion.json_path = ''
		assertion.header_name = ''
	}

	// 数据工厂选择器相关方法
	const openDataFactorySelector = (assertion, field, index) => {
		currentAssertion.value = assertion
		currentAssertionField.value = field
		currentAssertionIndex.value = index
		currentScriptField.value = ''
		showDataFactorySelector.value = true
	}

	const openDataFactorySelectorForScript = (field) => {
		currentScriptField.value = field
		currentAssertion.value = null
		currentAssertionField.value = ''
		currentAssertionIndex.value = -1
		showDataFactorySelector.value = true
	}

	const openVariableHelper = (field) => {
		currentEditingField.value = field
		showVariableHelper.value = true
	}

	const openDataFactorySelectorForBody = (field) => {
		currentBodyField.value = field
		currentAssertion.value = null
		currentAssertionField.value = ''
		currentAssertionIndex.value = -1
		currentScriptField.value = ''
		showDataFactorySelector.value = true
	}

	const openVariableHelperForAssertion = (assertion, field, index) => {
		currentAssertion.value = assertion
		currentAssertionField.value = field
		currentAssertionIndex.value = index
		showVariableHelper.value = true
	}

	const insertVariable = (variable) => {
		if (currentEditingField.value) {
			const example = variable.example

			if (currentEditingField.value === 'rawBody') {
				const currentValue = rawBody.value || ''
				if (!currentValue) {
					rawBody.value = example
				} else {
					rawBody.value = currentValue + example
				}
			} else if (currentEditingField.value === 'pre_request_script') {
				const currentValue = selectedRequest.value.pre_request_script || ''
				if (!currentValue) {
					selectedRequest.value.pre_request_script = example
				} else {
					selectedRequest.value.pre_request_script = currentValue + example
				}
			} else if (currentEditingField.value === 'post_request_script') {
				const currentValue = selectedRequest.value.post_request_script || ''
				if (!currentValue) {
					selectedRequest.value.post_request_script = example
				} else {
					selectedRequest.value.post_request_script = currentValue + example
				}
			}

			ElMessage.success(`已插入变量: ${variable.name}`)
			showVariableHelper.value = false
		} else if (currentAssertion.value) {
			const example = variable.example
			const field = currentAssertionField.value

			if (field) {
				const currentValue = currentAssertion.value[field] || ''
				if (!currentValue) {
					currentAssertion.value[field] = example
				} else {
					currentAssertion.value[field] = currentValue + example
				}

				ElMessage.success(`已插入变量: ${variable.name}`)
				showVariableHelper.value = false
			}
		}
	}

	const handleDataFactorySelect = (record) => {
		if (!record || !record.output_data) return

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

		// 如果是断言字段
		if (currentAssertion.value) {
			currentAssertion.value[currentAssertionField.value] = valueToSet
			ElMessage.success(`已引用数据工厂数据到断言: ${record.tool_name}`)
		}
		// 如果是Body字段
		else if (currentBodyField.value) {
			if (currentBodyField.value === 'rawBody') {
				rawBody.value = valueToSet
			}
			ElMessage.success(`已引用数据工厂数据到Body: ${record.tool_name}`)
		}
		// 如果是脚本字段
		else if (currentScriptField.value && selectedRequest.value) {
			// 将值插入到脚本中
			const insertText =
				`\n// 来自数据工厂: ${record.tool_name}\nconst ${record.tool_name.replace(/\s+/g, '_')} = ${JSON.stringify(valueToSet)}\n`
			selectedRequest.value[currentScriptField.value] += insertText
			ElMessage.success(`已引用数据工厂数据到脚本: ${record.tool_name}`)
		}

		showDataFactorySelector.value = false
	}

	// WebSocket消息处理函数
	const handleWebSocketFileUpload = (file) => {
		websocketBinaryFile.value = file.raw
		return false
	}

	const clearWebSocketBinaryFile = () => {
		websocketBinaryFile.value = null
	}

	const sendWebSocketMessage = () => {
		if (websocketConnectionStatus.value !== 'connected') {
			ElMessage.warning(t('apiTesting.messages.warning.pleaseConnect'))
			return
		}

		if (!websocketConnection.value) {
			ElMessage.error(t('apiTesting.messages.error.connectFailed'))
			return
		}

		try {
			let messageToSend = ''

			if (websocketMessageType.value === 'text' || websocketMessageType.value === 'json') {
				messageToSend = websocketMessageContent.value
			} else if (websocketMessageType.value === 'binary' && websocketBinaryFile.value) {
				// 对于二进制文件，需要读取文件内容
				const reader = new FileReader()
				reader.onload = (e) => {
					websocketConnection.value.send(e.target.result)
					addWebSocketMessage('sent', '[Binary Data]')
					ElMessage.success(t('apiTesting.messages.success.binaryMessageSent'))
				}
				reader.onerror = () => {
					ElMessage.error(t('apiTesting.messages.error.readFileFailed'))
				}
				reader.readAsArrayBuffer(websocketBinaryFile.value)
				return
			} else {
				ElMessage.warning(t('apiTesting.messages.warning.pleaseInputContent'))
				return
			}

			websocketConnection.value.send(messageToSend)
			addWebSocketMessage('sent', messageToSend)
			ElMessage.success(t('apiTesting.messages.success.messageSent'))

		} catch (error) {
			const errorMsg = t('apiTesting.messages.error.sendFailed') + ': ' + error.message
			addWebSocketMessage('error', errorMsg)
			ElMessage.error(errorMsg)
		}
	}

	const clearWebSocketMessage = () => {
		websocketMessageContent.value = ''
		websocketBinaryFile.value = null
		websocketMessageType.value = 'text'
	}

	// WebSocket消息历史记录相关方法
	const addWebSocketMessage = (type, content) => {
		const timestamp = new Date().toLocaleTimeString()
		websocketMessages.value.push({
			type,
			content,
			timestamp
		})
	}

	const clearWebSocketMessages = () => {
		websocketMessages.value = []
	}

	const isJsonString = (str) => {
		try {
			JSON.parse(str)
			return true
		} catch (e) {
			return false
		}
	}

	const formatJson = (str) => {
		try {
			return JSON.stringify(JSON.parse(str), null, 2)
		} catch (e) {
			return str
		}
	}

	// WebSocket连接管理函数
	const toggleWebSocketConnection = () => {
		if (websocketConnectionStatus.value === 'disconnected') {
			connectWebSocket()
		} else {
			disconnectWebSocket()
		}
	}

	const connectWebSocket = () => {
		if (!selectedRequest.value || !selectedRequest.value.url) {
			ElMessage.warning(t('apiTesting.messages.warning.pleaseInputUrl'))
			return
		}

		websocketConnectionStatus.value = 'connecting'

		try {
			// 替换环境变量
			let url = selectedRequest.value.url
			if (selectedEnvironment.value) {
				const env = environments.value.find(e => e.id === selectedEnvironment.value)
				if (env && env.variables) {
					Object.entries(env.variables).forEach(([key, value]) => {
						url = url.replace(`{{${key}}}`, value.currentValue || value.initialValue || '')
					})
				}
			}

			// 创建WebSocket连接
			websocketConnection.value = new WebSocket(url)

			websocketConnection.value.onopen = () => {
				websocketConnectionStatus.value = 'connected'
				// 添加连接成功的特殊消息
				addWebSocketMessage('connected', t('apiTesting.messages.info.websocketConnectedTo', {
					url
				}))
				ElMessage.success(t('apiTesting.messages.success.connect'))
			}

			websocketConnection.value.onmessage = (event) => {
				// 处理接收到的消息
				console.log('WebSocket message received:', event.data)
				addWebSocketMessage('received', event.data)
				ElMessage.info(t('apiTesting.messages.info.websocketMessageReceived'))
			}

			websocketConnection.value.onclose = () => {
				websocketConnectionStatus.value = 'disconnected'
				addWebSocketMessage('info', t('apiTesting.messages.info.websocketClosed'))
				ElMessage.info(t('apiTesting.messages.info.websocketClosed'))
			}

			websocketConnection.value.onerror = (error) => {
				websocketConnectionStatus.value = 'disconnected'
				const errorMsg = t('apiTesting.messages.error.websocketError') + ': ' + (error.message || '')
				addWebSocketMessage('error', errorMsg)
				ElMessage.error(errorMsg)
			}

		} catch (error) {
			websocketConnectionStatus.value = 'disconnected'
			const errorMsg = t('apiTesting.messages.error.connectFailed') + ': ' + error.message
			addWebSocketMessage('error', errorMsg)
			ElMessage.error(errorMsg)
		}
	}

	const disconnectWebSocket = () => {
		if (websocketConnection.value) {
			websocketConnection.value.close()
			websocketConnection.value = null
		}
		websocketConnectionStatus.value = 'disconnected'
		// 清空消息历史
		clearWebSocketMessages()
	}

	const createEmptyRequest = async () => {
		// 检查是否有选中的项目
		if (!selectedProject.value) {
			ElMessage.warning(t('apiTesting.messages.warning.pleaseSelectProject'))
			return
		}

		// 检查是否有可用的集合
		if (!flatCollections.value || flatCollections.value.length === 0) {
			ElMessage.warning(t('apiTesting.messages.warning.pleaseCreateCollection'))
			return
		}

		// 使用第一个集合作为默认集合
		const defaultCollection = flatCollections.value[0]

		// 获取当前项目信息
		const currentProject = projects.value.find(p => p.id === selectedProject.value)
		const isWebSocketProject = currentProject && currentProject.project_type === 'WEBSOCKET'

		saving.value = true
		try {
			// 创建一个空的接口，参照"获取宠物列表"的样式
			const data = {
				name: '新建接口',
				method: isWebSocketProject ? 'CONNECT' : 'GET',
				url: isWebSocketProject ? 'ws://{{host}}/websocket' : '{{base_url}}/api/new-endpoint',
				description: '',
				collection: defaultCollection.id,
				project: selectedProject.value,
				request_type: isWebSocketProject ? 'WEBSOCKET' : 'HTTP',
				params: {},
				headers: isWebSocketProject ? {} : {
					'Content-Type': 'application/json'
				},
				body: {},
				auth: {},
				pre_request_script: '',
				post_request_script: ''
			}

			const res = await api.post('/api-testing/requests/', data)
			ElMessage.success(t('apiTesting.messages.success.create'))

			// 重新加载集合和请求
			await Promise.all([loadCollections(), loadRequests()])

			// 自动选中新创建的请求并进入编辑状态
			selectedRequest.value = {
				id: res.data.id,
				name: res.data.name,
				method: res.data.method,
				url: res.data.url,
				description: res.data.description || '',
				collection: res.data.collection,
				project: res.data.project,
				request_type: res.data.request_type,
				params: convertObjectToKeyValueArray(res.data.params || {}),
				headers: convertObjectToKeyValueArray(res.data.headers || {}),
				body: res.data.body || {},
				auth: res.data.auth || {},
				pre_request_script: res.data.pre_request_script || '',
				post_request_script: res.data.post_request_script || ''
			}

			// 默认进入params标签页
			activeTab.value = 'params'

			// 初始化body相关变量
			bodyType.value = 'none'
			rawType.value = 'json'
			formData.value = []
			formUrlEncoded.value = []
			rawBody.value = ''

		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.createFailed'))
			console.error('Create request error:', error)
		} finally {
			saving.value = false
		}
	}

	const sendRequest = async () => {
		if (!selectedRequest.value) return

		// 检查是否为WebSocket接口
		if (selectedRequest.value.request_type === 'WEBSOCKET') {
			ElMessage.warning(t('apiTesting.messages.warning.websocketNotSupported'))
			return
		}

		// 检查是否选择了环境
		if (!selectedEnvironment.value) {
			ElMessage.warning(t('apiTesting.messages.warning.pleaseSelectEnvironment'))
			return
		}

		sending.value = true
		try {
			// 发送请求前先自动保存当前的修改
			await saveRequest()

			// 准备请求体数据
			let bodyData = {}
			if (hasBody.value) {
				if (bodyType.value === 'none') {
					bodyData = {}
				} else if (bodyType.value === 'raw' && rawBody.value) {
					if (rawType.value === 'json') {
						try {
							bodyData = {
								type: 'json',
								data: JSON.parse(rawBody.value)
							}
						} catch (e) {
							bodyData = {
								type: 'raw',
								data: rawBody.value
							}
						}
					} else {
						bodyData = {
							type: 'raw',
							data: rawBody.value
						}
					}
				} else if (bodyType.value === 'form-data') {
					bodyData = {
						type: 'form-data',
						data: formData.value || []
					}
				} else if (bodyType.value === 'x-www-form-urlencoded') {
					bodyData = {
						type: 'x-www-form-urlencoded',
						data: formUrlEncoded.value || []
					}
				} else if (bodyType.value === 'binary') {
					bodyData = {
						type: 'binary',
						data: null
					}
				}
			}

			const requestData = {
				params: convertKeyValueArrayToObject(selectedRequest.value.params || []),
				headers: selectedRequest.value.headers,
				body: bodyData,
				environment_id: selectedEnvironment.value
			}

			const res = await api.post(`/api-testing/requests/${selectedRequest.value.id}/execute/`, requestData)

			// 检查组件是否仍然存在
			if (!selectedRequest.value) return

			console.log('Response data:', res.data)
			console.log('Response headers:', res.data.response_data?.headers)
			response.value = res.data
			ElMessage.success(t('apiTesting.messages.success.requestSent'))
		} catch (error) {
			ElMessage.error(t('apiTesting.messages.error.requestFailed'))
			if (error.response?.data) {
				// 检查组件是否仍然存在
				if (!selectedRequest.value) return
				response.value = error.response.data
			}
		} finally {
			sending.value = false
		}
	}

	// 存储最新的headers数据
	const currentHeaders = ref({})

	const onHeadersUpdate = (newHeaders) => {
		console.log('Headers updated:', newHeaders)
		currentHeaders.value = newHeaders
		if (selectedRequest.value) {
			// 强制更新整个selectedRequest对象以触发响应式更新
			selectedRequest.value = {
				...selectedRequest.value,
				headers: newHeaders
			}
			console.log('Updated selectedRequest.headers:', selectedRequest.value.headers)
		}
	}

	const saveRequest = async () => {
		if (!selectedRequest.value) return

		saving.value = true
		try {
			// 准备保存的数据
			let bodyData = {}

			if (hasBody.value) {
				if (bodyType.value === 'none') {
					bodyData = {}
				} else if (bodyType.value === 'raw' && rawBody.value) {
					if (rawType.value === 'json') {
						try {
							bodyData = {
								type: 'json',
								data: JSON.parse(rawBody.value)
							}
						} catch (e) {
							bodyData = {
								type: 'raw',
								data: rawBody.value
							}
						}
					} else {
						bodyData = {
							type: 'raw',
							data: rawBody.value
						}
					}
				} else if (bodyType.value === 'form-data') {
					// 处理 form-data 类型
					bodyData = {
						type: 'form-data',
						data: formData.value || []
					}
				} else if (bodyType.value === 'x-www-form-urlencoded') {
					// 处理 x-www-form-urlencoded 类型
					bodyData = {
						type: 'x-www-form-urlencoded',
						data: formUrlEncoded.value || []
					}
				} else if (bodyType.value === 'binary') {
					// 处理 binary 类型
					bodyData = {
						type: 'binary',
						data: null
					}
				}
			}

			// 直接从KeyValueEditor组件获取当前headers（完整数组格式）
			let finalHeaders = []
			console.log('headersEditorRef.value:', headersEditorRef.value)
			if (headersEditorRef.value) {
				// 直接访问KeyValueEditor的rows数据，保持完整的数组格式
				const rows = headersEditorRef.value.rows || []
				console.log('Direct access to headers rows:', rows)
				finalHeaders = rows
					.filter(row => row.enabled && row.key && row.key.trim())
					.map(row => ({
						key: row.key.trim(),
						value: row.value || '',
						description: row.description || '',
						enabled: row.enabled !== false
					}))
				console.log('Final headers array format:', finalHeaders)
			} else {
				console.log('headersEditorRef.value is null or undefined')
				// 如果无法获取，使用selectedRequest中的headers
				if (selectedRequest.value.headers && Array.isArray(selectedRequest.value.headers)) {
					finalHeaders = selectedRequest.value.headers.filter(item => item.enabled && item.key)
				}
			}

			console.log('Final headers to save:', finalHeaders)
			console.log('selectedRequest.value.params:', selectedRequest.value.params)

			const data = {
				...selectedRequest.value,
				params: convertKeyValueArrayToObject(selectedRequest.value.params || []),
				headers: finalHeaders, // 保存完整的数组格式，包含description
				body: bodyData
			}

			console.log('Data being sent to backend:', data)

			console.log('Final save data:', data)
			console.log('Headers being saved:', data.headers)

			if (selectedRequest.value.id) {
				await api.put(`/api-testing/requests/${selectedRequest.value.id}/`, data)

				// 检查组件是否仍然存在
				if (!selectedRequest.value) return

				// 更新树中的请求名称，避免重新加载
				const updateRequestName = (collections, requestId, newName) => {
					for (const collection of collections) {
						if (collection.children) {
							const request = collection.children.find(child => child.type === 'request' && child
								.id === requestId)
							if (request) {
								request.name = newName
								return true
							}
						}
						if (collection.children && updateRequestName(collection.children, requestId,
							newName)) {
							return true
						}
					}
					return false
				}

				updateRequestName(collections.value, selectedRequest.value.id, selectedRequest.value.name)
			} else {
				const res = await api.post('/api-testing/requests/', data)

				// 检查组件是否仍然存在
				if (!selectedRequest.value) return

				selectedRequest.value.id = res.data.id
				// 新建的请求需要重新加载树以显示新请求
				await loadCollections()
			}

			ElMessage.success(t('apiTesting.messages.success.save'))
		} catch (error) {
			ElMessage.error('保存失败')
		} finally {
			saving.value = false
		}
	}

	const importCurl = () => {
		showCurlImportDialog.value = true
		curlCommand.value = ''
	}

	const parseAndImportCurl = async () => {
		try {
			if (!curlCommand.value.trim()) {
				ElMessage.warning('请输入CURL命令')
				return
			}

			const requestModel = await RequestModelParser.parseCurl(curlCommand.value)

			if (!selectedRequest.value) {
				createEmptyRequest()
			}

			selectedRequest.value.method = requestModel.method
			selectedRequest.value.url = requestModel.baseURL + requestModel.path
			selectedRequest.value.headers = requestModel.headers
			selectedRequest.value.params = requestModel.query

			if (requestModel.body.mode !== 'none') {
				if (requestModel.body.mode === 'json') {
					bodyType.value = 'raw'
					rawType.value = 'json'
					rawBody.value = requestModel.body.json || ''
				} else if (requestModel.body.mode === 'raw') {
					bodyType.value = 'raw'
					rawType.value = 'text'
					rawBody.value = requestModel.body.raw || ''
				} else if (requestModel.body.mode === 'formdata') {
					bodyType.value = 'form-data'
					formData.value = requestModel.body.formdata || []
				} else if (requestModel.body.mode === 'urlencoded') {
					bodyType.value = 'x-www-form-urlencoded'
					formUrlEncoded.value = requestModel.body.urlencoded || []
				}
			}

			showCurlImportDialog.value = false
			ElMessage.success('CURL命令导入成功')
		} catch (error) {
			console.error('解析CURL命令失败:', error)
			ElMessage.error('解析CURL命令失败: ' + error.message)
		}
	}

	const exportRequest = () => {
		if (!selectedRequest.value) {
			ElMessage.warning('请先选择一个请求')
			return
		}

		generateCode('curl')
	}

	const generateCode = async (language) => {
		if (!selectedRequest.value) {
			ElMessage.warning('请先选择一个请求')
			return
		}

		if (!selectedRequest.value.url) {
			ElMessage.warning('请求URL不能为空')
			return
		}

		try {
			let bodyMode = 'none'

			if (bodyType.value === 'raw') {
				bodyMode = rawType.value === 'json' ? 'json' : 'raw'
			} else if (bodyType.value === 'form-data') {
				bodyMode = 'formdata'
			} else if (bodyType.value === 'x-www-form-urlencoded') {
				bodyMode = 'urlencoded'
			} else if (bodyType.value === 'binary') {
				bodyMode = 'binary'
			}

			const requestModel = {
				method: selectedRequest.value.method || 'GET',
				baseURL: new URL(selectedRequest.value.url || '').origin,
				path: new URL(selectedRequest.value.url || '').pathname,
				query: convertObjectToKeyValueArray(selectedRequest.value.params || {}),
				headers: convertObjectToKeyValueArray(selectedRequest.value.headers || {}),
				body: {
					mode: bodyMode,
					raw: rawBody.value,
					json: rawBody.value,
					formdata: formData.value,
					urlencoded: formUrlEncoded.value
				},
				timeout: 30000
			}

			generatedCode.value = await CodeGenerator.generateCode(requestModel, language)
			codeLanguage.value = language
			showCodeGenerateDialog.value = true
		} catch (error) {
			console.error('生成代码失败:', error)
			ElMessage.error('生成代码失败: ' + error.message)
		}
	}

	const copyGeneratedCode = () => {
		navigator.clipboard.writeText(generatedCode.value).then(() => {
			ElMessage.success('代码已复制到剪贴板')
		}).catch(() => {
			ElMessage.error('复制失败')
		})
	}

	const onBodyTypeChange = () => {
		if (bodyType.value === 'raw') {
			rawType.value = 'json'
			rawBody.value = ''
		}
	}

	const formatResponse = () => {
		if (!response.value?.response_data) {
			ElMessage.warning('没有响应数据可格式化')
			return
		}

		try {
			if (response.value?.response_data?.json) {
				response.value.response_data.body = JSON.stringify(response.value.response_data.json, null, 2)
			}
		} catch (e) {
			ElMessage.error(t('apiTesting.messages.error.formatFailed'))
		}
	}

	const copyResponse = () => {
		if (responseBody.value) {
			navigator.clipboard.writeText(responseBody.value)
			ElMessage.success(t('apiTesting.messages.success.copiedToClipboard'))
		}
	}

	onMounted(() => {
		loadProjects()
	})

	onBeforeUnmount(() => {
		// 清理WebSocket连接
		if (websocketConnection.value) {
			websocketConnection.value.close()
			websocketConnection.value = null
		}
	})
</script>

<style scoped>
	.interface-management {
		height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.interface-layout {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.sidebar {
		width: 300px;
		border-right: 1px solid #e4e7ed;
		background: #f8f9fa;
		overflow: visible;
		display: flex;
		flex-direction: column;
	}

	.sidebar-header {
		padding: 10px;
		border-bottom: 1px solid #e4e7ed;
		display: flex;
		flex-direction: column;
		gap: 10px;
		align-items: stretch;
		position: relative;
	}

	.header-actions {
		display: flex;
		gap: 8px;
		align-items: center;
		flex-wrap: wrap;
	}

	.collection-tree {
		flex: 1;
		overflow: auto;
		padding: 10px;
	}

	.tree-node {
		display: flex;
		align-items: center;
		gap: 5px;
		flex: 1;
	}

	.node-label {
		flex: 1;
	}

	.node-edit {
		flex: 1;
	}

	.node-edit .el-input {
		font-size: 14px;
	}

	.method-tag {
		font-size: 10px;
		padding: 1px 4px;
		border-radius: 2px;
		color: white;
		font-weight: bold;
	}

	.method-tag.get {
		background: #67c23a;
	}

	.method-tag.post {
		background: #409eff;
	}

	.method-tag.put {
		background: #e6a23c;
	}

	.method-tag.delete {
		background: #f56c6c;
	}

	.method-tag.patch {
		background: #909399;
	}

	.search-results {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: white;
		border: 1px solid #e4e7ed;
		border-radius: 4px;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
		z-index: 1000;
		max-height: 400px;
		overflow: auto;
	}

	.search-results-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 15px;
		border-bottom: 1px solid #e4e7ed;
		background: #f5f7fa;
		font-weight: 500;
	}

	.search-results-list {
		padding: 5px 0;
	}

	.search-result-item {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 15px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.search-result-item:hover {
		background: #f5f7fa;
	}

	.search-result-content {
		flex: 1;
		min-width: 0;
	}

	.search-result-name {
		font-weight: 500;
		color: #303133;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.search-result-url {
		font-size: 12px;
		color: #909399;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.main-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.empty-state {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.request-detail {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 20px;
		overflow: auto;
	}

	.request-header {
		margin-bottom: 20px;
		padding: 15px;
		background: #f8f9fa;
		border-radius: 4px;
		border: 1px solid #e4e7ed;
	}

	.request-line {
		display: flex;
		gap: 8px;
		margin-bottom: 12px;
		align-items: center;
	}

	.method-select {
		width: 100px;
	}

	.url-input {
		flex: 1;
	}

	.env-select {
		width: 120px;
	}

	.send-button {
		min-width: 80px;
	}

	.request-meta {
		display: flex;
		gap: 10px;
		align-items: center;
	}

	.name-input {
		flex: 1;
		min-width: 200px;
	}

	.action-buttons {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.request-tabs {
		margin-bottom: 20px;
	}

	.body-container {
		padding: 10px 0;
	}

	.body-content {
		margin-top: 15px;
	}

	.raw-options {
		margin-bottom: 10px;
		display: flex;
		gap: 10px;
		align-items: center;
	}

	.raw-body {
		font-family: 'Courier New', monospace;
	}

	.response-section {
		border-top: 1px solid #e4e7ed;
		padding-top: 20px;
	}

	.response-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
	}

	.response-info {
		display: flex;
		gap: 10px;
		align-items: center;
	}

	.response-time {
		color: #909399;
		font-size: 12px;
	}

	.response-body {
		position: relative;
	}

	.response-actions {
		margin-bottom: 10px;
	}

	.response-content {
		background: #f8f9fa;
		padding: 15px;
		border-radius: 4px;
		font-family: 'Courier New', monospace;
		font-size: 12px;
		max-height: 400px;
		overflow: auto;
		white-space: pre-wrap;
		word-break: break-all;
		line-height: 1.6;
	}

	.jsonpath-extractor {
		margin-bottom: 15px;
		padding: 10px;
		background: #f0f7ff;
		border: 1px solid #b3d8ff;
		border-radius: 4px;
	}

	.jsonpath-input {
		margin-bottom: 10px;
	}

	.jsonpath-result {
		padding: 10px;
		background: white;
		border-radius: 4px;
		border: 1px solid #e4e7ed;
	}

	.jsonpath-result pre {
		margin: 5px 0 0 0;
		font-family: 'Courier New', monospace;
		font-size: 12px;
		color: #303133;
	}

	.response-headers {
		padding: 15px;
		background: #f8f9fa;
		border-radius: 4px;
	}

	.header-row {
		margin-bottom: 5px;
		font-size: 12px;
	}

	/* 断言样式 */
	.assertions-editor {
		padding: 10px;
	}

	.assertions-header {
		margin-bottom: 15px;
	}

	.assertion-item {
		border: 1px solid #e4e7ed;
		border-radius: 4px;
		margin-bottom: 15px;
		background: #fafafa;
	}

	.assertion-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px;
		border-bottom: 1px solid #e4e7ed;
		background: white;
	}

	.assertion-name {
		flex: 1;
		margin-right: 10px;
	}

	.assertion-config {
		padding: 10px;
	}

	.assertion-config .el-select {
		width: 100%;
		margin-bottom: 10px;
	}

	.assertion-params {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.assertion-input {
		margin-bottom: 5px;
	}

	.no-assertions {
		text-align: center;
		padding: 30px;
		color: #909399;
	}

	/* 脚本编辑器样式 */
	.script-editor-container {
		position: relative;
	}

	.script-buttons {
		position: absolute;
		top: 10px;
		right: 10px;
		display: flex;
		gap: 8px;
		z-index: 10;
	}

	.script-factory-btn {
		background-color: #409eff !important;
		border-color: #409eff !important;
		color: white !important;
	}

	.script-factory-btn:hover {
		background-color: #66b1ff !important;
		border-color: #66b1ff !important;
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

	.script-variable-btn {
		background-color: #67c23a;
		border-color: #67c23a;
		color: white;
	}

	.script-variable-btn:hover {
		background-color: #5daf34;
		border-color: #5daf34;
	}

	.variable-helper-btn {
		margin-left: 10px;
		background-color: #67c23a;
		border-color: #67c23a;
		color: white;
	}

	.variable-helper-btn:hover {
		background-color: #5daf34;
		border-color: #5daf34;
	}

	/* WebSocket信息样式 */
	.websocket-info-section {
		padding: 20px;
	}

	.websocket-tips {
		margin-top: 20px;
		padding: 15px;
		background-color: #f5f7fa;
		border-radius: 4px;
	}

	.websocket-tips h4 {
		margin-top: 0;
		margin-bottom: 10px;
	}

	.websocket-tips ul {
		margin: 0;
		padding-left: 20px;
	}

	.websocket-tips li {
		margin-bottom: 5px;
	}

	/* WebSocket消息样式 */
	.message-container {
		padding: 15px;
	}

	.message-input-section {
		margin-bottom: 20px;
	}

	.uploaded-file {
		margin-top: 10px;
		padding: 10px;
		background-color: #f5f7fa;
		border-radius: 4px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	/* WebSocket响应区域样式 */
	.websocket-response-section {
		border-top: 1px solid #e4e7ed;
		padding-top: 20px;
	}

	.websocket-response-section h3 {
		margin-top: 0;
		margin-bottom: 15px;
	}

	.websocket-messages {
		max-height: 400px;
		overflow-y: auto;
		margin-bottom: 15px;
	}

	.websocket-message-item {
		border: 1px solid #e4e7ed;
		border-radius: 4px;
		margin-bottom: 10px;
		background-color: #fafafa;
	}

	.websocket-message-item.sent {
		border-left: 3px solid #409eff;
	}

	.websocket-message-item.received {
		border-left: 3px solid #67c23a;
	}

	.websocket-message-item.info {
		border-left: 3px solid #909399;
	}

	.websocket-message-item.error {
		border-left: 3px solid #f56c6c;
	}

	.websocket-message-item.connected {
		border-left: 3px solid #67c23a;
	}

	.message-header {
		display: flex;
		justify-content: space-between;
		padding: 8px 12px;
		background-color: #f5f7fa;
		border-bottom: 1px solid #e4e7ed;
		font-size: 12px;
	}

	.message-type.sent {
		color: #409eff;
		font-weight: bold;
	}

	.message-type.received {
		color: #67c23a;
		font-weight: bold;
	}

	.message-type.info {
		color: #909399;
		font-weight: bold;
	}

	.message-type.error {
		color: #f56c6c;
		font-weight: bold;
	}

	.message-type.connected {
		color: #67c23a;
		font-weight: bold;
	}

	.message-time {
		color: #909399;
	}

	.message-content {
		padding: 10px 12px;
	}

	.message-content pre {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-all;
		font-family: 'Courier New', monospace;
		font-size: 12px;
		line-height: 1.4;
	}

	/* WebSocket URL样式 */
	.websocket-url {
		flex: 1;
	}

	/* 断言结果样式 */
	.assertions-results {
		padding: 15px;
	}

	.assertion-result-item {
		border: 1px solid #e4e7ed;
		border-radius: 4px;
		margin-bottom: 10px;
		padding: 10px;
	}

	.assertion-result-item.passed {
		border-color: #67c23a;
		background-color: #f0f9ff;
	}

	.assertion-result-item.failed {
		border-color: #f56c6c;
		background-color: #fef0f0;
	}

	.assertion-result-header {
		display: flex;
		align-items: center;
		margin-bottom: 8px;
	}

	.assertion-name {
		margin-left: 8px;
		font-weight: 500;
	}

	.assertion-result-details {
		padding-left: 24px;
		font-size: 12px;
	}

	.result-row {
		display: flex;
		margin-bottom: 4px;
	}

	.label {
		width: 50px;
		font-weight: 500;
	}

	.value {
		flex: 1;
		word-break: break-all;
	}

	.value.error {
		color: #f56c6c;
	}

	.context-menu {
		position: fixed;
		background: white;
		border: 1px solid #e4e7ed;
		border-radius: 4px;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
		padding: 5px 0;
		margin: 0;
		list-style: none;
		z-index: 9999;
	}

	.context-menu li {
		padding: 8px 15px;
		cursor: pointer;
		font-size: 14px;
	}

	.context-menu li:hover {
		background: #f5f7fa;
	}

	/* 变量助手弹窗样式优化 */
	:deep(.el-dialog .el-dialog__body) {
		padding: 0;
	}

	:deep(.el-dialog .el-tabs__content) {
		height: 100%;
	}

	:deep(.el-dialog .el-tab-pane) {
		height: 100%;
	}

	:deep(.el-dialog .el-table) {
		font-size: 13px;
	}

	:deep(.el-dialog .el-table th) {
		background-color: #f5f7fa;
		font-weight: 600;
		color: #303133;
		padding: 12px 0;
	}

	:deep(.el-dialog .el-table td) {
		padding: 12px 0;
	}

	:deep(.el-dialog .el-table .cell) {
		padding: 0 10px;
		line-height: 1.6;
	}

	:deep(.el-dialog .el-table__row) {
		cursor: pointer;
	}

	:deep(.el-dialog .el-table__row:hover) {
		background-color: #f5f7fa;
	}

	:deep(.el-dialog .el-table__row.current-row) {
		background-color: #ecf5ff;
	}

	:deep(.el-dialog .el-tabs__item) {
		padding: 0 20px;
		height: 45px;
		line-height: 50px;
	}
</style>