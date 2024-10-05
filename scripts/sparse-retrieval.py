from tempfile import mkdtemp
from sys import argv, stdin, stdout

from dotenv import load_dotenv
from jsonlines import Reader, Writer
from whoosh.analysis import (
    LowercaseFilter,
    RegexTokenizer,
    StemFilter,
    StopFilter,
)
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser


def main():
    load_dotenv()

    analyzer = (
        RegexTokenizer()
        | LowercaseFilter()
        | StopFilter()
        | StemFilter()
    )
    schema = Schema(
        id_=ID(stored=True),
        description=TEXT(stored=True, analyzer=analyzer),
    )
    index = create_in(mkdtemp(), schema)
    writer = index.writer()

    with Reader(stdin) as reader:
        inputs = list(reader)

    lookup = {}

    for i, input_ in enumerate(inputs):
        id_ = str(i)
        writer.add_document(id_=id_, description=input_['description'])
        lookup[id_] = input_

    writer.commit()

    query_parser = QueryParser('description', schema=schema)
    searcher = index.searcher()
    raw_k, *queries = argv[1:]
    k = int(raw_k)

    with Writer(stdout) as writer:
        for i, query in enumerate(queries):
            parsed_query = query_parser.parse(query)
            hits = searcher.search(parsed_query, limit=k)

            for j, hit in enumerate(hits):
                writer.write(
                    (
                        {'query': query, 'rank': j + 1}
                        | lookup[hit['id_']]
                    ),
                )


if __name__ == '__main__':
    main()
