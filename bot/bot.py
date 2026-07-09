import os
import yaml
import discord
import sqlite3

from dotenv import load_dotenv
from discord import app_commands


#sqlite3 initialisieren
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
                    if TRIGGER_WORD.lower() in message.content.lower():
                        increment_count(guild_id, message.author.id)
            except discord.Forbidden:
                print(f"Kein Zugriff auf {channel.name}, überspringe.", flush=True)

def backfill_already_done() -> bool:
    row = db.execute("SELECT value FROM meta WHERE key = 'backfill_done'").fetchone()
    return row is not None

def mark_backfill_done():
    db.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('backfill_done', '1')")
    db.commit()

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

#setup discord client
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

#At startup, check if backfill has already been done. If not, perform backfill of message history to count trigger word occurrences.
@client.event
async def on_ready():
    print(f"Eingeloggt als {client.user}", flush=True)
    if not backfill_already_done():
        print("Starte Backfill der Nachrichten-Historie...", flush=True)
        await backfill_counts()
        mark_backfill_done()
        print("Backfill abgeschlossen.", flush=True)

#check if the bot is allowed to join the server. If not, leave immediately.
@client.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_SERVER_IDS:
        await guild.leave()


#check message for trigger and increment count if found.
@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None or message.guild.id not in ALLOWED_SERVER_IDS:
        return
    if TRIGGER_WORD.lower() in message.content.lower():
        increment_count(message.guild.id, message.author.id)
        
#define the slash command to trigger the bot's response
@client.tree.command(name=COMMAND_NAME, description="Get the count of how many times you said the trigger word.")
async def trigger_command(interaction: discord.Interaction):
    if interaction.guild is None or interaction.guild.id not in ALLOWED_SERVER_IDS:
        await interaction.response.send_message("Not allowed", ephemeral=True)
        return
    count = get_count(interaction.guild_id, interaction.user.id)
    await interaction.response.send_message(RESPONSE_MESSAGE.format(count=count, user=interaction.user.mention, triggerword=TRIGGER_WORD))

client.run(TOKEN)