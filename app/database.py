import atexit
from threading import Lock

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

COLLECTION_NAME = "resume_portfolio"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

client = QdrantClient(path="./data/qdrant_db")
client.set_model(EMBEDDING_MODEL)
_CLIENT_LOCK = Lock()
atexit.register(client.close)


def _result_to_chunk(result) -> dict:
    payload = getattr(result, "metadata", None) or getattr(result, "payload", None) or {}
    document = getattr(result, "document", None) or payload.get("document", "")
    metadata = {k: v for k, v in payload.items() if k != "document"}
    return {"text": str(document), "metadata": metadata}


def retrieve_resume_chunks(query: str, chunk_type: str, top_k: int = 5) -> list[dict]:
    print(f"🔍 [Database] Searching Qdrant for {chunk_type} chunks...")
    qdrant_filter = Filter(
        must=[FieldCondition(key="type", match=MatchValue(value=chunk_type))]
    )
    with _CLIENT_LOCK:
        results = client.query(
            collection_name=COLLECTION_NAME,
            query_text=query,
            query_filter=qdrant_filter,
            limit=top_k,
        )
    return [_result_to_chunk(result) for result in results]

def get_matching_projects(job_description: str, top_k: int = 3) -> list[str]:
    print("🔍 [Database] Searching Qdrant for matches...")
    
    # Using query_text explicitly forces Qdrant to treat the input as text, not an ID
    with _CLIENT_LOCK:
        search_results = client.query(
            collection_name=COLLECTION_NAME,
            query_text=job_description,
            limit=top_k
        )
    
    # Safely extract the text, handling both old and new Qdrant formats
    projects = []
    for result in search_results:
        if hasattr(result, 'document') and result.document:
            projects.append(str(result.document))
        else:
            projects.append(str(result.payload.get("page_content", "")))
            
    return projects
