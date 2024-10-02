import os
import json
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import argparse
class IR():

    def __init__(self, embedding_path, document_dir):
        load_dotenv()
        self.text_embedding = json.load(open(embedding_path, "r"))
        self.embedding_model = os.getenv('EMBEDDING_MODEL')
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
        chroma_client = chromadb.Client()

        name = 'capstone'

        if name in [collection.name for collection in
                               chroma_client.list_collections()]:
            chroma_client.delete_collection(name)
        
        metadata = {"hnsw:space": "cosine"}

        self.index_sys = chroma_client.get_or_create_collection(name=name, metadata=metadata)


    def add_files(self):
        """
        INPUT:
            None
        OUTPUT:
            None

        NOTE: Add embedding of each document from self.text_embedding,
              and content of each document, to self.index_sys
        """
        for i, file_path in enumerate(self.file_list):
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                doc_id = os.path.basename(file_path)
                embedding = self.text_embedding[i]
                self.index_sys.add(ids = doc_id,       
                            documents = file_content,
                            embeddings = embedding)

    def create_parser_searcher(self):
        """
        INPUT:
            None
        OUTPUT:
            None

        """


        self.query_parser = SentenceTransformer(self.embedding_model)
        self.searcher = self.index_sys

    def perform_search(self, topic_phrase):
        """
        INPUT:
            topic_phrase: string
        OUTPUT:
            topicResults: dict

        NOTE: Utilize self.query_parser and self.searcher to calculate the result for topic_phrase
        """
        query_embedding = self.query_parser.encode(topic_phrase, normalize_embeddings=True).tolist()
        topicResults = self.searcher.query(query_embeddings = [query_embedding], n_results = 10)
        return topicResults

def main():
    parser = argparse.ArgumentParser(description='IR System')
    parser.add_argument('--embedding', type=str, help='Path to the embedding file')
    parser.add_argument('--document_dir', type=str, help='Path to the directory of documents')
    parser.add_argument('--topic_phrase', type=str, help='Topic phrase to search for')
    args = parser.parse_args()

    ir = IR(args.embedding, args.document_dir)
    ir.add_files()
    topic_phrase = args.topic_phrase
    topicResults = ir.perform_search(topic_phrase)
    for name in topicResults['ids'][0]:
        print(name)

if __name__ == '__main__':
    main()


    