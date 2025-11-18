from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from datetime import datetime
from utils import create_vocabulary_table, week_of_month

def style_vocabulary_table(chinese_font):
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
    table.setStyle(style_vocabulary_table(chinese_font))

    # Add table to elements
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"PDF generated: {filename}")