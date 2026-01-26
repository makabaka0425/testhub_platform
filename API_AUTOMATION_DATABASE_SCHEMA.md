# 接口自动化测试用例设计 - 数据库表结构

## 概述

接口自动化测试用例存储在TestHub平台的API模块中，使用MySQL数据库存储。主要包括4个核心表和相关的辅助表。

## 核心表结构

### 1. api_test_suites (测试套件表)

存储接口自动化测试套件的基本信息。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| project_id | ForeignKey | 关联项目ID | 指向 api_projects 表 |
| name | CharField(200) | 套件名称 | 必填 |
| description | TextField | 套件描述 | 可选 |
| environment_id | ForeignKey | 执行环境ID | 指向 api_environments 表，可为空 |
| created_by_id | ForeignKey | 创建者ID | 指向 users 表，必填 |
| created_at | DateTimeField | 创建时间 | 自动生成 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

**数据库表名**: `api_test_suites`

**排序**: 按创建时间降序排列

---

### 2. api_test_suite_requests (套件请求关联表)

存储测试套件中包含的具体API请求及其执行配置。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| test_suite_id | ForeignKey | 测试套件ID | 指向 api_test_suites 表 |
| request_id | ForeignKey | API请求ID | 指向 api_requests 表 |
| order | IntegerField | 执行顺序 | 用于排序请求执行顺序，默认为0 |
| assertions | JSONField | 断言规则 | JSON格式，默认为空列表 |
| enabled | BooleanField | 是否启用 | 布尔值，默认为True |

**数据库表名**: `api_test_suite_requests`

**唯一约束**: test_suite_id + request_id (同一套件中不能有重复请求)

**排序**: 按执行顺序排列

---

### 3. api_requests (API请求表)

存储具体的API请求定义，可被多个测试套件引用。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| collection_id | ForeignKey | 所属集合ID | 指向 api_collections 表 |
| name | CharField(200) | 请求名称 | 必填 |
| description | TextField | 请求描述 | 可选 |
| request_type | CharField(20) | 请求类型 | 选项: 'HTTP', 'WebSocket'，默认'HTTP' |
| method | CharField(10) | HTTP方法 | 选项: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS |
| url | TextField | 请求URL | 必填，支持环境变量占位符 |
| headers | JSONField | 请求头 | JSON格式，默认为空对象 |
| params | JSONField | URL参数 | JSON格式，默认为空对象 |
| body | JSONField | 请求体 | JSON格式，默认为空对象 |
| auth | JSONField | 认证信息 | JSON格式，支持多种认证方式 |
| pre_request_script | TextField | 请求前脚本 | 在发送请求前执行的脚本 |
| post_request_script | TextField | 请求后脚本 | 在收到响应后执行的脚本 |
| assertions | JSONField | 断言规则 | JSON格式，默认为空列表 |
| order | IntegerField | 排序 | 用于显示顺序，默认为0 |
| created_by_id | ForeignKey | 创建者ID | 指向 users 表 |
| created_at | DateTimeField | 创建时间 | 自动生成 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

**数据库表名**: `api_requests`

**排序**: 按执行顺序和创建时间排列

---

### 4. api_collections (API集合表)

对API请求进行逻辑分组，支持多级目录结构。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| project_id | ForeignKey | 所属项目ID | 指向 api_projects 表 |
| parent_id | ForeignKey | 父级集合ID | 自引用，支持嵌套，可为空 |
| name | CharField(200) | 集合名称 | 必填 |
| description | TextField | 集合描述 | 可选 |
| order | IntegerField | 排序 | 用于显示顺序，默认为0 |
| created_at | DateTimeField | 创建时间 | 自动生成 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

**数据库表名**: `api_collections`

**排序**: 按排序字段和创建时间排列

---

## 辅助表结构

### 5. api_environments (环境变量表)

存储不同执行环境的配置和变量。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| name | CharField(200) | 环境名称 | 必填 |
| scope | CharField(10) | 作用域 | 选项: 'GLOBAL'(全局), 'LOCAL'(局部) |
| variables | JSONField | 环境变量 | JSON格式存储各种环境变量 |
| is_active | BooleanField | 是否激活 | 布尔值，默认为False |
| project_id | ForeignKey | 关联项目 | 指向 api_projects 表，可为空 |
| created_by_id | ForeignKey | 创建者ID | 指向 users 表 |
| created_at | DateTimeField | 创建时间 | 自动生成 |
| updated_at | DateTimeField | 更新时间 | 自动更新 |

**数据库表名**: `api_environments`

---

### 6. api_request_histories (请求历史表)

记录每次API请求的执行历史和结果。

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| id | BigAutoField | 主键 | 自增 |
| request_id | ForeignKey | API请求ID | 指向 api_requests 表 |
| environment_id | ForeignKey | 使用环境ID | 指向 api_environments 表，可为空 |
| request_data | JSONField | 请求数据 | JSON格式存储完整请求 |
| response_data | JSONField | 响应数据 | JSON格式存储响应内容 |
| status_code | IntegerField | HTTP状态码 | 可为空 |
| response_time | FloatField | 响应时间 | 单位毫秒(ms)，可为空 |
| error_message | TextField | 错误信息 | 执行出错时的错误描述 |
| assertions_results | JSONField | 断言结果 | JSON格式存储各断言的执行结果 |
| executed_by_id | ForeignKey | 执行者ID | 指向 users 表 |
| executed_at | DateTimeField | 执行时间 | 自动生成 |

**数据库表名**: `api_request_histories`

**排序**: 按执行时间降序排列

---

## 表关系图

```
api_projects (项目)
    │
    ├─── api_collections (集合) ─┐
    │        │                    │ (parent关联)
    │        │
    │        └─── api_requests (请求)
    │                 │
    │                 └─── api_request_histories (请求历史)
    │
    ├─── api_test_suites (测试套件)
    │        │
    │        └─── api_test_suite_requests (套件请求关联) ──┐
    │                                                      │
    │                                                api_requests
    │
    └─── api_environments (环境)
```

---

## 数据流程

### 1. 创建测试用例流程
```
1. 创建项目 (api_projects)
   └─ 创建集合 (api_collections)
      └─ 创建请求 (api_requests)
         └─ 创建测试套件 (api_test_suites)
            └─ 关联请求到套件 (api_test_suite_requests)
```

### 2. 执行测试流程
```
1. 选择测试套件 (api_test_suites)
   ├─ 选择执行环境 (api_environments)
   └─ 遍历套件中的请求 (api_test_suite_requests)
      ├─ 获取请求详情 (api_requests)
      ├─ 执行请求
      ├─ 记录历史 (api_request_histories)
      └─ 验证断言 (assertions)
```

---

## 关键字段说明

### assertions (断言规则)
断言规则以JSON列表格式存储，每个断言包含：
- `type` - 断言类型(response_code, json_path等)
- `expected` - 预期值
- `actual` - 实际值(执行时填充)
- `pass` - 是否通过

### variables (环境变量)
以JSON对象格式存储，例如：
```json
{
  "base_url": "https://api.example.com",
  "api_key": "xxx",
  "timeout": 5000
}
```

### request_data & response_data
完整记录HTTP请求和响应，便于测试结果查询和追踪。

---

## 使用建议

1. **合理设计集合结构** - 使用嵌套集合组织相关的API请求
2. **复用性** - 同一请求可被多个测试套件引用，提高维护效率
3. **环境管理** - 为不同环境配置不同的变量值(开发、测试、预发等)
4. **断言策略** - 每个请求可包含多条断言，确保响应的多个方面都被验证
5. **历史追踪** - 通过请求历史表快速定位问题

---

## 相关Django模型位置

文件: [apps/api_testing/models.py](apps/api_testing/models.py)

所有表对应的Django ORM模型均定义在此文件中。
