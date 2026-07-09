import os
import yaml
import discord

from dotenv import load_dotenv
from discord import app_commands

#.env laden
load_dotenv()

TOKEN = os.environ['DISCORD_BOT_TOKEN']

# config.yml laden
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

ALLOWED_SERVER_IDS = set(config['allowed_server_ids'])
TRIGGER_WORD = config['triggerword']
RESPONSE_MESSAGE = config['response_message']
COMMAND_NAME = config['command_name']

#intents defineiren
intents = discord.Intents.default()
intents.message_content = True

class Triggerbot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        for guild_id in ALLOWED_SERVER_IDS:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

client = Triggerbot()

@client.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_SERVER_IDS:
        await guild.leave()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None or message.guild.id not in ALLOWED_SERVER_IDS:
        return
    if TRIGGER_WORD.lower() in message.content.lower():
        await message.channel.send(RESPONSE_MESSAGE)

@client.tree.command(name=COMMAND_NAME, description="Trigger the bot to send a response.")
async def trigger_command(interaction: discord.Interaction):
    if interaction.guild is None or interaction.guild.id not in ALLOWED_SERVER_IDS:
        await interaction.response.send_message("Not allowed", ephemeral=True)
        return
    await interaction.response.send_message(RESPONSE_MESSAGE)

client.run(TOKEN)