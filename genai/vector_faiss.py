import os
import json
import shutil
import faiss
import numpy as np

BASE_FOLDER=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_FOLDER=os.path.join(BASE_FOLDER,"policy_store")

def get_folder(admin_id):
    return os.path.join(STORE_FOLDER,"admin_"+str(admin_id))

def has_vectors(admin_id):
    return os.path.exists(os.path.join(get_folder(admin_id),"index.faiss"))

def delete_vectors(admin_id):
    folder=get_folder(admin_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)

def save_vectors(admin_id,chunks,vectors):
    delete_vectors(admin_id)
    folder=get_folder(admin_id)
    os.makedirs(folder)

    index=faiss.IndexFlatIP(vectors.shape[1])
    index.add(np.array(vectors,dtype="float32"))
    faiss.write_index(index,os.path.join(folder,"index.faiss"))

    with open(os.path.join(folder,"chunks.json"),"w") as f:
        json.dump(chunks,f)

def search_vectors(admin_id,question_vector,k):
    if not has_vectors(admin_id):
        return []
    folder=get_folder(admin_id)
    index=get_folder(admin_id)
    index=faiss.read_index(os.path.join(folder,"index.faiss"))
    with open(os.path.join(folder,"chunks.json")) as f:
        chunks=json.load(f)

    query=np.array([question_vector],dtype="float32")
    scores,positions=index.search(query,k)

    results=[]
    for score, i in zip(scores[0],positions[0]):
        if i==-1:
            continue
        results.append({"page":chunks[i]["page"],"text":chunks[i]["text"],"score":float(score)})
    return results


    