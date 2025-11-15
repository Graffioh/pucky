# pucky

A tiny coding agent with minimal dependencies 🐤.

<img width="819" height="588" alt="image" src="https://github.com/user-attachments/assets/04204f1e-7344-4695-8c62-c1d99081da1c" />

If you want to understand the general workflow of a coding agent without too much abstraction and with an easy to read language, then this is for you 🫵.

Otherwise go read [codex](https://github.com/openai/codex/tree/main/codex-rs) rust repository.

## Dependencies

- `google-genai`

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

(If you want to experiment while changing the code, then use `-e` flag)

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

Ask pucky to read/edit/create/remove files, then `y` to accept / `n` to decline.

Type `quit` or `q` to quit pucky.

### Async commands (context prep)

While the CLI is running you can execute local commands prefixed with `@` to
stage context without immediately querying the LLM:

- `@file path/to/file` &mdash; read a file and inline its content into the next prompt
- `@help` &mdash; list all available async commands

You can chain multiple `@file` commands and then type your actual question. The
agent will see every staged file before answering.

## Warning

Right now there is no security check for *dangerous* operations, so **be careful, everything is at your own risk!!!**.

## Feedback

For feedbacks, DM me on [X](https://x.com/graffioh).
