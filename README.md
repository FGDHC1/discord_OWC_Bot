# discord_OWC_Bot

A simple Discord bot that watches for a configurable trigger word in messages, keeps a per-user count, and reports it via a slash command.

## Features

- Detects a trigger word (case-insensitive) across all text channels of the allowed servers
- Tracks how often each user has said the word, per server (SQLite)
- Backfill: on first startup, the bot scans the entire existing message history once to catch up on past mentions
- Slash command to query your own count
- Optional server allowlist

## Requirements

- Docker & Docker Compose
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- The `message_content` intent enabled under *Privileged Gateway Intents* in the Developer Portal

## Repository structure

```
.
├── .gitignore
├── Dockerfile
├── LICENSE
├── README.md
├── docker-compose.yml
└── bot/
    ├── .env.template
    ├── bot.py
    ├── config.yml
    └── requirements.txt
```

## Setup: Discord Developer Portal
1. Create an application in the [Developer Portal](https://discord.com/developers/applications)
2. Under **Bot**:
   - Enable **Message Content Intent** (under "Privileged Gateway Intents")
   - Disable **Public Bot** so only you can invite the bot (optional)
   - Generate and copy the Token
3. Under **OAuth2** -> **OAuth2 URL Generator**:
   - Scopes: `bot`, `applications.commands
   - Bot permissions: `Send Messages`, `Read Message History``
   - Open the generated URL to invite the bot to your server



## Setup: Deploy

1. Clone the repository.

2. Create your environment file from the template inside `bot/`:
   ```bash
   cp bot/.env.template bot/.env
   ```
   Then open `bot/.env` and add your bot token:
   ```
   DISCORD_BOT_TOKEN="your_token_here"
   ```

3. Adjust `bot/config.yml` to your needs (see [Configuration](#configuration) below).

4. Build and start the bot:
   ```bash
   docker compose up -d --build
   ```

5. Check the logs to confirm it started correctly:
   ```bash
   docker compose logs -f
   ```
   On first startup you'll see a backfill run — this can take a while on servers with a long message history.

## Configuration

All bot behavior is controlled via `bot/config.yml`:

| Key | Type | Description |
|---|---|---|
| `allowed_server_ids` | list of integers (optional) | Discord server (guild) IDs the bot is allowed to operate on. See allowlist behavior below. |
| `triggerword` | string | The word to track (matched case-insensitively, as a substring) |
| `response_message` | string | Reply text for the slash command. Supports the placeholders `{user}`, `{count}`, and `{triggerword}` |
| `command_name` | string | Name of the slash command users will type (e.g. `/command_name`) |
 
**Allowlist behavior (`allowed_server_ids`):**
 
| Config state | Behavior |
|---|---|
| Key not there | No restriction, the bot operates on any server it's invited to |
| Key present but empty (`allowed_server_ids: []`) | The bot leaves every server immediately (effectively disabled) |
| Key present with one or more IDs | The bot only operates on the listed servers and leaves any other |

**Example:**
```yaml
allowed_server_ids:
  - 123456789012345678  # Replace with your Discord server ID
triggerword: example 
response_message: "{user} has said '{triggerword}' {count} times!"
command_name: example_command
```

To find a Discord server ID, right klick into the server-icon in your sidebar choose `Copy Server-ID`

## Usage

Once running, type `/<command_name>` in any allowed server to see how many times you've said the trigger word.

## Known limitations

- `counts.db` is not currently mounted on a persistent volume — a container rebuild will wipe the counts and trigger a full backfill on next startup. Consider adding a volume mapping for `counts.db` if you want the data to survive rebuilds.

## License

This project is licensed under the [MIT License](LICENSE).
