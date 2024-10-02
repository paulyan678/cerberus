import json
import argparse
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import shutil

def load_json_file(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as f:
        return [json.loads(line) for line in f]

def generate_embeddings(descriptions, embedding_model):
    """Generate embeddings for the given descriptions."""
    model = SentenceTransformer(embedding_model)
    embeddings = model.encode(descriptions)
    return embeddings

def main():

    load_dotenv()
    embedding_model = os.getenv('EMBEDDING_MODEL')

    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Generate embeddings for descriptions from a JSON Lines file.')
    parser.add_argument('--input_file', type=str, help='Path to the input JSON Lines file')
    parser.add_argument('--output_file_embedding', type=str, help='Path to the output JSON file')
    parser.add_argument('--output_file_text_dir', type=str, help='Path to the output JSON file')

    args = parser.parse_args()

    # Load JSON data from the input file
    data = load_json_file(args.input_file)

    # Extract descriptions
    descriptions = [entry.get('description', '') for entry in data]

    # Generate embeddings for the descriptions
    embeddings = generate_embeddings(descriptions, embedding_model)

    # Print or save the embeddings as needed
    with open(args.output_file_embedding, 'w') as f:
        json.dump(embeddings.tolist(), f)
    
    print(f"Embeddings written to {args.output_file_embedding}")

    # make a directory to store the text files
    if os.path.exists(args.output_file_text_dir):
        # delete the entire directory
        shutil.rmtree(args.output_file_text_dir)

    os.makedirs(args.output_file_text_dir)    
    for description, entry in zip(descriptions, data):
        text_file_path = os.path.join(args.output_file_text_dir, f"{os.path.basename(entry['pathname']).split('.')[0]}.txt")
        with open(text_file_path, 'w') as f:
            if description == None:
                description = ""
            f.write(description)

    print(f"Descriptions written to {args.output_file_text_dir}")

if __name__ == '__main__':
    main()
