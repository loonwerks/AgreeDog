import re
import csv


def extract_lemma_names(coq_file):
    with open(coq_file, 'r') as file:
        content = file.read()

    lemmas = re.findall(r"Lemma\s+(\w+)\s*:(.*?)(?:Proof|Qed|Defined|\.)(?!\s*with)", content, re.DOTALL)
    return [lemma[0].strip() for lemma in lemmas]


def write_to_csv(lemma_names, csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Sample', 'lemma-name', 'relative-acc_w (change) per shot', 'number of shots'])

        for idx, name in enumerate(lemma_names, 1):
            writer.writerow([idx, name, '', ''])


def main():
    # Specify your Coq file name
    coq_file_name = "LTS.v"
    csv_file_name = "metrics.csv"

    # Extract lemma names and write to CSV
    lemma_names = extract_lemma_names(coq_file_name)
    write_to_csv(lemma_names, csv_file_name)

    print(f"CSV file '{csv_file_name}' has been created with the extracted lemma names.")


if __name__ == "__main__":
    main()
