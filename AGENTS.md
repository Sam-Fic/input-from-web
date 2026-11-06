# AGENTS 约束（UI / @m3e/web 2.7.9）

本文件适用于所有涉及本项目 WebUI 的改动。**不满足以下要求时，改动视为未完成。**

## 1. 硬性规则

- 动手改 UI 组件前，必须查阅官方文档或组件源码，确认属性名、取值、插槽、默认数值真实存在。
- 禁止凭印象写组件标签、属性或数值；不确定就查 `dist/*.js` 源码。
- 不得为了“看起来更好”而临时发明属性、slot 或 token。

## 2. 必须使用官方组件库

- 本项目 UI 组件库固定为 `@m3e/web` 2.7.9。
- 能用 `m3e-*` 组件解决的就不要自绘。
- 确需自绘（例如组件库不支持多行 textarea）时：
  - 必须写明原因；
  - 尽量复用 `--md-sys-color-*` 与官方规范值；
  - 不能假装它是官方组件。

## 3. 禁止随意覆盖默认样式

- 不得叠加圆角、底色、间距、hover 色等纯外观覆盖。
- 只允许两类补充，并必须注释理由：
  - **布局必要**：防压缩、防换行、防溢出、安全区；
  - **可访问性**：焦点、可访问名称、状态语义。
- 组件默认已提供的外观（shape、state layer、elevation、typography）不要重写。

## 4. 数值必须来自官方（项目已核实速查表）

以下数值来自 `@m3e/web` 2.7.9 组件源码，不是估算：

| 组件 | 官方默认值 |
|---|---|
| `m3e-list-item` | 单行 / 双行 / 三行最小高度 **56 / 72 / 88px**；左右 padding **16px**；列间距 **16px**；正文 bodyLarge **16 / 24px** |
| `m3e-switch` | 轨道 **52 × 32px**；图标 **16px** |
| `m3e-button` large | 容器高 **96px**；图标 **32px**；按下 shape-morph **16px** |
| `m3e-button` text small | 容器高 **40px**；图标 **20px** |
| `m3e-icon-button` | 默认 small：**40px**；图标 **24px** |
| `m3e-menu` | 容器内边距 **4px**；min-width **112px**；max-width **280px**；项高 **44px**；项内边距 **12px**；图标 **20px**；elevation **level 3**；shape **12 / 16px** |
| `m3e-bottom-sheet` | header titleLarge **22 / 28px**；body 左右 **16px**、底部 **8px** |

多行列表项的行数由组件自行测量，不要手动写死行高或模拟 `--two-line` 状态。

## 5. 颜色

- UI 色值只能使用 `--md-sys-color-*` 语义角色，禁止硬编码 hex / rgba。
- 配色体系为 **M3 Expressive**：`SchemeExpressive` + `MaterialDynamicColors`。
- 主题种子固定为 `#6750A4`；`<m3e-theme color>` 只接受种子 hex，属于配置值，不是 UI 色。
- `<meta name="theme-color">` 的初始值必须在运行时同步为 `--md-sys-color-*` 的实际值。

## 6. 可访问性底线

- 每个交互控件必须有可访问名称。
- 键盘可达；Enter / Space / Esc 行为符合组件语义。
- 焦点必须可见；`<m3e-theme>` 必须保留 `strong-focus`。
- 状态语义正确：`aria-expanded` / `aria-checked` / `role`。
- 文本对比度满足 WCAG AA；边框、焦点环至少 3:1。

## 7. 自检清单

- [ ] 属性是否真实存在于组件源码？
- [ ] 插槽是否为官方推荐用法？
- [ ] 数值是否等于官方默认值？
- [ ] 是否存在多余的外观覆盖？
- [ ] 颜色是否全部走 `--md-sys-color-*`？
- [ ] 键盘路径和读屏语义是否实际验证过？
- [ ] 焦点环是否可见（`strong-focus` 是否保留）？

## 8. 依据位置

- `@m3e/web` 源码：`node_modules/@m3e/web/dist/*.js`，或 CDN 上同版本 `dist/*.js`。
- Material 3 / M3 Expressive 官方规范。
- `@material/material-color-utilities` 的 `SchemeExpressive` 与 `MaterialDynamicColors`。
- 组件默认值优先看源码里的 `M3e*Element.styles`、`tokens`、`@attr`、`@slot`、`@cssprop`。

## 9. 完成标准

不满足上述要求时，改动视为未完成。
