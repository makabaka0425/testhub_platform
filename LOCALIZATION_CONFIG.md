# 本地化配置指南 (Localization Configuration Guide)

本文档说明如何配置 TestHub 平台的语言和时区设置。

## 配置方式

在 `.env` 文件中设置以下环境变量：

```env
# 语言代码
LANGUAGE_CODE=zh-hans

# 时区
TIME_ZONE=Asia/Shanghai
```

修改后需要重启 Django 服务器才能生效。

---

## 支持的语言代码 (Language Codes)

### 常用语言

| 语言 | 代码 | 说明 |
|------|------|------|
| 英语 (美国) | `en-us` | English (United States) |
| 英语 (英国) | `en-gb` | English (United Kingdom) |
| 简体中文 | `zh-hans` | Chinese (Simplified) |
| 繁体中文 | `zh-hant` | Chinese (Traditional) |
| 日语 | `ja` | Japanese |
| 韩语 | `ko` | Korean |
| 法语 | `fr` | French |
| 德语 | `de` | German |
| 西班牙语 | `es` | Spanish |
| 葡萄牙语 | `pt` | Portuguese |
| 俄语 | `ru` | Russian |
| 意大利语 | `it` | Italian |
| 阿拉伯语 | `ar` | Arabic |
| 印地语 | `hi` | Hindi |

### 其他语言

完整的语言代码列表请参考：
- [Django 支持的语言列表](https://github.com/django/django/blob/main/django/conf/global_settings.py#L50)
- [ISO 639-1 语言代码](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)

---

## 常用时区 (Time Zones)

### 亚洲 (Asia)

| 城市/国家 | 时区代码 | UTC 偏移 |
|----------|---------|---------|
| 上海/北京 (中国) | `Asia/Shanghai` | UTC+8 |
| 香港 | `Asia/Hong_Kong` | UTC+8 |
| 台北 | `Asia/Taipei` | UTC+8 |
| 东京 (日本) | `Asia/Tokyo` | UTC+9 |
| 首尔 (韩国) | `Asia/Seoul` | UTC+9 |
| 新加坡 | `Asia/Singapore` | UTC+8 |
| 曼谷 (泰国) | `Asia/Bangkok` | UTC+7 |
| 河内 (越南) | `Asia/Ho_Chi_Minh` | UTC+7 |
| 雅加达 (印尼) | `Asia/Jakarta` | UTC+7 |
| 吉隆坡 (马来西亚) | `Asia/Kuala_Lumpur` | UTC+8 |
| 马尼拉 (菲律宾) | `Asia/Manila` | UTC+8 |
| 孟买 (印度) | `Asia/Kolkata` | UTC+5:30 |
| 迪拜 (阿联酋) | `Asia/Dubai` | UTC+4 |

### 欧洲 (Europe)

| 城市/国家 | 时区代码 | UTC 偏移 |
|----------|---------|---------|
| 伦敦 (英国) | `Europe/London` | UTC+0/+1 |
| 巴黎 (法国) | `Europe/Paris` | UTC+1/+2 |
| 柏林 (德国) | `Europe/Berlin` | UTC+1/+2 |
| 马德里 (西班牙) | `Europe/Madrid` | UTC+1/+2 |
| 罗马 (意大利) | `Europe/Rome` | UTC+1/+2 |
| 阿姆斯特丹 (荷兰) | `Europe/Amsterdam` | UTC+1/+2 |
| 莫斯科 (俄罗斯) | `Europe/Moscow` | UTC+3 |
| 雅典 (希腊) | `Europe/Athens` | UTC+2/+3 |
| 伊斯坦布尔 (土耳其) | `Europe/Istanbul` | UTC+3 |

### 美洲 (Americas)

| 城市/国家 | 时区代码 | UTC 偏移 |
|----------|---------|---------|
| 纽约 (美国东部) | `America/New_York` | UTC-5/-4 |
| 芝加哥 (美国中部) | `America/Chicago` | UTC-6/-5 |
| 丹佛 (美国山地) | `America/Denver` | UTC-7/-6 |
| 洛杉矶 (美国西部) | `America/Los_Angeles` | UTC-8/-7 |
| 多伦多 (加拿大) | `America/Toronto` | UTC-5/-4 |
| 温哥华 (加拿大) | `America/Vancouver` | UTC-8/-7 |
| 墨西哥城 | `America/Mexico_City` | UTC-6/-5 |
| 圣保罗 (巴西) | `America/Sao_Paulo` | UTC-3/-2 |
| 布宜诺斯艾利斯 (阿根廷) | `America/Argentina/Buenos_Aires` | UTC-3 |

### 大洋洲 (Oceania)

| 城市/国家 | 时区代码 | UTC 偏移 |
|----------|---------|---------|
| 悉尼 (澳大利亚) | `Australia/Sydney` | UTC+10/+11 |
| 墨尔本 (澳大利亚) | `Australia/Melbourne` | UTC+10/+11 |
| 珀斯 (澳大利亚) | `Australia/Perth` | UTC+8 |
| 奥克兰 (新西兰) | `Pacific/Auckland` | UTC+12/+13 |

### 非洲 (Africa)

| 城市/国家 | 时区代码 | UTC 偏移 |
|----------|---------|---------|
| 开罗 (埃及) | `Africa/Cairo` | UTC+2 |
| 约翰内斯堡 (南非) | `Africa/Johannesburg` | UTC+2 |
| 拉各斯 (尼日利亚) | `Africa/Lagos` | UTC+1 |
| 内罗毕 (肯尼亚) | `Africa/Nairobi` | UTC+3 |

### UTC 标准时间

| 名称 | 时区代码 | 说明 |
|------|---------|------|
| UTC | `UTC` | 协调世界时 (Coordinated Universal Time) |
| GMT | `GMT` | 格林威治标准时间 |

---

## 完整时区列表

完整的时区列表请参考：
- [IANA 时区数据库](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- [Python pytz 时区列表](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568)

---

## 配置示例

### 示例 1: 英语 + 纽约时区
```env
LANGUAGE_CODE=en-us
TIME_ZONE=America/New_York
```

### 示例 2: 日语 + 东京时区
```env
LANGUAGE_CODE=ja
TIME_ZONE=Asia/Tokyo
```

### 示例 3: 简体中文 + 上海时区 (默认)
```env
LANGUAGE_CODE=zh-hans
TIME_ZONE=Asia/Shanghai
```

### 示例 4: 英语 + UTC 时区
```env
LANGUAGE_CODE=en-us
TIME_ZONE=UTC
```

---

## 验证配置

修改配置后，重启 Django 服务器：

```bash
# 停止当前服务器 (Ctrl+C)
# 然后重新启动
source .venv/bin/activate
python manage.py runserver
```

访问 Django Admin 后台 (http://localhost:8000/admin/) 查看语言和时间显示是否正确。

---

## 注意事项

1. **语言包支持**：Django 内置支持多种语言，但某些语言可能需要额外的翻译文件
2. **夏令时**：某些时区会自动处理夏令时 (DST)，如 `America/New_York` 会在夏季自动切换
3. **数据库时间**：Django 使用 `USE_TZ=True` 时，所有日期时间会以 UTC 存储在数据库中，显示时自动转换为配置的时区
4. **前端同步**：修改后端时区后，可能需要同步修改前端的时区配置

---

## 相关文档

- [Django 国际化文档](https://docs.djangoproject.com/en/4.2/topics/i18n/)
- [Django 时区设置](https://docs.djangoproject.com/en/4.2/topics/i18n/timezones/)
- [Python datetime 时区处理](https://docs.python.org/3/library/datetime.html)
