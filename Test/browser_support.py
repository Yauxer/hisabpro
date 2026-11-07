"""Choix d'un navigateur Chromium local pour les recettes sans données réelles."""
import os
from pathlib import Path
import shutil


def chromium_executable():
    configured = os.getenv("HISABPRO_CHROMIUM_PATH")
    if configured:
        if not Path(configured).is_file():
            raise RuntimeError("HISABPRO_CHROMIUM_PATH ne désigne pas un fichier existant")
        return configured
    candidates = [shutil.which(name) for name in ("chromium", "chromium-browser", "google-chrome", "msedge")]
    candidates += [
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
    ]
    return next((p for p in candidates if p and Path(p).is_file()), None)
