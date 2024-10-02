import os
import os
import argparse
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import RegexTokenizer, LowercaseFilter

from whoosh import index, writing
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import *
from whoosh.qparser import QueryParser
import os.path
import tempfile
class IR():

    def __init__(self, document_dir):
        self.file_list = [os.path.join(document_dir, file) for file in os.listdir(document_dir) if file.endswith(".txt")]


        self.create_index()
        self.create_parser_searcher()
    def create_index(self):
        """
        INPUT:
            None
        OUTPUT:
            None

        """
        my_analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter() | StemFilter()
        schema = Schema(file_path=ID(stored=True), file_content=TEXT(stored=True, analyzer=my_analyzer))
        index_dir = tempfile.mkdtemp()
        self.index_sys = index.create_in(index_dir, schema)

    def add_files(self):
        """
        INPUT:
            None
        OUTPUT:
            None

        NOTE: Add buffer to self.index_sys
        """
        writer = writing.BufferedWriter(self.index_sys, period=None, limit=1000)

        for file_path in self.file_list:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                writer.add_document(file_path=file_path, file_content=file_content)
                # print(f"Indexing {file_path}")
        print(f"Done Indexing {len(self.file_list)} files")
        writer.close()

    def create_parser_searcher(self):
        """
        INPUT:
            None
        OUTPUT:
            None

        NOTE: Please update self.query_parser and self.self.searcherwhich should have type whoosh.qparser.default.QueryParser and whoosh.searching.Searcher respectively
        """
        self.query_parser = QueryParser("file_content", schema=self.index_sys.schema)
        self.searcher = self.index_sys.searcher()

    def perform_search(self, topic_phrase):
        """
        INPUT:
            topic_phrase: string
        OUTPUT:
            topicResults: whoosh.searching.Results

        NOTE: Utilize self.query_parser and self.searcher to calculate the result for topic_phrase
        """
        query = self.query_parser.parse(topic_phrase)
        topicResults = self.searcher.search(query, limit=None)
        return topicResults
    
    def inspect_terms(self):
        """
        Inspect terms in the index and print details.
        """
        # with self.searcher as searcher:
        #     doc_count = searcher.doc_count()
        #     print(f"Number of documents indexed: {doc_count}")

        #     # Check if there are any documents at all.
        #     if doc_count == 0:
        #         print("No documents have been indexed.")
        #         return

        #     # Check for terms in the file_content field.
        #     found_terms = False
        #     for fieldname, text in searcher.lexicon("file_path"):
        #         found_terms = True
        #         print(f"Term: {text.decode('utf-8')}")
        #         postings = searcher.postings("file_content", text)
        #         print(f"Postings for term '{text.decode('utf-8')}': {list(postings.all_ids())}")

        #     if not found_terms:
        #         print("No terms found in the 'file_content' field.")

        # for stored_fields in self.searcher.documents():
        #     print(stored_fields)






def main():
    parser = argparse.ArgumentParser(description='IR System')
    parser.add_argument('--document_dir', type=str, help='Path to the directory of documents')
    parser.add_argument('--topic_phrase', type=str, help='Topic phrase to search for')
    args = parser.parse_args()

    ir = IR(args.document_dir)
    ir.add_files()
    ir.inspect_terms()
    topic_phrase = args.topic_phrase
    topicResults = ir.perform_search(topic_phrase)
    for (i, result) in enumerate(topicResults):
        score = topicResults.score(i)
        fileName = os.path.basename(result["file_path"])
        print(fileName, i, score)

if __name__ == '__main__':
    main()


    