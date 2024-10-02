from os import getenv
from sys import stdout

from dotenv import load_dotenv
from google.generativeai import configure, list_files
from jsonlines import Writer
from tqdm import tqdm


def main():
    load_dotenv()
    configure(api_key=getenv('GOOGLE_GENERATIVE_AI_API_KEY'))

    with Writer(stdout) as writer:
        for file in tqdm(list_files()):
            writer.write({'name': file.name})


if __name__ == '__main__':
    main()
