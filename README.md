# discord_WC_Bot

A simple Discord bot that watches for a configurable trigger word in messages, keeps a per-user count, and reports it via a slash command.

## Features

- Detects a trigger word (case-insensitive) across all text channels of the allowed servers
- Tracks how often each user has said the word, per server (SQLite)
- Backfill: on first startup, the bot scans the entire existing message history once to catch up on past mentions
- Slash command to query your own count
- Automatically leaves any server that isn't on the allowlist

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

## Installation

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
| `allowed_server_ids` | list of integers | Discord server (guild) IDs the bot is allowed to operate on. If the bot is added to any other server, it leaves immediately. |
| `triggerword` | string | The word to track (matched case-insensitively, as a substring) |
| `response_message` | string | Reply text for the slash command. Supports the placeholders `{user}`, `{count}`, and `{triggerword}` |
| `command_name` | string | Name of the slash command users will type (e.g. `/command_name`) |

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
