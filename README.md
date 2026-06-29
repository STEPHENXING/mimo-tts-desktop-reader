# MiMo TTS Desktop Reader

一个 Windows 桌面全局朗读小工具：在浏览器、Word、PDF 阅读器等软件里划选文字，旁边弹出小浮窗，点击即可用小米 MiMo TTS 朗读。它支持长文分片、边生成边播放、暂停/继续、停止，以及音色、方言、情绪、语速配置。

![Product flow](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/product-flow.png)

## 为什么做它

很多 TTS demo 只在自己的输入框里工作。真实阅读时，我们往往在浏览器、文档、聊天窗口和各种软件之间切换。MiMo TTS Desktop Reader 的目标是：**不要改变阅读习惯，只在你选中文字时多给一个“听”的入口**。

典型场景：

- 看长篇文章时，从当前位置一直听到末尾。
- 阅读英文或技术文档时，把一段文字立刻读出来。
- 用方言、情绪和不同音色做更自然的朗读。
- 声音打扰时，右键悬浮球立刻停止。

## 功能

- 全局划词悬浮按钮
- 朗读选中文字
- 从当前位置往下读：自动执行 `Ctrl+Shift+End` 扩展选区
- 长文智能切片：按标点分段，后台逐段请求 TTS
- 队列播放器：前一段播放完自动接下一段
- 暂停/继续：配置面板、系统托盘、中键悬浮球都可触发
- 一键停止：配置面板、系统托盘、右键悬浮球
- 剪贴板保护：不会长期覆盖你的 `Ctrl+C / Ctrl+V`
- API key 支持环境变量，不必写进配置文件

## 架构

![Architecture](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/architecture.png)

主要文件：

- `main.py`：程序入口、文本切片、线程管理、暂停/停止调度
- `tts_engine.py`：MiMo TTS API 请求和声音风格 prompt
- `audio_player.py`：Qt 多媒体队列播放器
- `hook_service.py`：全局鼠标拖拽监听
- `clipboard_reader.py`：安全读取当前选区并恢复剪贴板
- `config_manager.py`：配置文件和环境变量读取
- `ui_widgets/`：浮窗、悬浮球、配置面板

## 安装运行

推荐使用 Windows 10/11。

1. 克隆项目：

```powershell
git clone https://github.com/STEPHENXING/mimo-tts-desktop-reader.git
cd mimo-tts-desktop-reader
```

2. 设置 API key，推荐用环境变量：

```powershell
setx MIMO_API_KEY "你的 API key"
```

重新打开 PowerShell 或重新登录后，环境变量会生效。

临时运行也可以这样设置：

```powershell
$env:MIMO_API_KEY = "你的 API key"
```

3. 启动：

```powershell
.\run.ps1
```

## 配置文件

如果不想用环境变量，可以复制示例配置：

```powershell
Copy-Item config.example.json config.json
```

然后编辑 `config.json`：

```json
{
  "api_key": "",
  "api_url": "https://api.xiaomimimo.com/v1/chat/completions",
  "model": "mimo-v2.5-tts",
  "voice": "mimo_default",
  "speed": 1.0,
  "dialect": "无",
  "emotion": "无"
}
```

优先级：

1. `MIMO_API_KEY` 环境变量
2. `config.json` 里的 `api_key`
3. 默认空值

同理，`MIMO_API_URL` 和 `MIMO_TTS_MODEL` 也会覆盖配置文件里的 `api_url` 和 `model`。

## 使用方式

启动后，桌面右侧会出现一个蓝色悬浮球。

- 左键悬浮球：打开配置面板
- 中键悬浮球：暂停/继续朗读
- 右键悬浮球：立即停止朗读
- 划选文字：出现浮动按钮
- 点击“朗读选中”：朗读当前选区
- 点击“从此往下读”：从当前位置选择到文末并朗读

## 为什么不会弄乱剪贴板

跨软件读取选区没有统一可靠的 Windows API。很多工具会偷偷 `Ctrl+C`，这会覆盖用户原本的剪贴板。这个项目仍然使用兼容性最强的复制路径，但做了保护：

![Clipboard safe copy](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/clipboard-safe-copy.png)

流程是：

1. 保存当前剪贴板里的所有可复制格式
2. 放入一个临时 marker
3. 发送一次 `Ctrl+C`
4. 如果 marker 被替换，说明复制到了选中文本
5. 把用户原来的剪贴板恢复回去

另外，普通“划词”阶段不会触发复制。只有用户真的点击朗读按钮时，才短暂读取当前选区。

## 打包成 exe

```powershell
.\build.ps1
```

输出文件：

```text
dist/MiMoReader.exe
```

分享给别人时，建议同时提供：

- `MiMoReader.exe`
- `config.example.json` 或空白 `config.json`

不要分享你自己带 key 的 `config.json`。

## 常见问题

### 为什么杀毒软件可能提醒？

这个程序会监听全局鼠标拖拽，并模拟少量快捷键读取选区。这些能力对朗读工具是必要的，但也属于安全软件比较敏感的行为。请只运行你自己构建或信任来源的版本。

### 为什么“从此往下读”会改变选区？

它通过 `Ctrl+Shift+End` 选择当前位置到文末，这是为了兼容浏览器、Word 和多数文本编辑场景。读取完成后不会覆盖剪贴板，但选区本身会被扩展。

### 暂停时还会请求接口吗？

已经发出去的当前分片请求无法瞬间撤回；但暂停后，后台 worker 会停在下一段之前，不会继续无限请求和堆队列。

## 开发

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## License

MIT
