from os import getenv
from sys import stdin

from dotenv import load_dotenv
from google.generativeai import configure, delete_file
from jsonlines import Reader
from tqdm import tqdm


def main():
    load_dotenv()
    configure(api_key=getenv('GOOGLE_GENERATIVE_AI_API_KEY'))

    with Reader(stdin) as reader:
        inputs = list(reader)

    for input_ in tqdm(inputs):
        delete_file(name=input_['name'])


if __name__ == '__main__':
    main()
