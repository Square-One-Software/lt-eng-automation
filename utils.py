import csv, asyncio, calendar, os, datetime, requests
from googletrans import Translator  # For translation
from pathlib import Path

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

def parse_tuition_file(files: list[str] | str):
    TUITION_SCHEMA = {
        "JS": "1 對 1 初中英文面授課",
        "SS": "1 對 1 DSE 英文面授課",
        "GS": "1 對 1 英文語法面授課",
        "MC": "補堂",
        "PE": "Pending 未付",
        "PA": "Paid 已付",
        "NA": "N/A",
        "S": "Scheduled 已安排",
        "C": "Completed 完成",
        "R": "Rescheduled 調堂"
    }

    if not isinstance(files, list):
        files = [files]

    lesson_data = []
    months = []
    sorted_files = sorted(files, key=lambda x: int(x.split("-")[-1].split(".")[0]), reverse=True)
    
    try:
        for file in sorted_files:
            tuition_data_dir = "tuition_data"
            data_dir_path = Path(tuition_data_dir)
            if not data_dir_path.exists():
                os.makedirs(tuition_data_dir)

            file_path = os.path.join(tuition_data_dir, file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file}")

            name_parts = file.split(".")[0].split("-") 
            
            if len(name_parts) != 3:
                raise ValueError(f"Invalid file name error. Expected 'COURSECODE-NAME-Month.csv', but got {file}")
            
            course_code, student_name, month = name_parts 
            
            if "/" in course_code:
                course_code = course_code.split("/")[1]

            if course_code not in TUITION_SCHEMA:
                raise ValueError(f"Invalid Course Code: {course_code} is not a valid course code")

            months.append(int(month))

            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                lesson_data.append([{key: TUITION_SCHEMA.get(val, val) for (key, val) in row.items()} for row in reader])
        
        months = sorted(months, reverse=True)
        month_name = calendar.month_abbr[months[0]]
        return lesson_data, TUITION_SCHEMA[course_code], student_name, months, month_name
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except ValueError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error parsing file '{file}': {e}")
        raise

def parse_note_txt(filename):
    try:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        # Use 'with open' for automatic file closing
        with open(filename, 'r', encoding='utf-8') as file:
            data_list = [line.strip() for line in file]
        return data_list
    except FileNotFoundError as e:
        print(f"Error: {e}")
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
    tasks = [translate_to_chinese(translator, vocab) for vocab, _, _ in data]
    translations = await asyncio.gather(*tasks)
    for (vocab, pos, custom_meaning), chinese in zip(data, translations):
        meaning = custom_meaning if custom_meaning else chinese
        table_data.append([f"{vocab} ({pos})", meaning])
    return table_data

def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text safe for Telegram Markdown
    """
    if not text:
        return ""
    
    # Characters that need to be escaped in Telegram Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    escaped_text = text
    for char in special_chars:
        escaped_text = escaped_text.replace(char, "")
    
    return escaped_text

def format_news_article(article: dict) -> str:
    """
    Format a single news article for Telegram display in Markdown.
    
    Args:
        article: Dictionary containing article data from news API
        
    Returns:
        Formatted string in Telegram Markdown format
    """
    # Extract fields with fallbacks
    title = article.get('title', 'No Title')
    description = article.get('description', "")
    url = article.get('url', article.get('url', ''))
    
    # Build the formatted message
    message_parts = []
    
    # Title (bold and larger)
    if title:
        # Escape special characters for Markdown
        title_escaped = escape_markdown(title)
        message_parts.append(f"*{title_escaped}*")
    
    # Description
    if description:
        desc_escaped = escape_markdown(description)
        # Truncate if too long
        if len(desc_escaped) > 300:
            desc_escaped = desc_escaped[:297] + "..."
        message_parts.append(f"\n{desc_escaped}")
    
    # Read more link
    if url:
        message_parts.append(f"\n[Read Full Article: {url}]")
    
    return "\n".join(message_parts)


def format_multiple_news_articles(articles: list, max_articles: int = 3) -> list[str]:
    """
    Format multiple news articles for Telegram, splitting into multiple messages if needed.
    
    Args:
        articles: List of article dictionaries
        max_articles: Maximum number of articles to format
        
    Returns:
        List of formatted message strings (split to avoid Telegram's message length limit)
    """
    messages = []
    max_length = 4000  # Telegram's limit is 4096, leave some buffer
    header = f"📰 *Latest News* ({min(len(articles), max_articles)} articles)\n"
    messages.append(header)
    
    for _, article in enumerate(articles[:max_articles]):
        formatted_article = format_news_article(article)
        article_length = len(formatted_article)
        # Check if adding this article would exceed the limit
        if article_length < max_length:
            # Save current message and start a new one
            messages.append(formatted_article)
    return messages


def fetch_news(NEWS_API_TOKEN):
    try:
        res = requests.get(
            "https://api.thenewsapi.com/v1/news/all",
            params={
            'api_token': NEWS_API_TOKEN,
            'categories': 'tech,business,general',
            'language': "en",
            'limit': 3,
            },
            timeout=10)
    
        res.raise_for_status()
        news_data = res.json()
        if 'error' in news_data:
            raise ValueError(f"API error: {news_data['error']}")
        return news_data.get("data", [])
    except requests.exceptions.Timeout:
        print("Request timed out")
        raise TimeoutError("News API request timed out") from None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        raise ConnectionError("Failed to connect to news API") from e
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        raise ValueError(f"API returned error: {e}") from e
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        raise RuntimeError("Failed to fetch news") from e
