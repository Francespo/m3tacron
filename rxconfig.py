import reflex as rx
import os
import importlib

# Determine which environment configuration to use (beta or prod)
# Default to "prod" if not specified
reflex_env = os.environ.get("REFLEX_ENV", "prod").lower()

if reflex_env == "beta":
    from rxconfig_beta import config
else:
    from rxconfig_prod import config