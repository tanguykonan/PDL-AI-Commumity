"""Configuration parameters and environment settings for the PDL-AI bot."""

import os
from pathlib import Path
import tomli
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as error:
    print(f"[FATAL ERROR] Failed to load .env file: {error}")

with open("settings/resources/strings/prompts.toml", "rb") as file:
    _PROMPT = tomli.load(file)

# Discord bot configuration
NAME = os.getenv("NAME")
PREFIX = os.getenv("PREFIX")
VERSION = os.getenv("VERSION")
GROQ_TOKEN = os.getenv("GROQ_TOKEN")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Storage and file paths
TEMP_PATH = "app/cluster/ram/temp/"
RAG_PATH = "app/cluster/rom/servers/log/"
RAG_FILE_MAX_LINES = 30
META_PATH = "app/cluster/rom/"
ERROR_PATH = "debug/error.log"
WARNING_PATH = "debug/warning.log"
DATABASE_PATH = "app/cluster/rom/datas/db.json"
TESSERACT_PATH = "/usr/bin/tesseract"

# Memory engine parameters (DDR)
META_LIMIT = 5
META_CLEAR_TIME = 1440
META_USER_LIMIT = 60
META_SERVER_LIMIT = 200
META_INACTIVE_TIME = 0.1
META_CONTEXT_MESSAGES = 20
META_SERVER_INJECT = 6
META_SUMMARY_THRESHOLD = 40
META_SAVE_EVERY = 5

# Runtime timing (seconds)
STATUS_UPDATE_TIME = 5
FLOWTYPE_TIME = 0.5

# Support and guild identity
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL")
SUPPORT_MEMBERS = os.getenv("SUPPORT_MEMBERS")

# LLM generation parameters (Groq)
GROQ_MODEL = os.getenv("GROQ_MODEL")
GROQ_STOP = []
GROQ_TOP_P = 0.9
GROQ_FREQUENCY = 0.4
GROQ_MAX_TOKENS = 1024
GROQ_TEMPERATURE = 0.9
GROQ_PRESENCE_PENALTY = 0.5

# System prompts
PERSONALITY_PROMPT = _PROMPT["PERSONALITY"]

# Web Search Engine configuration (Tavily)
TAVILY_TOKEN = os.getenv("TAVILY_TOKEN")
TAVILY_TOPIC = ["general", "news", "finance"]
TAVILY_DEPTH = ["basic", "advanced", "fast", "ultra-fast"]
TAVILY_MAX_TEXT_LENGTH = 256
TAVILY_MIN_QUERY_LENGTH = 10
TAVILY_MAX_SEARCH_RESULTS = 5
TAVILY_TIME_RANGE = ["day", "week", "month", "year"]
TAVILY_INCLUDE_DOMAINS = []
TAVILY_EXCLUDE_DOMAINS = [
    "dailymail.co.uk",
    "tmz.com",
    "buzzfeed.com",
    "infowars.com",
    "rt.com",
    "sputniknews.com",
    "reddit.com",
    "quora.com",
    "yahoo.answers.com",
    "medium.com",
    "blogspot.com",
    "wordpress.com",
]
TAVILY_INCLUDE_RAW_CONTENT = True
TAVILY_INCLUDE_ANSWER = ["advanced", "basic"]
TAVILY_RELEVANCE_SCORE = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

# Tutorial Search Engine configuration (TSE)
TSE_FILE_PATH = "settings/resources/strings/tutoriels.md"
TSE_CHUNK_SIZE = 150
TSE_COLLECTION_NAME = "hands_on_training"
TSE_TOP_N = 2

# Lavalink audio nodes configuration
LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PORT = os.getenv("LAVALINK_PORT")
LAVALINK_PASS = os.getenv("LAVALINK_PASS")
RETRY_ATTEMPTS = 3
CONNEXION_TIMEOUT = 30
HEALTHCHECK_INTERVAL = 120