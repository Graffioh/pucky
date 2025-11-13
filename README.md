# pucky

A tiny coding agent with minimal dependencies 🐤.

If you want to understand the general workflow of a coding agent without too much abstraction and with an easy to read language, then this is for you 🫵.

Otherwise go read [codex](https://github.com/openai/codex/tree/main/codex-rs) rust repository.

## Requirements

- Python >= 3.10
- Install `uv` if you don't have it already, follow [this](https://docs.astral.sh/uv/getting-started/installation/)

## Setup

1) Clone the repository:
```bash
git clone https://github.com/Graffioh/pucky.git
cd pucky
```

2) Create virtual environment:
```bash
uv venv
```

3) Install packages:
```bash
uv pip install .
```

4) Add pucky to your PATH (add this to your `~/.zshrc` or `~/.bashrc`) so that you can run it with `pucky` cmd:
```bash
export PATH="$PATH:/path/to/pucky"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

5) Create a `.env` file in the pucky directory with your Google API key (can be obtained [here](https://aistudio.google.com/api-keys)):
```bash
echo "GOOGLE_API_KEY=<your_api_key>" > .env
```

## Usage

Run pucky from any directory (it will operate on that directory):
```bash
cd /path/to/your/project
pucky
```

Type 'quit' or 'q' to quit pucky.