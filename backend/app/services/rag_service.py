# app/services/rag_service.py
import time
from glob import glob

from app.core.config import settings
from fastapi import HTTPException
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec
from utils import logging


def initialize_pinecone():
    """Pinecone 초기화 및 인덱스 생성"""
    try:
        pc = Pinecone()
        db_index_name = settings.PINECONE_INDEX_NAME

        # 인덱스 존재 여부 확인
        indexes = pc.list_indexes()
        index_exists = any(index.name == db_index_name for index in indexes)

        if not index_exists:
            print(f"Creating new index: {db_index_name}")
            pc.create_index(
                name=db_index_name,
                dimension=4096,
                metric="dotproduct",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            # 인덱스 생성 완료 대기
            time.sleep(20)  # Pinecone 인덱스 생성에 시간이 걸림
            print(f"{db_index_name} has been successfully created")
        else:
            print(f"{db_index_name} already exists")

        return pc

    except Exception as e:
        print(f"Error initializing Pinecone: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pinecone initialization failed: {str(e)}")


def preprocess_documents(split_docs, metadata_keys, min_length, subject="default"):
    """문서 전처리"""
    try:
        result_docs = []
        for doc in split_docs:
            doc.metadata = {key: doc.metadata.get(key, "") for key in metadata_keys}
            doc.metadata["subject"] = subject
            if len(doc.page_content) > min_length:
                result_docs.append(doc)
        return result_docs
    except Exception as e:
        print(f"Error in document preprocessing: {str(e)}")
        return []


def add_document(pdf_dir, subject="default"):
    try:
        db_index_name = settings.PINECONE_INDEX_NAME
        logging.langsmith(settings.LANGSMITH_PROJECT_NAME)

        # 문서 로드
        docs = []
        files = sorted(glob(f"{pdf_dir}/*.pdf"))

        # 기존 문서 목록 가져오기
        pc = Pinecone()
        index = pc.Index(db_index_name)

        # 기존 문서의 메타데이터에서 파일명 추출
        existing_files = set()
        query_response = index.query(vector=[0] * 4096, top_k=10000, include_metadata=True)  # 더미 벡터
        for match in query_response.matches:
            if "source" in match.metadata:
                existing_files.add(match.metadata["source"])

        # 새로운 파일만 처리
        new_files = []
        for file_path in files:
            if file_path not in existing_files:
                new_files.append(file_path)
                loader = PyMuPDFLoader(file_path)
                docs.extend(loader.load())

        print(f"기존 문서 수: {len(existing_files)}")
        print(f"새로 추가할 문서 수: {len(new_files)}")
        print(f"새로 추가할 문서들: {new_files}")

        if not new_files:
            return {"message": "No new documents to add"}

        # 새 문서 처리
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_documents = text_splitter.split_documents(docs)
        print(f"분할된 청크의수: {len(split_documents)}")

        # 문서 전처리
        split_documents_processed = preprocess_documents(
            split_docs=split_documents,
            metadata_keys=["source", "page", "author"],
            subject=subject,
            min_length=20,
        )

        # 임베딩 생성 및 저장
        embeddings = UpstageEmbeddings(model="embedding-passage")
        vectorstore = PineconeVectorStore.from_existing_index(index_name=db_index_name, embedding=embeddings)
        vectorstore.add_documents(split_documents_processed)

        return {"message": "Documents added successfully", "added_files": new_files}

    except Exception as e:
        print(f"Error in add_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add documents: {str(e)}")


def create_chain(db_index_name):
    """RAG 체인 생성"""
    try:
        # Pinecone 초기화 확인
        pc = initialize_pinecone()
        index = pc.Index(db_index_name)

        # 임베딩 설정
        embeddings = UpstageEmbeddings(
            model="embedding-query",
        )
        vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

        # 검색기 생성
        retriever = vectorstore.as_retriever()

        # 프롬프트 설정
        prompt = PromptTemplate.from_template(
            """너는 입력을 보고 틀린 부분에 대해서 피드백을 주는 선생님이야.
            입력과 관련있는 정보를 참고해서 피드백을 생성해줘.
            참고한 정보의 페이지도 같이 알려줘.
            만약 틀린 부분이 없을 경우, 칭찬 한문장 작성해줘.

            #정보:
            {context}

            #입력:
            {question}

            #답:"""
        )

        # LLM 설정
        llm = ChatUpstage(
            model="solar-pro",
        )

        # 체인 생성
        chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

        return chain

    except Exception as e:
        print(f"Error creating chain: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create RAG chain: {str(e)}")


def analysis_chunk(input_data):
    # LangSmith 시작
    logging.langsmith(settings.LANGSMITH_PROJECT_NAME)
    db_index_name = settings.PINECONE_INDEX_NAME

    pc = Pinecone()
    index = pc.Index(db_index_name)
    embeddings = UpstageEmbeddings(model="embedding-query")
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

    # 검색기(Retriever) 생성
    retriever = vectorstore.as_retriever()

    retrieved_docs = retriever.invoke(input_data)
    doc = retrieved_docs[0]
    doc_context = doc.page_content
    rag_id = doc.id

    # 프롬프트 생성(Create Prompt)
    prompt = PromptTemplate.from_template(
        """너는 입력을 보고 틀린 부분에 대해서 피드백을 주는 선생님이야.
    입력과 관련있는 정보를 참고해서 피드백을 생성해줘.
    참고한 정보의 페이지도 같이 알려줘.
    만약 틀린 부분이 없을 경우, 칭찬 한문장 작성해줘.

    #정보:
    {context}

    #입력:
    {question}

    #답:"""
    )
    print(doc_context)
    # 언어모델(LLM) 생성
    llm = ChatUpstage(model="solar-pro")
    chain = {"context": RunnablePassthrough(), "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()
    response = chain.invoke({"context": doc_context, "question": input_data})

    return {
        "rag_id": rag_id,
        "response": response,
    }
