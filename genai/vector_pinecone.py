import os
import time

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX", "store-policy")
pc = None


def get_pinecone():
    global pc
    if pc is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc


def namespace_name(admin_id):
    return "admin_" + str(admin_id)


def index_exists():
    return INDEX_NAME in get_pinecone().list_indexes().names()


def get_index():
    return get_pinecone().Index(INDEX_NAME)


def make_index(dimension):
    if index_exists():
        return
    get_pinecone().create_index(
        name=INDEX_NAME,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
    while not get_pinecone().describe_index(INDEX_NAME).status["ready"]:
        time.sleep(1)                              # wait until the index is ready


def has_vectors(admin_id):
    if not index_exists():
        return False
    stats = get_index().describe_index_stats()
    namespace = namespace_name(admin_id)
    return namespace in stats.namespaces and stats.namespaces[namespace].vector_count > 0


def delete_vectors(admin_id):
    if not index_exists():
        return
    try:
        get_index().delete(delete_all=True, namespace=namespace_name(admin_id))
    except Exception:
        pass                                       


def save_vectors(admin_id, chunks, vectors):
    make_index(vectors.shape[1])
    delete_vectors(admin_id)                       

    items = []
    for i, chunk in enumerate(chunks):
        items.append({
            "id": str(i),
            "values": vectors[i].tolist(),
            "metadata": {"page": chunk["page"], "text": chunk["text"]},   
        })
    get_index().upsert(vectors=items, namespace=namespace_name(admin_id))

    for _ in range(15):
        if has_vectors(admin_id):
            break
        time.sleep(1)


def search_vectors(admin_id, question_vector, k):
    if not has_vectors(admin_id):
        return []

    found = get_index().query(
        vector=question_vector.tolist(),
        top_k=k,
        namespace=namespace_name(admin_id),
        include_metadata=True,
    )

    results = []
    for match in found.matches:
        results.append({"page": int(match.metadata["page"]), "text": match.metadata["text"],
                        "score": float(match.score)})
    return results