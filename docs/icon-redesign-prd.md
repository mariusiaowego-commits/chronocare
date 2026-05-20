# ChronoCare Icon Redesign — 设计文档 & PRD

> 版本: v1.0 | 日期: 2026-05-20 | 状态: 待评估

## 1. 背景

当前 ChronoCare 前端使用原始 emoji 作为 icon（共 46 处），存在以下问题：
- emoji 在不同平台/浏览器渲染不一致
- 深色模式下 emoji 颜色不可控，对比度差
- 风格不统一，显得不够专业
- 部分 emoji 在小尺寸下可读性差

## 2. 方案选型

### 决策: Lucide Icons (Outline 风格)

| 维度 | 选择 |
|------|------|
| Icon 库 | [Lucide](https://lucide.dev) — 1500+ 图标，MIT 协议 |
| 风格 | Outline (线性描边)，1.5px stroke，圆角端点 |
| 颜色 | 单色，通过 Tailwind `text-*` 类控制 |
| 尺寸 | 基准 20px（导航/行内），24px（标题），32px（大卡片） |
| 深色模式 | 同一 icon，颜色类跟随 dark: 前缀自动切换 |

### 选型理由
1. **最轻量** — 只需引入使用的 icon，无需全量打包
2. **Tailwind 原生配合** — stroke 颜色 = `currentColor`，直接用 `text-*` 控制
3. **Jinja2 友好** — 纯 SVG，可通过 macro 或 sprite 方式集成
4. **现代审美** — 线性风格是当前 SaaS 主流（Linear、Vercel、Notion）
5. **深色模式零成本** — `text-slate-600 dark:text-slate-300` 一行搞定

## 3. Icon 映射表

### 3.1 导航 Sidebar（base.html）

| 原 emoji | 新 icon | Lucide 名称 | 尺寸 | 语义 |
|----------|---------|-------------|------|------|
| 🩺 | SVG | `heart-pulse` | 24px | Logo 区品牌 icon |
| 📊 | SVG | `layout-dashboard` | 20px | 仪表盘 |
| 👤 | SVG | `users` | 20px | 人员档案 |
| 🩸 | SVG | `droplet` | 20px | 血糖监控 |
| 📈 | SVG | `trending-up` | 20px | 趋势分析 |
| 🏥 | SVG | `hospital` | 20px | 就诊记录 |
| 📄 | SVG | `file-text` | 20px | 就医 OCR |
| 🌙/☀️ | SVG | `moon` / `sun` | 20px | 深色模式切换 |

### 3.2 Dashboard（dashboard.html）

| 原 emoji | 新 icon | Lucide 名称 | 尺寸 | 语义 |
|----------|---------|-------------|------|------|
| 📊 | SVG | `layout-dashboard` | 32px | 页面标题 |
| 👨/👩/👤 | SVG | `user` / `user-round` | 32/48px | 人物头像 |
| 🚨 | SVG | `circle-alert` | 20px | 严重预警 |
| ⚠️ | SVG | `triangle-alert` | 20px | 一般预警 |
| ✏️ | SVG | `pencil` | 16px | 编辑按钮 |
| 🏥 | SVG | `hospital` | 24px | 就诊卡片 |
| 📄 | SVG | `file-text` | 24px | 记录卡片 |
| 📋 | SVG | `clipboard-list` | 24px | 报告卡片 |
| 📅 | SVG | `calendar` | 16px | 复诊日期 |
| 👨‍⚕️ | SVG | `stethoscope` | 16px | 医生 |

### 3.3 血糖页面（blood_sugar/）

| 原 emoji | 新 icon | Lucide 名称 | 尺寸 | 语义 |
|----------|---------|-------------|------|------|
| 👤 | SVG | `user` | 16px | 人员选择器 |
| 📈 | SVG | `trending-up` | 24px | 趋势标题 |
| 📅 | SVG | `calendar` | 16px | 日期筛选 |
| 🎯 | SVG | `target` | 20px | 目标范围 |
| 📊 | SVG | `bar-chart-3` | 20px | 统计数据 |
| ⚠️ | SVG | `triangle-alert` | 16px | 血糖预警 |
| ✓ | SVG | `check` | 16px | 正常值 |
| ✓ | SVG | `check` | 16px | 保存按钮 |

### 3.4 就诊页面（visit/）

| 原 emoji | 新 icon | Lucide 名称 | 尺寸 | 语义 |
|----------|---------|-------------|------|------|
| 🏥 | SVG | `hospital` | 24/48px | 标题/空状态 |
| 👤 | SVG | `user` | 16px | 患者信息 |
| 👨‍⚕️ | SVG | `stethoscope` | 16px | 医生信息 |
| 📅 | SVG | `calendar` | 16px | 复诊日期 |
| ✏️ | SVG | `pencil` | 16px | 编辑就诊 |
| ✓ | SVG | `check` | 16px | 保存按钮 |

### 3.5 就医记录页面（medical_record/）

| 原 emoji | 新 icon | Lucide 名称 | 尺寸 | 语义 |
|----------|---------|-------------|------|------|
| 📋 | SVG | `clipboard-list` | 24px | 记录详情标题 |
| 📷 | SVG | `camera` | 20px | 图片上传 |
| ✏️ | SVG | `pencil` | 16px | 编辑记录 |
| 📄 | SVG | `file-plus` | 24px | 新增记录 |
| 📤 | SVG | `upload` | 32px | 上传区域 |
| 📋 | SVG | `clipboard-list` | 16px | 就医记录选项 |
| 🧪 | SVG | `flask-conical` | 16px | 化验报告选项 |
| 💊 | SVG | `pill` | 16px | 处方选项 |
| 📝 | SVG | `file-pen` | 16px | 医嘱选项 |
| ✓ | SVG | `check` | 16px | 保存按钮 |

### 3.6 通用组件

| 原 | 新 icon | Lucide 名称 | 场景 |
|----|---------|-------------|------|
| ✓ | `check` | toast success |
| ✗ | `x` | toast error |
| ⚠ | `triangle-alert` | toast warning |
| ℹ | `info` | toast info |
| 菜单 SVG | `menu` | 移动端汉堡菜单 |

## 4. 技术方案

### 4.1 集成方式: Jinja2 Macro + Inline SVG

```jinja2
{# templates/macros/icon.html #}
{% macro icon(name, size=20, class='') %}
<svg class="inline-block {{ class }}" width="{{ size }}" height="{{ size }}"
     viewBox="0 0 24 24" fill="none" stroke="currentColor"
     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
  {% include 'icons/' + name + '.svg' ignore missing %}
</svg>
{% endmacro %}
```

使用方式:
```jinja2
{% from 'macros/icon.html' import icon %}
{{ icon('layout-dashboard', 20, 'text-slate-600 dark:text-slate-300') }} 仪表盘
```

### 4.2 SVG 文件管理

```
src/chronocare/templates/
├── macros/
│   └── icon.html              # Jinja2 macro 定义
├── icons/                     # Lucide SVG 片段 (不含外层<svg>)
│   ├── layout-dashboard.svg
│   ├── users.svg
│   ├── droplet.svg
│   ├── trending-up.svg
│   ├── hospital.svg
│   ├── file-text.svg
│   ├── moon.svg
│   ├── sun.svg
│   ├── user.svg
│   ├── pencil.svg
│   ├── calendar.svg
│   ├── circle-alert.svg
│   ├── triangle-alert.svg
│   ├── check.svg
│   ├── x.svg
│   ├── info.svg
│   ├── menu.svg
│   ├── heart-pulse.svg
│   ├── stethoscope.svg
│   ├── target.svg
│   ├── bar-chart-3.svg
│   ├── clipboard-list.svg
│   ├── camera.svg
│   ├── upload.svg
│   ├── file-plus.svg
│   ├── flask-conical.svg
│   ├── pill.svg
│   └── file-pen.svg
```

### 4.3 颜色规范

| 语义 | Light | Dark | Tailwind 类 |
|------|-------|------|------------|
| 默认 | #64748b | #94a3b8 | `text-slate-500 dark:text-slate-400` |
| 强调 | #0284c7 | #38bdf8 | `text-sky-600 dark:text-sky-400` |
| 警告 | #f59e0b | #fbbf24 | `text-amber-500 dark:text-amber-400` |
| 危险 | #ef4444 | #f87171 | `text-red-500 dark:text-red-400` |
| 成功 | #14b8a6 | #2dd4bf | `text-teal-500 dark:text-teal-400` |

### 4.4 不改动的部分

- Chart.js 图表内的 icon（由 Chart.js 自己管理）
- 数据库/后端返回的 alert.icon 字段（需同步改为 Lucide 名称）

## 5. 实施计划

| 步骤 | 内容 | 估时 |
|------|------|------|
| 1 | 下载 28 个 Lucide SVG 文件到 `templates/icons/` | 10min |
| 2 | 创建 `macros/icon.html` Jinja2 macro | 5min |
| 3 | 替换 base.html — 导航 + 主题切换 + 菜单 + toast | 15min |
| 4 | 替换 dashboard.html | 10min |
| 5 | 替换 blood_sugar/list.html + trend.html + form.html | 10min |
| 6 | 替换 visit/list.html + form.html | 10min |
| 7 | 替换 medical_record/detail.html + form.html + list.html | 10min |
| 8 | 后端 services 中 alert.icon 字段改为 Lucide 名称 | 5min |
| 9 | 测试深色模式 + 移动端 + 所有页面 | 10min |
| **总计** | | **~85min** |

## 6. 验收标准

- [ ] 所有 46 处 emoji 替换为 Lucide SVG
- [ ] 深色模式下所有 icon 清晰可见，对比度 ≥ 4.5:1
- [ ] 移动端 icon 不溢出、不错位
- [ ] 页面加载无明显延迟（SVG 文件总体积 < 30KB）
- [ ] Toast 通知 icon 正常显示
- [ ] 血糖预警 icon 颜色正确（红=危险，黄=警告，绿=正常）
