---
version: alpha
name: ChronoCare
description: 温暖专业的老年健康管理平台 — 信任感与关怀感并重，大字号高对比度，面向中老年用户群体。
colors:
  primary: "#0F766E"
  primary-light: "#14B8A6"
  primary-dark: "#115E59"
  secondary: "#D97706"
  secondary-light: "#F59E0B"
  secondary-dark: "#B45309"
  neutral: "#F8F6F3"
  neutral-dark: "#1E293B"
  surface: "#FFFFFF"
  surface-elevated: "#FFFFFF"
  background: "#F1F0ED"
  success: "#059669"
  error: "#DC2626"
  warning: "#D97706"
  info: "#0284C7"
  text-primary: "#1E293B"
  text-secondary: "#64748B"
  text-muted: "#94A3B8"
  border: "#E2E1DE"
  border-light: "#F1F0ED"
typography:
  h1:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 2rem
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  h2:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  h3:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 1.25rem
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 1.125rem
    fontWeight: 400
    lineHeight: 1.7
  body-md:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: 1.4
  label:
    fontFamily: "Inter, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif"
    fontSize: 0.875rem
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: 6px
  md: 10px
  lg: 16px
  xl: 20px
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
elevation:
  low: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)"
  medium: "0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)"
  high: "0 12px 32px rgba(0,0,0,0.12), 0 4px 8px rgba(0,0,0,0.06)"
components:
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: 24px
  card-interactive-hover:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: 24px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.primary-dark}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 12px
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: 12px
  sidebar:
    backgroundColor: "{colors.surface}"
    width: 256px
  sidebar-active:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  input-focus:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: 12px
  badge:
    rounded: "{rounded.full}"
    padding: "4px 10px"
  alert-warning:
    backgroundColor: "#FEF3C7"
    textColor: "#92400E"
    rounded: "{rounded.lg}"
  alert-danger:
    backgroundColor: "#FEE2E2"
    textColor: "#991B1B"
    rounded: "{rounded.lg}"
---

## Overview

ChronoCare 是面向中老年用户的健康管理平台。设计语言强调**温暖、信任、清晰**。

核心原则：
- **大即是好** — 字号 ≥16px，触控目标 ≥44px，行高宽松
- **暖色基调** — 深青色 (Teal) 主色传递专业信任，琥珀色 (Amber) 点缀温暖关怀
- **高对比度** — 所有文本满足 WCAG AA 标准 (4.5:1)，关键元素满足 AAA (7:1)
- **克制动效** — GSAP 交互动效提升体验，但不干扰操作

## Colors

- **Primary (#0F766E):** 深青色 — 专业医疗感，用于导航激活态、主按钮、标题
- **Secondary (#D97706):** 琥珀色 — 温暖关怀感，用于警示、强调、数据高亮
- **Neutral (#F8F6F3):** 暖灰底色 — 比纯白更柔和，减少视觉疲劳
- **Surface (#FFFFFF):** 卡片白色 — 与暖灰底形成自然层次
- **Success (#059669):** 翡翠绿 — 血糖正常、操作成功
- **Error (#DC2626):** 玫瑰红 — 血糖异常、操作失败、健康预警
- **Text Primary (#1E293B):** 深石板色 — 主要文字，高对比度
- **Text Secondary (#64748B):** 中灰 — 辅助信息

## Typography

采用 Inter (拉丁) + Noto Sans SC (中文) 双字体方案。Inter 提供优秀的
数字和英文字母可读性，Noto Sans SC 确保中文在所有平台一致渲染。

- **h1 (2rem/bold):** 页面标题，带 -0.025em 字间距收紧
- **h2 (1.5rem/semibold):** 区块标题
- **h3 (1.25rem/semibold):** 卡片标题
- **body-lg (1.125rem):** 老年用户的默认正文大小
- **body-md (1rem):** 标准正文
- **body-sm (0.875rem):** 辅助信息、元数据
- **label (0.875rem/semibold):** 表单标签

## Layout

- 侧边栏固定宽度 256px，主内容区自适应
- 内容最大宽度 max-w-7xl (80rem)
- 卡片间距 24px (gap-6)
- 移动端 (<1024px) 侧边栏折叠为抽屉

## Elevation & Depth

三层阴影体系：
- **Low:** 卡片默认态 (subtle shadow)
- **Medium:** 卡片悬浮态、下拉菜单
- **High:** 模态框、弹出层

背景色 `#F1F0ED` (暖灰) 与白色卡片自然形成层次，减少对阴影的依赖。

## Shapes

- **sm (6px):** 按钮、输入框、badge
- **md (10px):** 小卡片、标签
- **lg (16px):** 大卡片、面板
- **xl (20px):** 弹窗、模态框
- **full (9999px):** 药丸形按钮、头像

## Components

`card` 是最基础的容器组件，白色背景 + 暖灰边框 + lg 圆角。

`button-primary` 使用 primary 色，hover 时加深到 primary-dark。
`button-secondary` 使用白色底 + primary 文字，用于次要操作。

`sidebar` 固定 256px 宽，白色背景。active 项用 primary 色填充 + 白色文字。

`input` 使用 surface 底色，focus 时显示 primary 色 ring。
表单标签用 label 字体样式 (semibold)。

`badge` 全圆角，用于血糖类型标签 (空腹/餐前/餐后/睡前/随机)。

`alert-warning` 琥珀色背景，用于健康预警。
`alert-danger` 玫瑰红背景，用于严重异常。

## Do's and Don'ts

**Do:**
- 使用暖灰 (#F1F0ED) 作为页面背景，不要用纯白
- 血糖值用颜色编码：正常=翡翠绿，偏高=琥珀，危险=玫红
- 所有可点击元素至少 44px 高度
- 使用 SVG 图标 (Lucide)，不要用 emoji

**Don't:**
- 不要在同一页面使用超过 3 种强调色
- 不要用纯黑 (#000) 文字，用 #1E293B
- 不要在列表/表格上加过多动效，保持克制
- 不要用小于 14px 的字号
