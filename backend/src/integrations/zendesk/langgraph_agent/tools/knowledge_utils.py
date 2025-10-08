"""
Reusable utilities for knowledge base content extraction and chunking.
Uses LangChain's document processing and chunking capabilities.
"""

from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document


def extract_pdf_content_chunked(file_path: Path, max_chars: int = 2000) -> str:
    """
    Extract PDF content using LangChain's PyPDFLoader and text splitter.

    Args:
        file_path: Path to the PDF file
        max_chars: Maximum characters to return (roughly 500 tokens)

    Returns:
        Chunked PDF content using LangChain
    """
    try:
        if not file_path.exists():
            return f"File not found: {file_path.name}"

        loader = PyPDFLoader(str(file_path))
        documents = loader.load()

        if not documents:
            return f"No content extracted from {file_path.name}"

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=200,  # 200 char overlap for context preservation
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],  # Prioritize paragraph/sentence breaks
        )

        all_chunks = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.page_content)
            all_chunks.extend(chunks)

        return _select_relevant_chunks(all_chunks, max_chars)

    except Exception as e:
        return f"Error reading {file_path.name}: {str(e)}"


def extract_text_content_chunked(file_path: Path, max_chars: int = 2000) -> str:
    """
    Extract text file content using LangChain's TextLoader and text splitter.

    Args:
        file_path: Path to the text file
        max_chars: Maximum characters to return

    Returns:
        Chunked text content using LangChain
    """
    try:
        if not file_path.exists():
            return f"File not found: {file_path.name}"

        loader = TextLoader(str(file_path), encoding="utf-8")
        documents = loader.load()

        if not documents:
            return f"No content found in {file_path.name}"

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        all_chunks = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.page_content)
            all_chunks.extend(chunks)

        return _select_relevant_chunks(all_chunks, max_chars)

    except Exception as e:
        return f"Error reading {file_path.name}: {str(e)}"


def _select_relevant_chunks(chunks: List[str], max_chars: int) -> str:
    """
    Select the most relevant chunks based on key terms and content quality.

    Args:
        chunks: List of text chunks from LangChain's text splitter
        max_chars: Maximum characters to return

    Returns:
        Combined relevant chunks within character limit
    """
    if not chunks:
        return "No content available"

    key_terms = [
        "plan",
        "price",
        "pricing",
        "cost",
        "$",
        "month",
        "year",
        "internet",
        "service",
        "package",
        "residential",
        "business",
        "premium",
        "unlimited",
        "promotion",
        "offer",
        "installation",
        "mobile",
        "phone",
        "speed",
        "mbps",
        "gbps",
        "fiber",
        "wifi",
        "router",
    ]

    scored_chunks = []
    for chunk in chunks:
        score = 0
        chunk_lower = chunk.lower()

        for term in key_terms:
            score += chunk_lower.count(term)

        if "$" in chunk and ("month" in chunk_lower or "year" in chunk_lower):
            score += 5

        if any(word in chunk_lower for word in ["plan", "package", "service"]):
            score += 3

        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    result = ""
    current_length = 0

    for score, chunk in scored_chunks:
        if current_length + len(chunk) + 10 <= max_chars:  # +10 for separator
            if result:
                result += "\n\n---\n\n"
                current_length += 7
            result += chunk
            current_length += len(chunk)
        else:
            break

    if not result and chunks:
        result = chunks[0][: max_chars - 50] + "...\n[Content truncated]"

    return result or "Content processing error"


def get_knowledge_file_path(filename: str, subfolder: Optional[str] = None) -> Path:
    """
    Get the full path to a knowledge base file.

    Args:
        filename: Name of the file
        subfolder: Optional subfolder within knowledge base

    Returns:
        Path object for the knowledge base file
    """
    base_path = Path("myawesomefakecompanyBaseKnowledge")

    if subfolder:
        return base_path / subfolder / filename
    else:
        return base_path / filename
