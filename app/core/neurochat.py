"""Conversational AI engine managing Groq LLM inference, personas, and tool orchestration."""

import asyncio
from typing import List, Dict, Optional, Any
from groq import AsyncGroq, GroqError
from app.helps.utils import logger
from settings.config import params
from plugins.integrating.storing.database import database
from plugins.processing.agenticRag.wse import WebSearchEngine
from plugins.processing.agenticRag.ise import InternalSearchEngine
from plugins.processing.agenticRag.tse import TutorialSearchEngine
from app.core.ai_tools import AIToolManager


class ChatEngine:
    """Core chat engine handling prompt assembly, persona switching, and tool calling."""

    def __init__(self, max_history_per_user: int = params.META_LIMIT):
        try:
            if not params.GROQ_TOKEN:
                logger.error("[ERROR NEUROCHAT] Invalid or missing Groq API Token.")
                return

            self.client = AsyncGroq(api_key=params.GROQ_TOKEN)
            self.personality_prompt = params.PERSONALITY_PROMPT
            self.max_history_per_user = max_history_per_user

            self.wse = WebSearchEngine()
            self.ise = InternalSearchEngine()
            self.tse = TutorialSearchEngine()

            self.mode_mapping = {
                "défaut": "default",
                "caveman": "caveman",
                "cartman": "eric_cartman",
                "homerSimpson": "homer_simpson",
                "support": "support",
            }

        except ValueError as err:
            logger.error(f"[ERROR NEUROCHAT] Incorrect initialization parameter: {err}", exc_info=True)
            raise
        except Exception as err:
            logger.error(f"[ERROR NEUROCHAT] Initialization error: {err}", exc_info=True)
            raise

    async def _get_server_mode(self, server_id: str) -> str:
        """Fetch server conversation mode asynchronously."""
        try:
            server_config = await asyncio.to_thread(database.get_server_config, server_id=server_id)
            if server_config and "mode" in server_config:
                return server_config["mode"]
            return "default"
        except Exception as e:
            logger.error(f"[ERROR NEUROCHAT] Failed to retrieve server mode: {e}", exc_info=True)
            return "default"

    async def _build_system_prompt(
        self,
        username: Optional[str] = None,
        server_mode: Optional[str] = None,
    ) -> str:
        """Construct the system prompt with active persona and user context."""
        chosen_mode = self.mode_mapping.get(server_mode, "default") if server_mode else "default"
        base_prompt = self.personality_prompt.get(
            chosen_mode, self.personality_prompt.get("default", "You are an AI assistant.")
        )

        if username:
            user_context = (
                f"\n\n📋 **Conversation Context**\n"
                f"You are talking to Discord user: **{username}**\n"
                f"Address them naturally when appropriate, without overusing their name."
            )
            return base_prompt + user_context

        return base_prompt

    async def _prepare_messages(
        self,
        conversation_history: List[Dict[str, str]],
        username: Optional[str] = None,
        server_mode: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Assemble system prompt and conversation history for the API request."""
        try:
            system_prompt = await self._build_system_prompt(username=username, server_mode=server_mode)
            messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                if self.max_history_per_user > 0:
                    truncated_history = conversation_history[-self.max_history_per_user :]
                else:
                    truncated_history = conversation_history
                messages.extend(truncated_history)

            return messages
        except Exception as error:
            logger.error(f"[ERROR NEUROCHAT] Message preparation failed: {error}", exc_info=True)
            return []

    @staticmethod
    def _validate_messages(messages: List[Dict[str, str]]) -> bool:
        """Validate input message structure."""
        if not messages or not isinstance(messages, list):
            logger.warning("[WARNING NEUROCHAT] Empty or invalid message structure.", exc_info=True)
            return False

        has_user_message = any(msg.get("role") == "user" for msg in messages)
        if not has_user_message:
            logger.warning("[WARNING NEUROCHAT] No user message found in history.", exc_info=True)
            return False

        last_user_msg = next(
            (msg.get("content", "").strip() for msg in reversed(messages) if msg.get("role") == "user"), None
        )
        if not last_user_msg:
            logger.warning("[WARNING NEUROCHAT] Last user message is empty.", exc_info=True)
            return False

        return True

    async def generate_response(
        self,
        conversation_history: List[Dict[str, str]],
        username: Optional[str] = None,
        server_id: Optional[str] = None,
        bot=None,
        message=None,
    ) -> str:
        """Generate response based on conversation history with integrated tool execution."""
        try:
            if not self._validate_messages(conversation_history):
                logger.error("[ERROR NEUROCHAT] Message validation failed.", exc_info=True)
                return "Je n'ai pas pu comprendre votre message. Pouvez-vous reformuler ?"

            last_user_msg = next((m["content"] for m in reversed(conversation_history) if m["role"] == "user"), "")

            server_mode = None
            if server_id:
                server_mode = await self._get_server_mode(server_id)

            api_messages = await self._prepare_messages(
                conversation_history=conversation_history,
                username=username,
                server_mode=server_mode,
            )

            if not api_messages:
                return "Je n'ai pas pu initialiser la conversation. Veuillez réessayer."

            # Support mode: Vector RAG search only (TSE)
            if server_mode == "support":
                tse_chunks = await asyncio.to_thread(self.tse.call_tutorial_engine, last_user_msg)
                if not tse_chunks:
                    return "Je n'ai pas trouvé d'information correspondante dans les tutoriels."

                tse_context = "\n\n".join(tse_chunks)
                api_messages[0]["content"] += f"\n\n[Tutorial Context:\n{tse_context}]"
                return await self._execute_groq_call(api_messages)

            # Standard mode with Agentic Tool Calling
            tool_manager = AIToolManager(bot, message) if bot and message else None
            available_tools = tool_manager.get_tools(server_id) if tool_manager else []

            if available_tools:
                response = await self.client.chat.completions.create(
                    model=params.GROQ_MODEL,
                    messages=api_messages,
                    tools=available_tools,
                    tool_choice="auto",
                    max_tokens=params.GROQ_MAX_TOKENS,
                    temperature=params.GROQ_TEMPERATURE,
                    top_p=params.GROQ_TOP_P,
                    frequency_penalty=params.GROQ_FREQUENCY,
                    presence_penalty=params.GROQ_PRESENCE_PENALTY,
                    stop=params.GROQ_STOP,
                )
            else:
                response = await self.client.chat.completions.create(
                    model=params.GROQ_MODEL,
                    messages=api_messages,
                    max_tokens=params.GROQ_MAX_TOKENS,
                    temperature=params.GROQ_TEMPERATURE,
                    top_p=params.GROQ_TOP_P,
                    frequency_penalty=params.GROQ_FREQUENCY,
                    presence_penalty=params.GROQ_PRESENCE_PENALTY,
                    stop=params.GROQ_STOP,
                )

            if not response or not response.choices:
                logger.error("[ERROR NEUROCHAT] Empty API response on initial call.", exc_info=True)
                return "Je n'ai pas pu générer de réponse. Veuillez réessayer."

            response_message = response.choices[0].message

            # Process tool execution requests if requested by LLM
            if response_message.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in response_message.tool_calls
                    ],
                }
                if response_message.content:
                    assistant_msg["content"] = response_message.content
                api_messages.append(assistant_msg)

                async def execute_tool(tool_call):
                    if tool_manager:
                        return await tool_manager.execute_tool(tool_call, last_user_msg, server_id)
                    return {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": "Error: AIToolManager not initialized.",
                    }

                tool_results = await asyncio.gather(*(execute_tool(tc) for tc in response_message.tool_calls))
                api_messages.extend(tool_results)

                # Second Groq call with tool results injected
                return await self._execute_groq_call(api_messages)

            reply = response_message.content
            return reply.strip() if reply else "Je n'ai pas de réponse à fournir pour le moment."

        except GroqError as error:
            logger.error(f"[ERROR NEUROCHAT] Groq API error: {error}", exc_info=True)
            if "rate_limit" in str(error).lower():
                return "Trop de requêtes simultanées. Veuillez patienter quelques secondes."
            elif "invalid" in str(error).lower():
                return "Erreur de configuration de l'API. Contactez un administrateur."
            else:
                return "Erreur lors de la communication avec l'API. Veuillez réessayer."

        except Exception as error:
            logger.error(f"[ERROR NEUROCHAT] Unexpected error: {error}", exc_info=True)
            return "Une erreur inattendue s'est produite. Veuillez contacter un administrateur."

    async def _execute_groq_call(self, api_messages: List[Dict[str, Any]]) -> str:
        """Helper to execute final Groq completion call."""
        response = await self.client.chat.completions.create(
            model=params.GROQ_MODEL,
            messages=api_messages,
            max_tokens=params.GROQ_MAX_TOKENS,
            temperature=params.GROQ_TEMPERATURE,
            top_p=params.GROQ_TOP_P,
            frequency_penalty=params.GROQ_FREQUENCY,
            presence_penalty=params.GROQ_PRESENCE_PENALTY,
            stop=params.GROQ_STOP,
        )
        if not response or not response.choices:
            logger.error("[ERROR NEUROCHAT] Empty response on final API call.", exc_info=True)
            return "Je n'ai pas pu générer de réponse finale."

        reply = response.choices[0].message.content
        return reply.strip() if reply else "Je n'ai pas de réponse à fournir pour le moment."

    async def generate_simple_response(
        self,
        user_message: str,
        username: Optional[str] = None,
    ) -> str:
        """Generate response for a single message without history."""
        conversation_history = [{"role": "user", "content": user_message}]
        return await self.generate_response(conversation_history, username)
