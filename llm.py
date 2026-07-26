'''
Shared LLM client for the three agents;

The inference source is picked once at startup (main.py --llm / --model) via
configure(); every agent then calls chat() with a plain list of
{"role": ..., "content": ...} messages and gets the response text back
Providers:

    openai  - OpenAI API (default: gpt-5.1). Needs OPENAI_API_KEY in .env
    claude  - Anthropic API (default: claude-opus-4-8). Needs ANTHROPIC_API_KEY
    ollama  - local Ollama install (default: qwen3.5:9b). No key needed

Clients are created so a provider's SDK/key is only required if that
provider is actually selected
'''

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')

DEFAULT_MODELS = {
    "openai": "gpt-5.1",
    "claude": "claude-opus-4-8",
    "ollama": "qwen3.5:9b",
}

PROVIDERS = tuple(DEFAULT_MODELS)

provider = "openai"
model = DEFAULT_MODELS["openai"]
client = None


def configure(new_provider: str, new_model: str | None = None) -> None:
    '''Set the inference source for the whole run. Called once from main.'''
    global provider, model, client
    if new_provider not in DEFAULT_MODELS:
        raise ValueError(f"unknown provider '{new_provider}', expected one of {PROVIDERS}")
    provider = new_provider
    model = new_model or DEFAULT_MODELS[new_provider]
    client = None  # rebuilt lazily on first chat()


def description() -> str:
    '''Human-readable "provider/model" tag, shown as run metadata.'''
    return f"{provider}/{model}"


def chat(messages: list[dict]) -> str:
    '''Send a chat-format message list to the configured provider, return the text.'''
    if provider == "openai":
        return chat_openai(messages)
    if provider == "claude":
        return chat_claude(messages)
    return chat_ollama(messages)


def chat_openai(messages: list[dict]) -> str:
    global client
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    completion = client.chat.completions.create(model=model, messages=messages)
    return completion.choices[0].message.content


def chat_claude(messages: list[dict]) -> str:
    global client
    if client is None:
        import anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    # Anthropic takes the system prompt as a separate parameter, not a message role
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    turns = [m for m in messages if m["role"] != "system"]
    response = client.messages.create(
        model= model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=system or None,
        messages=turns,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def chat_ollama(messages: list[dict]) -> str:
    import ollama
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]
