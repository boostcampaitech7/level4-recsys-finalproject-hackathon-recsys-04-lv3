import argparse
import glob
import re

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec


def is_toc_or_appendix_page(text, page_num, total_pages):
    """목차나 부록 페이지인지 확인하는 함수"""
    # 앞부분 목차 페이지 체크 (처음 10페이지 내에서)
    if page_num <= 10:
        toc_patterns = [
            r"목\s*차",
            r"책의\s*차례",
            r"제\s*\d+\s*장",
            r"CONTENTS",
            r"\d+\.\s*.+\s*\.{2,}\s*\d+",  # 챕터 번호와 페이지 번호를 잇는 점선 패턴
        ]
        return any(re.search(pattern, text) for pattern in toc_patterns)

    # 뒷부분 부록 페이지 체크 (마지막 20페이지 내에서)
    if page_num >= total_pages - 20:
        appendix_patterns = [
            r"부\s*록",
            r"찾아보기",
            r"APPENDIX",
            r"INDEX",
            r"참고문헌",
            r"용어\s*찾기",
            r"찾아\s*보기",
        ]
        return any(re.search(pattern, text) for pattern in appendix_patterns)

    return False


def filter_sentences(text):
    """특정 패턴의 문장을 제거하는 함수"""
    sentences = re.split(r"[.!?]\s+", text)
    filtered_sentences = []

    for sentence in sentences:
        if sentence.strip() and not sentence.strip().endswith("?") and not sentence.strip().endswith("보자"):
            filtered_sentences.append(sentence)

    return ". ".join(filtered_sentences)


def init_pinecone(index_name: str):
    pc = Pinecone()
    if index_name not in [index_info["name"] for index_info in pc.list_indexes()]:
        pc.create_index(
            name=index_name, dimension=4096, metric="dotproduct", spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"{index_name} has been successfully created")
    else:
        print(f"{index_name} already exists.")

    return pc.Index(index_name)


def process_document(file_path, text_splitter, exclude_words=None, filter_toc=False, filter_sentences_flag=False):
    """Process a single PDF document with optional preprocessing steps"""
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    total_pages = len(pages)
    filtered_pages = []

    # Extract subject from filename (assuming filename format contains subject after third underscore)
    subject = file_path.split("/")[-1].split("_")[0] if "_" in file_path else "unknown"
    source = file_path.split("/")[-1]

    for page_num, page in enumerate(pages, 1):
        content = page.page_content

        # Check TOC/appendix pages if enabled
        if filter_toc and is_toc_or_appendix_page(content, page_num, total_pages):
            continue

        # Check excluded words if provided
        if exclude_words:
            if any(word in content for word in exclude_words):
                continue

        # Apply sentence filtering if enabled
        if filter_sentences_flag:
            content = filter_sentences(content)

        # Skip if content is too short after filtering
        if len(content) < 50:
            continue

        # Update page content and metadata
        page.page_content = content
        page.metadata = {
            "subject": subject,
            "page_num": page_num,
            "total_pages": total_pages,
            "source": source,
        }

        filtered_pages.append(page)

    return text_splitter.split_documents(filtered_pages)


def main(args):
    pdf_paths = glob.glob(args.pdf_path)

    embeddings_passage = UpstageEmbeddings(model="embedding-passage")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    # Process exclude words if provided
    exclude_words = args.exclude_words.split(",") if args.exclude_words else None

    all_chunks = []
    for file in pdf_paths:
        chunks = process_document(
            file,
            text_splitter,
            exclude_words=exclude_words,
            filter_toc=args.filter_toc,
            filter_sentences_flag=args.filter_sentences,
        )
        all_chunks.extend(chunks)
        print(f"Processed {file}: {len(chunks)} chunks")

    print(f"Total number of chunks: {len(all_chunks)}")

    docsearch = PineconeVectorStore.from_existing_index(
        index_name=args.index_name, embedding=embeddings_passage, namespace=f"{args.chunk_size}-{args.chunk_overlap}"
    )
    docsearch.add_documents(all_chunks)
    print("All documents have been added to the index.")


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--index_name", type=str, default="test-pre")
    parser.add_argument("--pdf_path", type=str, default="data/*.pdf")
    parser.add_argument("--chunk_size", type=int, default=500)
    parser.add_argument("--chunk_overlap", type=int, default=150)
    parser.add_argument("--filter_toc", action="store_true", help="Enable TOC and appendix filtering")
    parser.add_argument("--filter_sentences", action="store_true", help="Enable sentence pattern filtering")
    parser.add_argument(
        "--exclude_words",
        type=str,
        default="창의·융합,창의·융복합,마무리,자료 해석,부록,정답과 해설,융•복합적 사고",
        help="Comma-separated list of words to exclude",
    )
    args = parser.parse_args()
    main(args)
