import os
""" 
@Auther : Amer N. Tahat, Collins Aerospace.
@Description : from coqdog_lemma_proofshots_json_dictionaries import extract_lemmas_and_proofs, 
 write_results_proofshots_dictionary_to_json """

import v2_coqdog_conversation_proofshots_dict
from accuracy_measurements import process_json_and_write_csv


def analyze_proofs(conversation_history_json_file_path='',
                   # './temp-history/conversation_history_20231127_141025.json',
                   # './conversation_histories/conversation_history.json', used to be default directory and it should be
                   dictionary_file_path='',
                   csv_file_path=None, conversation_title=""):
    """
    Analyzes proofs from a conversation history, writes them to a dictionary, and computes their accuracy.
    Saves the results in a 'proof_analysis' directory.
    """
    os.makedirs('proof_analysis', exist_ok=True)

    if csv_file_path is None:
        # Use the conversation_title in the file name
        csv_file_path = f'proof_analysis/{conversation_title}_accuracy_measurements.csv'

    formatted_results = v2_coqdog_conversation_proofshots_dict.extract_lemmas_and_proofs(conversation_history_json_file_path)
    print(f"the extract lemma and proofs script used the path {conversation_history_json_file_path}")
    v2_coqdog_conversation_proofshots_dict.write_results_proofshots_dictionary_to_json(formatted_results, dictionary_file_path)
    print(f"created dictionary at {dictionary_file_path}")
    process_json_and_write_csv(dictionary_file_path, csv_file_path)
    print(f"created accuracy analysis csv file at {csv_file_path}")


def main():
    """
    Main function to execute the script.
    """
    # Get conversation title from user input
    conversation_title = input("Enter the conversation title: ")
    temp_history_path = input("Enter the conversation history path: ")
    output_dictionary_path = input("Enter the conversation history dictionary output path: ")
    output_stats_path = f"./{conversation_title}_stats.csv"
    analyze_proofs(conversation_title=conversation_title,conversation_history_json_file_path=f"./{temp_history_path}",
                   # './temp-history/conversation_history_20231127_141025.json',
                   # './conversation_histories/conversation_history.json', used to be default directory and it should be
                   dictionary_file_path=f"./{output_dictionary_path}",
                   csv_file_path=output_stats_path)
    print(f"created accuracy analysis csv file")


if __name__ == "__main__":
    main()
