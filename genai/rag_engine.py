# ============================================================
# genai/rag_engine.py
# RAG Engine — FAISS + sentence-transformers
#
# What it does:
#   1. Maintains a per-admin FAISS vector store of "knowledge chunks"
#   2. Chunks come from 3 sources:
#        a) Static business-knowledge docs (tips, definitions)
#        b) Sales summaries dynamically built from DB at query time
#        c) Any text context the user provides (uploaded reports, notes)
#   3. At query time, retrieves the top-k most relevant chunks
#   4. Returns them as a context string for the LLM prompt
# ============================================================

import os
import json
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional

from sentence_transformers import SentenceTransformer

try:
    import faiss
    FAISS_OK = True
except ImportError:
    FAISS_OK = False

# ── Model (loaded once at module level) ─────────────────────
# all-MiniLM-L6-v2: fast, lightweight, great for semantic search
_EMBED_MODEL: Optional[SentenceTransformer] = None

def _get_model() -> SentenceTransformer:
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBED_MODEL


# ── Static knowledge base ────────────────────────────────────
# These chunks are always available — they give the LLM grounding
# in business concepts without needing to query the DB.
STATIC_KNOWLEDGE = [
    # Revenue & KPIs
    "Revenue is the total income generated from sales transactions. "
    "It equals sum of (unit_price × quantity) minus discounts.",

    "Average Order Value (AOV) = Total Revenue / Number of Orders. "
    "Increasing AOV by 10% is usually easier than acquiring new customers.",

    "Month-over-Month (MoM) growth measures the percentage change in "
    "revenue compared to the previous month. Healthy retail MoM is 5-15%.",

    "Customer Lifetime Value (CLV) estimates how much revenue a single "
    "customer generates over their entire relationship with your business.",

    # Inventory & products
    "Top-selling products by quantity are not always the highest revenue "
    "generators — high-volume cheap items vs low-volume premium items.",

    "Product categories help segment revenue. If one category dominates "
    ">60% of revenue, the business has concentration risk.",

    "Slow-moving products (low quantity sold) may need promotions or "
    "should be discontinued to free up working capital.",

    # Customers
    "The Pareto Principle in sales: typically 20% of customers generate "
    "80% of revenue. Identify and retain these top customers.",

    "Customer churn is when a customer stops purchasing. "
    "If a regular customer hasn't bought in 90 days, they may be churning.",

    "City and state-level sales data reveals geographic concentration. "
    "Expanding to new cities is a growth lever if current cities are saturated.",

    # Payments & operations
    "Payment mode analysis reveals customer preferences. "
    "High cash payments may indicate difficulty accepting digital payments.",

    "Order status tracking: Delivered = successful, Pending = needs follow-up, "
    "Returned = possible product quality or logistics issue.",

    "High return rates (>5% of orders) signal product quality issues, "
    "wrong product sent, or misleading product descriptions.",

    # Trends
    "Seasonality: many businesses see peaks during festivals, "
    "year-end, or harvest seasons. Compare same periods year-over-year.",

    "A sales trend line with consistent week-over-week growth is healthy. "
    "Sudden drops need investigation — supply issues, competition, or market shift.",

    "Discounts should be monitored carefully. "
    "If average discount >15%, it may be eroding margins significantly.",

    # India-specific
    "In Indian retail, UPI and digital wallets have overtaken cash "
    "in urban markets. A high UPI share indicates a tech-savvy customer base.",

    "GST compliance: all invoices should have valid invoice IDs for "
    "tax filing. Missing invoice IDs may create compliance issues.",

    "Indian business peak seasons: Diwali (Oct-Nov), financial year-end "
    "(March), and back-to-school (June-July) drive significant sales spikes.",

    "Salesperson performance tracking helps identify top performers "
    "and those who may need training or support.",

    "Regional sales analysis by zone/state reveals where marketing "
    "budget should be concentrated for maximum ROI.",
]


# ── RAGEngine class ─────────────────────────────────────────
class RAGEngine:
    """
    Per-admin RAG engine.

    Usage:
        rag = RAGEngine(admin_id=5)
        rag.build_index(db_engine)          # call once per session
        context = rag.retrieve("top products")  # call at query time
    """

    def __init__(self, admin_id: int):
        self.admin_id   = admin_id
        self.chunks     : list[str] = []
        self.index      = None          # FAISS index
        self.embeddings = None          # np.ndarray  shape (N, dim)
        self._built     = False

    # ── Build ────────────────────────────────────────────────
    def build_index(self, db_engine=None) -> int:
        """
        Build / rebuild the FAISS index.
        Combines static knowledge + dynamic DB summaries.
        Returns the total number of chunks indexed.
        """
        if not FAISS_OK:
            return 0

        self.chunks = list(STATIC_KNOWLEDGE)  # start with static

        # Dynamic chunks from DB
        if db_engine is not None:
            self.chunks.extend(
                self._build_dynamic_chunks(db_engine)
            )

        model = _get_model()
        self.embeddings = model.encode(
            self.chunks,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine via inner-product
            show_progress_bar=False,
        ).astype("float32")

        dim        = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)   # Inner Product = cosine (normalised)
        self.index.add(self.embeddings)
        self._built = True
        return len(self.chunks)

    def _build_dynamic_chunks(self, engine) -> list[str]:
        """Pull aggregated summaries from MySQL and turn them into text chunks."""
        chunks = []
        p      = (self.admin_id,)
        try:
            # ── Total revenue / orders ───────────────────────
            kpi = pd.read_sql(
                "SELECT COALESCE(SUM(total_amount),0) AS rev, "
                "COUNT(*) AS orders, "
                "COALESCE(AVG(total_amount),0) AS aov "
                "FROM sales WHERE admin_id=%s", engine, params=p
            )
            if not kpi.empty:
                rev   = float(kpi["rev"].iloc[0])
                ords  = int(kpi["orders"].iloc[0])
                aov   = float(kpi["aov"].iloc[0])
                chunks.append(
                    f"Business summary: Total all-time revenue is "
                    f"₹{rev:,.0f} from {ords:,} orders. "
                    f"Average order value is ₹{aov:,.0f}."
                )

            # ── Top 5 products ───────────────────────────────
            prods = pd.read_sql(
                "SELECT p.product_name, SUM(s.total_amount) AS rev "
                "FROM sales s JOIN products p ON s.product_id=p.product_id "
                "WHERE s.admin_id=%s "
                "GROUP BY p.product_name ORDER BY rev DESC LIMIT 5",
                engine, params=p
            )
            if not prods.empty:
                lines = "; ".join(
                    f"{r['product_name']} (₹{r['rev']:,.0f})"
                    for _, r in prods.iterrows()
                )
                chunks.append(
                    f"Top 5 products by revenue for this business: {lines}."
                )

            # ── Top 5 customers ──────────────────────────────
            custs = pd.read_sql(
                "SELECT c.customer_name, SUM(s.total_amount) AS rev "
                "FROM sales s JOIN customers c ON s.customer_id=c.customer_id "
                "WHERE s.admin_id=%s "
                "GROUP BY c.customer_name ORDER BY rev DESC LIMIT 5",
                engine, params=p
            )
            if not custs.empty:
                lines = "; ".join(
                    f"{r['customer_name']} (₹{r['rev']:,.0f})"
                    for _, r in custs.iterrows()
                )
                chunks.append(
                    f"Top 5 customers by total spending: {lines}."
                )

            # ── Category breakdown ───────────────────────────
            cats = pd.read_sql(
                "SELECT cat.category_name, SUM(s.total_amount) AS rev "
                "FROM sales s "
                "JOIN products p   ON s.product_id  = p.product_id "
                "JOIN categories cat ON p.category_id = cat.category_id "
                "WHERE s.admin_id=%s "
                "GROUP BY cat.category_name ORDER BY rev DESC",
                engine, params=p
            )
            if not cats.empty:
                lines = "; ".join(
                    f"{r['category_name']} (₹{r['rev']:,.0f})"
                    for _, r in cats.iterrows()
                )
                chunks.append(f"Sales by product category: {lines}.")

            # ── Payment mode ─────────────────────────────────
            pay = pd.read_sql(
                "SELECT payment_mode, COUNT(*) AS cnt "
                "FROM sales WHERE admin_id=%s "
                "GROUP BY payment_mode ORDER BY cnt DESC",
                engine, params=p
            )
            if not pay.empty:
                lines = "; ".join(
                    f"{r['payment_mode']} ({r['cnt']} orders)"
                    for _, r in pay.iterrows()
                )
                chunks.append(f"Payment mode distribution: {lines}.")

            # ── Order status ─────────────────────────────────
            stat = pd.read_sql(
                "SELECT order_status, COUNT(*) AS cnt "
                "FROM sales WHERE admin_id=%s "
                "GROUP BY order_status ORDER BY cnt DESC",
                engine, params=p
            )
            if not stat.empty:
                lines = "; ".join(
                    f"{r['order_status']} ({r['cnt']})"
                    for _, r in stat.iterrows()
                )
                chunks.append(f"Order status breakdown: {lines}.")

            # ── Monthly trend (last 6 months) ────────────────
            monthly = pd.read_sql(
                "SELECT DATE_FORMAT(sale_date,'%%Y-%%m') AS m, "
                "SUM(total_amount) AS rev "
                "FROM sales WHERE admin_id=%s "
                "GROUP BY m ORDER BY m DESC LIMIT 6",
                engine, params=p
            )
            if not monthly.empty:
                lines = "; ".join(
                    f"{r['m']}: ₹{r['rev']:,.0f}"
                    for _, r in monthly.iterrows()
                )
                chunks.append(
                    f"Monthly revenue (last 6 months, newest first): {lines}."
                )

            # ── Top regions ──────────────────────────────────
            regions = pd.read_sql(
                "SELECT region, SUM(total_amount) AS rev "
                "FROM sales WHERE admin_id=%s AND region != 'Unknown' "
                "GROUP BY region ORDER BY rev DESC LIMIT 5",
                engine, params=p
            )
            if not regions.empty:
                lines = "; ".join(
                    f"{r['region']} (₹{r['rev']:,.0f})"
                    for _, r in regions.iterrows()
                )
                chunks.append(f"Top regions by revenue: {lines}.")

        except Exception as e:
            # Silently degrade — DB might not be available during tests
            chunks.append(
                f"[DB summary unavailable: {e}]"
            )

        return chunks

    # ── Retrieve ─────────────────────────────────────────────
    def retrieve(self, query: str, top_k: int = 4) -> str:
        """
        Retrieve the top_k most relevant chunks for a query.
        Returns a formatted string ready to inject into an LLM prompt.
        """
        if not self._built or not FAISS_OK or self.index is None:
            return ""

        model     = _get_model()
        q_vec     = model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")

        scores, indices = self.index.search(q_vec, min(top_k, len(self.chunks)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score > 0.2:   # relevance threshold
                results.append(self.chunks[idx])

        if not results:
            return ""

        context = "\n".join(f"• {c}" for c in results)
        return context

    # ── Add custom chunks ────────────────────────────────────
    def add_custom_chunks(self, texts: list[str]):
        """
        Add extra knowledge chunks at runtime (e.g., from uploaded PDFs,
        user-pasted notes, or previous conversation summaries).
        Rebuilds the index incrementally.
        """
        if not FAISS_OK:
            return

        model     = _get_model()
        new_embs  = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype("float32")

        self.chunks.extend(texts)

        if self.embeddings is None:
            self.embeddings = new_embs
            dim        = new_embs.shape[1]
            self.index = faiss.IndexFlatIP(dim)
        else:
            self.embeddings = np.vstack([self.embeddings, new_embs])

        self.index.add(new_embs)
        self._built = True

    # ── Semantic similarity score ────────────────────────────
    @staticmethod
    def similarity_score(text_a: str, text_b: str) -> float:
        """
        Cosine similarity between two texts using the same embedding model.
        Used by the BERT scorer to rate answer quality.
        Returns a value between 0 and 1.
        """
        model  = _get_model()
        embs   = model.encode(
            [text_a, text_b],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        score  = float(np.dot(embs[0], embs[1]))  # cosine (normalised)
        return round(max(0.0, min(1.0, score)), 3)


# ── Per-session cache (keyed by admin_id) ───────────────────
_rag_cache: dict[int, RAGEngine] = {}

def get_rag_engine(admin_id: int, db_engine=None, force_rebuild: bool = False) -> RAGEngine:
    """
    Return a cached RAGEngine for this admin.
    Rebuilds on first call or if force_rebuild=True.
    """
    global _rag_cache
    if admin_id not in _rag_cache or force_rebuild:
        engine = RAGEngine(admin_id)
        engine.build_index(db_engine)
        _rag_cache[admin_id] = engine
    return _rag_cache[admin_id]