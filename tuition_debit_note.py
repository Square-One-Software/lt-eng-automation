# tuition_debit_note.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from functools import reduce
from utils import parse_tuition_file, month_conversion
import os

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
    month: str,                     # e.g. "11月" or "9月"
    lessons: list,                  # List of dicts → see example below
    lesson_desc: str,
    notes: str = None               # Optional notes (e.g. payment received message)
) -> None:
    """
    Generates a Tuition Fee Debit Note that looks identical to your PDF.
    """
        # Register Chinese font - using a better approach
    # Try multiple Chinese font options
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
    
    doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=0.8*inch, bottomMargin=0.8*inch)
    elements = []
    styles, table_style = set_tuition_debit_note_style(chinese_font)
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
    elements.append(Paragraph(month, month_style))
    elements.append(Spacer(1, 12))

    # 5. Table data
    table_data = [
        ["Tuition Fees\n學費", "Payment\n付款狀態", "Lesson\n課堂狀態"],
    ]
    for lesson in lessons:
        row = [
            f"{lesson_desc} ({lesson['date']}) - {lesson['amount']} HKD",
            lesson['payment'],
            lesson['status']
        ]
        table_data.append(row)

    # Add total row with proper spacing
    total = reduce(lambda curr, next: curr + next, [int(lesson["amount"]) for lesson in lessons])
    table_data.append(["Total 總數", "", f"${total:,} HKD"])

    # 6. Table styling with fixed borders
    table = Table(table_data, colWidths=[3.8*inch, 1.3*inch, 1.3*inch])
    
    table.setStyle(table_style)
    elements.append(table)

    # 7. Optional Notes
    if notes:
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
        elements.append(Paragraph(notes, note_style))

    # Build PDF
    doc.build(elements)
    print(f"Tuition debit note generated: {filename}")


if __name__ == "__main__":
    lesson_data, course_desc, student_name = parse_tuition_file("1 對 1 初中英文面授課-Emma.csv")
    month = 11
    month_name = month_conversion(month)
    generate_tuition_debit_note(
        filename=f"{student_name}_{month_name}_2025.pdf",
        student_name=student_name,
        month=f"{month}月",
        lessons=lesson_data,
        lesson_desc=course_desc,
        notes=""
    )