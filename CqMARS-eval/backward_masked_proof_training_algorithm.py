import json
import re
import sys

"""
Auther: @Amer N. Tahat, Collins Aerospace, This is a legacy coqdog code for the early desktop version of coqdog, can be used for training (fine-tune). 2023 all rights reserved.
"""


def read_file_content(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content


def extract_lemmas_and_proofs(content):
    lemma_pattern = r'Lemma\s+(?P<name>[\w]+)\s*:\s*(?P<context>.*?)\s*Proof\.\s*(?P<proof>.*?)(' \
                    r'?P<end_statement>\s*Qed\.|\s*Defined\.)'
    return re.findall(lemma_pattern, content, re.DOTALL)


def create_jsonl_file(lemmas_and_proofs, output_file):

    ends_prompt = "\n####\n"
    white_space = " "
    ends_completion = "###"

    with open(output_file, 'w') as file:

        for name, context, proof, end_statement in lemmas_and_proofs:
            proof_lines = proof.split('\n')
            mask_size = 1 if len(proof_lines) <= 30 else 2

            for i in range(0, len(proof_lines), mask_size):
                masked_proof = '\n'.join(proof_lines[:i]) + '\n' + ' '.join(['_' for _ in proof_lines[i:i+mask_size]])
                prompt = f"Prove that Lemma {name}: {context} Proof: {masked_proof}" + ends_prompt
                completion = f"{white_space}Proof. {proof} {end_statement.strip()}" + ends_completion
                data = {'prompt': prompt, 'completion': completion}
                file.write(json.dumps(data) + '\n')


def main():
    """use terminal to input paths"""
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    file_content = read_file_content(input_file)
    lemmas_and_proofs = extract_lemmas_and_proofs(file_content)
    create_jsonl_file(lemmas_and_proofs, output_file)


if __name__ == "__main__":
    main()
