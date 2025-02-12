import argparse
import os
from glob import glob

import pandas as pd
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from tqdm import tqdm


class RAGEvalOutput(BaseModel):
    """Output format containing modified statement and feedback"""

    modified_statement: str = Field(description="A statement containing core concepts from the original text")
    feedback: str = Field(description="Whether the statement is correct or not (O, X)")


def process_document(file_path, text_splitter):
    """Process a single PDF document with optional preprocessing steps"""
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    total_pages = len(pages)
    filtered_pages = []

    # Extract subject from filename (assuming filename format contains subject after third underscore)
    subject = file_path.split("/")[-1].split("_")[0] if "_" in file_path else "unknown"
    source = file_path.split("/")[-1]
    print(f"Processing {file_path} with subject: {subject}, length: {total_pages}")
    for page_num, page in enumerate(pages, 1):
        content = page.page_content

        # Skip if content is too short after filtering
        if len(content) < 50:
            continue

        # if page contain "?" simbol, skip
        if "?" in content or "이 책의 차례" in content or "이 책의 구성과 특징" in content:
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
    print(f"Filtered pages: {len(filtered_pages)}")
    return text_splitter.split_documents(filtered_pages)


def generate_OXtest(chunks):
    """
    Generate OX test questions from document chunks and save them by subject

    Args:
        chunks: List of document chunks with metadata
    """
    # Initialize components
    parser = JsonOutputParser(pydantic_object=RAGEvalOutput)

    prompt = ChatPromptTemplate.from_template(
        """Given the following text, please:
    1) Create 2 statements using the core concepts - one correct and one incorrect
    2) Mark each statement as O (correct) or X (incorrect)

    All statements must:
    - Include core concepts from the original text
    - Be different from the original text format
    Original text:
    {text}

    Please respond in the following format:
    {format_instructions}
    """
    )

    model = ChatOpenAI(model="gpt-4o", temperature=0.2)
    chain = prompt | model | parser

    # Group chunks by subject
    test_data = {}
    for chunk in chunks:
        subject = chunk.metadata["subject"]
        if subject not in test_data:
            test_data[subject] = []
        test_data[subject].append(chunk)

    # Process each subject
    for subject, subject_chunks in test_data.items():
        print(f"Processing subject: {subject}")
        evaluation_data = []

        # Generate questions for each chunk
        for chunk in tqdm(subject_chunks, desc=f"Generating questions for {subject}"):
            try:
                # Generate questions using LangChain
                result = chain.invoke(
                    {"text": chunk.page_content, "format_instructions": parser.get_format_instructions()}
                )
                # result의 type이 list일 경우
                if isinstance(result, list):
                    for res in result:
                        evaluation_data.append(
                            {
                                "source": chunk.metadata["source"],
                                "page_num": chunk.metadata["page_num"],
                                "statement": res["modified_statement"],
                                "feedback": res["feedback"],
                            }
                        )
                elif isinstance(result, dict):
                    evaluation_data.append(
                        {
                            "source": chunk.metadata["source"],
                            "page_num": chunk.metadata["page_num"],
                            "statement": result["modified_statement"],
                            "feedback": result["feedback"],
                        }
                    )
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue

        # Create and save DataFrame
        if evaluation_data:
            df = pd.DataFrame(evaluation_data)

            # Create output directory if it doesn't exist
            os.makedirs("OX", exist_ok=True)

            # Save to CSV
            save_path = f"OX/{subject}.csv"
            df.to_csv(save_path, index=False)
            print(f"Saved {len(df)} questions for {subject} to {save_path}")
        else:
            print(f"No questions generated for {subject}")


def main(args):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)

    all_chunks = []

    pdf_paths = glob(args.pdf_path)
    for file in pdf_paths:
        chunks = process_document(
            file,
            text_splitter,
        )
        all_chunks.extend(chunks)
        print(f"Processed {file}: {len(chunks)} chunks")

    print(f"Total number of chunks: {len(all_chunks)}")

    generate_OXtest(all_chunks)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_path", type=str, default="test_data/*.pdf")
    args = parser.parse_args()
    main(args)
