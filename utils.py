import csv, asyncio, calendar, os, datetime
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
        "C": "Completed 完成",
        "R": "Rescheduled 調堂"
    }
    
    try:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File not found: {file}")

        name_parts = file.split(".")[0].split("-") 
        
        if len(name_parts) != 3:
            raise ValueError(f"Invalid file name error. Expected 'COURSECODE-NAME-Month.csv', but got {file}")
        
        course_code, student_name, month = name_parts

        month_name = calendar.month_abbr[int(month)]

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
    tasks = [translate_to_chinese(translator, vocab) for vocab, _ in data]
    translations = await asyncio.gather(*tasks)
    for (vocab, pos), chinese in zip(data, translations):
        table_data.append([f"{vocab} ({pos})", chinese])
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
        escaped_text = escaped_text.replace(char, f"//{char}")
    
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
    source = article.get('source_id', article.get('domain', 'Unknown Source'))
    description = article.get('description', article.get('snippet', ''))
    url = article.get('url', article.get('link', ''))
    pub_date = article.get('published_at', article.get('pubDate', ''))
    author = article.get('author', '')
    image_url = article.get('image_url', article.get('urlToImage', ''))
    categories = article.get('categories', [])
    
    # Format publication date
    date_str = ''
    if pub_date:
        try:
            # Try parsing ISO format
            if isinstance(pub_date, str):
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%b %d, %Y at %I:%M %p')
        except:
            date_str = pub_date
    
    # Build the formatted message
    message_parts = []
    
    # Title (bold and larger)
    if title:
        # Escape special characters for Markdown
        title_escaped = escape_markdown(title)
        message_parts.append(f"*{title_escaped}*")
    
    # Source and date
    metadata = []
    if source:
        source_clean = source.replace('.com-1', '').replace('-', ' ').title()
        metadata.append(f"📰 {source_clean}")
    if date_str:
        metadata.append(f"🕐 {date_str}")
    if metadata:
        message_parts.append(' • '.join(metadata))
    
    # Author
    if author and author.lower() not in ['unknown', 'none', 'n/a']:
        message_parts.append(f"✍️ By {escape_markdown(author)}")
    
    # Description
    if description:
        desc_escaped = escape_markdown(description)
        # Truncate if too long
        if len(desc_escaped) > 300:
            desc_escaped = desc_escaped[:297] + "..."
        message_parts.append(f"\n{desc_escaped}")
    
    # Read more link
    if url:
        message_parts.append(f"\n[Read Full Article: {url}")
    
    return "\n\n".join(message_parts)


def format_multiple_news_articles(articles: list, max_articles: int = 5) -> list[str]:
    """
    Format multiple news articles for Telegram, splitting into multiple messages if needed.
    
    Args:
        articles: List of article dictionaries
        max_articles: Maximum number of articles to format
        
    Returns:
        List of formatted message strings (split to avoid Telegram's message length limit)
    """
    messages = []
    current_message = []
    current_length = 0
    max_length = 2000  # Telegram's limit is 4096, leave some buffer
    
    # Add header
    header = f"📰 *Latest News* ({min(len(articles), max_articles)} articles)\n"
    current_message.append(header)
    current_length += len(header)
    
    for _, article in enumerate(articles[:max_articles]):
        formatted_article = format_news_article(article)
        article_length = len(formatted_article)
        
        # Check if adding this article would exceed the limit
        if current_length + article_length > max_length and current_message:
            # Save current message and start a new one
            messages.append("".join(current_message))
            current_message = []
            current_length = 0
        
        current_message.append(formatted_article)
        current_length += article_length
    
    # Add the last message
    if current_message:
        messages.append("".join(current_message))
    
    return messages

