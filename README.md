# Verkhovyna Helper Bot

Триразові нагадування + кнопки "зроблено/нагадай/не встигла" + критичні задачі (павліни/двері/вода/ліки) з повтором.

## Запуск локально (Python Telegram Bot)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in TELEGRAM_BOT_TOKEN and TARGET_CHAT_ID
python bot.py
```

## Команди бота

| Команда | Опис |
|---------|------|
| `/ping` | перевірити, що бот живий |
| `/morning` `/day` `/evening` | ручний виклик повідомлення для слоту |
| `/quiet` | тихий режим (коротко, без історій) |
| `/normal` | звичайний режим |
| `/stats` | статистика виконання за 7 днів |
| `/tasks` | показати всі поточні таски |
| `/addtask <slot> <text>` | додати таск до слоту (`morning`/`day`/`evening`) |
| `/deltask <slot> <index>` | видалити таск за індексом |

## Деплой через GitHub Actions (автоматичний)

При кожному push до гілки `main` CI/CD pipeline автоматично:
1. Перевіряє код (flake8 + py_compile)
2. Збирає Docker-образ і публікує його в GitHub Container Registry (GHCR)
3. Підключається до сервера по SSH і перезапускає контейнер

### Необхідні GitHub Secrets

Відкрийте **Settings → Secrets and variables → Actions → New repository secret**  
([пряме посилання](https://github.com/rsumko-sys/chatbot/settings/secrets/actions)) і додайте:

| Secret | Опис |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | Токен бота — отримайте у [@BotFather](https://t.me/BotFather) |
| `TARGET_CHAT_ID` | ID чату/користувача для розсилки — отримайте через [@userinfobot](https://t.me/userinfobot) |
| `TZ_NAME` | Часовий пояс, наприклад `Europe/Kyiv` |
| `OPENWEATHER_API_KEY` | Ключ [OpenWeatherMap](https://openweathermap.org/api) (опціонально) |
| `GH_PAT` | GitHub Personal Access Token з правами `read:packages` — для завантаження образу на сервері |
| `SSH_HOST` | IP-адреса або hostname вашого сервера |
| `SSH_USER` | Ім'я SSH-користувача на сервері |
| `SSH_KEY` | Вміст приватного SSH-ключа (`~/.ssh/id_ed25519` або `id_rsa`) |

> **Важливо:** Ніколи не додавайте реальні токени, паролі чи ключі безпосередньо у файли репозиторію.  
> Git зберігає всю історію — видалення файлу не видаляє секрет. Використовуйте виключно GitHub Secrets.

### Як отримати GitHub PAT

1. Відкрийте [github.com/settings/tokens](https://github.com/settings/tokens) → **Generate new token (classic)**
2. Виберіть scope: `read:packages`
3. Скопіюйте токен і збережіть як секрет `GH_PAT`

### Перша настройка SSH-ключа на сервері

```bash
# На вашому локальному комп'ютері
ssh-keygen -t ed25519 -C "chatbot-deploy"
# Скопіюйте публічний ключ на сервер
ssh-copy-id -i ~/.ssh/id_ed25519 gonzo@YOUR_SERVER_IP
# Додайте вміст ~/.ssh/id_ed25519 (приватний ключ) як GitHub Secret SSH_KEY
```

### Запуск контейнера вручну (без CI)

```bash
docker pull ghcr.io/rsumko-sys/chatbot-bot:latest
docker run -d \
  --name chatbot-bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN="..." \
  -e TARGET_CHAT_ID="..." \
  -e TZ_NAME="Europe/Kyiv" \
  -e OPENWEATHER_API_KEY="..." \
  -v chatbot-bot-data:/data \
  ghcr.io/rsumko-sys/chatbot-bot:latest
```

---

<a href="https://chat.vercel.ai/">
  <img alt="Chatbot" src="app/(chat)/opengraph-image.png">
  <h1 align="center">Chatbot</h1>
</a>

<p align="center">
    Chatbot (formerly AI Chatbot) is a free, open-source template built with Next.js and the AI SDK that helps you quickly build powerful chatbot applications.
</p>

<p align="center">
  <a href="https://chatbot.dev"><strong>Read Docs</strong></a> ·
  <a href="#features"><strong>Features</strong></a> ·
  <a href="#model-providers"><strong>Model Providers</strong></a> ·
  <a href="#deploy-your-own"><strong>Deploy Your Own</strong></a> ·
  <a href="#running-locally"><strong>Running locally</strong></a>
</p>
<br/>

## Features

- [Next.js](https://nextjs.org) App Router
  - Advanced routing for seamless navigation and performance
  - React Server Components (RSCs) and Server Actions for server-side rendering and increased performance
- [AI SDK](https://ai-sdk.dev/docs/introduction)
  - Unified API for generating text, structured objects, and tool calls with LLMs
  - Hooks for building dynamic chat and generative user interfaces
  - Supports OpenAI, Anthropic, Google, xAI, and other model providers via AI Gateway
- [shadcn/ui](https://ui.shadcn.com)
  - Styling with [Tailwind CSS](https://tailwindcss.com)
  - Component primitives from [Radix UI](https://radix-ui.com) for accessibility and flexibility
- Data Persistence
  - [Neon Serverless Postgres](https://vercel.com/marketplace/neon) for saving chat history and user data
  - [Vercel Blob](https://vercel.com/storage/blob) for efficient file storage
- [Auth.js](https://authjs.dev)
  - Simple and secure authentication

## Model Providers

This template uses the [Vercel AI Gateway](https://vercel.com/docs/ai-gateway) to access multiple AI models through a unified interface. The default model is [OpenAI](https://openai.com) GPT-4.1 Mini, with support for Anthropic, Google, and xAI models.

### AI Gateway Authentication

**For Vercel deployments**: Authentication is handled automatically via OIDC tokens.

**For non-Vercel deployments**: You need to provide an AI Gateway API key by setting the `AI_GATEWAY_API_KEY` environment variable in your `.env.local` file.

With the [AI SDK](https://ai-sdk.dev/docs/introduction), you can also switch to direct LLM providers like [OpenAI](https://openai.com), [Anthropic](https://anthropic.com), [Cohere](https://cohere.com/), and [many more](https://ai-sdk.dev/providers/ai-sdk-providers) with just a few lines of code.

## Deploy Your Own

You can deploy your own version of Chatbot to Vercel with one click:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/templates/next.js/chatbot)

## Running locally

You will need to use the environment variables [defined in `.env.example`](.env.example) to run Chatbot. It's recommended you use [Vercel Environment Variables](https://vercel.com/docs/projects/environment-variables) for this, but a `.env` file is all that is necessary.

> Note: You should not commit your `.env` file or it will expose secrets that will allow others to control access to your various AI and authentication provider accounts.

1. Install Vercel CLI: `npm i -g vercel`
2. Link local instance with Vercel and GitHub accounts (creates `.vercel` directory): `vercel link`
3. Download your environment variables: `vercel env pull`

```bash
pnpm install
pnpm db:migrate # Setup database or apply latest database changes
pnpm dev
```

Your app template should now be running on [localhost:3000](http://localhost:3000).
