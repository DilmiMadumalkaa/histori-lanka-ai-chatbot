"""
Chat Interface for Historical Sites Chatbot
==========================================

Simple interactive interface for testing the RAG chatbot end-to-end
"""

import os
import sys
import json
import logging
import re
from typing import Optional, Dict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

DEFAULT_GPT_INSTRUCTIONS = (
    "Answer using only the retrieved context. "
    "If information is missing, explicitly say it is not available in retrieved sources. "
    "Prioritize factual historical details such as period, significance, and location. "
    "Do not invent citations or uncertain claims. "
    "If retrieved sources are about a different place than the user asked, state that mismatch and do not answer for the wrong place."
)

FOCUS_STOP_WORDS = {
    "tell", "me", "about", "what", "is", "are", "the", "a", "an", "of", "for", "in",
    "on", "to", "do", "does", "did", "please", "give", "explain", "describe", "summarize",
    "with", "from", "this", "that", "site", "historical", "history", "facts", "important",
    "why", "how", "where", "when", "which", "can", "you", "we", "have", "information",
    "details", "key", "quick", "concise", "factual", "keep", "grounded", "data", "dataset"
}

TARGET_BOUNDARY_WORDS = {
    "located", "location", "district", "province", "city", "town", "area",
    "nearby", "nearest", "distance", "km", "kilometer", "kilometers",
    "travel", "route", "from", "to", "in", "around", "near", "for",
}


class MockGPTGenerator:
    """Mock GPT generator for testing without Azure credentials"""
    
    RESPONSES = {
        "sigiriya": "Sigiriya is an impressive 5th-century rock fortress standing 147 meters tall in central Sri Lanka. Built by King Kasyapa I (477-495 CE), it served as a royal residence and defensive fortification. The site features remarkable architectural elements including an elaborate water garden system, magnificent frescoes on the rock face, and a palace complex on top. Archaeological evidence suggests it was later converted into a Buddhist monastery. Today, Sigiriya is recognized as a UNESCO World Heritage Site and stands as one of Asia's most impressive ancient fortified sites.",
        
        "kandy": "Kandy served as the last royal capital of Sri Lanka and remains culturally significant. The city is home to the Temple of the Tooth, which houses the sacred tooth relic of Buddha. This sacred Buddhist site attracts pilgrims from around the world. Kandy is surrounded by beautiful hills and gardens, most notably the Royal Botanical Garden of Peradeniya.",
        
        "galle": "Galle Fort is a prominent coastal fortress built through several centuries of European control. The fort reflects Dutch and British colonial architecture and engineering. It features fortification walls, historic buildings, and picturesque streets. The site is a UNESCO World Heritage Site and one of Sri Lanka's most visited historical attractions.",
        
        "anuradhapura": "Anuradhapura was the ancient capital of Sri Lanka and served as a major Buddhist center from approximately 380 BCE to 1017 CE. The city housed magnificent temples, stupas, and monasteries that made it one of Asia's greatest Buddhist centers. It remains a pilgrimage site, particularly for the sacred Bodhi Tree believed to be a descendant of the original tree under which Buddha attained enlightenment.",
        
        "polonnaruwa": "Polonnaruwa was a powerful medieval kingdom and important Buddhist center. The site contains well-preserved ancient structures including temples, stupas, and monasteries that showcase medieval architecture. Archaeological evidence reveals sophisticated water management systems and strategic urban planning.",
        
        "dambulla": "Dambulla Rock Temple is the largest cave temple complex in Sri Lanka, featuring five caves filled with Buddha statues and religious paintings. Built from the 1st century BCE onwards, the temple complex houses over 150 Buddha statues and intricate murals depicting scenes from Buddhist scriptures. The site is a UNESCO World Heritage Site and remains an active place of worship and pilgrimage.",
        
        "adam's peak": "Adam's Peak is a 2,243-meter-tall conical sacred mountain located in central Sri Lanka. It is famous for the Sri Pada, a 1.8-meter rock formation resembling a footprint near the summit. In Buddhist tradition, this footprint is believed to belong to the Buddha, while Hindu traditions associate it with Shiva or Hanuman. Christian and Islamic traditions connect it to Adam or St. Thomas the Apostle. The mountain is also known as Mount Malaya in Buddhist sources and remains a major pilgrimage destination.",
        
        "vessagiri": "Vessagiri (Issarasamanarama) is an ancient Buddhist forest monastery that is part of the ruins of Anuradhapura. Founded in the mid-3rd century BCE during King Devanampiya Tissa's reign, the monastery was expanded during King Kasyapa's rule (473-491 CE) to house about 500 monks. The site features rock shelters carved from local boulders and contains inscriptions in Brahmi script marking donor names. Today visitors can see the bare stones, though much of the original structure has been reused elsewhere.",
        
        "mihintale": "Mihintale is a sacred Buddhist mountain and monastery complex believed to be the site where Buddhism was introduced to Sri Lanka. According to legend, the Indian Buddhist missionary Mahinda arrived here in the 3rd century BCE and converted King Ashoka of Maurya to Buddhism. The site contains ancient stupas, rock shelters, and a monks' refectory. It remains an important pilgrimage destination and offers panoramic views of the surrounding landscape.",
        
        "temple": "Sri Lanka has many important Buddhist temples. The Temple of the Tooth in Kandy is the most sacred, housing a relic believed to be a tooth of Buddha. Other significant temples include those in Anuradhapura and Polonnaruwa. These temples remain active pilgrimage destinations and represent important aspects of Sri Lankan Buddhist heritage.",
        
        "default": "Sri Lanka contains numerous historically significant sites. Major destinations include ancient rock fortresses like Sigiriya, historic kingdoms such as Anuradhapura and Polonnaruwa, important Buddhist temples and sacred relics throughout the island, sacred mountains like Adam's Peak, and colonial forts built during European influence. Each site offers unique insights into Sri Lanka's rich cultural heritage spanning thousands of years."
    }
    
    def generate_response(self, user_query: str, context: str, **kwargs) -> Dict:
        """Generate mock response based on query keywords"""
        
        # Handle empty query error case
        if not user_query or not user_query.strip():
            return {
                "success": False,
                "error": "Query cannot be empty",
                "response": None,
                "quality": {"overall_score": 0.0, "rating": "invalid"}
            }
        
        query_lower = user_query.lower()
        response_text = self.RESPONSES["default"]
        
        # Keyword synonyms for better matching
        synonyms = {
            "sigiriya": ["sigiriya", "rock fortress", "lion rock", "kasyapa"],
            "anuradhapura": ["anuradhapura", "ancient capital", "bodhi tree"],
            "polonnaruwa": ["polonnaruwa", "medieval kingdom", "ruwanwella"],
            "kandy": ["kandy", "temple of tooth", "tooth relic", "last capital"],
            "galle": ["galle", "galle fort", "coastal fortress"],
            "dambulla": ["dambulla", "cave temple", "rock temple", "five caves"],
            "adam's peak": ["adam's peak", "adams peak", "sri pada", "sacred footprint", "sacred mountain"],
            "vessagiri": ["vessagiri", "issarasamanarama", "forest monastery"],
            "mihintale": ["mihintale", "mahinda", "buddhism introduced"],
            "temple": ["temple", "Buddhist temple", "shrine", "pagoda", "stupa", "relic"]
        }
        
        # Try to match query against all keywords
        for keyword, keyword_synonyms in synonyms.items():
            for synonym in keyword_synonyms:
                if synonym in query_lower:
                    if keyword in self.RESPONSES:
                        response_text = self.RESPONSES[keyword]
                        break
            if response_text != self.RESPONSES["default"]:
                break
        
        return {
            "success": True,
            "user_query": user_query,
            "response": response_text,
            "response_length": len(response_text),
            "tokens_used": len(response_text.split()),
            "model": "mock-gpt-4",
            "timestamp": datetime.now().isoformat(),
            "style": kwargs.get("style", "informative"),
            "temperature": kwargs.get("temperature", 0.7),
            "quality": {
                "overall_score": 0.75,
                "factors": {
                    "length_adequate": True,
                    "has_specifics": True,
                    "well_structured": True,
                    "uses_context": True,
                    "no_placeholder": True
                },
                "rating": "good"
            },
            "retrieval_method": "Mock Retriever",
            "context_length": len(context),
            "retrieved_sites_count": 2
        }

    def call_gpt_with_rag_context(
        self,
        user_query: str,
        rag_context: str,
        instructions: Optional[str] = None,
        **kwargs,
    ) -> Dict:
        """Step 9-compatible mock method using query + RAG context + optional instructions."""
        _ = instructions  # kept for API compatibility with real generator
        return self.generate_response(user_query=user_query, context=rag_context, **kwargs)


class ChatInterface:
    """Interactive chat interface for users"""
    
    def __init__(self, use_mock: bool = False):
        """Initialize chat interface"""
        self.use_mock = use_mock
        self.conversation_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize GPT generator, retriever, and evaluator"""
        # In mock mode, always use mock implementations first
        if self.use_mock:
            self.generator = MockGPTGenerator()
            logger.info("[+] Mock GPT Generator initialized")
            
            from rag_evaluation_simulator import MockRetriever
            self.retriever = MockRetriever()
            logger.info("[+] Mock Retriever initialized")
        else:
            try:
                from gpt41_mini_response_generator import ResponseGenerator
                self.generator = ResponseGenerator()
                logger.info("[+] GPT Response Generator initialized")
            except Exception as e:
                logger.warning(f"[-] GPT Generator failed: {e}")
                self.generator = None
            
            try:
                from pinecone_retrieval import PineconeRetrieverWithReranking
                self.retriever = PineconeRetrieverWithReranking()
                logger.info("[+] Pinecone Retriever initialized")
            except Exception as e:
                logger.warning(f"[-] Retriever failed: {e}")
                self.retriever = None
        
        try:
            from response_evaluator import ResponseEvaluator
            self.evaluator = ResponseEvaluator()
            logger.info("[+] Response Evaluator initialized")
        except Exception as e:
            logger.warning(f"[-] Evaluator failed: {e}")
            self.evaluator = None
        
        if not self.generator or not self.retriever:
            logger.error("Critical components failed to initialize")
            raise RuntimeError("Cannot initialize chat interface")

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"[^a-z0-9\s]", " ", (value or "").lower()).strip()

    def _extract_focus_terms(self, user_input: str):
        text = self._normalize_text(user_input)
        terms = [t for t in text.split() if t and t not in FOCUS_STOP_WORDS and len(t) > 2]
        return terms[:6]

    def _extract_focus_phrase(self, user_input: str) -> str:
        text = self._normalize_text(user_input)
        patterns = [
            r"(?:tell me about|about|describe|summarize|explain)\s+([a-z0-9\s]+)",
            r"(?:what is|where is|who is)\s+([a-z0-9\s]+)",
            r"(?:information on|facts about)\s+([a-z0-9\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip()
                tokens = [t for t in candidate.split() if t not in FOCUS_STOP_WORDS and len(t) > 2]
                if tokens:
                    return " ".join(tokens[:5])

        tokens = self._extract_focus_terms(user_input)
        return " ".join(tokens[:4])

    def _extract_target_place(self, user_input: str) -> str:
        """Extract explicit place phrase from common travel/location question patterns."""
        text = self._normalize_text(user_input)
        patterns = [
            r"(?:from|around|near|in)\s+([a-z0-9\s]{3,60})",
            r"(?:visit|about|to|for)\s+([a-z0-9\s]{3,60})",
            r"(?:is|are)\s+([a-z0-9\s]{3,60})\s+(?:located|in)",
            r"(?:district|province|city)\s+(?:is\s+)?([a-z0-9\s]{3,60})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            candidate = match.group(1).strip()
            raw_tokens = [t for t in candidate.split() if t]
            clipped_tokens = []
            for tok in raw_tokens:
                if tok in TARGET_BOUNDARY_WORDS:
                    break
                clipped_tokens.append(tok)

            tokens = [t for t in clipped_tokens if t not in FOCUS_STOP_WORDS and len(t) > 2]
            if tokens:
                return " ".join(tokens[:4])

        # Fallback: if query contains "from <place>"-style wording, try lexical tail extraction.
        tail_match = re.search(r"(?:from|around|near)\s+([a-z0-9\s]{3,40})", text)
        if tail_match:
            tail_tokens = []
            for tok in tail_match.group(1).strip().split():
                if tok in TARGET_BOUNDARY_WORDS:
                    break
                if tok not in FOCUS_STOP_WORDS and len(tok) > 2:
                    tail_tokens.append(tok)
            if tail_tokens:
                return " ".join(tail_tokens[:4])
        return ""

    def _query_requires_strict_place_match(self, user_input: str) -> bool:
        text = self._normalize_text(user_input)
        triggers = [
            "nearby",
            "nearest",
            "from",
            "province",
            "district",
            "city",
            "located",
            "distance",
            "kilometer",
            "km",
            "travel from",
        ]
        return any(t in text for t in triggers)

    def _is_nearby_query(self, user_input: str) -> bool:
        text = self._normalize_text(user_input)
        return ("nearby" in text or "nearest" in text) and ("from" in text or "around" in text or "near" in text)

    def _build_nearby_response(self, selected_results, target_place: str) -> str:
        target_tokens = set((target_place or "").split())
        names = []
        for item in selected_results or []:
            name = (item.get("site_name") or "").strip()
            if not name:
                continue
            name_norm_tokens = set(self._normalize_text(name).split())
            if target_tokens and target_tokens.issubset(name_norm_tokens):
                continue
            if name not in names:
                names.append(name)

        if not names:
            return (
                f"I could not find reliable nearby-place entries for '{target_place}' in the retrieved sources. "
                "Please try the exact place name or ask for a broader region."
            )

        return (
            f"Based on retrieved context for {target_place.title()}, nearby/related places include: "
            + ", ".join(names[:3])
            + ". Exact inter-site distance in km is not available in current sources."
        )

    def _retrieval_matches_target(self, selected_results, target_place: str, strict_site_only: bool = False) -> bool:
        if not target_place:
            return True
        target_tokens = [t for t in target_place.split() if t]
        if not target_tokens:
            return True

        for item in selected_results or []:
            site_name = self._normalize_text(item.get("site_name", ""))
            if site_name and all(tok in site_name for tok in target_tokens):
                return True
            if strict_site_only:
                continue
            chunk_text = self._normalize_text(item.get("chunk_text", ""))
            if chunk_text and len(target_tokens) <= 2 and all(tok in chunk_text for tok in target_tokens):
                return True
        return False

    def _lexical_metadata_fallback(self, focus_terms, focus_phrase: str = "", top_k: int = 3):
        metadata_cache = getattr(self.retriever, "metadata_cache", {}) or {}
        if not metadata_cache or not focus_terms:
            return []

        min_required = 1 if len(focus_terms) <= 2 else 2
        candidates = []
        for item in metadata_cache.values():
            site_name = item.get("site_name") or item.get("title") or "Unknown"
            chunk_text = (
                item.get("chunk_text")
                or item.get("text")
                or item.get("rag_text")
                or ""
            )
            haystack = self._normalize_text(f"{site_name} {chunk_text}")
            if not haystack:
                continue

            site_norm = self._normalize_text(site_name)
            phrase_tokens = [t for t in (focus_phrase or "").split() if t]
            site_phrase_match = bool(
                focus_phrase and (
                    focus_phrase in site_norm
                    or (phrase_tokens and all(t in site_norm for t in phrase_tokens))
                )
            )

            matched = sum(1 for term in focus_terms if term in haystack)
            if matched >= min_required:
                candidates.append({
                    "chunk_id": item.get("chunk_id") or item.get("id") or "fallback",
                    "site_name": site_name,
                    "category": item.get("category", item.get("site_type", "Unknown")),
                    "source": item.get("source", "Unknown"),
                    "chunk_text": chunk_text,
                    "scores": {
                        "semantic": 0.0,
                        "keyword": round(matched / max(len(focus_terms), 1), 4),
                        "metadata": 0.5,
                        "combined": round(0.35 + 0.1 * matched + (0.25 if site_phrase_match else 0.0), 4),
                    },
                })

        candidates.sort(key=lambda x: x["scores"]["combined"], reverse=True)
        return candidates[:top_k]

    def _is_focus_match(self, result: Dict, focus_terms, focus_phrase: str = "") -> bool:
        if not focus_terms:
            return True

        site_name = self._normalize_text(result.get("site_name", ""))
        chunk_text = self._normalize_text(result.get("chunk_text", ""))
        if not site_name and not chunk_text:
            return False

        if focus_phrase:
            phrase_tokens = [t for t in focus_phrase.split() if t]
            if focus_phrase in site_name or (phrase_tokens and all(t in site_name for t in phrase_tokens)):
                return True

            # For explicit site queries, avoid accepting chunk-only mentions from other sites.
            if len(phrase_tokens) <= 3:
                return False

        haystack = f"{site_name} {chunk_text}"

        matched = sum(1 for term in focus_terms if term in haystack)
        min_required = 1 if len(focus_terms) <= 2 else 2
        return matched >= min_required

    def _format_context(self, results):
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"📍 Source {i}: {result.get('site_name', 'Unknown')}\n"
                f"Category: {result.get('category', 'Unknown')}\n"
                f"Relevance Score: {result.get('scores', {}).get('combined', 0):.1%}\n"
                f"\n{result.get('chunk_text', '')}\n"
            )
        return "\n" + "=" * 70 + "\n".join(context_parts)

    def _retrieve_context_with_focus(self, user_input: str, top_k: int = 3):
        raw = self.retriever.retrieve_with_reranking(user_input, top_k=top_k * 3, rerank_top_k=top_k * 3)
        results = raw.get("results", [])
        focus_terms = self._extract_focus_terms(user_input)
        focus_phrase = self._extract_focus_phrase(user_input)

        focused_results = [r for r in results if self._is_focus_match(r, focus_terms, focus_phrase)]
        if focus_terms and focused_results:
            selected = focused_results[:top_k]
            focused_mode = True
        else:
            selected = results[:top_k]
            focused_mode = False

        if focus_terms and not focused_results:
            fallback_results = self._lexical_metadata_fallback(focus_terms, focus_phrase, top_k=top_k)
            if fallback_results:
                selected = fallback_results
                focused_mode = True

        # If we extracted a probable target but retrieved sources don't mention it,
        # pass an explicit mismatch context to prevent answering from unrelated sites.
        if focus_terms and not selected:
            focus_label = " ".join(focus_terms)
            context = (
                "No retrieved source explicitly matches the requested place in the user question.\n"
                f"Requested focus terms: {focus_label}\n"
                "Do not answer with facts from a different site. State that matching data was not found."
            )
            return {
                "context": context,
                "selected_results": [],
                "focused_mode": True,
                "focus_terms": focus_terms,
                "focus_phrase": focus_phrase,
            }

        context = self._format_context(selected)
        return {
            "context": context,
            "selected_results": selected,
            "focused_mode": focused_mode,
            "focus_terms": focus_terms,
            "focus_phrase": focus_phrase,
        }
    
    def get_response(self, user_input: str, style: str = "informative") -> Dict:
        """Get response to user query"""
        
        if not user_input.strip():
            return {"error": "Empty query"}
        
        try:
            # Step 1: Retrieve context
            logger.info(f"[*] Processing: {user_input[:50]}...")
            
            if self.retriever:
                retrieval = self._retrieve_context_with_focus(user_input, top_k=3)
                context = retrieval["context"]
                logger.info(f"[+] Retrieved context ({len(context)} chars)")
            else:
                context = ""
                retrieval = {"selected_results": []}
                logger.warning("[-] No retriever available")
            
            # Step 2: Generate response
            target_place = self._extract_target_place(user_input)
            strict_match_needed = self._query_requires_strict_place_match(user_input)
            target_match = self._retrieval_matches_target(
                retrieval.get("selected_results", []),
                target_place,
                strict_site_only=strict_match_needed,
            )

            if self.generator and self._is_nearby_query(user_input) and target_place and target_match:
                nearby_msg = self._build_nearby_response(retrieval.get("selected_results", []), target_place)
                result = {
                    "success": True,
                    "user_query": user_input,
                    "response": nearby_msg,
                    "response_length": len(nearby_msg),
                    "tokens_used": len(nearby_msg.split()),
                    "model": "retrieval-nearby-guard",
                    "timestamp": datetime.now().isoformat(),
                    "style": style,
                    "temperature": 0.0,
                }
                logger.info("[+] Nearby query answered via retrieval guard")
            elif self.generator and retrieval.get("selected_results") and (not strict_match_needed or target_match):
                result = self.generator.call_gpt_with_rag_context(
                    user_query=user_input,
                    rag_context=context,
                    instructions=DEFAULT_GPT_INSTRUCTIONS,
                    style=style,
                    temperature=0.7,
                    max_tokens=1000
                )
                logger.info(f"[+] Response generated ({result.get('response_length', 0)} chars)")
            elif self.generator and strict_match_needed and target_place and not target_match:
                fallback_msg = (
                    f"I could not find retrieved records that clearly match '{target_place}' for this query. "
                    "Please try the exact site/place name or rephrase your question."
                )
                result = {
                    "success": True,
                    "user_query": user_input,
                    "response": fallback_msg,
                    "response_length": len(fallback_msg),
                    "tokens_used": len(fallback_msg.split()),
                    "model": "retrieval-guard",
                    "timestamp": datetime.now().isoformat(),
                    "style": style,
                    "temperature": 0.0,
                }
            elif self.generator and retrieval.get("focus_terms"):
                focus_label = " ".join(retrieval.get("focus_terms", []))
                fallback_msg = (
                    f"I could not find matching retrieved records for '{focus_label}' in the current knowledge base. "
                    "Please try a more specific site name or rephrase the question."
                )
                result = {
                    "success": True,
                    "user_query": user_input,
                    "response": fallback_msg,
                    "response_length": len(fallback_msg),
                    "tokens_used": len(fallback_msg.split()),
                    "model": "retrieval-guard",
                    "timestamp": datetime.now().isoformat(),
                    "style": style,
                    "temperature": 0.0,
                }
            else:
                result = {
                    "success": False,
                    "error": "Generator not available",
                    "user_query": user_input
                }

            # Attach retrieval metadata for API/UI diagnostics.
            result["retrieved_sites_count"] = len(retrieval.get("selected_results", []))
            result["retrieved_sites"] = [
                item.get("site_name", "Unknown")
                for item in retrieval.get("selected_results", [])
            ]
            
            # Step 3: Evaluate response (optional)
            if result.get("success") and self.evaluator:
                evaluation = self.evaluator.evaluate_response(
                    user_query=user_input,
                    response=result["response"],
                    context=context
                )
                result["evaluation"] = evaluation
                logger.info(f"[+] Quality score: {evaluation.get('overall_score', 'N/A')}")
            
            # Store in history
            self.conversation_history.append({
                "user": user_input,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_query": user_input
            }
    
    def display_response(self, result: Dict):
        """Display response in user-friendly format"""
        
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            print(f"\n❌ Error: {error}\n")
            return
        
        # Main response
        print("\n" + "=" * 70)
        print("RESPONSE")
        print("=" * 70)
        print(result["response"])
        print("=" * 70)
        
        # Quality info
        if "evaluation" in result:
            eval_data = result["evaluation"]
            print(f"\n📊 Quality Assessment:")
            print(f"  Score: {eval_data['overall_score']}/1.0 ({eval_data['quality_rating']})")
            
            # Show key metrics
            metrics = eval_data.get("metrics", {})
            print(f"  Relevance: {metrics.get('relevance', {}).get('score', 'N/A')}")
            print(f"  Grounding: {metrics.get('factual_grounding', {}).get('score', 'N/A')}")
            print(f"  Completeness: {metrics.get('completeness', {}).get('score', 'N/A')}")
            
            # Show recommendations if quality is low
            if eval_data['overall_score'] < 0.7:
                print(f"\n💡 Suggestions:")
                for rec in eval_data.get("recommendations", [])[:3]:
                    print(f"  • {rec}")
        
        # Token usage
        if "tokens_used" in result:
            print(f"\n⚡ Tokens used: {result['tokens_used']}")
        
        print()
    
    def interactive_mode(self):
        """Run interactive chat mode"""
        
        print("\n" + "=" * 70)
        print("HISTORICAL SITES CHATBOT - INTERACTIVE MODE")
        print("=" * 70)
        print("Ask questions about Sri Lankan historical sites")
        print("Type 'quit' to exit, 'style' to change response style")
        print("Type 'history' to see conversation, 'export' to save")
        print("=" * 70 + "\n")
        
        current_style = "informative"
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == "quit":
                    print("\nGoodbye!")
                    break
                
                if user_input.lower() == "history":
                    self.show_conversation_history()
                    continue
                
                if user_input.lower() == "export":
                    self.export_conversation()
                    continue
                
                if user_input.lower().startswith("style"):
                    parts = user_input.split()
                    if len(parts) > 1:
                        current_style = parts[1]
                        print(f"Response style changed to: {current_style}\n")
                    continue
                
                if not user_input:
                    continue
                
                # Get and display response
                result = self.get_response(user_input, style=current_style)
                self.display_response(result)
                
            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    
    def show_conversation_history(self):
        """Display conversation history"""
        
        print("\n" + "=" * 70)
        print("CONVERSATION HISTORY")
        print("=" * 70)
        
        if not self.conversation_history:
            print("(empty)")
            return
        
        for i, exchange in enumerate(self.conversation_history, 1):
            print(f"\n[Turn {i}]")
            print(f"Q: {exchange['user'][:70]}...")
            
            result = exchange['result']
            if result.get('success'):
                print(f"A: {result.get('response', '')[:100]}...")
                if 'evaluation' in result:
                    score = result['evaluation']['overall_score']
                    print(f"   Quality: {score}/1.0")
            else:
                print(f"A: (Error: {result.get('error', 'Unknown')})")
        
        print("\n" + "=" * 70 + "\n")
    
    def export_conversation(self, filename: str = None) -> str:
        """Export conversation to JSON"""
        
        if not filename:
            filename = f"chat_export_{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "exchanges": []
        }
        
        for exchange in self.conversation_history:
            data["exchanges"].append({
                "user_query": exchange['user'],
                "response": exchange['result'].get('response', ''),
                "success": exchange['result'].get('success', False),
                "quality_score": exchange['result'].get('evaluation', {}).get('overall_score'),
                "timestamp": exchange['timestamp']
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n[+] Conversation exported to {filename}\n")
        return filename
    
    def get_statistics(self) -> Dict:
        """Get conversation statistics"""
        
        if not self.conversation_history:
            return {"turns": 0}
        
        successful = sum(1 for e in self.conversation_history if e['result'].get('success'))
        qualities = [
            e['result'].get('evaluation', {}).get('overall_score', 0)
            for e in self.conversation_history
            if e['result'].get('evaluation')
        ]
        
        return {
            "total_turns": len(self.conversation_history),
            "successful_responses": successful,
            "average_quality": round(sum(qualities) / len(qualities), 2) if qualities else 0,
            "total_tokens": sum(
                e['result'].get('tokens_used', 0)
                for e in self.conversation_history
            ),
            "session_duration": f"{(datetime.now() - datetime.fromisoformat(self.conversation_history[0]['timestamp'])).seconds}s"
            if self.conversation_history else "0s"
        }


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Historical Sites Chatbot Interface")
    parser.add_argument("--mock", action="store_true", help="Use mock retriever")
    parser.add_argument("--query", type=str, help="Single query mode")
    parser.add_argument("--style", default="informative", help="Response style")
    
    args = parser.parse_args()
    
    try:
        # Initialize chat interface
        chat = ChatInterface(use_mock=args.mock)
        logger.info("Chat interface ready")
        
        if args.query:
            # Single query mode
            result = chat.get_response(args.query, style=args.style)
            chat.display_response(result)
        else:
            # Interactive mode
            chat.interactive_mode()
            
            # Show final statistics
            stats = chat.get_statistics()
            print(f"\nSession Statistics: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
