# input-from-web

<div align="center">
<img src="icon.svg" alt="input-from-web" width="128" height="128">
</div>

[English](README.md)

---

使用手机的语音听写功能，在 Linux、Windows 或 macOS 桌面端的任意应用中进行输入。

## 动机
手机键盘拥有出色的语音转文本引擎，其表现远超 Linux 桌面端原生的任何方案。本工具填补了这一空白：它在您的计算机上运行一个轻量级的 Web 服务器，您在手机上打开该网页，进行语音听写，文本随后会被注入到桌面端当前获得焦点的应用中。
手机端无需安装任何应用——只需使用浏览器即可。

## 工作原理
```
手机浏览器  ──HTTP POST──>  Python (Flask)  ──> 平台注入器
│                 Linux:   ydotool / wl-copy
│                 Windows: SendInput / 剪贴板
│                 macOS:   AppleScript / pbcopy
启动时打印
包含密钥 Token 的
二维码 URL
```
1. 脚本在您的局域网 IP 上启动一个 Flask Web 服务器
2. 终端中会打印出一个包含随机安全 Token 的 URL 二维码
3. 用手机扫描二维码以打开移动端 Web UI
4. 输入或听写文本，点击“发送 (SEND)”
5. 文本将被注入到桌面端当前获得焦点的应用中

## 组件
| 组件 | 作用 |
|---|---|
| **Python 3 / Flask** | 轻量级 HTTP 服务器，提供移动端 UI 并接收文本 |
| **qrcode** (Python) | 在启动时在终端中生成可扫描的二维码 |
| **ydotool** (Linux) | 通过 `/dev/uinput` 模拟按键（支持 Wayland 和 X11） |
| **wl-clipboard** (Linux) | 将文本复制到 Wayland 剪贴板（剪贴板模式） |
| **ydotoold** (Linux) | ydotool 所需的守护进程，需要访问 `/dev/uinput` 的权限 |
| **Win32 SendInput / 剪贴板** (Windows) | 通过 ctypes 实现按键注入和剪贴板操作——无需额外的原生工具 |
| **AppleScript / System Events** (macOS) | 通过内置的 `osascript` 实现按键注入——无需额外的原生工具 |
| **pbcopy** (macOS) | 将文本复制到 macOS 剪贴板（剪贴板模式） |

## 安装
### Linux (从源码)
```bash
# 系统依赖
sudo apt install ydotool wl-clipboard python3.12-venv
# 克隆并设置
git clone <repo-url> && cd input-from-web
python3 -m venv venv
venv/bin/pip install flask qrcode
# 运行
./run.sh
# 等价于:
# PYTHONPATH=src venv/bin/python -m input_from_web
```

### macOS (从源码)
```bash
# 需要 Python 3.10+ (python.org 或 Homebrew)
git clone <repo-url> && cd input-from-web
python3 -m venv venv
venv/bin/pip install flask qrcode
# 运行 (二维码将打印在当前终端中)
./run.sh
```

### macOS (.app 捆绑包 / DMG)
使用 `python setup.py py2app` 在本地构建 `.app` 捆绑包（参见 [macOS 注意事项](#macos-notes)），然后打开生成的 `Input from Web.app` 并将其拖入“应用程序”文件夹。启动该应用会打开一个显示二维码的终端窗口。有关辅助功能和 Gatekeeper 的步骤，请参见 [macOS 注意事项](#macos-notes)。

### Windows (从源码)
```powershell
# 需要 PATH 中包含 Python 3.10+ (python 或 py 启动器)
git clone <repo-url>
cd input-from-web
.\run.bat
```
`run.bat` 会创建一个虚拟环境，安装 `flask` + `qrcode`，并启动服务器。
无需 ydotool 或管理员权限——打字和剪贴板操作使用 Win32 API。
安装依赖后，您也可以直接运行包入口：
```powershell
$env:PYTHONPATH = "$PWD\src"
python -m input_from_web
# 或兼容性垫片
python input-from-web.py
```

### 项目结构
```
input-from-web.py          # 薄层兼容性垫片
macos-launcher.py          # macOS .app 捆绑包的入口点
src/input_from_web/        # Python 包 (CLI, Flask, 配置, 注入)
templates/index.html       # 手机端 UI 外壳
static/                    # app.css, app.js, theme-init.js, icon.svg
backends/                  # 平台注入器: windows / linux / macos
run.bat / run.sh           # venv 引导 + python -m input_from_web
setup.py                   # py2app 配置 (macOS .app 捆绑包)
pyproject.toml
```

## 使用方法
```bash
# Linux
./run.sh [选项]
# Windows
.\run.bat [选项]
```

### 命令行标志
| 标志 | 描述 |
|---|---|
| `--method type` | 模拟按键（Linux 下为 ydotool，Windows 下为 SendInput，macOS 下为 AppleScript）。默认值 |
| `--method clipboard` | 复制到系统剪贴板，由您手动粘贴 |
| `--port PORT` | 监听的 TCP 端口（默认：5123） |
| `--profile NAME` | 使用配置文件中的指定名称的配置档案 (profile) |
| `--permanent-link` | 在会话之间重用已存储的 Token（见下文） |
| `--permanent-link-refresh` | 用新的 Token 替换已存储的永久 Token |
| `--install-autostart` | 安装用户级开机自启项（macOS 上的 LaunchAgent，Windows 上的启动文件夹，Linux 上的 .desktop 文件） |
| `--uninstall-autostart` | 如果存在，则移除用户级开机自启项 |

### 示例
```bash
./run.sh                          # 默认值 (type 模式, 端口 5123)
./run.sh --method clipboard       # 仅剪贴板模式，您需手动使用 Ctrl+Shift+V 粘贴
./run.sh --port 8080              # 监听 8080 端口
./run.sh --profile work           # 使用配置文件中的 "work" 档案
```
Windows 下的等效命令：`.\run.bat --method clipboard`、`.\run.bat --port 8080` 等。

### 应用内设置
上述大多数选项（输入方式、自动粘贴、粘贴快捷键、自动回车、语音命令、安全 Token）也可以直接从手机 UI 实时切换——打开**设置面板**（调节图标）并切换开关。
更改将持久化保存到 `~/.input-from-web-conf.json` 中的当前活动档案中。
`--port` 和 `--profile` 仅在启动时生效，保留为命令行选项。

## 配置
首次运行时，会在 `~/.input-from-web-conf.json` 创建一个包含 `default` 档案的配置文件。您可以添加更多档案并在它们之间切换。

### 档案字段 (Profile fields)
| 字段 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `method` | `"type"` 或 `"clipboard"` | `"type"` | 输入注入方式。会被 `--method` 覆盖 |
| `auto_paste` | 布尔值 | `false` | 复制到剪贴板后，模拟粘贴按键（Linux/Windows 下为 Ctrl+V，macOS 下为 Cmd+V）。仅适用于 `clipboard` 模式。对 GUI 应用有用，对终端无用 |
| `paste_key` | `"ctrl+v"` 或 `"ctrl+shift+v"` | `"ctrl+v"` | 当 `auto_paste` 开启时模拟的粘贴快捷键（Linux/Windows 下为 Ctrl+Shift+V，macOS 下为 Cmd+Shift+V）。仅适用于 `clipboard` 模式 |
| `auto_press_enter` | 布尔值 | `false` | 注入后，按下 Enter 键以提交（聊天框、即时通讯软件、Shell） |
| `port` | 整数 | `5123` | TCP 端口。会被 `--port` 覆盖 |
| `use_security_token` | 布尔值 | `true` | 要求在 URL 中包含秘密 Token。**仅在受信任的网络中禁用** |
| `voice_send` | 对象 | (见下文) | 语音命令自动触发设置 |
| `substitutions` | 对象 | (见下文) | 词汇/短语替换映射 |

### voice_send
| 字段 | 类型 | 默认值 | 描述 |
|---|---|---|---|
| `enabled` | 布尔值 | `true` | 启用语音命令检测 |
| `delay_seconds` | 数字 | `1.5` | 最后一次编辑后等待触发的秒数 |
| `send_words` | 字符串数组 | `["send", "发送"]` | 当最后输入这些词时触发自动发送的词汇 |
| `clear_words` | 字符串数组 | `["clear", "清除"]` | 当最后输入这些词时触发自动清除的词汇 |

在进行语音听写时，在文本末尾说出 "send" 或 "发送"。如果 1.5 秒内没有进一步的编辑，文本（不含命令词）将被自动发送。

### substitutions
短语会在您输入时实时替换。这对于语音听写非常有用，因为您可以直接读出标点符号的名称。
默认替换：
| 短语 | 替换为 |
|---|---|
| `full stop` (句号) | `.` |
| `question mark` (问号) | `?` |
| `exclamation mark` (感叹号) | `!` |
| `comma` (逗号) | `,` |
| `colon` (冒号) | `:` |
| `semicolon` (分号) | `;` |
| `quote` (引号) | `"` |
| `new line` (换行) | 换行符 |
| `new paragraph` (新段落) | 双换行符 |

### 包含多个档案的配置示例
```json
{
  "default_profile": "default",
  "profiles": {
    "default": {
      "method": "type",
      "port": 5123,
      "use_security_token": true,
      "voice_send": {
        "enabled": true,
        "delay_seconds": 1.5,
        "send_words": ["send", "发送"],
        "clear_words": ["clear", "清除"]
      },
      "substitutions": {
        "full stop": ".",
        "question mark": "?"
      }
    },
    "quick": {
      "method": "clipboard",
      "port": 8080,
      "use_security_token": false,
      "voice_send": { "enabled": false },
      "substitutions": {}
    }
  }
}
```

## 永久链接
默认情况下，每次服务器启动时都会生成一个新的随机 Token，这意味着您每次会话都需要重新扫描二维码。使用 `--permanent-link`，Token 将被保存到配置文件中并在重启后重用。

### 首次设置
```bash
./run.sh --permanent-link
```
首次运行时，二维码包含 Token。用手机扫描它——Token 将保存到浏览器的 localStorage 中。从现在起，手机会自动记住该 Token。

### 后续运行
```bash
./run.sh --permanent-link
```
现在的二维码显示一个干净的 URL（无 Token）——更短且可加入书签。您的手机会从 localStorage 加载 Token。带有 Token 的设置 URL 仍会打印在终端中，以防您需要在新设备上使用。

### 刷新 Token
```bash
./run.sh --permanent-link-refresh
```
用新的 Token 替换已存储的 Token。二维码将包含新 Token，以便您再次扫描。如果您怀疑 Token 已泄露，请使用此命令。

## 添加到主屏幕 (PWA)
该应用包含 Web App Manifest，因此您可以将其安装在手机主屏幕上以便更快地访问。

### Android (Chrome)
1. 在 Chrome 中打开二维码中的链接
2. 点击**三点菜单**（右上角）
3. 点击 **“添加到主屏幕”** 或 **“安装应用”**
4. 从主屏幕图标启动

### iOS (Safari)
1. 在 Safari 中打开二维码中的链接
2. 点击**分享**按钮（底部中央）
3. 点击 **“添加到主屏幕”**
4. 从主屏幕图标启动

### 注意事项
- Token 存储在浏览器的 localStorage 中，因此在使用 `--permanent-link` 时，安装的应用在服务器重启后仍可继续工作。
- Chrome 要求使用 HTTPS 才能实现完整的独立 PWA 模式（无地址栏）。在普通的 HTTP 局域网设置下，应用仍可工作，但可能会显示最小化的浏览器地址栏。这不会影响功能。

## 安全性
**本工具仅设计用于受信任的家庭/私有网络。**
服务器通过纯 HTTP（非 HTTPS）运行。这意味着所有流量（包括安全 Token）都是未加密传输的。同一网络上的任何人都可以通过嗅探流量拦截 Token，然后向您的机器发送任意按键。
Token 提供了针对随意未经授权访问的基本保护，但它**不能**替代网络级安全。请勿在公共或不受信任的网络（咖啡馆、酒店、共享办公室等）上运行此工具。
将 `use_security_token` 设置为 `false` 会移除甚至这种基本保护。
启动时会打印红色警告。请仅在您完全控制的网络上执行此操作。

## 系统要求
### Linux
- Ubuntu 24.04+（或任何带有 ydotool 的 Linux；也适用于 X11）
- Python 3.12+
- ydotool + ydotoold（用于按键注入）
- wl-clipboard（用于剪贴板模式）
- 手机和计算机在同一局域网内

### Windows
- Windows 10/11
- Python 3.10+
- 手机和计算机在同一局域网内

### macOS
- macOS 11+ (Big Sur 或更高版本)
- Python 3.10+ (python.org 安装程序或 Homebrew)
- 终端/应用的辅助功能权限（仅适用于 `type` 模式、自动粘贴和自动回车）
- 手机和计算机在同一局域网内

## macOS 注意事项
- **直接打字**：通过内置的 `osascript` 使用 AppleScript `System Events`，因此不需要额外的二进制文件。需要在 `系统设置 → 隐私与安全性 → 辅助功能` 中授予终端应用（或捆绑的应用）辅助功能权限。首次使用时系统会提示；如果打字无反应，请检查该开关是否已打开。
- **剪贴板模式**：文本通过 `pbcopy` 复制；可选的自动粘贴通过 AppleScript 模拟 Cmd+V（或 Cmd+Shift+V）。仅剪贴板模式无需任何权限授予即可工作。
- **非 ASCII 回退**：与 Windows/Linux 一样，非 ASCII 文本（如中文）通过剪贴板 + Cmd+V 注入。
- **自动粘贴快捷键**：当 `paste_key: "ctrl+shift+v"` 时，自动粘贴使用 Cmd+Shift+V（终端、代码编辑器）。
- **Gatekeeper**：本地构建的捆绑包是临时签名的（无开发者 ID），因此 macOS 可能会隔离该应用——在 Finder 中右键点击该应用 → **打开**，或运行 `xattr -dr com.apple.quarantine "/Applications/Input from Web.app"`。
- **自动启动**：`--install-autostart` 会安装一个 LaunchAgent (`~/Library/LaunchAgents/com.input-from-web.plist`)，该代理会在登录时打开一个运行 `run.sh` 的终端窗口。使用 `--uninstall-autostart` 可将其移除。

## Windows 注意事项
- **直接打字**：ASCII 文本通过 `SendInput` (Unicode) 注入。非 ASCII 文本（如中文）回退到剪贴板 + Ctrl+V，与 Linux 的回退机制一致。
- **剪贴板模式**：文本通过 Win32 剪贴板 API 复制；可选的自动粘贴模拟 Ctrl+V 或 Ctrl+Shift+V。
- **自动启动**：将 `.bat` 文件安装到 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`。它会打开一个带有 10 秒倒计时的控制台（以便您可以取消），然后启动带有二维码的服务器。
- 防火墙：首次运行时，如果 Windows Defender 防火墙提示，请允许 Python 或所选端口在您的私有网络上通行。
- 某些提权（管理员）应用会忽略来自非提权服务器的 SendInput。如果向管理员窗口打字失败，请以管理员身份运行服务器，或使用剪贴板模式。