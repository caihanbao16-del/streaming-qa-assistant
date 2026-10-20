from fastapi import FastAPI, HTTPException
import httpx
from llm_service import generate_answer
from pydantic import BaseModel, Field, field_validator
import asyncio
from fastapi.responses import StreamingResponse, HTMLResponse
from pathlib import Path
from fastapi.responses import FileResponse
from llm_service import generate_answer_stream
import json
from database import get_question_answers, save_question_answer
import sqlite3

app = FastAPI()


# 定义传入数据的结构和校验规则
class QuestionRequest(BaseModel):#规定请求体怎么填
    question: str
    top_k: int = Field(default=3, ge=1, le=10, strict=True)

    @field_validator("question")
    @classmethod
    def check_question(cls, value):#`value`：来自 `@field_validator`
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("问题不能为空")

        return cleaned

def make_sse(event_name, payload):
    data_text = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_name}\ndata: {data_text}\n\n"

@app.post("/ask-stream")
async def ask_stream(data: QuestionRequest):

    async def answer_parts():
        print("[流式] 开始处理", flush=True)

        try:
            parts = []
            async for text in generate_answer_stream(data.question):
                parts.append(text)
                yield make_sse("answer", {"text": text})

            full_answer = "".join(parts)
            if full_answer.strip():
                await asyncio.to_thread(
                    save_question_answer, data.question, full_answer
                )
                print("[数据库] 回答已保存", flush=True)

            print("[流式] 已读完模型数据流", flush=True)

            # 正常结束：事件名为 done
            yield make_sse("done", {})

        except asyncio.CancelledError:
            print("[流式] 当前任务收到取消通知", flush=True)
            raise

        except httpx.TimeoutException:
            print("[流式] 模型响应超时", flush=True)
            yield make_sse(
                "error",
                {"message": "模型响应超时，请稍后重试。"},
            )

        except httpx.HTTPError as error:
            # 在运行后端的终端中记录具体异常类型
            print(
                "[模型调用异常]",
                type(error).__name__,
                flush=True,
            )

            # 如果模型服务返回了错误状态，再记录状态码
            if isinstance(error, httpx.HTTPStatusError):
                print(
                    "[模型服务状态码]",
                    error.response.status_code,
                    flush=True,
                )

            yield make_sse(
                "error",
                {"message": "模型调用失败，请检查网络和模型服务配置。"},
            )

        except RuntimeError as error:
            print("[流式] 运行配置异常", flush=True)
            yield make_sse("error", {"message": str(error)})

        except sqlite3.Error as error:
            print("[数据库] 保存失败", type(error).__name__, flush=True)
            yield make_sse("error", {"message": "回答已生成，但历史记录保存失败。"})

        finally:
            print("[流式] answer_parts 进入退出处理", flush=True)

    return StreamingResponse(
        answer_parts(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )

# 收到发往 /ask 的 POST 请求时，执行这个函数
@app.post("/ask")
async def ask_question(data: QuestionRequest):
    try:
        answer = await generate_answer(data.question)

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="模型响应超时，请稍后重试",
        )

    # 百炼返回了响应，但状态码表示失败
    except httpx.HTTPStatusError as error:
        upstream_status = error.response.status_code

        print("百炼返回的 HTTP 状态码：", upstream_status)

        raise HTTPException(
            status_code=502,
            detail=f"百炼返回错误，HTTP 状态码：{upstream_status}",
        )

    # 请求过程中发生网络或连接错误
    except httpx.RequestError as error:
        error_type = type(error).__name__

        print("模型请求异常类型：", error_type)
        print("异常说明：", str(error))

        raise HTTPException(
            status_code=502,
            detail=f"模型连接失败，异常类型：{error_type}",
        )

    return {
        "question": data.question,
        "top_k": data.top_k,
        "answer": answer,
    }


# 异步生成器：每隔一秒产出一段内容
async def demo_parts():
    texts = [
        "RAG 会先检索资料。",
        "然后把资料和问题交给模型。",
        "最后生成回答。",
    ]

    for text in texts:
        await asyncio.sleep(1)
        yield f"data: {text}\n\n"

    # 自定义一个结束事件，通知网页停止接收
    yield "event: done\ndata: 完成\n\n"


@app.get("/stream-demo")
async def stream_demo():
    return StreamingResponse(
        demo_parts(),
        media_type="text/event-stream",#声明响应为 SSE（服务器推送事件）标准格式
        headers={"Cache-Control": "no-cache"},#禁用缓存，确保数据实时推送，不会被浏览器或中间节点缓存
    )
@app.get("/stream-page", response_class=HTMLResponse)
def stream_page():
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>SSE 学习</title>
</head>
<body>
    <h2>SSE 流式输出演示</h2>
    <button id="start" onclick="startStream()">开始接收</button>
    <pre id="output"></pre>

    <script>
        function startStream() {
            const output = document.getElementById("output");
            const button = document.getElementById("start");

            output.textContent = "";
            button.disabled = true;

            const source = new EventSource("/stream-demo");

            source.onmessage = function(event) {
                output.textContent += event.data + "\\n";
            };

            source.addEventListener("done", function() {
                output.textContent += "——接收完成——";
                source.close();
                button.disabled = false;
            });

            source.onerror = function() {
                output.textContent += "\\n连接中断，请重新开始。";
                source.close();
                button.disabled = false;
            };
        }
    </script>
</body>
</html>
"""
@app.get("/chat")
def chat_page():
    html_path = Path(__file__).resolve().parent / "lesson_07.html"
    return FileResponse(html_path)

@app.get("/history")
def get_history():
    rows = get_question_answers()
    records = []
    for row in rows:
        records.append({
            "id": row[0],
            "question": row[1],
            "answer": row[2]
        })
    return {"records": records}