import openai
import os
from dotenv import load_dotenv, find_dotenv
from openai.embeddings_utils import get_embedding, distances_from_embeddings

load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.getenv('OPENAI_API_KEY')


def compute_distances(strings, model="text-embedding-ada-002"):
    """
    Computes the cosine distances between each string in the list and the final string,
    rounded to three decimal places.
    """
    embeddings = [get_embedding(string, engine=model) for string in strings]
    golden_example_embedding = embeddings[-1]
    raw_distances = distances_from_embeddings(golden_example_embedding, embeddings, distance_metric="cosine")

    # Round each distance to three decimal places
    rounded_distances = [round(distance, 3) for distance in raw_distances]
    return rounded_distances


def main():
    # List of strings to compute distances
    strings = ["string 1", "string 2", "string 3"]  # Replace with your actual strings

    # Compute distances
    distances = compute_distances(strings)

    # Print distances
    print("Cosine distances from the last string to each string in the list:")
    for i, distance in enumerate(distances):
        print(f"String {i + 1}: {distance}")


if __name__ == "__main__":
    main()
