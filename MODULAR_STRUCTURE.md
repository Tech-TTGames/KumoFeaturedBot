# KumoFeaturedBot - Modular Structure

This document describes the new modular structure of KumoFeaturedBot after the refactoring.

## Directory Structure

```
kumo_bot/
├── __init__.py              # Main package initialization
├── bot.py                   # Main KumoBot class with cog loading
├── debug_bot.py             # Debug-specific bot extension
├── setup_bot.py             # Setup-specific bot extension
├── config/                  # Configuration and constants
│   ├── __init__.py         # Config package initialization
│   ├── constants.py        # Constants (VERSION, EMOJI_ALPHABET, intents, handler)
│   └── settings.py         # Configuration classes (Config, Secret)
├── cogs/                    # Discord.py cogs for command organization
│   ├── __init__.py         # Auto-discovery of all cogs
│   ├── admin.py            # Admin commands (ping, version, blacklist, votecountmode, etc.)
│   ├── owner.py            # Owner-only commands (override, configuration)
│   ├── voting.py           # Voting commands (startvote, endvote, etc.)
│   └── events.py           # Event handlers (on_ready, on_command_error)
└── utils/                   # Shared utilities
    ├── __init__.py
    ├── checks.py           # Custom command checks
    ├── downloaders.py      # File download utilities
    └── voting.py           # Vote parsing utilities
```

## Main Bot Classes

### KumoBot (`kumo_bot/bot.py`)
The main bot class that:
- Initializes the Discord bot with proper intents and configuration
- Auto-loads all cogs using the discovery mechanism from Tickets-Plus
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

## Cogs

### UtilityCommands (`kumo_bot/cogs/utility.py`)
Basic utility commands:
- `/ping` - Check bot responsiveness
- `/version` - Display bot version

### AdminCommands (`kumo_bot/cogs/admin.py`)
Administrative and utility commands with role-based permissions:
- `/ping` - Check bot responsiveness
- `/version` - Display bot version
- `/blacklist` - Manage user blacklist
- `/votecountmode` - Configure vote counting
- `/accessrole` - Set bot access role
- `/setmention` - Set mention role
- `/pinops` - Pin/unpin messages
- `/download` - Download fanfiction files

### OwnerCommands (`kumo_bot/cogs/owner.py`)
Owner-only commands:
- `/override` - System commands (reboot, debug, log, pull)
- `/configuration` - View complete bot configuration

### VotingCommands (`kumo_bot/cogs/voting.py`)
Core voting functionality:
- `/startvote` - Start a new vote
- `/endvote` - End current vote
- `/autoclose` - Set automatic vote closing
- Vote processing and result calculation

### Events (`kumo_bot/cogs/events.py`)
Event handlers:
- Error handling for commands
- Bot ready event processing
- Vote auto-close functionality

## Configuration Management

### Constants (`kumo_bot/config/constants.py`)
Centralized constants following Tickets-Plus pattern:
- `VERSION` - Bot version string
- `EMOJI_ALPHABET` - Unicode emoji array for voting reactions  
- `intents` - Discord gateway intents configuration
- `handler` - Default logging handler configuration

### Settings (`kumo_bot/config/settings.py`)
Configuration management classes:
- `Secret` - Manages secret.json file access with token obfuscation
- `Config` - Comprehensive configuration management with auto-save properties

## Utility Modules

### Checks (`kumo_bot/utils/checks.py`)
Custom Discord command checks with improved permissions:
- `@vote_running()` - Ensure a vote is currently active
- `@is_owner()` - Restrict to bot owner using Discord.py app owner data
- `@has_admin_role()` - Allow configured admin role, Administrator permission, or owner

### Downloaders (`kumo_bot/utils/downloaders.py`)
File download utilities:
- `fetch_download()` - Download fanfiction from URLs
- Integration with lightnovel-crawler and FanFicFare

### Voting Utils (`kumo_bot/utils/voting.py`)
Vote processing utilities:
- `parse_votemsg()` - Parse vote messages for submissions

## Cog Discovery

Following the Tickets-Plus pattern, cogs are automatically discovered using:

```python
# In kumo_bot/cogs/__init__.py
import pkgutil
EXTENSIONS = [module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")]
```

This automatically finds all Python modules in the cogs directory and loads them as extensions.

## Entry Points

### `bot_control.py` (Recommended)
Main entry point that automatically detects mode and runs appropriate bot:
```python
from kumo_bot.bot import KumoBot
from kumo_bot.debug_bot import DebugBot  
from kumo_bot.setup_bot import SetupBot

def start_bot():
    # Automatically detects mode from config.json and runs appropriate bot
```

**Note**: The original bot files (`bot_prod.py`, `bot_debug.py`, `bot_setup.py`) have been removed as they were obsolete "launchpad" files that added unnecessary indirection.

## Benefits of Modular Structure

1. **Separation of Concerns**: Commands, events, and utilities are logically separated
2. **Maintainability**: Easier to modify and extend individual components
3. **Reusability**: Utility functions can be shared across modules
4. **Testing**: Individual modules can be tested in isolation
5. **Code Organization**: Clear structure makes navigation easier
6. **Scalability**: New commands and features can be added as separate cogs
7. **Auto-Discovery**: New cogs are automatically loaded without manual registration

## Migration Notes

- All original functionality has been preserved
- Command interfaces remain unchanged
- Configuration system unchanged
- All three operating modes (prod, debug, setup) maintained
- Existing config.json and secret.json files work unchanged
- **NEW**: Variables refactored from `variables.py` into `kumo_bot/config/` structure
- **NEW**: Owner commands separated into dedicated cog
- **NEW**: Permission checks improved with owner override support
- **NEW**: Bot control refactored to eliminate wrapper files
- **NEW**: Utility commands consolidated into admin cog for better organization
- **NEW**: Permission system uses Discord.py app owner data and Administrator permissions

## Adding New Features

### Adding a New Command
1. Add the command method to the appropriate cog class
2. Use proper Discord.py decorators (`@app_commands.command`)
3. Include type hints and docstrings

### Adding a New Cog
1. Create new file in `kumo_bot/cogs/`
2. Create a class inheriting from `commands.Cog`
3. Add `async def setup(bot):` function
4. The cog will be automatically discovered and loaded

### Adding New Utilities
1. Create new file in `kumo_bot/utils/`
2. Implement utility functions
3. Import in relevant cog modules