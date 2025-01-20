# app/services/rag_service.py
from openai import OpenAI
from .document_loader import DocumentLoader
from typing import Tuple
from app.core.config import settings

class RAGService:
   def __init__(self):
       self.client = OpenAI(
           api_key=settings.UPSTAGE_API_KEY,
           base_url=settings.UPSTAGE_BASE_URL
       )
       self.doc_loader = DocumentLoader()
   
   async def get_relevant_context(self, query: str) -> str:
       """Pinecone에서 관련 문서를 검색하여 컨텍스트 생성"""
       try:
           relevant_docs = await self.doc_loader.search_similar(query, top_k=3)
           if not relevant_docs:
               return ""
           
           context = "\n\n".join([doc['content'] for doc in relevant_docs])
           return context
       except Exception as e:
           print(f"Error getting context: {str(e)}")
           return ""

   async def generate_basic_feedback(self, content: str) -> str:
       """RAG 없이 기본 피드백 생성"""
       try:
           response = self.client.chat.completions.create(
               model="solar-mini", 
               messages=[
                   {
                       "role": "system",
                       "content": "당신은 학습을 돕는 선생님입니다. 학생의 노트에 대해 건설적인 피드백을 제공해주세요."
                   },
                   {
                       "role": "user",
                       "content": f"다음 노트에 대한 피드백을 제공해주세요: {content}"
                   }
               ]
           )
           return response.choices[0].message.content
       except Exception as e:
           print(f"Error generating basic feedback: {str(e)}")
           return "피드백 생성 중 오류가 발생했습니다."

   async def generate_rag_feedback(self, content: str, context: str) -> str:
       """RAG 기반 피드백 생성"""
       try:
           response = self.client.chat.completions.create(
               model="solar-mini",
               messages=[
                   {
                       "role": "system",
                       "content": """당신은 학습을 돕는 선생님입니다. 
                       주어진 참고자료를 기반으로 학생의 노트 내용이 정확한지 평가하고,
                       만약 틀린 내용이 있다면 참고자료를 바탕으로 올바른 정보를 제공해주세요."""
                   },
                   {
                       "role": "user",
                       "content": f"""참고자료:
                       {context}
                       
                       학생 노트:
                       {content}
                       
                       위 노트의 내용이 참고자료의 내용과 일치하는지 확인하고, 정확한 정보를 제공해주세요.
                       만약 노트의 내용이 부정확하다면, 참고자료를 바탕으로 올바른 정보를 알려주세요."""
                   }
               ]
           )
           return response.choices[0].message.content
       except Exception as e:
           print(f"Error generating RAG feedback: {str(e)}")
           return "RAG 피드백 생성 중 오류가 발생했습니다."

   async def generate_feedback(self, content: str) -> Tuple[str, str]:
       """기본 피드백과 RAG 기반 피드백을 모두 생성"""
       try:
           # 1. 관련 컨텍스트 검색
           context = await self.get_relevant_context(content)
           
           # 2. 기본 피드백 생성
           basic_feedback = await self.generate_basic_feedback(content)
           
           # 3. RAG 기반 피드백 생성
           if context:
               rag_feedback = await self.generate_rag_feedback(content, context)
           else:
               rag_feedback = "관련 참고 자료를 찾을 수 없습니다. 일반적인 피드백을 제공합니다: " + basic_feedback
           
           return basic_feedback, rag_feedback
           
       except Exception as e:
           print(f"Error in generate_feedback: {str(e)}")
           return "피드백 생성 실패", "피드백 생성 실패"