# app/services/document_loader.py
import os
from typing import List
import PyPDF2
from openai import OpenAI
import uuid
import asyncio
from pinecone import Pinecone, PodSpec

class DocumentLoader:
    def __init__(self):
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(
            api_key="up_SI9PGgvUYZuOygwwjR7J5psU0AyYa",
            base_url="https://api.upstage.ai/v1/solar"
        )
        
        # Pinecone 초기화
        PINECONE_API_KEY = "pcsk_2Ga39b_8ZL6Af8MDx2w3oWZ3wRbYbTpp2MQE4yYpJBBLNob6KLfn4x5tccf4LSHvCSzo3j"
        self.index_name = "quickstart"
        
        # Pinecone 클라이언트 초기화 및 인덱스 연결
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(self.index_name)
        
        # 디렉토리 설정 및 생성
        self.docs_dir = "app/data/documents"
        os.makedirs(self.docs_dir, exist_ok=True)

    async def process_documents(self):
        """문서를 처리하고 Pinecone에 저장"""
        try:
            documents = []
            # PDF 파일 목록 가져오기
            pdf_files = [f for f in os.listdir(self.docs_dir) if f.endswith('.pdf')]
            
            if not pdf_files:
                print(f"No PDF files found in {self.docs_dir}")
                return
            
            # 각 PDF 파일 처리
            for filename in pdf_files:
                try:
                    file_path = os.path.join(self.docs_dir, filename)
                    chunks = await self._process_pdf(file_path)
                    documents.extend(chunks)
                except Exception as e:
                    print(f"Error processing file {filename}: {str(e)}")
                    continue
            
            # 임베딩 생성 및 Pinecone에 저장
            if documents:
                await self._store_in_pinecone(documents)
                print(f"Successfully processed {len(documents)} chunks from {len(pdf_files)} files")
            
        except Exception as e:
            print(f"Error in process_documents: {str(e)}")
            raise

    async def _process_pdf(self, file_path: str) -> List[dict]:
        """PDF 파일을 처리하고 청크로 분할"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # 청크로 분할
                chunks = self._split_into_chunks(text)
                
                # 메타데이터 준비
                return [{'text': chunk, 'source': os.path.basename(file_path)} for chunk in chunks]
                
        except Exception as e:
            print(f"Error in _process_pdf: {str(e)}")
            return []

    def _split_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """텍스트를 청크로 분할"""
        try:
            words = text.split()
            chunks = []
            current_chunk = []
            current_size = 0
            
            for word in words:
                current_chunk.append(word)
                current_size += len(word) + 1
                
                if current_size >= chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                
            return chunks
            
        except Exception as e:
            print(f"Error in _split_into_chunks: {str(e)}")
            return []

    async def _store_in_pinecone(self, documents: List[dict], batch_size: int = 100):
        """문서를 Pinecone에 저장"""
        try:
            vectors = []
            
            # 청크별로 임베딩 생성 및 벡터 준비
            for doc in documents:
                try:
                    embedding = self.client.embeddings.create(
                        input=doc['text'],
                        model="embedding-query"
                    ).data[0].embedding

                    vectors.append({
                        'id': str(uuid.uuid4()),
                        'values': embedding,
                        'metadata': {
                            'text': doc['text'],
                            'source': doc['source']
                        }
                    })
                except Exception as e:
                    print(f"Error creating embedding: {str(e)}")
                    continue

            # 배치 단위로 Pinecone에 업로드
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    self.index.upsert(vectors=batch)
                    print(f"Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
                except Exception as e:
                    print(f"Error uploading batch to Pinecone: {str(e)}")

        except Exception as e:
            print(f"Error in _store_in_pinecone: {str(e)}")
            raise

    async def search_similar(self, query: str, top_k: int = 3):
        """쿼리와 유사한 문서 검색"""
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.client.embeddings.create(
                input=query,
                model="embedding-query"
            ).data[0].embedding

            # Pinecone에서 검색
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            return [
                {
                    'content': match.metadata['text'],
                    'score': match.score,
                    'source': match.metadata['source']
                }
                for match in results.matches
            ]

        except Exception as e:
            print(f"Error in search_similar: {str(e)}")
            return []

# 사용 예시
if __name__ == "__main__":
    async def main():
        loader = DocumentLoader()
        # 문서 처리 및 저장
        await loader.process_documents()
        
        # 검색 테스트
        results = await loader.search_similar("테스트 쿼리")
        print("Search results:", results)

    asyncio.run(main())