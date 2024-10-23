import re
import json

"""
Auther: @Amer N. Tahat, Collins Aerospace, Nov 2023 all rights reserved. 
Description: human readable conversation log file to json proof shots dictionary file. 
with acc_w and acc_tk (before making it optional).
"""


def extract_lemmas_and_proofs(file_path):
    with open(file_path, 'r') as file:
        text = file.read()

    # Regular expression to match the lemma and its proof
    lemma_pattern = r"Lemma\s+([a-zA-Z0-9_]+)\s*:(.*?)Proof\.(.*?)Qed\."

    # Find all matches
    matches = re.findall(lemma_pattern, text, re.DOTALL)

    # Dictionary to store lemmas and their proofs
    lemmas = {}

    for match in matches:
        lemma_name = match[0].strip()
        proof_text = match[2].strip().split("\n")
        proof_text = [line.strip() for line in proof_text if line.strip()]
        proof_text = '\n'.join(proof_text)  # Joining all proof lines into a single string

        # Append proof to existing lemma entry or create a new one
        if lemma_name in lemmas:
            lemmas[lemma_name]["proof-shots"].append(proof_text)
        else:
            lemmas[lemma_name] = {"lemma-name": lemma_name, "proof-shots": [proof_text]}

    # Convert the dictionary values to a list of dictionaries
    lemmas_list = list(lemmas.values())

    return lemmas_list


def main():
    file_name = input("Enter the file name: ")
    lemmas = extract_lemmas_and_proofs(file_name)

    # Convert the list of dictionaries to JSON
    json_output = json.dumps(lemmas, indent=4)

    # Save to a file
    output_file = "lemmas.json"
    with open(output_file, "w") as file:
        file.write(json_output)

    print(f"Lemmas and proofs have been saved to '{output_file}'")


if __name__ == "__main__":
    main()
