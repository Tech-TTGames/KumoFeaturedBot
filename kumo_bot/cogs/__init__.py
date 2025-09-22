"""Cog modules for KumoFeaturedBot."""

import pkgutil

# Auto-discover all cogs in this package
EXTENSIONS = [
    module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")
]
