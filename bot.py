# bot.py
import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)
from telegram.constants import ParseMode

# Import local modules
import database
import terabox_utils

# --- Configuration ---
# Get Telegram Bot Token from environment variable
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables!")

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Set higher logging level for httpx to avoid excessive debug messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Constants ---
TERABOX_LINK_PATTERN = re.compile(r'https?://(?:www\.)?terabox\.com/s/\S+|1024tera\.com/s/\S+')

# --- Bot Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    welcome_text = (
        f"Hello {user.mention_html()}!\n\n"
        "I can help you with Terabox links.\n\n"
        "➡️ Send me a Terabox link to get started.\n"
        "➡️ Use /help to see all available commands."
    )
    await update.message.reply_html(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message listing all commands."""
    help_text = (
        "Here's how you can use me:\n\n"
        "1️⃣  *Send a Terabox Link*: Just paste a Terabox link directly into the chat. I'll try to process it and give you options.\n\n"
        "2️⃣  `/download [Terabox Link]`\n    Gets the direct download link.\n\n"
        "3️⃣  `/stream [Terabox Link]`\n    Gets a direct link for online streaming (if it's a video).\n\n"
        "4️⃣  `/upload [Terabox Link] [Description]`\n    Adds a link to the public file board. Example:\n    `/upload https://terabox.com/s/1... My Awesome Movie`\n\n"
        "5️⃣  `/list`\n    Shows the most recent files added to the board.\n\n"
        "6️⃣  `/search [Keyword]`\n    Searches the board for files matching the keyword.\n\n"
        "7️⃣  `/request [ID or Keyword]`\n    Requests a specific file from the board using its ID (from /list or /search) or by keyword.\n\n"
        "8️⃣  `/help`\n    Shows this help message."
        "\n\n"
        "⚠️ *Disclaimer*: Fetching links from Terabox can be unreliable due to their anti-scraping measures. Success is not guaranteed."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles non-command messages, checking for Terabox links."""
    message_text = update.message.text
    if not message_text:
        return

    match = TERABOX_LINK_PATTERN.search(message_text)
    if match:
        terabox_link = match.group(0)
        logger.info(f"Detected Terabox link from message: {terabox_link}")
        await process_terabox_link(update, context, terabox_link, "message")
    else:
        # Optional: Reply if the message is not a command and not a link
        # await update.message.reply_text("Send me a Terabox link or use /help for commands.")
        pass # Or just ignore other messages

async def process_terabox_link(update: Update, context: ContextTypes.DEFAULT_TYPE, terabox_link: str, source: str):
    """Common function to process a detected or provided Terabox link."""
    processing_msg = await update.message.reply_text("⏳ Processing Terabox link, please wait...")

    try:
        link_info = terabox_utils.get_terabox_link(terabox_link)

        if not link_info or not link_info.get('download_link'):
            await processing_msg.edit_text(
                "❌ Failed to extract the direct link. This could be due to:\n"
                "- An invalid or expired Terabox link.\n"
                "- Terabox blocking the request (try again later).\n"
                "- Changes in Terabox's website structure."
                "\n\n_(Remember, Terabox scraping is unreliable)_"
            )
            return

        download_link = link_info['download_link']
        stream_link = link_info.get('stream_link')

        buttons = []
        response_text = f"✅ Link processed for: `{terabox_link}`\n\n"

        if download_link:
            response_text += f"🔗 **Direct Download Link:**\n`{download_link}`\n\n"
            # buttons.append([InlineKeyboardButton("Download", url=download_link)]) # Direct URL buttons often work

        if stream_link:
            response_text += f"🎬 **Streamable Link (Video):**\n`{stream_link}`\n_(May work directly in browser/player)_"
            # buttons.append([InlineKeyboardButton("Stream", url=stream_link)])
        else:
             response_text += "ℹ️ No specific stream link found (might be downloadable only or not a video)."


        # Limit message length
        if len(response_text) > 4000: # Telegram limit is 4096
            response_text = response_text[:4000] + "... (message truncated)"

        # Use InlineKeyboardMarkup if needed later, for now just send text
        # reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
        await processing_msg.edit_text(response_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error in process_terabox_link for {terabox_link}: {e}", exc_info=True)
        await processing_msg.edit_text(f"An unexpected error occurred: {e}")


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /download command."""
    if not context.args:
        await update.message.reply_text("Please provide a Terabox link after the command.\nExample: `/download https://terabox.com/s/1...`")
        return

    terabox_link = context.args[0]
    if not TERABOX_LINK_PATTERN.match(terabox_link):
        await update.message.reply_text("That doesn't look like a valid Terabox link.")
        return

    logger.info(f"/download command used for: {terabox_link}")
    await process_terabox_link(update, context, terabox_link, "download_command")

async def stream_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /stream command."""
    if not context.args:
        await update.message.reply_text("Please provide a Terabox link after the command.\nExample: `/stream https://terabox.com/s/1...`")
        return

    terabox_link = context.args[0]
    if not TERABOX_LINK_PATTERN.match(terabox_link):
        await update.message.reply_text("That doesn't look like a valid Terabox link.")
        return

    logger.info(f"/stream command used for: {terabox_link}")
    await process_terabox_link(update, context, terabox_link, "stream_command") # Same processing, will check for video

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /upload command to add a link to the board."""
    user = update.effective_user
    chat = update.effective_chat

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/upload [Terabox Link] [Description]`\n"
            "Example: `/upload https://terabox.com/s/1... My File Description`"
        )
        return

    terabox_link = context.args[0]
    description = " ".join(context.args[1:])

    if not TERABOX_LINK_PATTERN.match(terabox_link):
        await update.message.reply_text("The first argument must be a valid Terabox link.")
        return

    if not description:
        await update.message.reply_text("Please provide a description for the file.")
        return

    logger.info(f"User {user.id} attempting to upload link: {terabox_link} with description: {description}")

    success = database.add_link(
        user_id=user.id,
        chat_id=chat.id,
        description=description,
        terabox_link=terabox_link
    )

    if success:
        await update.message.reply_text(f"✅ Link added to the board with description: '{description}'")
    else:
        await update.message.reply_text("❌ Failed to add link. It might already exist or there was a database error.")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /list command to show recent board entries."""
    logger.info("Executing /list command")
    links = database.list_links(limit=20) # Get recent 20

    if not links:
        await update.message.reply_text("The file board is currently empty.")
        return

    response_text = "📋 **Recent Files on the Board:**\n\n"
    for link in links:
        # Format timestamp nicely if needed
        # timestamp_str = link['timestamp'].strftime('%Y-%m-%d %H:%M') # Need to parse it first if it's string
        response_text += f"🆔 `{link['id']}`: {link['description']}\n" # _{timestamp_str}_\n"

    response_text += "\nUse `/request [ID]` to get the link."

    if len(response_text) > 4096: response_text = response_text[:4090] + "\n... (list truncated)"

    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /search command."""
    if not context.args:
        await update.message.reply_text("Please provide a keyword to search for.\nExample: `/search Movie Title`")
        return

    query = " ".join(context.args)
    logger.info(f"Executing /search command with query: '{query}'")
    links = database.search_links(query, limit=20)

    if not links:
        await update.message.reply_text(f"No files found matching '{query}'.")
        return

    response_text = f"🔍 **Search Results for '{query}':**\n\n"
    for link in links:
        response_text += f"🆔 `{link['id']}`: {link['description']}\n"

    response_text += "\nUse `/request [ID]` to get the link."

    if len(response_text) > 4096: response_text = response_text[:4090] + "\n... (results truncated)"

    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)

async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /request command to get a link by ID or keyword search."""
    if not context.args:
        await update.message.reply_text("Please provide the ID (number) or a keyword for the file you want.\nExample: `/request 123` or `/request My Movie`")
        return

    query = " ".join(context.args)
    logger.info(f"Executing /request command with query: '{query}'")

    link_data = None
    # Try interpreting as ID first
    if query.isdigit():
        link_data = database.get_link_by_id(int(query))

    # If not found by ID, try searching by keyword (get the first match)
    if not link_data:
        search_results = database.search_links(query, limit=1)
        if search_results:
            link_data = database.get_link_by_id(search_results[0]['id']) # Fetch full data

    if not link_data:
        await update.message.reply_text(f"❌ Could not find a file matching '{query}' by ID or keyword.")
        return

    # Now process the Terabox link associated with this board entry
    await update.message.reply_text(f"Found entry: '{link_data['description']}'.\nNow processing the associated Terabox link...")
    await process_terabox_link(update, context, link_data['terabox_link'], "request_command")


# --- Main Bot Execution ---

def main() -> None:
    """Start the bot."""
    logger.info("Initializing database...")
    try:
        database.init_db() # Ensure table exists before starting bot
    except Exception as e:
        logger.critical(f"CRITICAL: Database initialization failed: {e}. Bot cannot start.", exc_info=True)
        return # Stop if DB fails

    logger.info("Starting bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("download", download_command))
    application.add_handler(CommandHandler("stream", stream_command))
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("request", request_command))

    # Handler for messages containing Terabox links
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(TERABOX_LINK_PATTERN), handle_message))
    # Optional: Handler for any other text messages (if you want to respond)
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, other_text_handler))

    logger.info("Bot polling started...")
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
