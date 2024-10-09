from functools import partial
from glob import glob
from itertools import chain
from os import getenv
from sys import argv, stdout

from dotenv import load_dotenv
from google.generativeai import configure, upload_file
from jsonlines import Writer
from tqdm import tqdm


def main():
    load_dotenv()
    configure(api_key=getenv('GOOGLE_GENERATIVE_AI_API_KEY'))

    pathnames = chain.from_iterable(
        map(partial(glob, recursive=True), argv[1:]),
    )

    with Writer(stdout) as writer:
        for pathname in tqdm(pathnames):
            while True:
                try:
                    video_file = upload_file(path=pathname)
                    break
                except Exception:
                    pass

            writer.write({'pathname': pathname, 'name': video_file.name})


if __name__ == '__main__':
    main()
