from utils import parse_vocab_file 
from pdf_utils import generate_vocabulary_pdf
import argparse, asyncio


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
    asyncio.run(generate_vocabulary_pdf(output_filename, vocab_data))

if __name__ == "__main__":
    main()