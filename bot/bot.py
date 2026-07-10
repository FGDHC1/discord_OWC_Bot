import os
import yaml
import discord
import sqlite3

from dotenv import load_dotenv
from discord import app_commands


#sqlite3 initialisation
db = sqlite3.connect('counts.db')
db.execute("""
    CREATE TABLE IF NOT EXISTS counts (
        guild_id INTEGER,
        user_id INTEGER,
        count INTEGER DEFAULT 0,
        PRIMARY KEY (guild_id, user_id)
    )
""")
db.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
""")
db.commit()


#increment the count for a specific user in a specific guild
def increment_count(guild_id: int, user_id: int) -> None:
    db.execute("""
        INSERT INTO counts (guild_id, user_id, count) VALUES (?, ?, 1)
        ON CONFLICT(guild_id, user_id) DO UPDATE SET count = count + 1
    """, (guild_id, user_id))
    db.commit()

#get the count for a specific user in a specific guild
def get_count(guild_id: int, user_id: int) -> int:
    row = db.execute(
        "SELECT count FROM counts WHERE guild_id = ? AND user_id = ?",
        (guild_id, user_id)
    ).fetchone()
    return row[0] if row else 0

# Search for the triggerword in the message history of all allowed servers and increment counts accordingly
async def backfill_counts():
    for guild_id in ALLOWED_SERVER_IDS:
        guild = client.get_guild(guild_id)
        if guild is None:
            continue
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None):
                    if message.author.bot:
                        continue
                    if any(word in message.content.lower() for word in TRIGGER_WORDS):
                        increment_count(guild.id, message.author.id)
            except discord.Forbidden:
                print(f"No permission on {channel.name}, skipping.", flush=True)

def backfill_already_done() -> bool:
    row = db.execute("SELECT value FROM meta WHERE key = 'backfill_done'").fetchone()
    return row is not None

def mark_backfill_done():
    db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('backfill_done', '1')")
    db.commit()

#load .env
load_dotenv()

TOKEN = os.environ['DISCORD_BOT_TOKEN']

#load config.yml 
with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

RESTRICT_SERVERS = "allowed_server_ids" in config
ALLOWED_SERVER_IDS = set(config.get('allowed_server_ids', []))
RESPONSE_MESSAGE = config['response_message']
COMMAND_NAME = config['command_name']
if "triggerwords" in config:
    TRIGGER_WORDS = [word.lower() for word in config['triggerwords']]
elif "triggerword" in config:
    TRIGGER_WORDS = [config['triggerword'].lower()]
elif "triggerword" in config and "triggerwords" in config:
    raise ValueError("Please specify either 'triggerword' or 'triggerwords', not both, in the config.yml file.")
else:
    raise ValueError("Please specify a 'triggerword' in the config.yml file.")

#define intents
intents = discord.Intents.default()
intents.message_content = True

#setup discord client
class Triggerbot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        if RESTRICT_SERVERS:
            for guild_id in ALLOWED_SERVER_IDS:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                try:
                    await self.tree.sync(guild=guild)
                except discord.Forbidden:
                    print(f"Failed to sync commands for guild {guild_id}. Bot may not have permission.")
        else:
            await self.tree.sync()

client = Triggerbot()

#At startup, check if backfill has already been done. If not, perform backfill of message history to count trigger word occurrences.
@client.event
async def on_ready():
    print(f"Logged in as {client.user}", flush=True)
    if not backfill_already_done():
        print("Starting backfill of message history...", flush=True)
        await backfill_counts()
        mark_backfill_done()
        print("Backfill completed.", flush=True)

#check if the bot is allowed to join the server. If not, leave immediately.
@client.event
async def on_guild_join(guild):
    if RESTRICT_SERVERS and guild.id not in ALLOWED_SERVER_IDS:
        await guild.leave()


#check message for trigger and increment count if found.
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None:
        return
    if RESTRICT_SERVERS and message.guild.id not in ALLOWED_SERVER_IDS:
        return
    if any(word in message.content.lower() for word in TRIGGER_WORDS):
        increment_count(message.guild.id, message.author.id)
        
#define the slash command to trigger the bot's response
@client.tree.command(name=COMMAND_NAME, description="Get the count of how many times you said the trigger word.")
async def trigger_command(interaction: discord.Interaction):
    if interaction.guild is None or interaction.guild.id not in ALLOWED_SERVER_IDS:
        await interaction.response.send_message("Not allowed", ephemeral=True)
        return
    count = get_count(interaction.guild_id, interaction.user.id)
    await interaction.response.send_message(RESPONSE_MESSAGE.format(count=count, user=interaction.user.mention, triggerword=", ".join(TRIGGER_WORDS)))

client.run(TOKEN)