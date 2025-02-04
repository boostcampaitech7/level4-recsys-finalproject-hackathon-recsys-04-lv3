# app/services/rag_service.py
import time
from glob import glob

from app.core.config import settings
from fastapi import HTTPException
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_experimental.text_splitter import SemanticChunker
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
    try:
        # LangSmith 시작
        logging.langsmith(settings.LANGSMITH_PROJECT_NAME)
        db_index_name = settings.PINECONE_INDEX_NAME
        pc = Pinecone()
        index = pc.Index(db_index_name)

        # 임베딩 및 검색기(Retriever) 설정
        embeddings_query = UpstageEmbeddings(model="embedding-query")
        vectorstore = PineconeVectorStore(index=index, embedding=embeddings_query)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 2})

        # 입력 데이터 청크 나누기
        embeddings_passage = UpstageEmbeddings(model="embedding-passage")
        text_splitter = SemanticChunker(
            embeddings=embeddings_passage,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95,
        )
        chunks = text_splitter.split_text(input_data)
        print("Input data chunk len:", len(chunks))

        # 청크별 검색
        retrieved_docs = []
        retrieved_ids = []
        for chunk in chunks:
            docs = retriever.invoke(chunk)
            for doc in docs:
                doc_id = doc.id
                if doc_id not in retrieved_ids:
                    retrieved_ids.append(doc_id)
                    retrieved_docs.append(doc)
        print("Retrieved docs len:", len(retrieved_docs))
        print("Retrieved ids len:", len(retrieved_ids))

        # 피드백 프롬프트 생성
        prompt_feedback = PromptTemplate.from_template(
            """너는 입력을 보고 틀린 부분에 대해서 피드백을 주는 선생님이야.
            입력과 관련 있는 정보를 참고해서 피드백을 형식화하여 작성해줘.
            만약 틀린 부분이 있다면, 다음 형식으로 피드백을 작성해줘:
            피드백 사항 {{피드백 숫자}}. {{잘못된 부분}} -> {{올바른 부분}}
            설명: {{잘못된 부분에 대한 설명}}
            만약 틀린 부분이 없다면 칭찬을 해줘: '잘했어요!'
            #정보:
            {context}
            #입력:
            {raw_text}
            #답:"""
        )

        # 퀴즈 프롬프트 생성
        prompt_quiz = PromptTemplate.from_template(
            """
            아래 텍스트를 기반으로 수능 수준의 O/X 퀴즈 5개를 만들어주세요.
            다음 조건을 충족해야 합니다:
            1. 질문은 개념 이해와 문제 해결 능력을 평가할 수 있어야 합니다.
            2. 정답이 "O"인 문제와 "X"인 문제의 비율은 균형 있게 구성해주세요.
            3. 질문의 난이도는 수능 수준에 맞춰 구체적이고 사고를 요하는 내용을 포함해야 합니다.
            4. 각 질문의 정답에 대한 설명은 간결하지만 충분히 납득 가능하게 작성해주세요.
            응답은 반드시 JSON 형식으로 반환하세요. 형식은 다음과 같습니다:
            [
                {{"question": "질문 내용", "answer": "O 또는 X", "explanation": "정답에 대한 간단한 설명"}},
                ...
            ]
            #참고 정보:
            {context}
            #입력:
            {raw_text}
            """
        )

        # 객관식 퀴즈 프롬프트 추가
        prompt_multiple = PromptTemplate.from_template(
            """
            아래 텍스트를 기반으로 수능 수준의 4지선다형 객관식 문제 5개를 만들어주세요.
            다음 조건을 충족해야 합니다:
            1. 질문은 개념 이해와 문제 해결 능력을 평가할 수 있어야 합니다.
            2. 선택지는 4개이며, 모두 그럴듯하게 구성되어야 합니다.
            3. 오답 선택지도 관련 있는 내용으로 구성해야 합니다.
            4. 정답에 대한 설명은 왜 그 답이 정답인지 명확하게 설명해야 합니다.
            응답은 반드시 JSON 형식으로 반환하세요. 형식은 다음과 같습니다:
            [
                {{
                    "question": "질문 내용",
                    "option1": "선택지 1",
                    "option2": "선택지 2",
                    "option3": "선택지 3",
                    "option4": "선택지 4",
                    "answer": "1~4 중 정답 번호",
                    "explanation": "정답에 대한 설명"
                }},
                ...
            ]
            #참고 정보:
            {context}
            #입력:
            {raw_text}
            """
        )

        # 언어 모델(LLM) 생성
        llm = ChatUpstage(model="solar-pro", temperature=0.2)

        # 피드백 생성
        feedback_chain = prompt_feedback | llm | StrOutputParser()
        response_feedback = feedback_chain.invoke({"context": retrieved_docs, "raw_text": input_data})
        print("Response Feedback:", response_feedback)  # 디버깅용 로그

        # 퀴즈 생성
        quiz_chain = prompt_quiz | llm | StrOutputParser()
        response_quiz = quiz_chain.invoke({"context": retrieved_docs, "raw_text": input_data})
        print("Response Quiz:", response_quiz)  # 디버깅용 로그

        # 객관식 퀴즈 생성
        multiple_chain = prompt_multiple | llm | StrOutputParser()
        response_multiple = multiple_chain.invoke({"context": retrieved_docs, "raw_text": input_data})
        print("Response Multiple:", response_multiple)  # 디버깅용 로그

        return {
            "rag_id": ",".join(retrieved_ids),
            "response": response_feedback,
            "quiz": response_quiz,
            "multiple": response_multiple,
        }

    except Exception as e:
        print(f"Error in analysis_chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze chunk: {str(e)}")
