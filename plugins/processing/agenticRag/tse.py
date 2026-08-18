# ==================================================================================
# ============================ MODULE TSE - TUTORIAL SEARCH ENGINE ==================
# ==================================================================================
# Auteur: @NYTHIQUE
# GitHub: https://github.com/Nythique
# Portfolio: https://nythique.github.io
# Date de création: 11/07/2026
# ==================================================================================
import os
import docx
import pymupdf
import chromadb
from app.helps.utils import logger
from settings.config import params


class ChunkBuilder:
    def __init__(self):
        self.file_path: str = params.TSE_FILE_PATH
        self.chunk_size: int = params.TSE_CHUNK_SIZE

    def _extract_pdf_text(self) -> str:
        """
            Extractor function for PDF document.
        @file_path: Document path.
        """

        doc = pymupdf.open(self.file_path)
        pages_text = []

        for page in doc:
            text = page.get_text()
            if isinstance(text, str) and text.strip():
                pages_text.append(text)
        doc.close()

        return "\n".join(pages_text)

    def _extract_docx_text(self) -> str:
        """
            Extractor function for docx document.
        @file_path: Document path.
        """

        doc = docx.Document(self.file_path) # type:ignore
        paragraph_text = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraph_text.append(text)

        return "\n".join(paragraph_text)

    def _extract_txt_text(self) -> str:
        """
            Extractor function for txt document.
        @file_path: Document path.
        """

        with open(self.file_path, 'r', encoding='utf-8', errors="ignore") as f:
            txt_content = f.read()

        return txt_content

    def _check_file_type(self) -> str:
        """
            Detector function to check the document type (txt, docx, PDF).
        @file_path: Document path.
        """

        extensions = {
            ".md":   self._extract_txt_text,
            ".txt":  self._extract_txt_text,
            ".docx": self._extract_docx_text,
            ".pdf":  self._extract_pdf_text,
        }

        _ext = os.path.splitext(self.file_path.lower())[1]

        if _ext not in extensions:
            logger.error(f"[ERROR TSE]=> Extension de fichier non supportée: '{_ext}'")
            raise ValueError(f"Extension de fichier non supportée: '{_ext}'")

        return extensions[_ext]()

    def load_and_chunk_file(self) -> list[str]:
        """
            The small function witch cutting file content in
        chunk list.
        """

        if not os.path.exists(self.file_path):
            logger.error(f"[ERROR TSE]=> Le fichier tutoriel est introuvable: '{self.file_path}'")
            raise FileNotFoundError(f"Le fichier tutoriel est introuvable: '{self.file_path}'")

        content = self._check_file_type()
        if not content.strip():
            logger.warning(f"[WARNING TSE]=> Le fichier tutoriel est vide: '{self.file_path}'")
            return []

        words = content.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i:i + self.chunk_size]  # cut the words list into portions
            '''
                Example:
                    len(words) = 1000
                    - first round (chunk 1): chunk_words = words[0 : 0 + 150]  => (0-149) words
                    - second round (chunk 2): chunk_words = words[150 : 150 + 150] => (150-299) words
                    - etc...
            '''
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)

        return chunks


class VectorialDB:
    def __init__(self):
        self.path = params.TEMP_PATH
        self.collection_name = params.TSE_COLLECTION_NAME

    def init_local_vector_db(self, chunks: list):
        """
            Initialization and Indexing of the vector database.
        Creation of the database that turns texts into numbers.
        @chunks: The chuncks obtain with chunk_builder module.
        """
        chroma_client = chromadb.PersistentClient(path=self.path)
        '''
            We create a collection witch a unique name
        NOTE: A collection is the equivalent of a sql table.
        '''
        collection = chroma_client.get_or_create_collection(name=self.collection_name)
        '''
            List comprehension of mandatory genereted IDs
        '''
        ids = [f'id_{i}' for i in range(len(chunks))]
        '''
            Automatic indexing
        NOTE: It's AT THAT EXACT MOMENT that ChromaDB calls its internal embedding model,
        calculates the numbers (vectors) for each chunk, and stores them in its geometric index.
        '''
        collection.upsert(
            documents=chunks,
            ids=ids
        )

        return collection

    @staticmethod
    def search_in_vector_db(collection, question: str, top_n: int = params.TSE_TOP_N):
        """
            The semantic query
        @collection: The collection obtain with init_local_vector_db function.
        @question : The input of a question.
        @top_n: Used to limit the number of texte piece that the database will return.
        """
        results = collection.query(
            query_texts=[question],
            n_results=top_n
        )
        '''
            NOTE: query() function will do:
                - Turning the question into numbers.
                - Calculating the geometric distance with the numbers of the stored pieces.
                - Sorts it and sends back the 'top_n' closest pieces.
        '''
        '''We neatly extract the list of texts found.'''
        best_chunks = results['documents'][0]

        return best_chunks


class TutorialSearchEngine:
    def __init__(self):
        self._chunk_builder = ChunkBuilder()
        self._vector_db = VectorialDB()

    def call_tutorial_engine(self, question: str, top_n: int = params.TSE_TOP_N) -> list[str]:
        """
            Main entry point for the Tutorial Search Engine.
        @question: The user's question to search for in the tutorial.
        @top_n: Number of best matching chunks to return.
        """
        try:
            chunks = self._chunk_builder.load_and_chunk_file()
            if not chunks:
                return []

            collection = self._vector_db.init_local_vector_db(chunks=chunks)
            response = self._vector_db.search_in_vector_db(
                collection=collection,
                question=question,
                top_n=top_n
            )
            return response

        except (FileNotFoundError, ValueError) as error:
            logger.error(f"[ERROR TSE]=> Erreur de configuration ou de fichier: {error}", exc_info=True)
            return []
        except Exception as error:
            logger.error(f"[ERROR TSE]=> Erreur inattendue lors de la recherche tutoriel: {error}", exc_info=True)
            return []
