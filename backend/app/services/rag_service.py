from glob import glob

from app.core.config import settings
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_pinecone import PineconeVectorStore
from langchain_teddynote.community.pinecone import preprocess_documents
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec
from utils import logging


def create_vectorstore(pdf_dir):
    """
    PDF 파일을 로드하고 벡터 저장소를 생성합니다.

    Args:
        pdf_dir (str): 처리할 PDF 폴더의 경로

    Returns:
        PineconeVectorStore or None: 생성된 벡터 저장소 객체. 인덱스가 이미 존재하는 경우 None 반환
    """
    # 단계 1: DB 생성(Create DB)
    pc = Pinecone()
    db_index_name = settings.PINECONE_INDEX_NAME

    # print(pc.list_indexes())
    if db_index_name in [index_info["name"] for index_info in pc.list_indexes()]:
        print(f"{db_index_name} is already exists.")

        return None
    else:
        pc.create_index(
            name=db_index_name,
            dimension=4096,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print(f"{db_index_name} has been successfully created")

        # LangSmith 시작
        logging.langsmith(settings.LANGSMITH_PROJECT_NAME)

        # 단계 1: 문서 로드(Load Documents)
        docs = []
        files = sorted(glob(f"{pdf_dir}/*.pdf"))
        print("files: ", files)

        for file_path in files:
            loader = PyMuPDFLoader(file_path)
            docs.extend(loader.load())
        print(f"문서의 페이지수: {len(docs)}")

        # 단계 2: 문서 분할(Split Documents)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        split_documents = text_splitter.split_documents(docs)
        print(f"분할된 청크의수: {len(split_documents)}")

        # 단계 3: 문서 전처리
        contents, metadatas = preprocess_documents(
            split_docs=split_documents,
            metadata_keys=["source", "page", "author"],
            min_length=3,
            use_basename=True,
        )

        # 단계 4: 임베딩(Embedding) 생성
        embeddings = UpstageEmbeddings(model="embedding-passage")

        # 단계 5: DB 생성(Create DB) 저장
        vectorstore = PineconeVectorStore.from_documents(split_documents, embeddings, index_name=db_index_name)

        return vectorstore


def create_chain(db_index_name):
    """
    RAG(Retrieval-Augmented Generation) 체인을 생성합니다.

    Args:
        db_index_name (str): 사용할 Pinecone 인덱스의 이름

    Returns:
        Chain: 구성된 RAG 체인 객체
    """
    # DB 불러오기
    pc = Pinecone()
    index = pc.Index(db_index_name)
    embeddings = UpstageEmbeddings(model="embedding-passage")
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings)

    # 검색기(Retriever) 생성
    retriever = vectorstore.as_retriever()

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

    # 언어모델(LLM) 생성
    llm = ChatUpstage(model="solar-pro")

    # 체인(Chain) 생성
    chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

    return chain


def analysis_note(input_data):
    """
    사용자 입력에 대한 분석을 수행합니다.

    이 함수는 create_chain 함수로 생성된 RAG 체인을 사용하여
    주어진 입력 데이터에 대한 분석을 수행합니다.

    Args:
        input_data (str): 분석할 사용자 입력 텍스트

    Returns:
        str: 분석 결과 및 피드백
    """
    # LangSmith 시작
    logging.langsmith(settings.LANGSMITH_PROJECT_NAME)

    db_index_name = settings.PINECONE_INDEX_NAME
    chain = create_chain(db_index_name)

    response = chain.invoke(input_data)

    return response
