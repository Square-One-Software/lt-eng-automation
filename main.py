from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, HRFlowable
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from googletrans import Translator  # For translation
from datetime import datetime
from utils import parse_vocab_file
import argparse

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

def translate_to_chinese(translator, text):
    """Translate English text to Simplified Chinese."""
    try:
        # Translate to 'zh-cn' (Simplified Chinese)
        result = translator.translate(text, dest='zh-tw')
        return result.text
    except Exception as e:
        print(f"Translation error for '{text}': {e}")
        return "Translation failed"  # Fallback


def create_vocabulary_table(data):
    """Create a table for the PDF from vocabulary data."""
    table_data = [['Vocabulary (Part of Speech)', 'Chinese Meaning']]
    for vocab, pos in data:
        translator = Translator()
        chinese = translate_to_chinese(translator, vocab)
        table_data.append([f"{vocab} ({pos})", chinese])
    return table_data

def style_vocabulary_table(table, chinese_font):
    """Apply styling to the vocabulary table with Chinese font support."""
    return TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header (English)
        ('FONTSIZE', (0, 0), (-1, 0), 14),  # Header font size
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),  # English column (vocab)
        ('FONTNAME', (1, 1), (1, -1), chinese_font),  # Chinese column
        ('FONTSIZE', (0, 1), (-1, -1), 13),  # Body font size
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Table grid
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
        ('LEFTPADDING', (0, 0), (-1, -1), 10),  # Left padding for all cells
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Right padding for all cells
        ('TOPPADDING', (0, 0), (-1, -1), 8),  # Top padding for all cells
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),  # Bottom padding for all cells
    ])

def generate_vocabulary_pdf(filename, vocab_data):
    """Generate a PDF with a vocabulary table."""
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    chinese_font = 'STSong-Light' # from Adobe's Asian Language Packs
    pdfmetrics.registerFont(UnicodeCIDFont(chinese_font))

    # Title
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.alignment = 0
    title_style.fontsize = 16
    dt = datetime.now()
    title_text = f'{dt.strftime("%b")} {dt.year} Week {week_of_month(dt)}'
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(HRFlowable(color=colors.black, thickness=2, spaceAfter=12, hAlign="LEFT"))

    # Create and style table
    table_data = create_vocabulary_table(vocab_data)
    table = Table(table_data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(style_vocabulary_table(table, chinese_font))

    # Add table to elements
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"PDF generated: {filename}")

def main():
    parser = argparse.ArgumentParser(prog="Vocabulary Generator", description="Generate a vocabulary list PDF.")
    parser.add_argument('-o', '--output', type=str, default="vocabulary_list.pdf",
                        help="Output PDF filename (default: vocabulary_list.pdf)")
    parser.add_argument('-f', '--file', type=str, help="Input vocabulary csv file name (vocab.csv)", required=True)
    # Parse arguments
    args = parser.parse_args()
    output_filename = args.output
    csv_filename = args.file

    vocab_data = parse_vocab_file(csv_filename)
    
    # Generate PDF
    generate_vocabulary_pdf(output_filename, vocab_data)

if __name__ == "__main__":
    main()