import csv, asyncio, os
from googletrans import Translator  # For translation

def parse_vocab_file(file):
    try:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")
        
        with open(file, "r") as f:
            reader = csv.reader(f)
            vocab_data = [tuple(i) for i in reader]
        return vocab_data
    except FileNotFoundError as error:
        print(error)
    except IOError as error:
        print(error)

def get_month_name(m: int):
   import calendar
   return calendar.month_abbr[m]

def parse_tuition_file(file):
    TUITION_SCHEMA = {
        "JS": "1 對 1 初中英文面授課",
        "SS": "1 對 1 DSE 英文面授課",
        "GS": "1 對 1 英文語法面授課",
        "MC": "補堂",
        "PE": "Pending 未付",
        "PA": "Paid 已付",
        "NA": "N/A",
        "S": "Scheduled 已安排",
        "R": "Rescheduled 調堂"
    }
    
    try:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")

        name_parts = file.split(".")[0].split("-") 
        
        if len(name_parts) != 3:
            raise ValueError(f"Invalid file name error. Expected 'COURSECODE-NAME-Month.csv', but got {file}")
        
        course_code, student_name, month = name_parts

        month_name = get_month_name(int(month))

        if course_code not in TUITION_SCHEMA:
            raise ValueError(f"Invalid Course Code: {course_code} is not a valid course code")
        
    
        with open(file, "r") as f:
            reader = csv.DictReader(f)
            tuition_data = [{key: TUITION_SCHEMA.get(val, val) for (key, val) in row.items()} for row in reader]
        return tuition_data, TUITION_SCHEMA[course_code], student_name, month, month_name
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except ValueError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error parsing file '{file}': {e}")
        raise

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