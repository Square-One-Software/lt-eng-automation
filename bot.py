"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
from dotenv import load_dotenv
from os import getenv 
from telegram import  Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from pdf_utils import generate_vocabulary_pdf

load_dotenv()
TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

ASKING_FOR_NAME, WAITING_FOR_LIST = range(2)


async def vocab_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! 1) Send me the name of the student first ^.^ \n\n"
        "Send /cancel to stop ^.^",
    )
    return ASKING_FOR_NAME 


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["student_name"] = text

    await update.message.reply_text(
        f"Got it! This note is for {text} n.n \n\n" 
        "Now send me the vocabulary list in this exact format:\n\n"
        "`word1,pos;word2,pos;word3,pos`\n\n"
        "Example:\n"
        "`suspend,v;mourn,v;tempest,n;infuriate,v;escalate,v;belligerent,adj;spat,n;allies,n`\n\n"
        "Send /cancel to stop ^.^",
        parse_mode="Markdown",
    ) 

    return WAITING_FOR_LIST

async def receive_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # ---- 1. Parse the input string ----
    try:
        pairs = [item.strip().split(",") for item in text.split(";")]
        vocab_data = []
        for word, pos_raw in pairs:
            if len(word) == 0 or len(pos_raw) == 0:
                raise ValueError("Empty word or POS")
            # Normalise POS (v → verb, n → noun, adj → adjective, adv → adverb)
            pos_map = {"v": "verb", "n": "noun", "adj": "adjective", "adv": "adverb"}
            pos = pos_map.get(pos_raw.lower(), pos_raw)  # fallback to original if unknown
            vocab_data.append((word.lower(), pos))   # Chinese meaning will be added later
    except Exception as e:
        await update.message.reply_text(
            f"Invalid format. Please try again.\nError: {e}\n\n"
            "Use: word,pos;word,pos;..."
        )
        return WAITING_FOR_LIST

    # ---- 3. Generate the PDF (reuse YOUR existing function) ----
    output_filename = f"review_notes_{context.user_data['student_name']}.pdf"
    try:
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # CALL YOUR EXISTING FUNCTION HERE
        generate_vocabulary_pdf(output_filename, vocab_data)
        # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
    except Exception as e:
        logger.error(e, exc_info=True)
        await update.message.reply_text("Something went wrong while creating the PDF.")
        return ConversationHandler.END

    # ---- 4. Send the PDF back to the user ----
    with open(output_filename, "rb") as pdf_file:
        await update.message.reply_document(
            document=pdf_file,
            filename=f"{output_filename}.pdf",
            caption="Here’s your vocabulary review notes!",
        )

    await update.message.reply_text("Done! Send /vocab again anytime.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(TG_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("vocab", vocab_start)],
        states={
            ASKING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_FOR_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_list)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Optional: simple /start command
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text(
        "Hi! Use /vocab to generate a review notes PDF."
    )))

    print("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()