# Migration Guide - Modular Structure

This guide explains how the refactoring affects users and developers.

## For Users

### No Changes Required
- All existing commands work exactly the same
- Configuration files (config.json, secret.json) remain unchanged
- Bot behavior and functionality is preserved
- All three modes (prod, debug, setup) work as before

### What Changed
- Code is now organized in modules instead of one large file
- Better error handling and logging
- Improved maintainability for future updates

## For Developers

### File Changes
- `bot_prod.py`: Simplified to use KumoBot class
- `bot_debug.py`: Simplified to use DebugBot class  
- `bot_setup.py`: Simplified to use SetupBot class
- New `kumo_bot/` package contains all modular code

### Adding Commands
Before (old structure):
```python
@bot.tree.command(name="mycommand")
async def mycommand(interaction: discord.Interaction):
    # command code
```

After (new structure):
```python
# In appropriate cog file
@app_commands.command(name="mycommand")
async def mycommand(self, interaction: discord.Interaction):
    # command code
```

### Accessing Configuration
Before:
```python
config = Config(bot)  # Global config
```

After:
```python
from variables import Config
config = Config(self.bot)  # In cog methods
```

### Import Changes
```python
# Old imports (no longer needed)
from variables import EMOJI_ALPHABET, VERSION, Config, Secret, handler, intents

# New imports (use specific modules)
from kumo_bot.utils.checks import vote_running, is_owner
from kumo_bot.utils.voting import parse_votemsg
from variables import Config  # Still needed for configuration
```

### Running the Bot
No changes - use the same entry points:
- `python bot_control.py` (automatic mode detection)
- `python bot_prod.py` (production mode)
- `python bot_debug.py` (debug mode)
- `python bot_setup.py` (setup mode)

## Benefits

### For Users
- More stable and reliable bot
- Better error messages
- Easier troubleshooting

### For Developers
- Cleaner, more organized code
- Easier to add new features
- Better separation of concerns
- Improved testing capabilities
- Reduced code duplication

## Compatibility

- ✅ All existing commands preserved
- ✅ Configuration system unchanged
- ✅ Deployment process unchanged
- ✅ Dependencies unchanged
- ✅ Bot behavior unchanged