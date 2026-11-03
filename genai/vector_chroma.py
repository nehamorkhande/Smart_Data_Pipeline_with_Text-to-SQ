import os

import chromadb

BASE_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_FOLDER = os.path.join(BASE_FOLDER, "policy_store", "chroma_db")

client = None


def get_client():
    global client
    if client is None:
        client = chromadb.PersistentClient(path=CHROMA_FOLDER)
    return client


def collection_name(admin_id):
    return "admin_" + str(admin_id)


def get_collection(admin_id):
    try:
        return get_client().get_collection(collection_name(admin_id))
    except Exception:
        return None


def has_vectors(admin_id):
    collection = get_collection(admin_id)
    return collection is not None and collection.count() > 0


def delete_vectors(admin_id):
    try:
        get_client().delete_collection(collection_name(admin_id))
    except Exception:
        pass                                       


def save_vectors(admin_id, chunks, vectors):
    delete_vectors(admin_id)                       

    collection = get_client().create_collection(
        name=collection_name(admin_id),
        metadata={"hnsw:space": "cosine"},
    )

    ids = [str(i) for i in range(len(chunks))]     
    texts = [c["text"] for c in chunks]
    pages = [{"page": c["page"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=vectors.tolist(),
        documents=texts,
        metadatas=pages,
    )


def search_vectors(admin_id, question_vector, k):
    collection = get_collection(admin_id)
    if collection is None:
        return []

    k = min(k, collection.count())                 
    if k == 0:
        return []

    found = collection.query(query_embeddings=[question_vector.tolist()], n_results=k)

    results = []
    for text, meta, distance in zip(found["documents"][0], found["metadatas"][0], found["distances"][0]):
        results.append({"page": meta["page"], "text": text, "score": float(1 - distance)})
    return results