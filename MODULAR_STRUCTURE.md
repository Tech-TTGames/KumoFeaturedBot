# KumoFeaturedBot - Modular Structure

This document describes the new modular structure of KumoFeaturedBot after the refactoring.

## Directory Structure

```
kumo_bot/
├── __init__.py              # Main package initialization
├── bot.py                   # Main KumoBot class with cog loading
├── debug_bot.py             # Debug-specific bot extension
├── setup_bot.py             # Setup-specific bot extension
├── commands/                # Command modules (Discord.py cogs)
│   ├── __init__.py
│   ├── admin.py            # Admin commands (blacklist, override, etc.)
│   ├── voting.py           # Voting commands (startvote, endvote, etc.)
│   └── utility.py          # Utility commands (ping, version, config)
├── events/                 # Event handlers
│   ├── __init__.py
│   └── handlers.py         # Event handling (on_ready, on_command_error)
└── utils/                  # Shared utilities
    ├── __init__.py
    ├── checks.py           # Custom command checks
    ├── downloaders.py      # File download utilities
    └── voting.py           # Vote parsing utilities
```

## Main Bot Classes

### KumoBot (`kumo_bot/bot.py`)
The main bot class that:
- Initializes the Discord bot with proper intents and configuration
- Loads all command cogs automatically
- Sets up event handlers
- Manages the lightnovel-crawler integration
- Provides the main entry point for production mode

### DebugBot (`kumo_bot/debug_bot.py`)
Extended bot class for debug mode that:
- Inherits from KumoBot
- Adds debug-specific commands
- Uses debug prefix (`<`)
- Loads only essential cogs
- Provides debug-specific logging

### SetupBot (`kumo_bot/setup_bot.py`)
Specialized bot for initial setup that:
- Provides guided configuration setup
- Creates initial config.json file
- Minimal command set for setup only

## Command Modules (Cogs)

### UtilityCommands (`kumo_bot/commands/utility.py`)
Basic utility commands:
- `/ping` - Check bot responsiveness
- `/version` - Display bot version
- `/configuration` - Show current configuration (owner only)

### AdminCommands (`kumo_bot/commands/admin.py`)
Administrative commands:
- `/blacklist` - Manage user blacklist
- `/votecountmode` - Configure vote counting
- `/override` - Owner-only system commands
- `/accessrole` - Set bot access role
- `/setmention` - Set mention role
- `/pinops` - Pin/unpin messages
- `/download` - Download fanfiction files

### VotingCommands (`kumo_bot/commands/voting.py`)
Core voting functionality:
- `/startvote` - Start a new vote
- `/endvote` - End current vote
- `/autoclose` - Set automatic vote closing
- Vote processing and result calculation

## Utility Modules

### Checks (`kumo_bot/utils/checks.py`)
Custom Discord command checks:
- `@vote_running()` - Ensure a vote is currently active
- `@is_owner()` - Restrict to bot owner

### Downloaders (`kumo_bot/utils/downloaders.py`)
File download utilities:
- `fetch_download()` - Download fanfiction from URLs
- Integration with lightnovel-crawler and FanFicFare

### Voting Utils (`kumo_bot/utils/voting.py`)
Vote processing utilities:
- `parse_votemsg()` - Parse vote messages for submissions

### Event Handlers (`kumo_bot/events/handlers.py`)
Centralized event handling:
- Error handling for commands
- Bot ready event processing
- Vote auto-close functionality

## Entry Points

The original bot files now serve as simple entry points:

### `bot_prod.py`
Production mode entry point:
```python
from kumo_bot.bot import KumoBot

def start():
    bot = KumoBot()
    bot.run_bot()
```

### `bot_debug.py`
Debug mode entry point:
```python
from kumo_bot.debug_bot import DebugBot

def start():
    bot = DebugBot()
    bot.run_bot()
```

### `bot_setup.py`
Setup mode entry point:
```python
from kumo_bot.setup_bot import SetupBot

def start():
    bot = SetupBot()
    bot.run_bot()
```

## Benefits of Modular Structure

1. **Separation of Concerns**: Commands, events, and utilities are logically separated
2. **Maintainability**: Easier to modify and extend individual components
3. **Reusability**: Utility functions can be shared across modules
4. **Testing**: Individual modules can be tested in isolation
5. **Code Organization**: Clear structure makes navigation easier
6. **Scalability**: New commands and features can be added as separate cogs

## Migration Notes

- All original functionality has been preserved
- Command interfaces remain unchanged
- Configuration system unchanged
- All three operating modes (prod, debug, setup) maintained
- Existing config.json and secret.json files work unchanged

## Adding New Features

### Adding a New Command
1. Add the command method to the appropriate cog class
2. Use proper Discord.py decorators (`@app_commands.command`)
3. Include type hints and docstrings

### Adding a New Cog
1. Create new file in `kumo_bot/commands/`
2. Create a class inheriting from `commands.Cog`
3. Add `async def setup(bot):` function
4. Import and load in `kumo_bot/bot.py`

### Adding New Utilities
1. Create new file in `kumo_bot/utils/`
2. Implement utility functions
3. Import in relevant command modules