"""DeepSeek API 客户端（基于 requests，兼容 OpenAI 接口格式）。"""

import json
import requests


def create_client(api_key: str, base_url: str = "https://api.deepseek.com") -> dict:
    """创建客户端配置。返回 dict 供 chat() 使用。"""
    return {"api_key": api_key, "base_url": base_url.rstrip("/")}


def chat(
    client: dict,
    system_prompt: str,
    user_message: str,
    model: str = "deepseek-v4-pro",
    temperature: float = 0.3,
    max_tokens: int = 16384,
) -> str:
    """发送聊天请求，返回模型回复文本。

    Args:
        client: create_client() 返回的配置 dict
        system_prompt: 系统提示词
        user_message: 用户消息
        model: 模型名称
        temperature: 生成温度
        max_tokens: 最大输出 token 数

    Returns:
        模型回复文本
    """
    url = f"{client['base_url']}/chat/completions"
    headers = {
        "Authorization": f"Bearer {client['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning_effort": "high",
        "thinking": {"type": "enabled"},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=300)
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]
