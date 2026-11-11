"""
Unified Hybrid Conversational Agent Controller.
Connects:
1. Responsible AI Guardrails & PII Masking
2. Approach 1: Classical Rule-Based FSM
3. Approach 2: Modern Semantic Vector Retrieval
4. Automatic Latency Measurement & Audit Logging
"""

import time
import uuid
from engine.guardrails import check_safety_guardrails, redact_pii
from engine.rule_engine import RuleBasedSalonChatbot
from engine.semantic_engine import SemanticSalonRetriever
from database.db import log_chat_interaction, add_to_handover_queue


class HybridSalonAgent:
    """
    Central Orchestrator for Salon Customer Support.
    Provides dynamic engine switching (Rule-Based vs Semantic vs Hybrid)
    and full explainability trace generation for INT428 evaluation.
    """
    def __init__(self):
        self.rule_engine = RuleBasedSalonChatbot()
        self.semantic_engine = SemanticSalonRetriever(use_dense_embeddings=True)
        self.session_id = str(uuid.uuid4())[:8]

    def reset_session(self):
        """Resets dialogue state and session ID."""
        self.rule_engine.reset_state()
        self.session_id = str(uuid.uuid4())[:8]

    def handle_message(self, user_message: str, engine_mode="Hybrid") -> dict:
        """
        Processes incoming user message.
        engine_mode options: "Hybrid", "Approach 1 (Rule-Based)", "Approach 2 (Semantic)"
        """
        start_time = time.perf_counter()

        # Step 1: Responsible AI Guardrails Check
        is_safe, guard_type, guard_resp = check_safety_guardrails(user_message)
        if not is_safe:
            latency = (time.perf_counter() - start_time) * 1000
            log_chat_interaction(
                self.session_id, redact_pii(user_message), guard_resp,
                guard_type, 1.0, "Guardrail_Layer", round(latency, 2)
            )
            return {
                "response": guard_resp,
                "latency_ms": round(latency, 2),
                "intent": guard_type,
                "confidence": 1.0,
                "engine_used": "Responsible_AI_Guardrails",
                "trace": {
                    "guardrail_triggered": guard_type,
                    "safety_violation": True,
                    "action": "Immediate safe refusal and redirect"
                }
            }

        # Step 2: Route Based on Selected Engine Mode
        if engine_mode == "Approach 1 (Rule-Based)":
            result = self.rule_engine.process_message(user_message)
            resp = result["response"]
            intent = result["detected_intent"]
            conf = result["confidence"]
            trace = result["trace"]
            engine_label = "Approach 1 (Rule-Based FSM)"

        elif engine_mode == "Approach 2 (Semantic)":
            sem_result = self.semantic_engine.query(user_message)
            resp = sem_result["response"]
            conf = sem_result["confidence"]
            intent = "semantic_faq" if sem_result["matched_id"] else "fallback"
            trace = sem_result["trace"]
            engine_label = "Approach 2 (Semantic Retrieval)"

            if sem_result["needs_handover"]:
                add_to_handover_queue("Customer", user_message, reason="Semantic confidence below threshold")

        else:
            # Mode C: "Hybrid" (Best of Both Worlds)
            # If the FSM is already engaged in slot filling, continue slot filling
            if self.rule_engine.state.startswith("AWAITING_"):
                result = self.rule_engine.process_message(user_message)
                resp = result["response"]
                intent = result["detected_intent"]
                conf = result["confidence"]
                trace = result["trace"]
                engine_label = "Hybrid (Active FSM Slot-Filler)"
            else:
                # First check rule-based intent
                rule_intent, rule_conf, rule_trace = self.rule_engine.detect_intent(user_message)

                # Transactional intents go to Rule Engine / DB operations
                if rule_intent in ["book_appointment", "cancel_appointment", "view_booking", "lodge_complaint", "human_handover"]:
                    result = self.rule_engine.process_message(user_message)
                    resp = result["response"]
                    intent = result["detected_intent"]
                    conf = result["confidence"]
                    trace = result["trace"]
                    engine_label = "Hybrid -> Transactional FSM"
                else:
                    # Informational intents go to Semantic Retrieval
                    sem_result = self.semantic_engine.query(user_message, threshold=0.40)
                    if sem_result["confidence"] >= 0.40 and not sem_result["needs_handover"]:
                        resp = sem_result["response"]
                        conf = sem_result["confidence"]
                        intent = f"semantic_{sem_result['matched_id']}"
                        trace = sem_result["trace"]
                        engine_label = "Hybrid -> Semantic Retrieval"
                    else:
                        # Fallback to rule engine
                        result = self.rule_engine.process_message(user_message)
                        resp = result["response"]
                        intent = result["detected_intent"]
                        conf = result["confidence"]
                        trace = result["trace"]
                        engine_label = "Hybrid -> Fallback FSM"

        latency = (time.perf_counter() - start_time) * 1000

        # Step 3: Log conversation audit trail with PII redaction
        log_chat_interaction(
            self.session_id,
            redact_pii(user_message),
            resp,
            intent,
            round(conf, 3),
            engine_label,
            round(latency, 2)
        )

        return {
            "response": resp,
            "latency_ms": round(latency, 2),
            "intent": intent,
            "confidence": round(conf, 3),
            "engine_used": engine_label,
            "trace": trace
        }
