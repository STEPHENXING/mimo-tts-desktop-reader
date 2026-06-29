# 我做了一个“划词就能听”的桌面小工具

有时候看长文章，眼睛真的会累。

我最开始只是想要一个很简单的东西：在浏览器、Word、PDF 里选中一段文字，旁边冒出一个按钮，点一下，它就开始读。

不用复制，不用切窗口，不用把文字粘到另一个软件里。

就这么一个小需求，最后长成了这个项目：

**MiMo TTS Desktop Reader**。

![Product flow](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/product-flow.png)

## 它能做什么

简单说，它就是一个 Windows 桌面朗读助手。

你可以：

- 在任何软件里划选文字，然后点“朗读选中”
- 点“从此往下读”，让它从当前位置一直读到文末
- 选择音色、方言、情绪和语速
- 暂停、继续、停止
- 右键桌面悬浮球，让它立刻闭嘴

它更像一个“小耳朵按钮”，平时不打扰你，需要的时候就在鼠标旁边出现。

## 为什么不是普通 TTS 输入框

普通 TTS demo 一般是这样的：

1. 打开网页或程序
2. 复制文字
3. 切到 TTS 工具
4. 粘贴
5. 点击生成

这当然能用，但很割裂。

我想要的是另一种感觉：

**我在哪里读，就在哪里听。**

所以这个工具的重点不是“做一个更大的窗口”，而是尽量少出现。你划词，它出现；你点一下，它朗读；你不用了，它自己消失。

## 背后其实就几块

项目拆得比较直白：

![Architecture](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/architecture.png)

- `hook_service.py`：看你有没有拖拽选中文字
- `float_icon.py`：显示那个小小的朗读按钮
- `main.py`：负责调度，谁该干活、谁该停下
- `tts_engine.py`：去请求 MiMo TTS
- `audio_player.py`：把生成好的音频排队播放
- `clipboard_reader.py`：安全地读取选区，不弄乱剪贴板

这套拆法的好处是，新人看起来不会太绕。你想改按钮，就看 UI；想换 TTS 服务，就看 `tts_engine.py`；想研究暂停和队列，就看 `main.py` 和 `audio_player.py`。

## 长文为什么要切片

如果把一整篇长文章一次性丢给 TTS，体验通常不太好。

你可能要等很久才听到第一句话。万一中途失败，还得整篇重来。

所以这里用了一个很朴素的办法：按标点切成小段，一段一段生成。

第一段好了就先播，后面的继续在后台排队。

这样听起来就像“马上开口”，而不是盯着进度条发呆。

## 剪贴板这个坑，真的要管

做全局划词工具，很容易踩到一个坑：怎么拿到用户选中的文字？

最兼容的办法是模拟 `Ctrl+C`，再从剪贴板读文本。

但这会带来一个坏体验：你刚复制的东西，被工具偷偷覆盖了。等你再 `Ctrl+V`，发现粘出来的是刚才朗读的文字。

这个就很烦。

所以我做了一个“借一下，用完还回去”的流程：

![Clipboard safe copy](https://gitee.com/xingxiliang/imgblog/raw/master/img2026/mimo-tts-desktop-reader/clipboard-safe-copy.png)

大概是这样：

1. 先把用户当前剪贴板保存起来
2. 临时触发一次复制，拿到选中的文字
3. 立刻把原来的剪贴板恢复回去

而且普通划词时不会复制。只有你真的点“朗读”时，才会短暂读取选区。

这就是为了不打扰你的正常 `Ctrl+C / Ctrl+V`。

## API key 不要写进代码

这个也很重要。

一开始为了跑通 demo，把 API key 写进代码里确实最快。但一旦要发 GitHub，就很危险。

所以现在推荐这样用：

```powershell
setx MIMO_API_KEY "你的 API key"
```

程序会优先从环境变量里读 key。

如果你只是自己玩，也可以复制 `config.example.json` 成 `config.json`，把 key 写进去。但要分享项目时，千万别把自己的 `config.json` 一起发出去。

## 新人可以怎么跑起来

克隆项目后：

```powershell
cd mimo-tts-desktop-reader
setx MIMO_API_KEY "你的 API key"
.\run.ps1
```

想打包成 exe：

```powershell
.\build.ps1
```

打包结果在：

```text
dist/MiMoReader.exe
```

## 后面还能怎么玩

这个项目很适合继续加小功能。

比如：

- 加一个音量滑块
- 加全局快捷键
- 加朗读历史
- 给悬浮球做拖拽吸边
- 换成别的 TTS 服务
- 做一个更正式的安装包

我觉得它适合新人练手的地方在于：它不是纯算法，也不是纯 UI，而是一个真的能每天用的小工具。

你改一个小功能，就会碰到桌面应用里很真实的东西：事件、线程、配置、状态、用户体验。

## 最后

这个项目的核心其实很简单：

让 TTS 不再是一个“复制粘贴后才能用”的工具，而是变成你阅读时随手可以叫出来的小助手。

选中文字，点一下，开始听。

就这样。
