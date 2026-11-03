import os
import json
import shutil
from datetime import datetime

import numpy as np
from pypdf import PdfReader


VECTOR_DB = "faiss"         
if VECTOR_DB == "faiss":
    from genai import vector_faiss as vector_db
elif VECTOR_DB == "chroma":
    from genai import vector_chroma as vector_db
elif VECTOR_DB == "pinecone":
    from genai import vector_pinecone as vector_db

BASE_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_FOLDER = os.path.join(BASE_FOLDER, "policy_store")
CHUNK_SIZE = 500      
OVERLAP = 100         
TOP_K = 3             
MIN_SCORE = 0.5       
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"    


POLICY_WORDS = ["policy", "policies", "refund", "warranty", "exchange", "replacement",
                "cancel", "can i return", "i can return", "can return", "return a", "return the", "return window",
                "return period", "return within", "days to return", "return days", "returnable", "return or exchange",
                "shipping charge", "delivery time", "support hours", "coupon", "discount code"]

DATA_WORDS = ["revenue", "total", "count", "top ", "bottom ", "average", "highest", "lowest",
              "how many orders", "pending orders", "completed orders", "returned orders"]



def get_folder(admin_id):
    return os.path.join(STORE_FOLDER, "admin_" + str(admin_id))


def has_policy(admin_id):
    return os.path.exists(os.path.join(get_folder(admin_id), "info.json")) and vector_db.has_vectors(admin_id)


def get_policy_info(admin_id):
    path = os.path.join(get_folder(admin_id), "info.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def delete_policy(admin_id):
    vector_db.delete_vectors(admin_id)
    folder = get_folder(admin_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)



def read_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():
            text = " ".join(text.split())   
            pages.append((number, text))
    return pages


def make_chunks(pages):
    chunks = []
    for page_number, text in pages:
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            piece = text[start:end].strip()
            if piece:
                chunks.append({"page": page_number, "text": piece})
            start = start + CHUNK_SIZE - OVERLAP
    return chunks



model = None


def get_embeddings(texts):
    global model
    if model is None:
        from fastembed import TextEmbedding
        model = TextEmbedding(EMBEDDING_MODEL)
    vectors = np.array(list(model.embed(texts)), dtype="float32")
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  



def save_policy(admin_id, file_name, pdf_file):
    try:
        pages = read_pdf(pdf_file)
    except Exception as e:
        return False, "Could not read this pdf: " + str(e)

    chunks = make_chunks(pages)
    if len(chunks) == 0:
        return False, "No text found. This pdf may be a scanned image."

    vectors = get_embeddings([c["text"] for c in chunks])

    delete_policy(admin_id)                    
    vector_db.save_vectors(admin_id, chunks, vectors)

    folder = get_folder(admin_id)              
    os.makedirs(folder, exist_ok=True)
    info = {"file_name": file_name, "pages": len(pages), "chunks": len(chunks),
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "vector_db": VECTOR_DB}
    with open(os.path.join(folder, "info.json"), "w") as f:
        json.dump(info, f)
    return True, "Saved " + str(len(chunks)) + " chunks from " + str(len(pages)) + " pages."



def search_policy(admin_id, question, k=TOP_K):
    if not has_policy(admin_id):
        return []
    question_vector = get_embeddings([question])[0]
    return vector_db.search_vectors(admin_id, question_vector, k)     



def is_policy_question(question):
    q = " " + question.lower() + " "
    for word in DATA_WORDS:
        if word in q:
            return False
    for word in POLICY_WORDS:
        if word in q:
            return True
    return False


def answer_from_policy(admin_id, business_name, question):
    if not has_policy(admin_id):
        return "No policy is uploaded yet. Please upload your policy pdf on the Store Policy page."

    info = get_policy_info(admin_id)
    not_found = ("I could not find this in your policy document (" + info["file_name"] +
                 "). Please check the document or contact the store.")

    hits = []
    for h in search_policy(admin_id, question):
        if h["score"] >= MIN_SCORE:
            hits.append(h)
    if len(hits) == 0:
        return not_found

    text = ""
    for h in hits:
        text += "[Page " + str(h["page"]) + "] " + h["text"] + "\n\n"

    prompt = ("You answer questions about the store policy of " + business_name + ".\n"
              "Use ONLY the policy text below. Do not use any other knowledge.\n"
              "If the answer is not in the text, reply with exactly: NOT_FOUND\n"
              "Keep the answer short. Do not make up numbers or days.\n\n"
              "POLICY TEXT:\n" + text +
              "QUESTION: " + question + "\nANSWER:")

    from genai.langchain_chatbot import get_llm, to_text     
    answer = to_text(get_llm().invoke(prompt).content).strip()

    if "NOT_FOUND" in answer:
        return not_found
    pages = sorted(set(h["page"] for h in hits))
    page_text = ", ".join(str(p) for p in pages)
    return answer + "\n\n📄 Source: " + info["file_name"] + ", page " + page_text