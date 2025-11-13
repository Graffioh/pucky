# pucky

A tiny coding agent with minimal dependencies 🐤.

If you want to understand the general workflow of a coding agent without too much abstraction and with an easy to read language, then this is for you 🫵.

Otherwise go read [codex](https://github.com/openai/codex/tree/main/codex-rs) rust repository.

## Setup

1) Clone the repository:
```bash
git clone https://github.com/Graffioh/pucky.git
```

2) Install `uv` if you don't have it already, follow [this](https://docs.astral.sh/uv/getting-started/installation/)

3) Create virtual environment:
```bash
uv venv
```

4) Install packages:
```bash
uv pip install .
```

5) Create a `.env` file with your Google API key (can be obtained [here](https://aistudio.google.com/api-keys)):
```bash
echo "GOOGLE_API_KEY=<your_api_key>" > .env
```

6) Run the agent:
```bash
uv run src/main.py
```

