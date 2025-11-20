import csv, asyncio
from googletrans import Translator  # For translation

def parse_vocab_file(file):
    try:
        with open(file, "r") as f:
            reader = csv.reader(f)
            vocab_data = [tuple(i) for i in reader]
        return vocab_data
    except IOError as error:
        print(error)

def week_of_month(dt):
    """ Returns the week of the month for the specified date."""
    # Get the day of the week for the first day of the month (Monday = 0, Sunday = 6)
    first_day_of_month = dt.replace(day=1)
    # Get the ISO week number for the first day of the month
    first_day_iso_week = first_day_of_month.isocalendar()[1]
    # Get the ISO week number for the target date
    target_iso_week = dt.isocalendar()[1]

    # Calculate the week number within the month
    # Add 1 because the week numbers are 1-indexed
    week_number_of_month = target_iso_week - first_day_iso_week + 1
    return week_number_of_month

async def translate_to_chinese(translator, text):
    """Translate English text to Simplified Chinese."""
    try:
        # Translate to 'zh-cn' (Simplified Chinese)
        result = await translator.translate(text, dest='zh-tw')
        return result.text
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return "Translation failed"  # Fallback

async def create_vocabulary_table(data):
    """Create a table for the PDF from vocabulary data."""
    table_data = [['Vocabulary (Part of Speech)', 'Chinese Meaning']]
    translator = Translator()
    tasks = [translate_to_chinese(translator, vocab) for vocab, _ in data]
    translations = await asyncio.gather(*tasks)
    for (vocab, pos), chinese in zip(data, translations):
        table_data.append([f"{vocab} ({pos})", chinese])
    return table_data