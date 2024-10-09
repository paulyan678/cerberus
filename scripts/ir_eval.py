import json
import subprocess
from os.path import basename as base_name
import numpy as np
import argparse


def search_documents(query, embeddings_file, return_k, spares_or_dense):
    """
    Executes the dense retrieval script and retrieves documents for a given query.

    Args:
        query (str): The query to search.
        embeddings_file (str): Path to the embeddings file.
        return_k (int, optional): Number of documents to return.

    Returns:
        list: Retrieved document identifiers.
    """
    # Build the command
    if spares_or_dense == "sparse":
        command = [
            "python", "scripts/sparse-retrieval.py",
            str(return_k),
            query
        ]
    elif spares_or_dense == "dense":
        command = [
            "python", "scripts/dense-retrieval.py",
            str(return_k),
            query
        ]
    else:
        raise ValueError("Invalid retrieval method. Choose either 'sparse' or 'dense'.")

    # Execute the command and capture the output
    relvent_ids = []
    try:
        process = subprocess.run(
            command,
            input=open(embeddings_file).read(),
            text=True,
            capture_output=True,
            check=True
        )
        # Parse output assuming one document per line
        retrieved_docs = process.stdout.strip().splitlines()
        retrieved_docs = [json.loads(ele) for ele in list(retrieved_docs)]
        for i in range(len(retrieved_docs)):
            relvent_ids.append(base_name(retrieved_docs[i]['pathname']))
    except subprocess.CalledProcessError as e:
        print(f"Error while running dense retrieval script: {e}")
        retrieved_docs = []

    # ranked results
    return relvent_ids


def compute_map(relevance_scores, total_relevant_docs):
    # Ensure the input is a NumPy array
    relevance_scores = np.array(relevance_scores)
    
    # Compute precision and recall at each rank
    num_hits = 0
    average_precision = 0.0
    
    for i, score in enumerate(relevance_scores, start=1):
        if score == 1:  # Relevant document
            num_hits += 1
            precision_at_i = num_hits / i
            average_precision += precision_at_i
    
    # Compute MAP
    map_score = average_precision / total_relevant_docs if total_relevant_docs > 0 else 0.0
    
    return map_score


def evaluate_ir_system(queries, embeddings_file, ground_truth_file, return_k, top_k, spares_or_dense):
    metrics = ['precision at k', "recall at k", "f1 at k", "MAP"]
    # Load ground truth data
    with open(ground_truth_file, "r") as gt_file:
        ground_truth = json.load(gt_file)

    overall_scores = {metric: [] for metric in metrics}
    results = {}
    wrong_results = {}
    right_results = {}

    for query in queries:
        retrieved_docs = search_documents(query, embeddings_file, return_k, spares_or_dense)
        relevant_docs = ground_truth.get(query, [])
        right_results[query] = [doc for doc in retrieved_docs if doc in relevant_docs]
        wrong_results[query] = [doc for doc in retrieved_docs if doc not in relevant_docs]
        right_results[query] = right_results[query]
        wrong_results[query] = wrong_results[query]
        

        # Compute precision at k
        top_k_retrieved = retrieved_docs[:top_k]
        relevant_in_top_k = len([doc for doc in top_k_retrieved if doc in relevant_docs])
        precision_at_k = relevant_in_top_k / top_k if top_k > 0 else 0

        recall = relevant_in_top_k / len(relevant_docs) if len(relevant_docs) > 0 else 0
        f1 = 2 * (precision_at_k * recall) / (precision_at_k + recall) if (precision_at_k + recall) > 0 else 0
        MAP = compute_map([1 if doc in relevant_docs else 0 for doc in retrieved_docs], len(relevant_docs))

        query_results = {}
        query_results['precision at k'] = precision_at_k
        query_results['recall at k'] = recall
        query_results['f1 at k'] = f1
        query_results['MAP'] = MAP
        results[query] = query_results

        overall_scores['precision at k'].append(precision_at_k)
        overall_scores['recall at k'].append(recall)
        overall_scores['f1 at k'].append(f1)
        overall_scores['MAP'].append(MAP)

    # Calculate averages
    for metric in metrics:
        overall_scores[metric] = (
            sum(overall_scores[metric]) / len(overall_scores[metric])
            if overall_scores[metric]
            else 0
        )

    # Print results
    print("\nEvaluation Results:")
    print("-" * 50)
    for query, query_results in results.items():
        print(f"Query: {query}")
        print("Right Results:")
        print(right_results[query])
        print("Wrong Results:")
        print(wrong_results[query])
        for metric, score in query_results.items():
            print(f"  {metric.upper()}: {score:.4f}")
        print("-" * 50)

    print("Overall Averages:")
    for metric, avg_score in overall_scores.items():
        print(f"  {metric.upper()}: {avg_score:.4f}")



if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Evaluate IR System with specified inputs.")
    parser.add_argument('--queries', nargs='+', required=True,
                        help='List of queries to evaluate, separated by spaces.')
    parser.add_argument('--embeddings_file', type=str, required=True,
                        help='Path to the embeddings file (e.g., data/video-description-embeddings.jsonl).')
    parser.add_argument('--ground_truth_file', type=str, required=True,
                        help='Path to the ground truth file (e.g., data/ground_truth.json).')
    parser.add_argument('--return_k', type=int, required=True,
                        help='Number of top documents to return from the IR system.')
    parser.add_argument('--top_k', type=int, required=True,
                        help='Number of top documents to evaluate precision for.')
    parser.add_argument('--sparse_or_dense', type=str, required=True,
                        help='Number of top documents to evaluate precision for.')
    

    # Parse the arguments
    args = parser.parse_args()

    # Call the evaluate_ir_system function with parsed arguments
    evaluate_ir_system(
        queries=args.queries,
        embeddings_file=args.embeddings_file,
        ground_truth_file=args.ground_truth_file,
        return_k=args.return_k,
        top_k=args.top_k,
        spares_or_dense=args.sparse_or_dense
    )
