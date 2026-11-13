"""
Approach 2: Modern Semantic AI & Embedding Retrieval Engine (Unit V & VI).
Implements:
1. TF-IDF & Dense Sentence-Transformer Semantic Vector Search
2. Cosine Similarity Matching over FAQ & Service Knowledge Base
3. Confidence Thresholding, Source Citation & Fallback Triggering
"""

import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_base.json")


class SemanticSalonRetriever:
    """
    Semantic Retrieval Engine for FAQ & Domain Question Answering.
    Supports both TF-IDF Vector Space Model and Dense Embeddings.
    """
    def __init__(self, use_dense_embeddings=None):
        if use_dense_embeddings is None:
            use_dense_embeddings = os.environ.get("USE_DENSE_EMBEDDINGS", "false").lower() in ("1", "true")
        self.use_dense = use_dense_embeddings
        self.documents = []
        self.doc_metadata = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.sentence_model = None
        self.dense_embeddings = None

        self._build_corpus()
        self._init_tfidf()
        if self.use_dense:
            self._init_dense()

    def _build_corpus(self):
        """Constructs knowledge corpus from knowledge_base.json."""
        if not os.path.exists(KB_PATH):
            return

        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)

        # 1. Index FAQs (Question + Answer for richer semantic coverage)
        for i, faq in enumerate(kb.get("faqs", [])):
            self.documents.append(f"{faq['question']} {faq['answer']}")
            self.doc_metadata.append({
                "type": "faq",
                "id": f"FAQ-{i+1}",
                "question": faq["question"],
                "answer": faq["answer"],
                "source": "Salon Knowledge Base > FAQs"
            })

        # 2. Index Operating Info & Policies
        s_info = kb.get("salon_info", {})
        hrs = s_info.get("operating_hours", {})
        hrs_text = f"Opening and closing hours timings: Monday-Friday {hrs.get('monday', '9:00-21:00')}, Saturday-Sunday {hrs.get('saturday', '8:30-21:30')}. Address: {s_info.get('address')} Phone: {s_info.get('contact_phone')}."
        self.documents.append(hrs_text)
        self.doc_metadata.append({
            "type": "info",
            "id": "INFO-1",
            "question": "What are your opening hours and location?",
            "answer": f"⏰ **Opening Hours:** Mon-Fri 9:00 AM – 9:00 PM, Sat-Sun 8:30 AM – 9:30 PM.\n📍 **Address:** {s_info.get('address')}",
            "source": "Salon Information & Policies"
        })

        # 2. Index Services
        for s in kb.get("services", []):
            desc = s.get("description", f"{s['category']} service at Razors-n-scissors.")
            service_text = f"{s['name']}: {desc} Category: {s['category']}, Price: ₹{s['price_inr']}, Duration: {s['duration_minutes']} minutes."
            self.documents.append(service_text)
            self.doc_metadata.append({
                "type": "service",
                "id": s["id"],
                "question": f"How much is {s['name']} and what does it include?",
                "answer": f"💈 **{s['name']}** — ₹{int(s['price_inr'])} (approx. {s['duration_minutes']} mins).",
                "source": f"Salon Service Catalog > {s['category']}"
            })

        # 3. Index Barbers (optional — KB may not have barbers)
        for b in kb.get("barbers", []):
            specs = ", ".join(b.get("specialties", []))
            title = b.get("title", "Stylist")
            exp = b.get("experience_years", "")
            rating = b.get("rating", "")
            barber_text = f"{b['name']}, {title}, {exp} years experience, rating {rating}. Specialties: {specs}."
            self.documents.append(barber_text)
            self.doc_metadata.append({
                "type": "barber",
                "id": b.get("id", b["name"]),
                "question": f"Who is {b['name']} and what are their styling specialties?",
                "answer": f"✂️ **{b['name']}** ({title}), {exp} yrs exp, {rating}⭐. Specialties: {specs}.",
                "source": "Salon Staff Profiles"
            })

    def _init_tfidf(self):
        """Initializes TF-IDF statistical vector space model."""
        if not self.documents:
            return
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents)

    def _init_dense(self):
        """Initializes lightweight pre-trained dense sentence transformer."""
        try:
            from sentence_transformers import SentenceTransformer
            try:
                # Use cached local weights to avoid network latency/timeout
                self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            except Exception:
                self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.dense_embeddings = self.sentence_model.encode(self.documents, convert_to_numpy=True, normalize_embeddings=True)
        except Exception:
            # Graceful fallback to TF-IDF if offline or loading fails
            self.use_dense = False
            self.sentence_model = None

    def retrieve_tfidf(self, query: str, top_k=3):
        """Computes TF-IDF cosine similarity."""
        if not self.tfidf_vectorizer:
            return []
        query_vec = self.tfidf_vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "score": float(sims[idx]),
                "meta": self.doc_metadata[idx]
            })
        return results

    def retrieve_dense(self, query: str, top_k=3):
        """Computes Dense Sentence-Transformer cosine similarity."""
        if not self.use_dense or self.sentence_model is None or self.dense_embeddings is None:
            return self.retrieve_tfidf(query, top_k)

        query_emb = self.sentence_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        sims = np.dot(self.dense_embeddings, query_emb.T).flatten()
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "score": float(sims[idx]),
                "meta": self.doc_metadata[idx]
            })
        return results

    def query(self, user_query: str, threshold=None) -> dict:
        """
        Executes semantic retrieval with confidence score and explainability provenance.
        """
        if threshold is None:
            threshold = 0.35 if self.use_dense else 0.12
        # Get both dense and tf-idf for comparative analysis
        dense_results = self.retrieve_dense(user_query, top_k=3)
        tfidf_results = self.retrieve_tfidf(user_query, top_k=3)

        best_match = dense_results[0] if dense_results else None
        conf = best_match["score"] if best_match else 0.0

        trace = {
            "approach": "Semantic Vector Retrieval (Approach 2)",
            "user_query": user_query,
            "dense_score": conf,
            "tfidf_score": tfidf_results[0]["score"] if tfidf_results else 0.0,
            "top_candidates": [
                {
                    "rank": i+1,
                    "doc_id": r["meta"]["id"],
                    "question_matched": r["meta"]["question"],
                    "score": round(r["score"], 4),
                    "source": r["meta"]["source"]
                } for i, r in enumerate(dense_results)
            ]
        }

        if best_match and conf >= threshold:
            response_text = best_match["meta"]["answer"]
            source = best_match["meta"]["source"]
            return {
                "response": f"{response_text}\n\n*📚 Source: {source} (Confidence: {conf*100:.1f}%)*",
                "confidence": conf,
                "matched_id": best_match["meta"]["id"],
                "trace": trace,
                "needs_handover": False
            }
        else:
            return {
                "response": "I could not find a confident match for your inquiry in our salon guidelines. Would you like me to connect you with our human salon manager?",
                "confidence": conf,
                "matched_id": None,
                "trace": trace,
                "needs_handover": True
            }
