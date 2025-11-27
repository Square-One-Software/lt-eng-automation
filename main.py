from utils import parse_vocab_file, parse_tuition_file, get_month_and_month_name 
from pdf_utils import generate_vocabulary_pdf
from tuition_debit_note import generate_tuition_debit_note
import argparse, asyncio


def main():
    VC, TU = "vc", "tu"
    parser = argparse.ArgumentParser(prog="LT ENG PDF Generator", description="Generate PDF for vocabulary list or tuition debit note.")
    parser.add_argument('-t', '--type', type=str, choices=[VC, TU], required=True, default="vc", help="Type of PDF to generate: vc = vocab list, tu = tuition debit note")
    parser.add_argument('-o', '--output', type=str, default="vocabulary_list.pdf",
                        help="Output PDF filename (default: vocabulary_list.pdf)")
    parser.add_argument('-f', '--file', type=str, help="Input vocabulary csv file name (vocab.csv)", required=True)
    # Parse arguments
    args = parser.parse_args()
    csv_filename = args.file
    if args.type == VC: 
        output_filename = args.output
        vocab_data = parse_vocab_file(csv_filename)
        # Generate PDF
        asyncio.run(generate_vocabulary_pdf(output_filename, vocab_data))
    else:
        lesson_data, course_desc, student_name = parse_tuition_file(csv_filename)
        month, month_name = get_month_and_month_name()
        generate_tuition_debit_note(
            filename=f"{student_name}_{month_name}_2025.pdf",
            student_name=student_name,
            month=f"{month}月",
            lessons=lesson_data,
            lesson_desc=course_desc,
            notes=""
        )
if __name__ == "__main__":
    main()