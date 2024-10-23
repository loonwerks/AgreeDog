import json
import re
import sys

"""
Auther: @Amer N. Tahat, Collins Aerospace, Nov 2023 all rights reserved. 
Description: extracts proof-shots dictionaries.
"""


def extract_lemmas_and_proofs(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    lemma_proofs = {}
    lemma_pattern = re.compile(r"Lemma\s+(\w+)\s*:(.*?)(?:Proof|Qed|Defined|\.)(?!\s*with)", re.DOTALL)  # r"Lemma\s+(
    # \w+)\s*:(.*?)Proof\.(.*?)Qed\.", re.DOTALL)

    for item in data:
        if item['role'] == 'assistant':
            content = item['content']
            matches = re.findall(lemma_pattern, content)
            for match in matches:
                lemma_name, _, proof_body = match
                lemma_name = lemma_name.strip()
                proof_body = proof_body.strip()

                if lemma_name not in lemma_proofs:
                    lemma_proofs[lemma_name] = []
                lemma_proofs[lemma_name].append(proof_body)

    # Convert to the desired format
    formatted_results = [{'lemma-name': lemma, 'proof-shots': proofs} for lemma, proofs in lemma_proofs.items()]
    return formatted_results


def write_results_proofshots_dictionary_to_json(formatted_results, output_file):
    with open(output_file, 'w') as file:
        json.dump(formatted_results, file, indent=4)


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py path_to_json_file path_to_output_file")
        sys.exit(1)

    json_file_path = sys.argv[1]
    output_file_path = sys.argv[2]

    formatted_results = extract_lemmas_and_proofs(json_file_path)
    write_results_proofshots_dictionary_to_json(formatted_results, output_file_path)

    print(f"Results have been written to {output_file_path}")


if __name__ == "__main__":
    main()
