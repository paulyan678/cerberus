from os import getenv
from sys import argv, stdin, stdout

from chromadb import Client
from dotenv import load_dotenv
from jsonlines import Reader, Writer
from sentence_transformers import SentenceTransformer


def main():
    load_dotenv()

    client = Client()
    name = getenv('CHROMADB_COLLECTION_NAME')

    for collection in client.list_collections():
        if collection.name == name:
            client.delete_collection(name)

    collection = client.get_or_create_collection(
        name,
        metadata={'hnsw:space': 'cosine'},
    )

    with Reader(stdin) as reader:
        inputs = list(reader)

    lookup = {}

    for i, input_ in enumerate(inputs):
        id_ = str(i)
        collection.add(ids=id_, embeddings=input_['embedding'])
        lookup[id_] = input_

    embedding_model = SentenceTransformer(getenv('EMBEDDING_MODEL'))
    raw_k, *queries = argv[1:]
    k = int(raw_k)
    query_embeddings = embedding_model.encode(queries).tolist()
    results = collection.query(query_embeddings=query_embeddings, n_results=k)

    with Writer(stdout) as writer:
        for i, query in enumerate(queries):
            for j, (id_, distance) in enumerate(
                    zip(results['ids'][i], results['distances'][i]),
            ):
                writer.write(
                    (
                        {'query': query, 'rank': j + 1, 'distance': distance}
                        | lookup[id_]
                    )
                )


if __name__ == '__main__':
    main()
