import csv

def parse_vocab_file(file):
    try:
        with open(file, "r") as f:
            reader = csv.reader(f)
            vocab_data = [tuple(i) for i in reader]
        return vocab_data
    except IOError as error:
        print(error)
