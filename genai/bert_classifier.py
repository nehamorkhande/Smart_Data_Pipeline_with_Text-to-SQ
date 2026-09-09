# ============================================================
# genai/bert_classifier.py
# BERT-based Intent Classifier + Answer Quality Scorer
#
# What it does:
#   1. IntentClassifier — classifies user questions into intents
#      using zero-shot semantic similarity (no training needed).
#      Uses sentence-transformers to embed the query and compare
#      against intent "anchor" sentences.
#
#   2. AnswerQualityScorer — scores how well an LLM answer
#      addresses the user's question using cosine similarity
#      on BERT embeddings.
#
# Why this approach instead of a fine-tuned BERT classifier?
#   - Zero-shot: works immediately with no labelled data
#   - Same sentence-transformers model already loaded for RAG
#   - For a portfolio project this showcases BERT understanding
#     without needing a GPU or training pipeline
#
# Intents:
#   revenue_query     → questions about money, sales totals
#   product_query     → questions about products, items, SKUs
#   customer_query    → questions about buyers, clients
#   trend_query       → time-based analysis, growth, comparison
#   operational_query → orders, payments, delivery, status
#   general_advice    → strategy, tips, recommendations
# ============================================================

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Optional

# ── Reuse the same model instance as rag_engine ─────────────
try:
    from rag_engine import _get_model
except ImportError:
    # Fallback if running standalone
    _MODEL: Optional[SentenceTransformer] = None
    def _get_model():
        global _MODEL
        if _MODEL is None:
            _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        return _MODEL


# ── Intent definitions ───────────────────────────────────────
# Each intent has multiple anchor sentences.
# The query is compared against ALL anchors; the intent whose
# anchors average the highest cosine similarity wins.

INTENT_ANCHORS: dict[str, list[str]] = {
    "revenue_query": [
        "What is the total revenue?",
        "How much money did we make?",
        "Show me sales amount and income",
        "What is our total earnings this month?",
        "How much revenue was generated?",
        "Total sales amount and profit",
        "How much did we earn this year?",
    ],
    "product_query": [
        "Which products sell the most?",
        "Show me the top performing products",
        "What are the best selling items?",
        "List all product categories",
        "Which item has the highest quantity sold?",
        "Product performance and sales breakdown",
        "Slow moving products inventory",
    ],
    "customer_query": [
        "Who are our top customers?",
        "List the best customers by spending",
        "Which customer bought the most?",
        "Show customer names and their purchases",
        "Customer analysis and demographics",
        "Which city or state has most buyers?",
        "New customers this month",
    ],
    "trend_query": [
        "How is business performance over time?",
        "Show monthly sales trend",
        "Compare this month vs last month",
        "Year over year growth analysis",
        "Is sales increasing or decreasing?",
        "Show me the revenue trend over time",
        "What is the growth rate?",
    ],
    "operational_query": [
        "How many orders are pending?",
        "Show payment mode breakdown",
        "Which payment method is most used?",
        "How many orders were returned?",
        "Order status and delivery analysis",
        "Invoice and transaction details",
        "Show me salesperson performance",
    ],
    "general_advice": [
        "What should I do to improve sales?",
        "Give me business suggestions",
        "How can I grow my business?",
        "What strategy should I follow?",
        "Advice on improving performance",
        "What am I doing wrong in my business?",
        "How to increase revenue?",
    ],
}

# ── Human-readable intent labels ────────────────────────────
INTENT_LABELS = {
    "revenue_query"    : "💰 Revenue Query",
    "product_query"    : "📦 Product Query",
    "customer_query"   : "👤 Customer Query",
    "trend_query"      : "📈 Trend Analysis",
    "operational_query": "⚙️ Operations Query",
    "general_advice"   : "💡 General Advice",
}

# ── Which intents NEED the SQL agent ────────────────────────
SQL_REQUIRED_INTENTS = {
    "revenue_query",
    "product_query",
    "customer_query",
    "trend_query",
    "operational_query",
}


# ── Pre-computed anchor embeddings (lazy) ───────────────────
_anchor_embeddings: Optional[dict] = None

def _get_anchor_embeddings() -> dict[str, np.ndarray]:
    """
    Compute and cache embeddings for all intent anchors.
    Shape per intent: (num_anchors, embedding_dim)
    """
    global _anchor_embeddings
    if _anchor_embeddings is not None:
        return _anchor_embeddings

    model = _get_model()
    result = {}
    for intent, anchors in INTENT_ANCHORS.items():
        embs = model.encode(
            anchors,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")
        result[intent] = embs   # shape: (num_anchors, dim)

    _anchor_embeddings = result
    return result


# ── IntentClassifier ────────────────────────────────────────
class IntentClassifier:
    """
    Classifies a user query into one of the defined intents.

    Example:
        clf = IntentClassifier()
        result = clf.classify("Which products sold the most this month?")
        # result = {
        #   "intent": "product_query",
        #   "label":  "📦 Product Query",
        #   "confidence": 0.87,
        #   "needs_sql": True,
        #   "scores": { "revenue_query": 0.41, "product_query": 0.87, ... }
        # }
    """

    def classify(self, query: str) -> dict:
        model       = _get_model()
        anchor_embs = _get_anchor_embeddings()

        # Embed query
        q_emb = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")[0]   # shape: (dim,)

        # Score each intent = mean cosine similarity to all its anchors
        scores = {}
        for intent, a_embs in anchor_embs.items():
            # cosine similarity: dot product (both are L2-normalised)
            sims          = a_embs @ q_emb          # shape: (num_anchors,)
            scores[intent] = float(np.mean(sims))

        best_intent = max(scores, key=scores.get)
        confidence  = scores[best_intent]

        return {
            "intent"    : best_intent,
            "label"     : INTENT_LABELS[best_intent],
            "confidence": round(confidence, 3),
            "needs_sql" : best_intent in SQL_REQUIRED_INTENTS,
            "scores"    : {k: round(v, 3) for k, v in scores.items()},
        }

    def needs_sql(self, query: str) -> bool:
        """Quick helper — does this query need the SQL agent?"""
        result = self.classify(query)
        return result["needs_sql"]

    def format_badge(self, classification: dict) -> str:
        """Returns a markdown string for display in Streamlit."""
        label      = classification["label"]
        confidence = int(classification["confidence"] * 100)
        color      = "#6366f1" if classification["needs_sql"] else "#10b981"
        return (
            f'<span style="display:inline-flex;align-items:center;gap:6px;'
            f'background:#f3f4f6;border:1px solid #e5e7eb;'
            f'border-radius:6px;padding:3px 10px;font-size:11px;'
            f'color:{color};font-weight:500;">'
            f'{label} · {confidence}% confidence</span>'
        )


# ── AnswerQualityScorer ──────────────────────────────────────
class AnswerQualityScorer:
    """
    Scores how well an answer addresses the question using BERT embeddings.

    Score interpretation:
        ≥ 0.75 → Excellent  ✅
        ≥ 0.55 → Good       👍
        ≥ 0.35 → Fair       ⚠️
        <  0.35 → Poor      ❌

    Usage:
        scorer = AnswerQualityScorer()
        score  = scorer.score("top products?", "The best products are ...")
        label  = scorer.label(score)
    """

    def score(self, question: str, answer: str) -> float:
        model = _get_model()
        embs  = model.encode(
            [question, answer],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        similarity = float(np.dot(embs[0], embs[1]))
        return round(max(0.0, min(1.0, similarity)), 3)

    def label(self, score: float) -> str:
        if score >= 0.75:
            return "✅ Excellent"
        elif score >= 0.55:
            return "👍 Good"
        elif score >= 0.35:
            return "⚠️ Fair"
        else:
            return "❌ Low relevance"

    def badge(self, question: str, answer: str) -> str:
        """Returns HTML badge for Streamlit display."""
        s     = self.score(question, answer)
        lbl   = self.label(s)
        pct   = int(s * 100)
        color = (
            "#10b981" if s >= 0.75 else
            "#6366f1" if s >= 0.55 else
            "#f59e0b" if s >= 0.35 else
            "#ef4444"
        )
        return (
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'background:#f9fafb;border:1px solid #e5e7eb;'
            f'border-radius:6px;padding:3px 10px;font-size:11px;'
            f'color:{color};font-weight:500;">'
            f'Answer quality: {lbl} ({pct}%)</span>'
        )


# ── Singletons ───────────────────────────────────────────────
_classifier = None
_scorer     = None

def get_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier

def get_scorer() -> AnswerQualityScorer:
    global _scorer
    if _scorer is None:
        _scorer = AnswerQualityScorer()
    return _scorer