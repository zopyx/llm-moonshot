# zopyx.llm-moonshot
LLM plugin for Moonshot AI's models

[![PyPI](https://img.shields.io/pypi/v/zopyx.llm-moonshot.svg)](https://pypi.org/project/zopyx.llm-moonshot/0.3.5/)
[![Changelog](https://img.shields.io/badge/changelog-CHANGELOG.md-blue.svg)](https://github.com/zopyx/llm-moonshot/blob/main/CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/zopyx/llm-moonshot/blob/main/LICENSE)

[LLM](https://llm.datasette.io/) plugin for models hosted by [Moonshot AI](https://platform.moonshot.ai/).

## Project Status

This package is maintained as the `zopyx.llm-moonshot` fork of the original `llm-moonshot` project.

The fork keeps the plugin usable in current environments and aligns packaging, CI/CD, and release workflow with the `zopyx` distribution. The post-fork changes and the reasons for them are documented in [CHANGELOG.md](./CHANGELOG.md).

## Installation

First, [install the LLM command-line utility](https://llm.datasette.io/en/stable/setup.html).

Now install this plugin in the same environment as LLM:
```bash
llm install zopyx.llm-moonshot
```

## Configuration

You'll need an API key from Moonshot. Grab one at [platform.moonshot.cn](https://platform.moonshot.cn).

Set secret key:
```bash
llm keys set moonshot
```
```
Enter key: <paste key here>
```

## Usage

List what's on the menu:
```bash
llm models list
```
You'll see something like:
```
[[[cog
import cog
from llm_moonshot._models import DEFAULT_MOONSHOT_MODEL_IDS
for model_id in DEFAULT_MOONSHOT_MODEL_IDS:
    cog.outl(f"Moonshot: moonshot/{model_id}")
]]]
Moonshot: moonshot/kimi-latest
Moonshot: moonshot/moonshot-v1-auto
Moonshot: moonshot/moonshot-v1-128k-vision-preview
Moonshot: moonshot/kimi-k2-0711-preview
Moonshot: moonshot/moonshot-v1-128k
Moonshot: moonshot/moonshot-v1-32k-vision-preview
Moonshot: moonshot/moonshot-v1-8k-vision-preview
Moonshot: moonshot/moonshot-v1-8k
Moonshot: moonshot/kimi-thinking-preview
Moonshot: moonshot/moonshot-v1-32k
Moonshot: moonshot/kimi-k2-thinking
[[[end]]]
```

Fire up a chat:
```bash
llm chat -m moonshot/kimi-k2-0711-preview
```
```
Chatting with  moonshot/kimi-k2-0711-preview
Type 'exit' or 'quit' to exit
Type '!multi' to enter multiple lines, then '!end' to finish
> yo moonie
yo! what's up, moonie?
>
```

Need raw completion?
```bash
llm -m moonshot/moonshot-v1-8k "Finish this haiku: Neon city rain"
```
```
Neon city rain,
Glistening streets, a symphony,
Echoes of the night.
```

## Reasoning Content Support

This plugin now supports **reasoning content** for Moonshot's thinking models (models with "thinking" in the name). When using thinking models, you'll see the model's reasoning process displayed in real-time before the final response:

```bash
llm chat -m moonshot/kimi-k2-thinking
```
```
[Reasoning] (shown in cyan dim)

The user is asking me to solve a complex problem. Let me think through this step by step...
First, I need to understand the core requirements...
Then I'll analyze the available options...

[Response] (shown in bold green)

Here's my well-reasoned answer to your question...
```

### Available Thinking Models
- `moonshot/kimi-k2-thinking` - Latest reasoning model
- `moonshot/kimi-thinking-preview` - Preview reasoning model

The reasoning content helps you understand:
- **Decision-making process** - See how the model analyzes problems
- **Multi-step reasoning** - Follow complex thought chains
- **Error detection** - Catch logical gaps or misunderstandings early

## Aliases

Save your wrists:
```bash
llm aliases set kimi moonshot/kimi-latest
```
Now:
```bash
llm -m kimi "write a haiku about the AI chatbot Sidney is misbehaving"
```

## Troubleshooting

**Models don't appear in `llm models list`**
- Make sure you have set a Moonshot API key with `llm keys set moonshot`.
- The plugin caches the model catalog for one hour. If the API was unreachable,
  it falls back to a built-in catalog.

**Streaming connection dropped**
- The plugin automatically retries without streaming when Moonshot closes the
  connection mid-stream. This is a known upstream behavior and is handled
  transparently.

**401 Unauthorized**
- Double-check your API key at https://platform.moonshot.cn.

## Development

Clone, sync, build:
```bash
git clone https://github.com/zopyx/llm-moonshot.git
cd llm-moonshot
uv sync --extra dev
make check
make dist
```

To publish using `.pypirc` with `twine`:
```bash
make upload
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.
