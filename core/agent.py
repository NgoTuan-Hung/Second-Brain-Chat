"""
AI Agent Core for Obsidian Second Brain.
Supports both Antigravity CLI (AGY) engine (High Quota & Gemini 3.7 models)
and Direct Gemini API (google-genai SDK) with streaming and tool execution.
"""

import os
import json
import time
import shutil
import subprocess
import traceback
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from config import config
from core.vault_reader import VaultReader
from core.tools import ALL_TOOLS

SYSTEM_PROMPT_TEMPLATE = """Bạn là trợ lý AI Second Brain cá nhân thông minh, tận tâm và thân thiện, luôn nổi trên màn hình để đồng hành cùng người dùng.
Nhiệm vụ chính của bạn là hỗ trợ quản lý công việc, ghi chép nhanh, tìm kiếm kiến thức, và tổ chức cuộc sống thông qua kho lưu trữ Obsidian Second Brain.

## Quyền hạn và Thao tác:
- Ghi nhanh nhật ký / log vào thư mục `Daily/YYYY-MM-DD.md` hoặc `Logs/YYYY-MM-DD.md`.
- Tạo note mới trong `Knowledge/`, `Ideas/`, `Tasks/`, `Projects/`.
- Thêm việc cần làm (Todo checkbox `- [ ]`) vào file công việc hoặc daily note.
- Tìm kiếm và đọc các ghi chú trong Vault.

## Nguyên tắc:
1. Trả lời súc tích, định dạng Markdown đẹp mắt (dùng emoji, bullet point, bold, [[wikilinks]]).
2. Luôn phản hồi bằng tiếng Việt thân thiện, thông minh và chu đáo.
"""

AGY_VALID_MODELS = [
    "gemini-3.8-flash-high",
    "gemini-3.8-flash-medium",
    "gemini-3.8-flash-low",
    "gemini-3.7-flash-high",
    "gemini-3.7-flash-medium",
    "gemini-3.7-flash-low",
    "gemini-3.6-flash-high",
    "gemini-3.6-flash-medium",
    "gemini-3.6-flash-low",
    "gemini-3.5-flash-high",
    "gemini-3.5-flash-medium",
    "gemini-3.5-flash-low",
    "gemini-3.1-pro-high",
    "gemini-3.1-pro-low",
    "claude-sonnet-4-6",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium"
]

MODEL_CONTEXT_LIMITS = {
    "gemini-3.8": 1_048_576,
    "gemini-3.7": 1_048_576,
    "gemini-3.6": 1_048_576,
    "gemini-3.5": 1_048_576,
    "gemini-3.1": 1_048_576,
    "gemini-2.5": 1_048_576,
    "gemini-1.5-pro": 2_097_152,
    "gemini-1.5-flash": 1_048_576,
    "claude-sonnet": 200_000,
    "claude-opus": 200_000,
    "gpt-oss": 128_000,
}

def get_model_context_limit(model_name: str) -> int:
    for prefix, limit in MODEL_CONTEXT_LIMITS.items():
        if prefix in model_name:
            return limit
    return 1_048_576


def format_tool_desc(tool_name: str, params: dict) -> str:
    """Creates a user-friendly description and summary for a tool call."""
    if not isinstance(params, dict):
        params = {}

    if tool_name == "run_command":
        cmd = params.get("CommandLine", "")
        return f"💻 Chạy lệnh: `{cmd[:65]}`" if cmd else "💻 Chạy lệnh terminal"
    elif tool_name in ("list_dir", "view_file", "read_file"):
        path = params.get("DirectoryPath") or params.get("AbsolutePath") or params.get("SearchPath") or params.get("TargetFile") or ""
        short_path = path.split("/")[-1] if "/" in path else path
        return f"📁 {tool_name}: `{short_path or path}`"
    elif tool_name in ("grep_search", "search_vault"):
        q = params.get("Query") or params.get("query") or ""
        return f"🔍 Tìm kiếm: \"{q}\"" if q else "🔍 Tìm kiếm trong Vault"
    elif tool_name in ("create_note", "write_to_file"):
        title = params.get("title") or params.get("TargetFile") or ""
        return f"📄 Tạo ghi chú: `{title}`" if title else "📄 Tạo ghi chú"
    elif tool_name == "append_daily_log":
        cat = params.get("category", "")
        return f"📝 Ghi nhật ký ({cat})" if cat else "📝 Ghi nhật ký hôm nay"
    elif tool_name == "add_task":
        task = params.get("task", "")
        return f"✅ Thêm việc: \"{task[:40]}\"" if task else "✅ Thêm công việc mới"
    elif tool_name == "read_note":
        title = params.get("title", "")
        return f"📖 Đọc ghi chú: `{title}`" if title else "📖 Đọc ghi chú"
    return f"⚡ Thực thi: {tool_name}"


class AgentWorker(QObject):
    chunk_received = pyqtSignal(str)
    tool_started = pyqtSignal(str, str, object)   # tool_name, desc, details_dict
    tool_finished = pyqtSignal(str, str, object)  # tool_name, result_str, details_dict
    thinking_updated = pyqtSignal(object)         # {"thinking_tokens": int, "duration": float}
    token_usage_updated = pyqtSignal(object)      # dict with token usage & context stats
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt: str, chat_history: List[Dict[str, str]], conversation_id: Optional[str] = None):
        super().__init__()
        self.prompt = prompt
        self.chat_history = chat_history
        self.conversation_id = conversation_id
        self._proc = None

    def run(self):
        engine = config.engine
        agy_path = shutil.which("agy") or "/home/hungdreamer/.local/bin/agy"

        if engine == "agy" or (not config.gemini_api_key and os.path.exists(agy_path)):
            self._run_agy(agy_path)
        else:
            self._run_gemini_api()

    def _run_agy(self, agy_path: str):
        try:
            vault_path = str(config.vault_path)
            model_name = config.model_name

            # Validate model name against AGY model list
            if model_name not in AGY_VALID_MODELS:
                model_name = "gemini-3.8-flash-medium"

            # Prepare initial context if starting new conversation
            reader = VaultReader(config.vault_path)
            vault_ctx = reader.get_context_for_prompt(max_length=2500)

            user_prompt = self.prompt
            if not self.conversation_id:
                full_prompt = f"{SYSTEM_PROMPT_TEMPLATE}\n\n[Obsidian Vault Info]\n{vault_ctx}\n\n[Yêu cầu]: {user_prompt}"
            else:
                full_prompt = user_prompt

            cmd = [
                agy_path,
                "-p", full_prompt,
                "--model", model_name,
                "--output-format", "stream-json",
                "--dangerously-skip-permissions",
            ]

            if os.path.exists(vault_path):
                cmd.extend(["--add-dir", vault_path])

            if self.conversation_id:
                cmd.extend(["--conversation", self.conversation_id])

            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            accumulated_response = ""
            input_tokens = 0
            output_tokens = 0
            thinking_tokens = 0
            total_tokens = 0
            limit = get_model_context_limit(model_name)

            for line in self._proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    event = data.get("event")

                    if event == "init":
                        cid = data.get("conversation_id")
                        if cid:
                            self.conversation_id = cid

                    elif event == "step_update":
                        su = data.get("step_update", {})
                        stype = su.get("step_type")
                        state = su.get("state")
                        delta = su.get("text_delta")
                        duration = float(su.get("duration_seconds", 0.0) or 0.0)
                        usage = su.get("usage", {})

                        if usage:
                            if usage.get("input_tokens"):
                                input_tokens = usage.get("input_tokens", input_tokens)
                            if usage.get("output_tokens"):
                                output_tokens = usage.get("output_tokens", output_tokens)
                            if usage.get("thinking_tokens"):
                                thinking_tokens = usage.get("thinking_tokens", thinking_tokens)
                            if usage.get("total_tokens"):
                                total_tokens = usage.get("total_tokens", total_tokens)

                            if usage.get("thinking_tokens"):
                                self.thinking_updated.emit({
                                    "thinking_tokens": thinking_tokens,
                                    "input_tokens": input_tokens,
                                    "output_tokens": output_tokens,
                                    "duration": duration
                                })

                            self.token_usage_updated.emit({
                                "model_name": model_name,
                                "context_limit": limit,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "thinking_tokens": thinking_tokens,
                                "total_tokens": total_tokens or (input_tokens + output_tokens + thinking_tokens),
                                "turn_count": len(self.chat_history) // 2 + 1,
                            })

                        if stype == "agent_response" and delta:
                            accumulated_response += delta
                            self.chunk_received.emit(delta)

                        elif stype in ("tool", "tool_call", "tool_use"):
                            tool_name = su.get("tool_name") or su.get("tool_info", {}).get("name") or "tool"
                            tool_info = su.get("tool_info", {})
                            params = tool_info.get("parameters") or su.get("parameters") or {}
                            output = tool_info.get("output") or su.get("output") or ""

                            if state == "ACTIVE":
                                desc = format_tool_desc(tool_name, params)
                                details = {
                                    "tool_name": tool_name,
                                    "parameters": params,
                                    "status": "running",
                                    "step_index": su.get("step_index", 0)
                                }
                                self.tool_started.emit(tool_name, desc, details)

                            elif state in ("DONE", "ERROR"):
                                output_str = str(output) if output else ("✅ Thành công" if state == "DONE" else "❌ Có lỗi xảy ra")
                                details = {
                                    "tool_name": tool_name,
                                    "parameters": params,
                                    "output": output_str,
                                    "duration": duration,
                                    "status": "done" if state == "DONE" else "error",
                                    "step_index": su.get("step_index", 0)
                                }
                                self.tool_finished.emit(tool_name, output_str, details)

                        elif stype == "tool_result":
                            tool_name = su.get("tool_name", "tool")
                            output = su.get("output") or ""
                            details = {
                                "tool_name": tool_name,
                                "output": str(output),
                                "duration": duration,
                                "status": "done"
                            }
                            self.tool_finished.emit(tool_name, str(output) or f"✅ Đã xong {tool_name}", details)

                    elif event == "result":
                        res_obj = data.get("result", {})
                        resp_text = res_obj.get("response", "")
                        res_usage = res_obj.get("usage") or res_obj.get("metrics", {})
                        if res_usage:
                            input_tokens = res_usage.get("input_tokens", input_tokens)
                            output_tokens = res_usage.get("output_tokens", output_tokens)
                            thinking_tokens = res_usage.get("thinking_tokens", thinking_tokens)
                            total_tokens = res_usage.get("total_tokens", total_tokens)

                        if resp_text and not accumulated_response:
                            accumulated_response = resp_text
                            self.chunk_received.emit(resp_text)

                except Exception:
                    pass

            self._proc.wait()

            if not accumulated_response:
                accumulated_response = "Đã hoàn thành yêu cầu."

            # If no explicit token usage was sent by AGY, provide estimate
            if total_tokens == 0 and (input_tokens == 0 and output_tokens == 0):
                est_input = (len(full_prompt) + sum(len(m.get("content", "")) for m in self.chat_history)) // 4
                est_output = len(accumulated_response) // 4
                input_tokens = est_input
                output_tokens = est_output
                total_tokens = est_input + est_output

            self.token_usage_updated.emit({
                "model_name": model_name,
                "context_limit": limit,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "thinking_tokens": thinking_tokens,
                "total_tokens": total_tokens or (input_tokens + output_tokens + thinking_tokens),
                "turn_count": len(self.chat_history) // 2 + 1,
            })

            self.response_finished.emit(accumulated_response)

        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit(f"❌ **Lỗi khi gọi AGY:** {str(e)}")

    def _run_gemini_api(self):
        api_key = config.gemini_api_key
        if not api_key:
            self.error_occurred.emit(
                "⚠️ **Chưa cấu hình Gemini API Key hoặc AGY!**\n\n"
                "Vui lòng chọn Engine **Antigravity CLI (AGY)** trong Cài đặt (⚙️) hoặc nhập `GEMINI_API_KEY`."
            )
            return

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            reader = VaultReader(config.vault_path)
            vault_ctx = reader.get_context_for_prompt()
            system_instruction = f"{SYSTEM_PROMPT_TEMPLATE}\n\nNgữ cảnh Vault:\n{vault_ctx}"

            tool_map = {func.__name__: func for func in ALL_TOOLS}
            contents = []
            for msg in self.chat_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                ))
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=self.prompt)]
            ))

            gen_config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=ALL_TOOLS,
                temperature=0.7,
            )

            accumulated_response = ""
            model_name = "gemini-2.5-flash"
            limit = get_model_context_limit(model_name)
            last_usage_meta = None

            for _ in range(5):
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=gen_config,
                )
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    last_usage_meta = response.usage_metadata

                candidate = response.candidates[0] if response.candidates else None
                if not candidate:
                    break

                content = candidate.content
                has_function_call = False
                function_calls = []

                if content and content.parts:
                    for part in content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            has_function_call = True
                            function_calls.append(part.function_call)
                        elif hasattr(part, "text") and part.text:
                            accumulated_response += part.text
                            self.chunk_received.emit(part.text)

                contents.append(content)

                if has_function_call:
                    function_response_parts = []
                    for fc in function_calls:
                        fname = fc.name
                        fargs = dict(fc.args) if fc.args else {}
                        t0 = time.time()
                        desc = format_tool_desc(fname, fargs)
                        self.tool_started.emit(fname, desc, {"tool_name": fname, "parameters": fargs, "status": "running"})
                        
                        if fname in tool_map:
                            try:
                                result_str = tool_map[fname](**fargs)
                            except Exception as te:
                                result_str = f"Lỗi: {te}"
                        else:
                            result_str = f"Không tìm thấy {fname}"

                        elapsed = round(time.time() - t0, 3)
                        status = "error" if "Lỗi:" in str(result_str) else "done"
                        self.tool_finished.emit(fname, str(result_str), {
                            "tool_name": fname,
                            "parameters": fargs,
                            "output": str(result_str),
                            "duration": elapsed,
                            "status": status
                        })
                        function_response_parts.append(
                            types.Part.from_function_response(name=fname, response={"result": result_str})
                        )

                    contents.append(types.Content(role="user", parts=function_response_parts))
                else:
                    break

            in_tok = getattr(last_usage_meta, "prompt_token_count", 0) if last_usage_meta else 0
            out_tok = getattr(last_usage_meta, "candidates_token_count", 0) if last_usage_meta else 0
            tot_tok = getattr(last_usage_meta, "total_token_count", 0) if last_usage_meta else (in_tok + out_tok)

            if tot_tok == 0:
                in_tok = (len(system_instruction) + sum(len(m.get("content", "")) for m in self.chat_history) + len(self.prompt)) // 4
                out_tok = len(accumulated_response) // 4
                tot_tok = in_tok + out_tok

            self.token_usage_updated.emit({
                "model_name": model_name,
                "context_limit": limit,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "thinking_tokens": 0,
                "total_tokens": tot_tok,
                "turn_count": len(self.chat_history) // 2 + 1,
            })

            self.response_finished.emit(accumulated_response)

        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit(f"❌ **Lỗi khi xử lý:** {str(e)}")


class SecondBrainAgent(QObject):
    chunk_received = pyqtSignal(str)
    tool_started = pyqtSignal(str, str, object)
    tool_finished = pyqtSignal(str, str, object)
    thinking_updated = pyqtSignal(object)
    token_usage_updated = pyqtSignal(object)
    response_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.history: List[Dict[str, str]] = []
        self.conversation_id: Optional[str] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[AgentWorker] = None

    def send_message(self, user_text: str):
        self._thread = QThread()
        self._worker = AgentWorker(user_text, list(self.history), self.conversation_id)
        self._worker.moveToThread(self._thread)

        self._worker.chunk_received.connect(self.chunk_received)
        self._worker.tool_started.connect(self.tool_started)
        self._worker.tool_finished.connect(self.tool_finished)
        self._worker.thinking_updated.connect(self.thinking_updated)
        self._worker.token_usage_updated.connect(self.token_usage_updated)
        self._worker.response_finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self.error_occurred)

        self._thread.started.connect(self._worker.run)
        self._worker.response_finished.connect(self._cleanup_thread)
        self._worker.error_occurred.connect(self._cleanup_thread)

        self.history.append({"role": "user", "content": user_text})
        self._thread.start()

    def _on_finished(self, full_text: str):
        if self._worker and self._worker.conversation_id:
            self.conversation_id = self._worker.conversation_id
        if full_text:
            self.history.append({"role": "model", "content": full_text})
        self.response_finished.emit(full_text)

    def _cleanup_thread(self, *args):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

    def clear_history(self):
        self.history.clear()
        self.conversation_id = None


