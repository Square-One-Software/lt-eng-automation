from utils import parse_vocab_file, parse_tuition_file, parse_note_txt
from pdf_utils import generate_vocabulary_pdf, generate_tuition_debit_note
from datetime import datetime
from pathlib import Path
import argparse, asyncio, shutil, os


def main():
    VC, TU = "vc", "tu"
    parser = argparse.ArgumentParser(prog="LT ENG PDF Generator", description="Generate PDF for vocabulary list or tuition debit note.")
    parser.add_argument('-t', '--type', type=str, choices=[VC, TU], required=True, default="vc", help="Type of PDF to generate: vc = vocab list, tu = tuition debit note")
    parser.add_argument('-o', '--output', type=str, default="vocabulary_list.pdf",
                        help="Output PDF filename (default: vocabulary_list.pdf)")
    parser.add_argument('-f', '--file', type=str, help="Input vocabulary csv file name (vocab.csv)", required=True)
    parser.add_argument('-n', '--note', type=str, help="Input txt file name for notes (notes.csv)", required=False)
    # Parse arguments
    args = parser.parse_args()
    csv_filename = args.file
    note_filename = args.note
    if args.type == VC: 
        output_filename = args.output
        vocab_data = parse_vocab_file(csv_filename)
        # Generate PDF
        asyncio.run(generate_vocabulary_pdf(output_filename, vocab_data))
    else:
        note_data = "\n"
        if note_filename:
            note_data = "\n".join(parse_note_txt(note_filename)) 
        tuition_data_dir = "tuition_data"
        lesson_data, course_desc, student_name, month, month_name = parse_tuition_file(os.path.join(tuition_data_dir, csv_filename))
        current_year = datetime.now().year
        file_name = f"TuitionFeeDebitNote_{student_name}_{month_name}_{current_year}.pdf"
        generate_tuition_debit_note(
            filename=file_name,
            student_name=student_name,
            month=f"{month}月",
            lesson_data=lesson_data,
            course_name=course_desc,
            notes=note_data
        )
        tuition_note_dir = "tuition_notes"
        if not Path(tuition_note_dir).is_dir():
            os.makedirs(tuition_note_dir)

        shutil.move(file_name, os.path.join(tuition_note_dir, file_name))
        
if __name__ == "__main__":
    main()