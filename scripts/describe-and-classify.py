from os import getenv
from pathlib import Path
from sys import argv, path, stdin, stdout

from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel, get_file
from jsonlines import Reader, Writer
from tqdm import tqdm

path.append(str(Path(__file__).parent.parent))

from cerberus import describe_and_classify  # noqa: E402


def main():
    load_dotenv()
    configure(api_key=getenv('GOOGLE_GENERATIVE_AI_API_KEY'))

    model = GenerativeModel(getenv('GOOGLE_GENERATIVE_AI_MODEL'))
    classes = getenv('CLASSES').split(', ')

    with Reader(stdin) as reader:
        inputs = list(reader)

    with Writer(stdout) as writer:
        for input_ in tqdm(inputs):
            while True:
                try:
                    # Attempt to download the file
                    video_file = get_file(input_['name'])
                    break  # Exit the loop if successful
                except Exception as e:
                    continue

            input_['description'], input_['classifications'] = (
                describe_and_classify(model, video_file, classes)
            )

            writer.write(input_)


if __name__ == '__main__':
    main()
