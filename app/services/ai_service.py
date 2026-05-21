import json
import httpx
from app.ai.registry import list_functions, get_function
from app.ai.permissions import check_permission
from app.schemas.user import UserInDB

MAX_TOOL_CALL_ROUNDS = 3
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


def _build_tools() -> list[dict]:
    tools: list[dict] = []
    for fn in list_functions():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": fn.name,
                    "description": fn.description,
                    "parameters": fn.parameters,
                },
            }
        )
    return tools


async def chat_with_deepseek(
    messages: list[dict],
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    user: UserInDB | None = None,
) -> dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    tools = _build_tools() if user is not None else None

    async with httpx.AsyncClient(timeout=60.0) as client:
        round_count = 0
        while round_count < MAX_TOOL_CALL_ROUNDS:
            round_count += 1
            payload: dict = {
                "model": model,
                "messages": messages,
            }
            if tools:
                payload["tools"] = tools

            response = await client.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                error_body = response.text
                return {
                    "reply": f"DeepSeek API 调用失败 (HTTP {response.status_code}): {error_body}",
                    "error": True,
                }

            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]

            if message.get("tool_calls") and user is not None:
                tool_calls = message["tool_calls"]
                messages.append(message)

                for tool_call in tool_calls:
                    function_name = tool_call["function"]["name"]
                    tool_call_id = tool_call["id"]

                    if not check_permission(user, function_name):
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": f"权限不足：当前用户无权调用功能 '{function_name}'",
                            }
                        )
                        continue

                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}

                    fn_def = get_function(function_name)
                    if fn_def is None:
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": f"未知功能: {function_name}",
                            }
                        )
                        continue

                    try:
                        result = await fn_def.handler(user, **arguments)
                    except Exception as exc:
                        result = f"功能执行失败: {str(exc)}"

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": result,
                        }
                    )

                continue

            assistant_reply = message.get("content") or ""
            return {"reply": assistant_reply, "error": False}

        return {
            "reply": "已达到最大工具调用轮次，请简化您的请求后重试。",
            "error": True,
        }
