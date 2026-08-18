# ==================================================================================
# ============================ PARAMÈTRE DU BOT DISCORD ============================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 03/04/2026
# ==================================================================================
import json
import asyncio
from groq import AsyncGroq, GroqError
from app.helps.utils import logger
from settings.config import params
from typing import List, Dict, Optional, Any
from plugins.integrating.storing.database import database
from plugins.processing.agenticRag.wse import WebSearchEngine
from plugins.processing.agenticRag.ise import InternalSearchEngine
from plugins.processing.agenticRag.tse import TutorialSearchEngine
from app.core.ai_tools import AIToolManager

class ChatEngine:
    def __init__(self, max_history_per_user: int = params.META_LIMIT):
        try:
            if not params.GROQ_TOKEN:
                logger.error("[ERROR NEUROCHAT]=> Groq Token invalide")
                print('[ERROR NEUROCHAT]=> Groq Token invalide')
                return

            # Utilisation du client asynchrone pour éviter de bloquer l'Event Loop !
            self.client = AsyncGroq(api_key=params.GROQ_TOKEN) 
            self.personality_prompt = params.PERSONALITY_PROMPT
            self.max_history_per_user = max_history_per_user
            
            self.wse = WebSearchEngine()
            self.ise = InternalSearchEngine()
            self.tse = TutorialSearchEngine()
            
            # Note: La gestion des outils (Function Calling) a été déplacée vers AIToolManager

            # Dictionnaire constant défini au niveau de l'instance pour éviter la recréation
            self.mode_mapping = {
                'défaut': 'default',
                'caveman': 'caveman',
                'cartman': 'eric_cartman',
                'homerSimpson': 'homer_simpson',
                'support': 'support'
            }

        except ValueError as err:
            logger.error(f'[ERROR NEUROCHAT]=> Une valeur d\'initialisation est incorrecte: {err}', exc_info=True)
            raise
        except Exception as err:
            logger.error(f'[ERROR NEUROCHAT]=> Une erreur d\'initialisation s\'est produite: {err}', exc_info=True)
            raise

    async def _get_server_mode(self, server_id: str) -> str:
        """Récupère le mode du serveur de manière asynchrone pour ne pas bloquer l'Event Loop"""
        try:
            server_config = await asyncio.to_thread(database.get_server_config, server_id=server_id)
            if server_config and 'mode' in server_config:
                return server_config['mode']
            return 'default'
        except Exception as e:
            logger.error(f"[ERROR NEUROCHAT]-> Erreur récupération mode serveur: {e}", exc_info=True)
            return 'default'

    async def _build_system_prompt(
            self,
            username: Optional[str] = None,
            server_mode: Optional[str] = None
    ) -> str:
        """Construction du prompt système avec le nom d'utilisateur"""
        chosen_mode = self.mode_mapping.get(server_mode, 'default') if server_mode else 'default'
        base_prompt = self.personality_prompt.get(chosen_mode, self.personality_prompt.get('default', 'Tu es un assistant IA.'))

        if username:
            user_context = (
                f"\n\n📋 **Contexte de conversation**\n"
                f"Tu discutes avec l'utilisateur Discord : **{username}**\n"
                f"Utilise ce prénom/pseudo naturellement dans tes réponses quand c'est approprié, "
                f"mais ne le répète pas systématiquement. Sois en harmonie avec ta personnalité."
            )
            return base_prompt + user_context
            
        return base_prompt

    async def _prepare_messages(
            self,
            conversation_history: List[Dict[str, str]],
            username: Optional[str] = None,
            server_mode: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Préparation des messages pour l'API en ajoutant le system prompt"""
        try:
            system_prompt = await self._build_system_prompt(username=username, server_mode=server_mode)
            messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

            if conversation_history:
                # Troncature de l'historique en fonction de la limite configurée
                if self.max_history_per_user > 0:
                    truncated_history = conversation_history[-self.max_history_per_user:]
                else:
                    truncated_history = conversation_history
                messages.extend(truncated_history)
            
            return messages
        except Exception as error:
            logger.error(f'[ERROR NEUROCHAT]=> Préparation des messages échoué {error}', exc_info=True)
            return []

    @staticmethod
    def _validate_messages(messages: List[Dict[str, str]]) -> bool:
        """Validation de la structure des messages"""
        if not messages or not isinstance(messages, list):
            logger.warning("[WARNING NEUROCHAT]-> Messages vides ou format invalide", exc_info=True)
            return False

        has_user_message = any(msg.get("role") == "user" for msg in messages)
        if not has_user_message:
            logger.warning("[WARNING NEUROCHAT]-> Aucun message utilisateur trouvé", exc_info=True)
            return False

        last_user_msg = next((msg.get("content", "").strip() for msg in reversed(messages) if msg.get("role") == "user"), None)

        if not last_user_msg:
            logger.warning("[WARNING NEUROCHAT]-> Dernier message utilisateur vide", exc_info=True)
            return False

        return True

    async def generate_response(
            self,
            conversation_history: List[Dict[str, str]],
            username: Optional[str] = None,
            server_id: Optional[str] = None,
            bot=None,
            message=None
    ) -> str:
        """Génère une réponse basée sur l'historique de conversation (Tool Use / Function Calling intégré)"""
        try:
            if not self._validate_messages(conversation_history):
                logger.error("[ERROR NEUROCHAT]-> Validation des messages échouée", exc_info=True)
                return "Je n'ai pas pu comprendre votre message. Pouvez-vous reformuler ?"

            last_user_msg = next((m["content"] for m in reversed(conversation_history) if m["role"] == "user"), "")

            # ── Détection du mode serveur ─────────────────────────────
            server_mode = None
            if server_id:
                server_mode = await self._get_server_mode(server_id)

            api_messages = await self._prepare_messages(
                conversation_history=conversation_history,
                username=username,
                server_mode=server_mode
            )
            
            if not api_messages:
                return "Je n'ai pas pu initialiser la conversation. Veuillez réessayer."

            # ── Mode support : TSE uniquement ─────────────────────────
            if server_mode == 'support':
                tse_chunks = await asyncio.to_thread(self.tse.call_tutorial_engine, last_user_msg)
                if not tse_chunks:
                    return "Je n'ai pas trouvé de tutoriel correspondant à votre question."

                tse_context = "\n\n".join(tse_chunks)
                api_messages[0]["content"] += f"\n\n[Contexte tutoriel: {tse_context}]"
                
                # Exécution simple sans outils
                return await self._execute_groq_call(api_messages)

            # ── Mode standard avec Tool Calling ───────────────────────
            
            # Instanciation du gestionnaire d'outils
            tool_manager = AIToolManager(bot, message) if bot and message else None
            
            # Récupération des outils disponibles
            available_tools = tool_manager.get_tools(server_id) if tool_manager else []

            # 1er appel à Groq (avec outils)
            if available_tools:
                response = await self.client.chat.completions.create(
                    model=params.GROQ_MODEL, #type:ignore
                    messages=api_messages, #type:ignore
                    tools=available_tools, #type:ignore
                    tool_choice="auto",
                    max_tokens=params.GROQ_MAX_TOKENS,
                    temperature=params.GROQ_TEMPERATURE,
                    top_p=params.GROQ_TOP_P,
                    frequency_penalty=params.GROQ_FREQUENCY,
                    presence_penalty=params.GROQ_PRESENCE_PENALTY,
                    stop=params.GROQ_STOP
                )
            else:
                response = await self.client.chat.completions.create(
                    model=params.GROQ_MODEL, #type:ignore
                    messages=api_messages, #type:ignore
                    max_tokens=params.GROQ_MAX_TOKENS,
                    temperature=params.GROQ_TEMPERATURE,
                    top_p=params.GROQ_TOP_P,
                    frequency_penalty=params.GROQ_FREQUENCY,
                    presence_penalty=params.GROQ_PRESENCE_PENALTY,
                    stop=params.GROQ_STOP
                )

            if not response or not response.choices:
                logger.error("[ERROR NEUROCHAT]-> Réponse API vide ou invalide (1er appel)", exc_info=True)
                return "Je n'ai pas pu générer de réponse. Veuillez réessayer."

            response_message = response.choices[0].message
            
            # Si le LLM veut utiliser un outil
            if response_message.tool_calls:
                # Ajout de l'intention d'outil de l'assistant dans l'historique
                assistant_msg = {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in response_message.tool_calls
                    ]
                }
                if response_message.content:
                    assistant_msg["content"] = response_message.content
                api_messages.append(assistant_msg)

                # Exécution des outils en parallèle via le ToolManager
                async def execute_tool(tool_call):
                    if tool_manager:
                        return await tool_manager.execute_tool(tool_call, last_user_msg, server_id)
                    else:
                        return {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": "Erreur : AIToolManager non initialisé (bot ou message manquant)."
                        }

                # On attend que tous les outils soient exécutés
                tool_results = await asyncio.gather(*(execute_tool(tc) for tc in response_message.tool_calls))
                api_messages.extend(tool_results)

                # 2ème appel à Groq (avec les résultats des outils injectés) pour générer la réponse finale
                return await self._execute_groq_call(api_messages)

            # Si pas d'appel d'outil, on renvoie simplement la réponse directe
            reply = response_message.content
            return reply.strip() if reply else "Je n'ai pas de réponse à fournir pour le moment."

        except GroqError as error:
            logger.error(f"[ERROR NEUROCHAT]-> Erreur API Groq: {error}", exc_info=True)
            if "rate_limit" in str(error).lower():
                return "Trop de requêtes simultanées. Veuillez patienter quelques secondes."
            elif "invalid" in str(error).lower():
                return "Erreur de configuration de l'API. Contactez un administrateur."
            else:
                return "Erreur lors de la communication avec l'API. Veuillez réessayer."

        except Exception as error:
            logger.error(f"[ERROR NEUROCHAT]-> Erreur inattendue: {error}", exc_info=True)
            return "Une erreur inattendue s'est produite. Veuillez contacter un administrateur (/help)."

    async def _execute_groq_call(self, api_messages: List[Dict[str, Any]]) -> str:
        """Méthode utilitaire pour factoriser le dernier appel à Groq"""
        response = await self.client.chat.completions.create(
            model=params.GROQ_MODEL, #type:ignore
            messages=api_messages, #type:ignore
            max_tokens=params.GROQ_MAX_TOKENS,
            temperature=params.GROQ_TEMPERATURE,
            top_p=params.GROQ_TOP_P,
            frequency_penalty=params.GROQ_FREQUENCY,
            presence_penalty=params.GROQ_PRESENCE_PENALTY,
            stop=params.GROQ_STOP
        )
        if not response or not response.choices:
            logger.error("[ERROR NEUROCHAT]-> Réponse API finale vide ou invalide", exc_info=True)
            return "Je n'ai pas pu générer de réponse finale."
            
        reply = response.choices[0].message.content
        return reply.strip() if reply else "Je n'ai pas de réponse à fournir pour le moment."

    async def generate_simple_response(
            self,
            user_message: str,
            username: Optional[str] = None
    ) -> str:
        """Génère une réponse simple sans historique de conversation"""
        conversation_history = [
            {"role": "user", "content": user_message}
        ]
        return await self.generate_response(conversation_history, username)
