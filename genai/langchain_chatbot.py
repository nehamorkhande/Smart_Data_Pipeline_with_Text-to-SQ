import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

def get_sql_database(admin_id: int):
    DB_USER = os.getenv("DB_USER1")
    DB_PASS = os.getenv("DB_PASS1")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    db = SQLDatabase.from_uri(
        db_uri,
        include_tables=["sales","customers","products","categories","upload_log"],
        sample_rows_in_table_info=2
    )
    return db

def get_sql_agent(admin_id: int, business_name: str):
    llm = get_llm()
    db = get_sql_database(admin_id)
    custom_prefix = f"""
You are a business analytics assistant for {business_name}.
You have access to a MySQL sales database.

STRICT RULES:
- ALWAYS filter with WHERE admin_id = {admin_id} in every SQL query
- Only use SELECT queries. Never INSERT, UPDATE, DELETE or DROP
- Write ONE simple focused SQL query per action
- Stop as soon as you have enough data to answer
- Use rupee symbol for Indian currency

DATE RULES:
- For "this month"  -> MONTH(sale_date) = MONTH(CURDATE()) AND YEAR(sale_date) = YEAR(CURDATE())
- For "last month"  -> MONTH(sale_date) = MONTH(CURDATE() - INTERVAL 1 MONTH) AND YEAR(sale_date) = YEAR(CURDATE() - INTERVAL 1 MONTH)
- For "this year"   -> YEAR(sale_date) = YEAR(CURDATE())
- For "today"       -> DATE(sale_date) = CURDATE()
- Never use hardcoded dates

OUTPUT RULES:
- NEVER mention admin_id in your response to the user
- NEVER say "for admin_id=5" or "(admin_id=5)" in the answer
- Always refer to the business by name: {business_name}
- Never return raw Python tuples or lists like ('item1', 'item2')
- Always present lists as clean numbered or bullet points
- Always include totals, counts and rupee amounts where relevant
- Give a short business insight after every answer
- Format numbers in Indian style: 1,44,76,072

EXAMPLE good output:
This Month Summary for {business_name}:
- Total Sales: Rs.1,44,76,072
- Total Orders: 2,948
- Insight: Sales are strong this month with nearly 3,000 orders.

EXAMPLE bad output (never do this):
The total sales for admin_id = 5 is Rs.144,760,721
"""
    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
        prefix=custom_prefix,
        top_k=15,
        max_iterations=15,
        max_execution_time=60,
    )
    return agent

def build_history_string(chat_history: list) -> str:
    lines = []
    for prev in chat_history[-5:]:
        lines.append(f"Human: {prev['question']}")
        lines.append(f"Assistant: {prev['answer']}")
    return "\n".join(lines)

def langchain_chat(
        question: str,
        admin_id: int,
        business_name: str,
        chat_history: list,
        use_sql_agent: bool = True
) -> str:
    data_keywords = [
        "revenue", "sales", "orders", "product", "customer",
        "how much", "how many", "top", "best", "worst",
        "total", "average", "month", "year", "show", "list",
        "compare", "which", "category", "payment", "pending",
        "returned", "city", "date", "trend", "performance",
        "day", "week", "profit", "loss", "stock", "quantity",
        "summarize", "summary", "give", "name", "all", "last",
        "this", "today", "yesterday", "popular", "lowest", "highest"
    ]
    question_lower = question.lower()
    needs_sql = any(kw in question_lower for kw in data_keywords)
    try:
        if needs_sql and use_sql_agent:
            agent = get_sql_agent(admin_id, business_name)
            full_question = f"""
{question}

Rules:
- Filter every SQL query by admin_id={admin_id}
- Use correct date functions for any time-based query
- Format output as clean readable text, never raw tuples or Python lists
- Never mention admin_id in the response, use business name "{business_name}" instead
- Give a business insight after the answer
"""
            lc_history = []
            for prev in chat_history[-4:]:
                lc_history.append(HumanMessage(content=prev["question"]))
                lc_history.append(AIMessage(content=prev["answer"]))
            result = agent.invoke({
                "input": full_question,
                "chat_history": lc_history
            })

            output = result.get("output", "I could not find an answer.")
            output = output.replace(f"admin_id = {admin_id}", business_name)
            output = output.replace(f"admin_id={admin_id}", business_name)
            output = output.replace(f"(admin_id = {admin_id})", "")
            output = output.replace(f"(admin_id={admin_id})", "")
            output = output.replace(f"for admin_id {admin_id}", f"for {business_name}")
            return output.strip()

        else:
            llm = get_llm()
            history_str = build_history_string(chat_history)
            prompt = f"""You are an intelligent business analytics advisor for {business_name}.
You help the store owner understand their sales data and improve their business.

Previous conversation:
{history_str}

Current question: {question}

Give a helpful, specific, and actionable answer.
Use data and numbers when available.
Be conversational but professional.
Never mention admin_id in your response."""
            response = llm.invoke(prompt)
            return response.content

    except Exception as e:
        err = str(e)
        if "429" in err or "rate_limit" in err.lower():
            return "⚠️ Rate limit hit. Please wait a moment and try again."
        if "iteration limit" in err.lower() or "time limit" in err.lower():
            return "⚠️ Query timed out. Please try a simpler question like 'show top 5 products by revenue'."
        return f"I encountered an error: {err}\n\nPlease try rephrasing your question."
