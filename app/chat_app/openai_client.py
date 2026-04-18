from openai import OpenAI
from dotenv import load_dotenv
import os
from collections import defaultdict, deque
from typing import Dict, Deque, List
from app.prompt_repo.system_prompt import system_prompt

load_dotenv()


class LLMClient:
    def __init__(self, memory_size: int = 2):
        self.base_url = "https://ollama.com/v1"
        self.model = "gemma4:31b-cloud"
        self.memory_size = memory_size

        # session_id -> conversation memory (ONLY chat history)
        self.memory: Dict[str, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=self.memory_size)
        )

        # 🔥 Permanent system prompt (NEVER stored in memory)
        self.system_prompt = system_prompt

    def _build_messages(self, session_id: str, user_input: str) -> List[dict]:
        """
        Build full message payload for OpenAI API
        """

        history = self.memory[session_id]

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Add conversation memory
        messages.extend(list(history))

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        return messages

    def chat(self, session_id: str, prompt: str) -> str:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY not found in environment variables")

        client = OpenAI(
            base_url=self.base_url,
            api_key=api_key
        )

        messages = self._build_messages(session_id, prompt)

        response = client.chat.completions.create(
            model=self.model,
            messages=messages # type: ignore
            
        )

        assistant_message = response.choices[0].message.content

        # 🔥 Store ONLY conversation (NOT system prompt)
        self.memory[session_id].append(
            {"role": "user", "content": prompt}
        )
        self.memory[session_id].append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message # type: ignore
    
    def chat_stream(self, session_id: str, prompt: str):
        api_key = os.getenv("API_KEY")

        client = OpenAI(
            base_url=self.base_url,
            api_key=api_key
        )

        messages = self._build_messages(session_id, prompt)

        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,# type: ignore
            stream=True        ) # type: ignore

        full_response = ""

        for chunk in stream:
            token = chunk.choices[0].delta.content

            if token:
                full_response += token
                yield token  # 🔥 stream token to frontend

        # store final result AFTER streaming completes
        self.memory[session_id].append({"role": "user", "content": prompt})
        self.memory[session_id].append({"role": "assistant", "content": full_response})
    