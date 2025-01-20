from sqlalchemy.orm import Session
from typing import Dict, List

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db

    async def get_comparison_metrics(self, note_id: str) -> Dict:
        # RAG 적용 전/후 메트릭 계산
        rag_metrics = await self._calculate_metrics(note_id, with_rag=True)
        non_rag_metrics = await self._calculate_metrics(note_id, with_rag=False)

        return {
            "rag_metrics": rag_metrics,
            "non_rag_metrics": non_rag_metrics,
            "improvement": {
                "rating_improvement": rag_metrics["avg_rating"] - non_rag_metrics["avg_rating"],
                "comparison": await self._compare_results(note_id)
            }
        }

    async def _calculate_metrics(self, note_id: str, with_rag: bool) -> Dict:
        query = self.db.query(
            func.avg(Feedback.rating).label('avg_rating'),
            func.count(Feedback.feedback_id).label('feedback_count')
        ).join(
            Analysis, Feedback.analyze_id == Analysis.analyze_id
        ).filter(
            Analysis.note_id == note_id
        )

        if with_rag:
            query = query.filter(Analysis.rag_id.isnot(None))
        else:
            query = query.filter(Analysis.rag_id.is_(None))

        result = query.first()
        return {
            "avg_rating": float(result.avg_rating) if result.avg_rating else 0,
            "feedback_count": result.feedback_count
        }

    async def _compare_results(self, note_id: str) -> Dict:
        # RAG 적용 전/후 결과 비교 로직
        results = self.db.query(Analysis).filter(
            Analysis.note_id == note_id
        ).all()

        return {
            "content_length_diff": self._calculate_length_difference(results),
            "response_similarity": await self._calculate_similarity(results)
        }