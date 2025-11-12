from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont


def create_vocabulary_table(data):
    """Create a table for the PDF from vocabulary data."""
    table_data = [['Vocabulary (Part of Speech)', 'Chinese Meaning']]
    for vocab, pos, chinese in data:
        table_data.append([f"{vocab} ({pos})", chinese])
    return table_data

def style_vocabulary_table(table, chinese_font):
    """Apply styling to the vocabulary table with Chinese font support."""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all text
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header (English)
        ('FONTSIZE', (0, 0), (-1, 0), 13),  # Header font size
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),  # English column (vocab)
        ('FONTNAME', (1, 1), (1, -1), chinese_font),  # Chinese column
        ('FONTSIZE', (0, 1), (-1, -1), 12),  # Body font size
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Table grid
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
    ])

def generate_vocabulary_pdf(filename, vocab_data):
    """Generate a PDF with a vocabulary table."""
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    chinese_font = 'STSong-Light' # from Adobe's Asian Language Packs
    pdfmetrics.registerFont(UnicodeCIDFont(chinese_font))

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
    # Sample vocabulary data: (vocabulary, part of speech, Chinese meaning)
    vocab_data = [
        ("apple", "noun", "蘋果"),
        ("run", "verb", "跑"),
        ("beautiful", "adjective", "美麗"),
        ("quickly", "adverb", "快速地"),
    ]

    # Generate PDF
    output_filename = "vocabulary_list.pdf"
    generate_vocabulary_pdf(output_filename, vocab_data)

if __name__ == "__main__":
    main()