# 流式问答助手

使用 FastAPI 和百炼模型接口构建的网页问答项目。

## 已实现功能

- 输入问题并逐步显示模型回答。
- 点击停止生成，保留已经显示的内容。
- 停止后可以再次发送问题。
- 校验请求参数，并显示错误提示。
- 使用 SSE 的 answer、done、error 事件区分回答、完成与错误。

## 主要文件

- main.py：定义接口、校验请求参数、组织 SSE 响应。
- llm_service.py：调用百炼模型接口，读取回答片段。
- lesson_07.html：提供网页，发送请求并显示回答。
- .gitignore：设置不纳入 Git 管理的文件。

## 环境准备

使用 Python 3.11，在项目根目录打开 PowerShell。

首次使用时创建虚拟环境；已有可用的 .venv 可以跳过：

```powershell
python -m venv .venv
```

安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn httpx
```

## 配置百炼 API Key

执行下面的命令，粘贴自己的 Key 后按回车：

```powershell
$ragKey = Read-Host "请粘贴百炼 API Key" -AsSecureString
$env:DASHSCOPE_API_KEY = [System.Net.NetworkCredential]::new("", $ragKey).Password
```

Key 只设置在当前终端环境中，不写进代码或 README。

## 启动项目

在配置 Key 的同一个终端中执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问：http://127.0.0.1:8000/chat

保持终端运行；按 Ctrl+C 停止后端。

## 验证功能

- 发送问题，确认回答逐步显示。
- 生成过程中点击停止，确认保留已有文字。
- 再次发送问题，确认能够正常回答。