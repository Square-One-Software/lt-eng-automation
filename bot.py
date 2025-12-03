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
from pdf_utils import generate_vocabulary_pdf, generate_tuition_debit_note
from utils import parse_tuition_file


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
WAITING_FOR_FILE, WAITING_FOR_NOTES = range(2)

async def tuition_note_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! 1) Send me the file for the student first~\n\n"
        "Send /cancel to stop ^.^",
    )
    return WAITING_FOR_FILE

async def vocab_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Hi! 1) Send me the name of the student first~\n\n"
        "Send /cancel to stop ^.^",
    )
    return ASKING_FOR_NAME 

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives a CSV file from the user, downloads it, parses it, and stores the data.
    """
    try:
        # Get the file from Telegram
        file = await context.bot.get_file(update.message.document)
        
        # Get the original filename
        original_filename = update.message.document.file_name
        
        # Validate file extension
        if not original_filename.lower().endswith('.csv'):
            await update.message.reply_text(
                "❌ Invalid file type. Please send a CSV file.\n"
                "Expected format: COURSECODE-NAME-MONTH.csv"
            )
            return WAITING_FOR_FILE
        
        # Create a temporary directory if it doesn't exist
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download the file to local storage
        local_file_path = os.path.join(temp_dir, original_filename)
        await file.download_to_drive(local_file_path)
        
        # Parse the CSV file
        try:
            tuition_data, course_desc, student_name, month, month_name = parse_tuition_file(local_file_path)
            
            # Store the parsed data in context for later use
            context.user_data['tuition_data'] = tuition_data
            context.user_data['course_desc'] = course_desc
            context.user_data['student_name'] = student_name
            context.user_data['month'] = month
            context.user_data['month_name'] = month_name
            context.user_data['file_path'] = local_file_path
            
            # Calculate total amount
            total_amount = sum(
                float(lesson['amount'].replace(' HKD', '').replace(',', ''))
                for lesson in tuition_data
            )
            
            # Send confirmation message with summary
            summary_message = (
                f"✅ File received and parsed successfully!\n\n"
                f"📋 **Summary:**\n"
                f"👤 Student: {student_name}\n"
                f"📚 Course: {course_desc}\n"
                f"📅 Month: {month_name} ({month})\n"
                f"📝 Total Lessons: {len(tuition_data)}\n"
                f"💰 Total Amount: ${total_amount:,.0f} HKD\n\n"
                f"Please send any notes you'd like to add to the invoice, or send /skip to generate without notes."
            )
            
            await update.message.reply_text(summary_message, parse_mode='Markdown')
            return WAITING_FOR_NOTES
        except (FileNotFoundError, ValueError) as e:
            # Clean up the downloaded file
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            
            await update.message.reply_text(
                f"❌ Error parsing file: {str(e)}\n\n"
                f"Please make sure your file follows the format:\n"
                f"**COURSECODE-NAME-MONTH.csv**\n\n"
                f"Valid course codes: JS, SS, GS, MC"
            )
            return WAITING_FOR_FILE
            
        except Exception as e:
            # Clean up the downloaded file
            if os.path.exists(local_file_path):
                os.remove(local_file_path)
            
            await update.message.reply_text(
                f"❌ Unexpected error: {str(e)}\n\n"
                f"Please try again or contact support."
            )
            return ConversationHandler.END
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error downloading file: {str(e)}\n\n"
            f"Please try sending the file again."
        )
        return WAITING_FOR_FILE

async def receive_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives notes from the user and generates the PDF invoice.
    """
    try:
        # Get the notes
        notes = update.message.text
        
        # Retrieve stored data
        tuition_data = context.user_data.get('tuition_data')
        course_desc = context.user_data.get('course_desc')
        student_name = context.user_data.get('student_name')
        month = context.user_data.get('month')
        month_name = context.user_data.get('month_name')
        file_path = context.user_data.get('file_path')
        
        if not all([tuition_data, course_desc, student_name, month]):
            await update.message.reply_text(
                "❌ Error: Missing data. Please start over by sending the CSV file again."
            )
            return ConversationHandler.END
        
        # Calculate total amount
        total_amount = sum(
            float(lesson['amount'].replace(' HKD', '').replace(',', ''))
            for lesson in tuition_data
        )
        
        # Generate PDF filename
        pdf_filename = f"{student_name}_{month_name}_{month}_2025.pdf"
        
        # Generate the PDF
        await update.message.reply_text("⏳ Generating PDF invoice...")
        
        # Format lessons for PDF generation
        lessons = [
            {
                "date": lesson.get('date', 'N/A'),
                "desc": lesson.get('desc', course_desc),
                "amount": lesson.get('amount', '0 HKD'),
                "payment": lesson.get('payment', 'N/A'),
                "status": lesson.get('status', 'N/A')
            }
            for lesson in tuition_data
        ]
        
        # Generate the PDF (using your existing function)
        generate_tuition_debit_note(
            filename=pdf_filename,
            student_name=student_name,
            month=f"{month_name} {month}月",
            lessons=lessons,
            total_amount=f"$ {total_amount:,.0f} HKD",
            notes=notes if notes else None
        )
        
        # Send the PDF file
        with open(pdf_filename, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=pdf_filename,
                caption=f"✅ Invoice generated for {student_name} - {month_name}"
            )
        
        # Clean up temporary files
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
        
        # Clear user data
        context.user_data.clear()
        
        await update.message.reply_text(
            "✨ Invoice sent successfully!\n\n"
            "Send another CSV file to generate a new invoice."
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error generating PDF: {str(e)}\n\n"
            f"Please try again or contact support."
        )
        return ConversationHandler.END


async def skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Skip notes and generate PDF without them.
    """
    # Just set empty notes and call receive_notes
    update.message.text = ""
    return await receive_notes(update, context)


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
    # ----  Parse the input string ----
    try:
        pairs = [item.strip().split(",") for item in text.split(";")]
        vocab_data = []
        
        for pair in pairs:
            if len(pair) < 2:
                raise ValueError(f"This pair of word has the word or pos missing: {pair}")
            word, pos_raw  = pair
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

    tuition_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("tuition", tuition_note_start)],
        states={
            WAITING_FOR_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_file)],
            WAITING_FOR_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_notes), CommandHandler("skip", skip_notes)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(vocab_conv_handler)
    app.add_handler(tuition_conv_handler)

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text(
        "Hi! Molly is here! Use /vocab to generate a review notes PDF."
    )))
    
    app.add_handler(CommandHandler("random", random_joke))

    print("Bot is running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()