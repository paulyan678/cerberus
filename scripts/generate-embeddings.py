from operator import itemgetter
from os import getenv
from sys import stdin, stdout

from dotenv import load_dotenv
from jsonlines import Reader, Writer
from sentence_transformers import SentenceTransformer


def main():
    load_dotenv()

    embedding_model = SentenceTransformer(getenv('EMBEDDING_MODEL'))

    with Reader(stdin) as reader:
        inputs = list(reader)

    descriptions = list(map(itemgetter('description'), inputs))
    embeddings = embedding_model.encode(descriptions)

    for input_, embedding in zip(inputs, embeddings):
        input_['embedding'] = embedding.tolist()

    with Writer(stdout) as writer:
        writer.write_all(inputs)


if __name__ == '__main__':
    main()
