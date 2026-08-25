"""Tutorial Search Engine (TSE): Local document vector search powered by ChromaDB."""

import os
import docx
import pymupdf
import chromadb
from app.helps.utils import logger
from settings.config import params


class ChunkBuilder:
    """Document text extractor and chunking processor."""

    def __init__(self):
        self.file_path: str = params.TSE_FILE_PATH
        self.chunk_size: int = params.TSE_CHUNK_SIZE

    def _extract_pdf_text(self) -> str:
        """Extract plain text from PDF file."""
        doc = pymupdf.open(self.file_path)
        pages_text = []
        for page in doc:
            text = page.get_text()
            if isinstance(text, str) and text.strip():
                pages_text.append(text)
        doc.close()
        return "\n".join(pages_text)

    def _extract_docx_text(self) -> str:
        """Extract plain text from DOCX file."""
        doc = docx.Document(self.file_path)
        paragraph_text = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                paragraph_text.append(text)
        return "\n".join(paragraph_text)

    def _extract_txt_text(self) -> str:
        """Extract plain text from Markdown or text file."""
        with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _check_file_type(self) -> str:
        """Detect file format and dispatch to appropriate extractor."""
        extensions = {
            ".md": self._extract_txt_text,
            ".txt": self._extract_txt_text,
            ".docx": self._extract_docx_text,
            ".pdf": self._extract_pdf_text,
        }

        ext = os.path.splitext(self.file_path.lower())[1]
        if ext not in extensions:
            logger.error(f"[ERROR TSE] Unsupported document format: '{ext}'")
            raise ValueError(f"Unsupported document format: '{ext}'")

        return extensions[ext]()

    def load_and_chunk_file(self) -> list[str]:
        """Load document and split into uniform word chunks."""
        if not os.path.exists(self.file_path):
            logger.error(f"[ERROR TSE] Tutorial file not found: '{self.file_path}'")
            raise FileNotFoundError(f"Tutorial file not found: '{self.file_path}'")

        content = self._check_file_type()
        if not content.strip():
            logger.warning(f"[WARNING TSE] Tutorial document is empty: '{self.file_path}'")
            return []

        words = content.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size):
            chunk_words = words[i : i + self.chunk_size]
            chunks.append(" ".join(chunk_words))

        return chunks


class VectorialDB:
    """ChromaDB client wrapper for vector embedding indexing and semantic retrieval."""

    def __init__(self):
        self.path = params.TEMP_PATH
        self.collection_name = params.TSE_COLLECTION_NAME

    def init_local_vector_db(self, chunks: list):
        """Index text chunks into ChromaDB vector database."""
        chroma_client = chromadb.PersistentClient(path=self.path)
        collection = chroma_client.get_or_create_collection(name=self.collection_name)
        ids = [f"id_{i}" for i in range(len(chunks))]
        collection.upsert(documents=chunks, ids=ids)
        return collection

    @staticmethod
    def search_in_vector_db(collection, question: str, top_n: int = params.TSE_TOP_N):
        """Perform cosine/geometric similarity search for given query."""
        results = collection.query(query_texts=[question], n_results=top_n)
        return results["documents"][0] if results.get("documents") else []


class TutorialSearchEngine:
    """Orchestrates document chunking, indexing, and semantic search."""

    def __init__(self):
        self._chunk_builder = ChunkBuilder()
        self._vector_db = VectorialDB()

    def call_tutorial_engine(self, question: str, top_n: int = params.TSE_TOP_N) -> list[str]:
        """Search tutorial knowledge base for matching passages."""
        try:
            chunks = self._chunk_builder.load_and_chunk_file()
            if not chunks:
                return []

            collection = self._vector_db.init_local_vector_db(chunks=chunks)
            return self._vector_db.search_in_vector_db(
                collection=collection,
                question=question,
                top_n=top_n,
            )

        except (FileNotFoundError, ValueError) as error:
            logger.error(f"[ERROR TSE] Tutorial file or configuration error: {error}", exc_info=True)
            return []
        except Exception as error:
            logger.error(f"[ERROR TSE] Unexpected error during tutorial search: {error}", exc_info=True)
            return []
