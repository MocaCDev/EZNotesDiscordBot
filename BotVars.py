import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

class BotVars:
    # Token for the bot to run
    TOKEN = os.getenv('DISCORD_TOKEN')

    # Claude AI API reference for commands to use
    code_chat_model = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Intents for the bot
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Variables regarding the actual bot
    bot = commands.Bot(command_prefix = "!", intents=intents)
    BOT_COMMAND = bot.command

    # Command-specific variables that will get manipulated
    reports = {}
    channel_ids = []

    # Report channel ID
    report_channel_id = 1302510627155087402

    # ALl channel IDs
    channel_ids = []

    OWNERS = [
        722861836822904935,
        411200864733233153
    ]