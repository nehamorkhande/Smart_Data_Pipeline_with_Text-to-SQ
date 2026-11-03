import os
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook

import genai.policy_rag as rag

load_dotenv()


ADMIN_ID = 998                                  
BUSINESS_NAME = "Neha Retail Store"
PDF_FILE = "rag_docs/sample_store_policy.pdf"
RUN_LLM = True                                  
MODEL = "openai/gpt-oss-120b"                   
WAIT_SECS = 3                                   
RETRIES = 3                                     
RETRY_WAIT = 60                                 
EXCEL_FILE = "results/rag_experiment_log.xlsx"

os.environ["GROQ_MODEL"] = MODEL                


TESTS = [
    ("How many days do I have to return a product?", ["7 days"], 1),
    ("for t shirt in how many days i can return", ["7 days"], 1),
    ("How soon must I report a damaged product?", ["48 hours"], 1),
    ("Can I return grocery items?", ["not eligible|not returnable|cannot|can't|can not|no,|not be returned"], 1),
    ("How long does a refund take after my return is approved?", ["5 to 7|5-7|5–7"], 2),
    ("What is the warranty on laptops?", ["1 year|one year|12 month"], 2),
    ("What is the warranty on furniture?", ["6 month|six month"], 2),
    ("Can I cancel an order after it is dispatched?", ["no longer|cannot|can't|can not|not be cancelled|not possible"], 2),
    ("Is shipping free?", ["1,000"], 2),
    ("What is the shipping charge for orders below Rs. 1000?", ["60"], 2),
    ("How many days does delivery take within the same city?", ["3 working days|3 days|three"], 3),
    ("Can I use two discount codes on one order?", ["one discount code|only one|only 1|cannot|can not|not allowed"], 3),
    ("Is Cash on Delivery available for an order of Rs. 30,000?", ["25,000"], 3),
    ("What are the customer support timings?", ["10:00|10 am|10am|10.00"], 3),
]


NOT_IN_PDF = [
    "Do you offer gift wrapping?",
    "Do you deliver outside India?",
    "What is the price of an iPhone 15?",
    "Do you have a shop in Mumbai?",
]


ROUTER_TESTS = [
    ("What is the return policy?", True),
    ("How many days to return a product?", True),
    ("for t shirt in how many days i can return", True),
    ("Can I cancel a pending order?", True),
    ("Is there a warranty on electronics?", True),
    ("How long does a refund take?", True),
    ("What is my total revenue?", False),
    ("How many Pending orders do I have?", False),
    ("Which product has the most returned orders?", False),
    ("average return time for shirt", False),
    ("Top 5 customers by sales", False),
    ("Show sales by city", False),
]

NOT_FOUND_TEXT = "could not find this in your policy"



def check(must_have, text):
    text = " ".join(text.lower().split())
    for item in must_have:
        found = False
        for option in item.lower().split("|"):
            if option in text:
                found = True
        if not found:
            return False
    return True


def made_up_numbers(answer, question, chunk_text):
    answer = answer.split("📄 Source")[0]
    bad = []
    for n in re.findall(r"\d[\d,]*", answer):
        n = n.rstrip(",")
        if n not in chunk_text and n not in question:
            bad.append(n)
    return bad


def get_source_pages(answer):
    if "📄 Source" not in answer or ", page " not in answer:
        return []
    pages = answer.split(", page ")[-1]
    return [int(p) for p in re.findall(r"\d+", pages)]


def ask_policy_bot(question):
    hits = 0
    for attempt in range(RETRIES + 1):
        try:
            answer = rag.answer_from_policy(ADMIN_ID, BUSINESS_NAME, question)
            return answer, hits
        except Exception as e:
            err = str(e)
            if ("429" in err or "rate_limit" in err.lower()) and attempt < RETRIES:
                hits += 1
                print("   rate limit hit, waiting", RETRY_WAIT, "seconds...")
                time.sleep(RETRY_WAIT)
            else:
                raise
    return "", hits



def run_test(test_type, question, must_have, page):
    row = {"Test_Type": test_type, "Question": question,
           "Expected": ", ".join(must_have) if must_have else "NOT FOUND",
           "Best_Score": "", "Retrieval_OK": "", "Answer_OK": "-", "Source_OK": "-",
           "Made_Up_Numbers": "-", "Status": "", "Retrieval_Sec": "", "Total_Sec": "",
           "Answer": "", "Rate_Limit_Hits": 0, "Error": ""}
    start = time.time()
    try:
        t = time.time()
        hits = rag.search_policy(ADMIN_ID, question)
        row["Retrieval_Sec"] = round(time.time() - t, 3)
        best = hits[0]["score"] if hits else 0
        row["Best_Score"] = round(best, 3)
        chunk_text = " ".join(h["text"] for h in hits)

        if test_type == "Answer":
            row["Retrieval_OK"] = check(must_have, chunk_text)
        else:
            row["Retrieval_OK"] = best < rag.MIN_SCORE      

        if RUN_LLM:
            answer, limit_hits = ask_policy_bot(question)
            row["Answer"] = answer[:300]
            row["Rate_Limit_Hits"] = limit_hits
            if test_type == "Answer":
                row["Answer_OK"] = check(must_have, answer.split("📄 Source")[0])
                row["Source_OK"] = page in get_source_pages(answer)
                bad = made_up_numbers(answer, question, chunk_text)
                row["Made_Up_Numbers"] = ", ".join(bad) if bad else "none"
                ok = row["Answer_OK"] and row["Source_OK"] and not bad
            else:
                row["Answer_OK"] = NOT_FOUND_TEXT in answer
                ok = row["Answer_OK"]
        else:
            ok = row["Retrieval_OK"]
        row["Status"] = "PASS" if ok else "FAIL"
    except Exception as e:
        row["Status"] = "ERROR"
        row["Error"] = str(e)[:300]
    row["Total_Sec"] = round(time.time() - start, 2)
    return row



LOG_COLUMNS = ["Experiment_ID", "Date_Time", "Vector_DB", "Embedding_Model", "LLM_Model",
               "Chunk_Size", "Overlap", "Top_K", "Min_Score", "Test_Type", "Question", "Expected",
               "Best_Score", "Retrieval_OK", "Answer_OK", "Source_OK", "Made_Up_Numbers", "Status",
               "Retrieval_Sec", "Total_Sec", "Rate_Limit_Hits", "Answer", "Error"]

SUMMARY_COLUMNS = ["Experiment_ID", "Date_Time", "Vector_DB", "Embedding_Model", "LLM_Model",
                   "Chunk_Size", "Overlap", "Top_K", "Min_Score", "Router_Passed", "Retrieval_Hit",
                   "Answer_Passed", "Source_Passed", "NotFound_Passed", "Overall_Pass_%",
                   "Save_PDF_Sec", "Avg_Retrieval_Sec", "Avg_Total_Sec", "Rate_Limit_Hits"]


def open_workbook():
    if os.path.exists(EXCEL_FILE):
        return load_workbook(EXCEL_FILE)
    wb = Workbook()
    wb.remove(wb.active)
    wb.create_sheet("Log").append(LOG_COLUMNS)
    wb.create_sheet("Summary").append(SUMMARY_COLUMNS)
    return wb


def next_experiment_id(wb):
    return "RAG_" + str(wb["Summary"].max_row).zfill(3)     


def save_excel(wb):
    os.makedirs("results", exist_ok=True)
    try:
        wb.save(EXCEL_FILE)
        print("Saved in", EXCEL_FILE)
    except PermissionError:                                
        new_name = "results/rag_experiment_log_" + datetime.now().strftime("%H%M%S") + ".xlsx"
        wb.save(new_name)
        print("Excel file was open, saved in", new_name, "instead")


def count(rows, column, value=True):
    return sum(1 for r in rows if r[column] == value)



def main():
    print("Vector db:", rag.VECTOR_DB, "| Embedding:", rag.EMBEDDING_MODEL,
          "| LLM:", MODEL if RUN_LLM else "not used", "\n")

    print("ROUTER TEST")
    router_passed = 0
    for question, expected in ROUTER_TESTS:
        result = rag.is_policy_question(question)
        ok = result == expected
        router_passed += ok
        print("  ", "PASS" if ok else "FAIL", "|", "policy" if result else "SQL   ", "|", question)


    print("\nSaving the policy pdf...")
    t = time.time()
    ok, message = rag.save_policy(ADMIN_ID, "sample_store_policy.pdf", PDF_FILE)
    save_sec = round(time.time() - t, 2)
    print(message, "(" + str(save_sec) + " sec)")
    if not ok:
        return

    rows = []
    try:
        
        print("\nPOLICY QUESTIONS")
        all_tests = [("Answer", q, m, p) for q, m, p in TESTS] + \
                    [("NotInPDF", q, [], 0) for q in NOT_IN_PDF]
        for number, (test_type, question, must_have, page) in enumerate(all_tests, start=1):
            row = run_test(test_type, question, must_have, page)
            rows.append(row)
            print("  ", number, row["Status"], "| score", row["Best_Score"], "|", question)
            if row["Error"]:
                print("      error:", row["Error"])
            if RUN_LLM and number < len(all_tests):
                time.sleep(WAIT_SECS)
    finally:
        rag.delete_policy(ADMIN_ID)                         

    
    answer_rows = [r for r in rows if r["Test_Type"] == "Answer"]
    notfound_rows = [r for r in rows if r["Test_Type"] == "NotInPDF"]
    passed = count(rows, "Status", "PASS")
    percent = round(100 * passed / len(rows), 1)

    print("\n================ RESULT ================")
    print("Router passed     :", router_passed, "/", len(ROUTER_TESTS))
    print("Retrieval hit     :", count(answer_rows, "Retrieval_OK"), "/", len(answer_rows))
    if RUN_LLM:
        print("Answer passed     :", count(answer_rows, "Answer_OK"), "/", len(answer_rows))
        print("Source page right :", count(answer_rows, "Source_OK"), "/", len(answer_rows))
    print("Not-found passed  :", count(notfound_rows, "Answer_OK" if RUN_LLM else "Retrieval_OK"),
          "/", len(notfound_rows))
    print("Overall           :", passed, "/", len(rows), "=", percent, "%")

    
    wb = open_workbook()
    exp_id = next_experiment_id(wb)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    llm_name = MODEL if RUN_LLM else "not used"
    common = [exp_id, now, rag.VECTOR_DB, rag.EMBEDDING_MODEL, llm_name,
              rag.CHUNK_SIZE, rag.OVERLAP, rag.TOP_K, rag.MIN_SCORE]

    for r in rows:
        wb["Log"].append(common + [r[c] for c in LOG_COLUMNS[9:]])

    times = [r["Retrieval_Sec"] for r in rows if r["Retrieval_Sec"] != ""]
    totals = [r["Total_Sec"] for r in rows if r["Total_Sec"] != ""]
    wb["Summary"].append(common + [
        str(router_passed) + "/" + str(len(ROUTER_TESTS)),
        str(count(answer_rows, "Retrieval_OK")) + "/" + str(len(answer_rows)),
        (str(count(answer_rows, "Answer_OK")) + "/" + str(len(answer_rows))) if RUN_LLM else "-",
        (str(count(answer_rows, "Source_OK")) + "/" + str(len(answer_rows))) if RUN_LLM else "-",
        str(count(notfound_rows, "Answer_OK" if RUN_LLM else "Retrieval_OK")) + "/" + str(len(notfound_rows)),
        percent, save_sec,
        round(sum(times) / len(times), 3) if times else "",
        round(sum(totals) / len(totals), 2) if totals else "",
        sum(r["Rate_Limit_Hits"] for r in rows),
    ])
    save_excel(wb)
    print("Experiment id:", exp_id)


if __name__ == "__main__":
    main()