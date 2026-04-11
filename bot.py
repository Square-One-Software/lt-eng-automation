"""
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
import logging, requests 
from dotenv import load_dotenv
from os import getenv, remove
from telegram import  Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from requests.exceptions import ConnectionError 
from pdf_utils import generate_vocabulary_pdf, generate_tuition_debit_note
from utils import parse_tuition_file, format_multiple_news_articles, fetch_news
from chat import GrokChat


load_dotenv()
TG_BOT_TOKEN = getenv("TG_BOT_TOKEN")
NEWS_API_TOKEN = getenv("NEWS_API_TOKEN")
MASTER_ID = getenv("MASTER_ID")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

ASKING_FOR_NAME, WAITING_FOR_LIST = range(2)

def auth(id: int) -> bool:
    return id == int(MASTER_ID)

async def start_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    if auth(chat_id):
        await update.message.reply_text("Hi! Molly is here! What do you need help with today?")
    else:
        await update.message.reply_text("This's Molly. Who are you? I don't think I know you...")
    return ConversationHandler.END


async def vocab_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    if auth(update.effective_chat.id):
        await update.message.reply_text(
            "Hi! 1) Send me the name of the student first~\n\n"
            "Send /cancel to stop ^.^",
        )
        return ASKING_FOR_NAME 
    else:
        await update.message.reply_text("Hey, Molly doesn't take order from stranger!")
        return ConversationHandler.END


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["student_name"] = text

    await update.message.reply_text(
        f"Got it! This note is for {text} n.n \n\n" 
        "Now send me the vocabulary list in this exact format:\n\n"
        "`word1,pos,(customised meaning [optional]);word2,pos,(customised meaning [optional]);word3,pos,(customised meaning [optional])`\n\n"
        "Example:\n"
        "`suspend,v;mourn,v;tempest,n,暴風雨;infuriate,v;escalate,v;belligerent,adj,好戰的`\n\n"
        "Send /cancel to stop ^.^",
        parse_mode="Markdown",
    ) 

    return WAITING_FOR_LIST

async def receive_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    # ----  Parse the input string ----
    try:
        pairs = [item.strip().split(",") for item in text.split(";") if item]
        vocab_data = []
        for pair in pairs:
            if len(pair) <= 2:
                raise ValueError(f"This pair of word has a missing part -> {pair}")
            word, pos_raw, custom_meaning = pair
            if len(word) == 0 or len(pos_raw) == 0:
                raise ValueError("Empty word or POS")
            # Normalise POS (v → verb, n → noun, adj → adjective, adv → adverb)
            pos_map = {"v": "verb", "n": "noun", "adj": "adjective", "adv": "adverb"}
            pos = pos_map.get(pos_raw.lower(), pos_raw)  # fallback to original if unknown
            vocab_data.append((word.lower(), pos, custom_meaning))   # Chinese meaning will be added later
    except Exception as e:
        await update.message.reply_text(
            f"Invalid format. Please try again.\nError: \n{e}\n\n"
            "Use: word,pos;word,pos;..."
        )
        return WAITING_FOR_LIST

    # ---- Generate the PDF (reuse YOUR existing function) ----
    output_filename = f"review_notes_{context.user_data['student_name']}.pdf"
    try:
        await generate_vocabulary_pdf(output_filename, vocab_data)
        # ---- Send the PDF back to the user ----
        with open(output_filename, "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"{output_filename}",
                caption="Here’s your vocabulary review notes!",
            )
        await update.message.reply_text("Done! Send /vocab again anytime.")
    except Exception as e:
        logger.error(e, exc_info=True)
        await update.message.reply_text("Something went wrong while creating the PDF >.< \n\n Try /vocab again later")
    finally:
        remove(output_filename)
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    file_path = context.user_data.get('file_path')
    
    # Clean up temporary file if exists
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    context.user_data.clear()
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def random_joke(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    joke = requests.get("http://www.official-joke-api.appspot.com/random_joke").json()
    await update.message.reply_text(f"Let me tell you something random hehe...\n\n{joke['setup']}\n{joke['punchline']}\n\nHave a nice day!")
    return ConversationHandler.END

async def send_news(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        if not auth(update.effective_chat.id):
            await update.message.reply_text("Why don't you search the news yourself!")
            return ConversationHandler.END

        articles = fetch_news(NEWS_API_TOKEN)
        if not articles:
            await update.message.reply_text("📰 No news articles found at the moment.")
            return ConversationHandler.END

        await update.message.reply_text("Okay, fetching news now! Please wait...")
        formatted_messages = format_multiple_news_articles(articles, max_articles=3)
        
        for message in formatted_messages:
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                disable_web_page_preview=False  # Set to True to hide link previews
            )

        return ConversationHandler.END
    except TimeoutError as e:
        print(e)
        await update.message.reply_text(
            f"❌ Sorry, there was an error fetching the news. {e} \n\n Please try again later T.T"
        )
    except ConnectionError as e:
        print(e)
        await update.message.reply_text(
            f"❌ Sorry, there was a conntection error when fetching the news. \n {e} \n\n Please try again later T.T"
        )
    except ValueError as e:
        print(e)
        await update.message.reply_text(
            f"❌ Sorry, there was an error fetching the news. \n\n Please try again later T.T"
        )
    except RuntimeError as e:
        print(e)
        await update.message.reply_text(
            f"❌ Sorry, there was an error fetching the news. \n\n Please try again later T.T"
        )
    finally:
        return ConversationHandler.END

async def send_chat(update: Update, _:ContextTypes.DEFAULT_TYPE) -> int:
    try:
        if not auth(update.effective_chat.id):
            await update.message.reply_text("Molly will not answer your question! Get off")
            return ConversationHandler.END
        else:
            agent = GrokChat()
            response = agent.send_message(update.message.text)
            await update.message.reply_text(response, parse_mode="Markdown")
            return ConversationHandler.END
    except Exception as e:
       logger.exception(f"Error in chat handler: {e}")
    finally:
        return ConversationHandler.END


def main() -> None:
    app = Application.builder().token(TG_BOT_TOKEN).build()

    vocab_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("vocab", vocab_start)],
        states={
            ASKING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_FOR_LIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_list)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(vocab_conv_handler)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("random", random_joke))
    app.add_handler(CommandHandler("news", send_news))
    
    app.add_handler(MessageHandler(filters.TEXT, send_chat))

    print("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()