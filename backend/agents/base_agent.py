"""Base agent class wrapping Mistral SDK for all COUNCIL agents."""

import os
import json
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()


class MistralBaseAgent:
    """Base class for COUNCIL agents. Pure Python — no framework dependencies."""

    model_name: str = "mistral-large-latest"
    temperature: float = 0.3
    system_prompt: str = ""
    agent_role: str = "agent"

    def __init__(self):
        self._mistral = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    async def call_mistral(self, messages: list[dict], tools=None, tool_choice=None, **kwargs) -> str:
        """Call Mistral API and return the assistant response text.

        If tools are provided and the model returns a tool call,
        returns the FunctionCall object instead of text content.
        """
        call_kwargs = {
            "model": kwargs.pop("model", self.model_name),
            "messages": messages,
            "temperature": kwargs.pop("temperature", self.temperature),
        }
        if tools:
            call_kwargs["tools"] = tools
        if tool_choice:
            call_kwargs["tool_choice"] = tool_choice
        call_kwargs.update(kwargs)

        response = await self._mistral.chat.complete_async(**call_kwargs)
        choice = response.choices[0]
        if choice.message.tool_calls:
            return choice.message.tool_calls[0].function
        return choice.message.content

    async def call_mistral_structured(self, messages: list[dict], response_model, **kwargs):
        """Call Mistral API with structured JSON output.

        Returns an instance of response_model (a Pydantic BaseModel subclass).
        Uses json_object response format with schema instructions.
        Resilient to minor schema violations from the LLM.
        """
        schema = response_model.model_json_schema()
        # Only include top-level schema properties to keep instructions concise
        props = schema.get("properties", {})
        simplified = {k: {"type": str(v.get("type", "string")), "description": v.get("description", "")} for k, v in props.items()}
        json_instruction = (
            "\n\nYou MUST respond with valid JSON. "
            f"Top-level keys: {json.dumps(list(props.keys()))}. "
            "Each finding MUST have: severity, category, file_path, description, recommendation. "
            "line_range is optional (null if unknown)."
        )

        modified_messages = list(messages)
        if modified_messages and modified_messages[0]["role"] == "system":
            modified_messages[0] = {
                "role": "system",
                "content": modified_messages[0]["content"] + json_instruction,
            }
        else:
            modified_messages.insert(0, {
                "role": "system",
                "content": f"Respond with valid JSON.{json_instruction}",
            })

        response = await self._mistral.chat.complete_async(
            model=self.model_name,
            messages=modified_messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            **kwargs,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return response_model.model_validate(data)

    async def call_mistral_stream(self, messages: list[dict], **kwargs):
        """Stream Mistral API response, yielding text chunks."""
        response = await self._mistral.chat.stream_async(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            **kwargs,
        )
        async for event in response:
            chunk = event.data.choices[0].delta.content
            if chunk:
                yield chunk

    async def analyze_files(self, file_paths: list[str], file_contents: dict[str, str]):
        """Analyze assigned files. Override in subclasses for specialization."""
        raise NotImplementedError
