from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, HRFlowable, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from utils import create_vocabulary_table, week_of_month 
from functools import reduce
import os

def register_chinese_font() -> str:
    chinese_font = None
    try:
        # use a TrueType font for Chinese        
        # Fonts from: https://fonts.google.com/noto/fonts
        if os.path.exists('fonts/NotoSansTC-Medium.ttf'): 
            pdfmetrics.registerFont(TTFont('ChineseFont', 'fonts/NotoSansTC-Medium.ttf'))
            chinese_font = 'ChineseFont'
        else:
            # Fallback to CID font
            chinese_font = 'STSong-Light'
            pdfmetrics.registerFont(UnicodeCIDFont(chinese_font))
    except:
        # Final fallback
        chinese_font = 'STSong-Light'
        pdfmetrics.registerFont(UnicodeCIDFont(chinese_font))
    
    return chinese_font

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

async def generate_vocabulary_pdf(filename, vocab_data):
    """Generate a PDF with a vocabulary table."""
    # Create PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    chinese_font = register_chinese_font()
    
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
    table_data = await create_vocabulary_table(vocab_data)
    table = Table(table_data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(style_vocabulary_table(chinese_font))

    # Add table to elements
    elements.append(table)

    # Build PDF
    doc.build(elements)
    print(f"PDF generated: {filename}")


def set_tuition_debit_note_style(chinese_font):
    styles = getSampleStyleSheet()
    
    # Updated styles with proper font settings
    styles.add(ParagraphStyle(
        name='ChineseNormal',
        fontName=chinese_font,
        fontSize=11,
        leading=16,
        alignment=TA_LEFT,
        wordWrap='CJK'
    ))

    styles.add(ParagraphStyle(
        name='TitleCenter',
        fontName='Helvetica-Bold',  # English title in English font
        fontSize=16,
        alignment=TA_CENTER,
        wordWrap='CJK',
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='BilingualTitle',
        fontName=chinese_font,
        fontSize=14,
        leading=12,
        alignment=TA_CENTER,
        wordWrap='CJK',
        spaceAfter=10
    ))

    table_style = TableStyle([
        # Font settings
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        
        # Alignment
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),      # First column left-aligned
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),   # Other columns centered
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        
        # Borders - complete grid for all rows including total
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Total row styling
        ('SPAN', (0, -1), (1, -1)),  # Merge first two columns for "Total"
        ('FONTNAME', (0, -1), (-1, -1), chinese_font),
        ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ])

    return styles, table_style

def generate_tuition_debit_note(
    filename: str,
    student_name: str,
    months: list,                     # e.g. [11, 10]
    lesson_data: list,                  # List of dicts → see example below
    course_name: str,
    notes: list = []               # Optional notes (e.g. payment received message)
) -> None:
    """
    Generates a Tuition Fee Debit Note that looks identical to your PDF.
    """
    chinese_font = register_chinese_font()
    
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch)
    elements = []
    styles, table_style = set_tuition_debit_note_style(chinese_font)

    is_nested = lesson_data and isinstance(lesson_data[0], list)
    if not is_nested:
        lesson_data = [lesson_data]
    
    if len(notes) < len(lesson_data):
        notes = notes + ["" for _ in range(len(lesson_data) - 1)]

    for page_num, page_lessons in enumerate(lesson_data, start=0):
        # 1. Header
        header = Paragraph("Louis English Tutorial Lesson", styles['TitleCenter'])
        elements.append(header)
        elements.append(Spacer(1, 6))

        # 2. Main title (bilingual)
        title = Paragraph("Tuition Fee Debit Note<br/><br/>學費單", styles['BilingualTitle'])
        elements.append(title)

        # 3. Student & Tutor info
        info = Paragraph(
            f"Student Name 學生姓名: <b>{student_name}</b><br/>"
            f"Tutor Name 導師姓名: <b>Louis Tsang</b>",
            styles['ChineseNormal']
        )
        elements.append(info)
        elements.append(Spacer(1, 12))

        # 4. Month
        month_style = ParagraphStyle(
            name='Month',
            fontName=chinese_font,
            fontSize=12,
            leading=10,
            alignment=TA_LEFT,
            spaceAfter=8
        )
        elements.append(Paragraph(f'{months[page_num]}月', month_style))
        elements.append(Spacer(1, 12))
         # 1. Header with student name and page number
        header_style = ParagraphStyle(
            name='Header',
            fontName=chinese_font,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # if len(lesson_data) > 1:
        #     header_text = f"<b>{student_name} - Page {page_num}/{len(lesson_data)}</b>"
        # else:
        #     header_text = f"<b>{student_name}</b>"
        
        # elements.append(Paragraph(header_text, header_style))
        # elements.append(Spacer(1, 10))

        if page_lessons:
            # 5. Table data
            table_data = [
                ["Tuition Fees\n學費", "Payment\n付款狀態", "Lesson\n課堂狀態"]
            ]

            for lesson in page_lessons:
                desc = f"補堂 -- {lesson['makeup']} ({lesson['date']})" if lesson["makeup"] else f"{course_name} ({lesson['date']}) - {lesson['amount']} HKD" 
                row = [
                    desc,
                    lesson['payment'],
                    lesson['status']
                ]
                table_data.append(row)

            # Add total row with proper spacing
            total = reduce(lambda curr, next: curr + next, [int(lesson["amount"]) for lesson in page_lessons if lesson["makeup"] is None])
            table_data.append(["Total 總數", "", f"${total:,} HKD"])

            # 6. Table styling with fixed borders
            table = Table(table_data, colWidths=[3.8*inch, 1.3*inch, 1.3*inch])
            
            table.setStyle(table_style)
            elements.append(table)

        # 7. Optional Notes
        elements.append(Spacer(1, 20))
        note_header = ParagraphStyle(
            name='NoteHeader',
            fontName=chinese_font,
            fontSize=12,
            leading=16,
            spaceAfter=6
        )
        elements.append(Paragraph("<b>Notes 備註</b>", note_header))
        note_style = ParagraphStyle(
            name='NoteBody',
            fontName=chinese_font,
            fontSize=10,
            leading=14
        )
        formatted_notes = notes[page_num].replace('\\n', '<br/>')
        elements.append(Paragraph(formatted_notes, note_style))
        
                # Add page break if not the last page
        if page_num < len(lesson_data):
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)
    print(f"Tuition debit note generated: {filename}")
    os.makedirs("tuition_notes", exist_ok=True)
    os.rename(f"{filename}", f"tuition_notes/{filename}")


# testing
if __name__ == "__main__":
    print("Testing...")