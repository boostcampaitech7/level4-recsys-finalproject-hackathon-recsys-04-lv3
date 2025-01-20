from pinecone import Pinecone

pc = Pinecone(api_key="pcsk_2Ga39b_8ZL6Af8MDx2w3oWZ3wRbYbTpp2MQE4yYpJBBLNob6KLfn4x5tccf4LSHvCSzo3j")
index = pc.Index("quickstart")

# 저장된 벡터 수 확인
stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")

# 샘플 데이터 조회
results = index.query(
    vector=[0.1] * 1536,  # 임시 벡터
    top_k=3,
    include_metadata=True
)

for match in results.matches:
    print(f"\nVector ID: {match.id}")
    print(f"Score: {match.score}")
    print(f"Metadata: {match.metadata}")