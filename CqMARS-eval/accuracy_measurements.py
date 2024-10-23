import json
import csv
from coqdog_special_stats_scripts import calculate_acc_w, calculate_acc_tk  # Import the function from your existing
from measure_relativeness_cosine_distances import compute_distances

"""
Auther: @Amer N. Tahat, Collins Aerospace, Nov 2023 all rights reserved. 
Description: Computes accuracy measurements for given json conversation history dictionary file and outputs a csv file
 with diff_w and diff_tk cosine distances rounded 0.3f (before making it optional) - fixes dir paths as user inputs.
"""


def process_json_and_write_csv(json_file_path, csv_file_path):
    # Read JSON data
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Open CSV file for writing
    with open(csv_file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['lemma-name', 'diff_w\' %', 'diff_tk\' %', 'cosine distance', 'number of shots']) # compute
        # the cosine distance

        # Process each entry in JSON data
        for entry in data:
            lemma_name = entry['lemma-name']
            proofshots = entry['proof-shots']
            cosine_distance = compute_distances(proofshots)
            acc_w_results = calculate_acc_w(proofshots)
            acc_tk_results = calculate_acc_tk(proofshots)
            number_of_shots = len(proofshots)

            # Write to CSV
            csvwriter.writerow([lemma_name, acc_w_results, acc_tk_results, cosine_distance, number_of_shots])


def main():
    json_file_path = './conversation_history/temp_human_readble_conversation_history_logout/Appraisal_Evidence_7397_dict.json'
    # './conversation_history/temp_human_readble_conversation_history_logout/MoreLists_good_conversation_6k.json'
    # './conversation_history_proofshots_dict.json' 'path_to_json_file_dict.json'  # Replace with
    # JSON file path
    csv_file_path = './conversation_statistical_analysis/acc_measurements_conversation_history_proofshots_Appraisal_7397.csv'  # Path for the output CSV file
    process_json_and_write_csv(json_file_path, csv_file_path)
    print(f"Processed data has been written to {csv_file_path}")


if __name__ == "__main__":
    main()
