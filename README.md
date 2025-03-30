# Telegram Terabox Bot

A Python-based Telegram bot to process Terabox links for direct download/streaming and manage a file-sharing board.

**⚠️ IMPORTANT DISCLAIMER ⚠️**

*   **Terabox Scraping is Unreliable:** Fetching direct links from Terabox is difficult due to their anti-scraping measures. The included scraping logic (`terabox_utils.py`) is a **basic placeholder** and **will likely NOT work** without significant modification and ongoing maintenance. You will need to implement a robust scraping solution yourself (e.g., using Selenium, Playwright, or reverse-engineering their private API calls). **This part is fragile and may break frequently.**
*   **Use Responsibly:** Respect Terabox's Terms of Service and copyright laws. Do not use this bot for illegal sharing.
*   **No Guarantees:** This bot is provided as-is. Success in fetching links is not guaranteed.

## Features

*   **Terabox Link Processing:** Extracts potential direct download links.
*   **Video Streaming Link:** Provides the same direct link if it appears to be a video (actual streaming depends on Terabox and the player).
*   **File Exchange Board:**
    *   Upload Terabox links with descriptions (`/upload`).
    *   List recent uploads (`/list`).
    *   Search for files by keyword (`/search`).
    *   Request the Terabox link for a board item (`/request`).
*   **User-Friendly Commands:** Standard Telegram bot commands (`/start`, `/help`, etc.).

## Technology Stack

*   Python 3.10+
*   `python-telegram-bot` library
*   `requests` (for basic HTTP calls - more needed for real scraping)
*   SQLite (for the file board database)

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd terabox-telegram-bot
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you modify `terabox_utils.py` to use Selenium/Playwright/BS4, add them to `requirements.txt` and reinstall.*

4.  **Get Telegram Bot Token:**
    *   Talk to @BotFather on Telegram.
    *   Create a new bot.
    *   Copy the **HTTP API token**.

5.  **Set Environment Variable:**
    Set the `TELEGRAM_BOT_TOKEN` environment variable. You can do this in your terminal (temporarily) or using a `.env` file (add `.env` to `.gitignore`!) and a library like `python-dotenv`.
    ```bash
    export TELEGRAM_BOT_TOKEN='YOUR_ACTUAL_BOT_TOKEN' # Linux/macOS
    # set TELEGRAM_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN    # Windows CMD
    # $env:TELEGRAM_BOT_TOKEN="YOUR_ACTUAL_BOT_TOKEN" # Windows PowerShell
    ```

## Running the Bot Locally

```bash
python bot.py
