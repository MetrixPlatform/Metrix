from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PresetImage:
    image: str
    language: str
    run_command: str
    use_venv: bool


PRESET_IMAGES: tuple[PresetImage, ...] = (
    PresetImage("python:3.13.11-slim", "python", "python main.py", True),
    PresetImage("python:3.12-slim", "python", "python main.py", True),
    PresetImage("python:3.11-slim", "python", "python main.py", True),
    PresetImage("node:20-slim", "node", "node index.js", False),
    PresetImage("node:18-slim", "node", "node index.js", False),
    PresetImage("golang:1.22", "go", "go run .", False),
    PresetImage("alpine:3.20", "shell", "sh main.sh", False),
    PresetImage("bash:5.2", "shell", "bash main.sh", False),
)
