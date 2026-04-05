"""
Response Quality Evaluator
==========================
Step 11: Evaluate GPT responses for quality, accuracy, and helpfulness

Metrics include: relevance, grounding, completeness, coherence, hallucination detection
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ResponseEvaluator:
    """Evaluate response quality across multiple dimensions"""
    
    def __init__(self):
        """Initialize evaluator"""
        self.metrics = {}
    
    def evaluate_response(
        self,
        user_query: str,
        response: str,
        context: str,
        retrieved_chunks: List[Dict] = None,
        reference_answer: str = None
    ) -> Dict:
        """
        Comprehensive response evaluation
        
        Args:
            user_query: Original user question
            response: Generated response from GPT
            context: Retrieved context used
            retrieved_chunks: List of retrieved document chunks with scores
            reference_answer: Ground truth answer (optional)
        
        Returns:
            Dictionary with evaluation metrics and quality assessment
        """
        
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "query": user_query,
            "response_length": len(response),
            "metrics": {}
        }
        
        # 1. Relevance Score
        evaluation["metrics"]["relevance"] = self._evaluate_relevance(
            user_query, response, context
        )
        
        # 2. Factual Grounding
        evaluation["metrics"]["factual_grounding"] = self._evaluate_factual_grounding(
            response, context
        )
        
        # 3. Completeness
        evaluation["metrics"]["completeness"] = self._evaluate_completeness(
            user_query, response, context
        )
        
        # 4. Coherence and Quality
        evaluation["metrics"]["coherence"] = self._evaluate_coherence(response)
        
        # 5. Hallucination Risk
        evaluation["metrics"]["hallucination_risk"] = self._detect_hallucination(
            response, context
        )
        
        # 6. Citation Density
        evaluation["metrics"]["citation_quality"] = self._evaluate_citations(
            response, context
        )
        
        # 7. Specificity
        evaluation["metrics"]["specificity"] = self._evaluate_specificity(response)
        
        # 8. Length Appropriateness
        evaluation["metrics"]["length_appropriateness"] = self._evaluate_length(
            response, user_query
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(evaluation["metrics"])
        evaluation["overall_score"] = overall_score
        evaluation["quality_rating"] = self._rate_quality(overall_score)
        
        # Add recommendations
        evaluation["recommendations"] = self._generate_recommendations(evaluation["metrics"])
        
        return evaluation
    
    def _evaluate_relevance(self, query: str, response: str, context: str) -> Dict:
        """Evaluate how well response addresses the query"""
        
        score = 0.0
        factors = {}
        
        # Check if response addresses query topic
        query_keywords = self._extract_keywords(query)
        response_has_keywords = sum(1 for kw in query_keywords if kw.lower() in response.lower())
        keyword_coverage = response_has_keywords / len(query_keywords) if query_keywords else 0
        factors["keyword_coverage"] = keyword_coverage
        score += keyword_coverage * 0.4
        
        # Check if response is focused (not going off-topic)
        context_keywords = self._extract_keywords(context)
        response_relevance = sum(1 for kw in context_keywords if kw.lower() in response.lower())
        response_relevance /= len(context_keywords) if context_keywords else 0
        factors["context_alignment"] = response_relevance
        score += response_relevance * 0.3
        
        # Check length appropriateness for query
        if len(response) > 100:
            factors["adequate_length"] = True
            score += 0.3
        else:
            factors["adequate_length"] = False
        
        return {
            "score": round(min(score, 1.0), 2),
            "factors": factors
        }
    
    def _evaluate_factual_grounding(self, response: str, context: str) -> Dict:
        """Check if response is grounded in provided context"""
        
        score = 0.0
        factors = {}
        
        # Extract specific facts (numbers, dates, names)
        response_facts = self._extract_facts(response)
        context_facts = self._extract_facts(context)
        
        # Check what percentage of response facts are in context
        grounded_facts = sum(1 for fact in response_facts if fact in context_facts)
        grounding_ratio = grounded_facts / len(response_facts) if response_facts else 1.0
        factors["fact_grounding"] = grounding_ratio
        score += grounding_ratio * 0.6
        
        # Check for citation patterns
        has_citations = any(pattern in response for pattern in ["source", "according", "evidence", "documented"])
        factors["explicit_citations"] = has_citations
        score += 0.2 if has_citations else 0.1
        
        # Check for uncertainty markers when appropriate
        has_appropriate_uncertainty = ("unclear" in response.lower() and len(response_facts) == 0) or (
            len(response_facts) > 0
        )
        factors["uncertainty_markers"] = has_appropriate_uncertainty
        score += 0.2
        
        return {
            "score": round(min(score, 1.0), 2),
            "factors": factors
        }
    
    def _evaluate_completeness(self, query: str, response: str, context: str) -> Dict:
        """Check if response covers main aspects of the query"""
        
        score = 0.5  # Base score
        factors = {}
        
        # Check for multiple aspects if query seems complex
        query_aspects = self._identify_query_aspects(query)
        response_aspects = sum(1 for aspect in query_aspects if aspect.lower() in response.lower())
        aspect_coverage = response_aspects / len(query_aspects) if query_aspects else 1.0
        factors["aspect_coverage"] = aspect_coverage
        score += aspect_coverage * 0.3
        
        # Check for depth of explanation
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        factors["explanation_depth"] = "deep" if avg_sentence_length > 15 else "moderate" if avg_sentence_length > 8 else "shallow"
        if avg_sentence_length > 12:
            score += 0.2
        
        # Check if follow-up questions could be answered with this response
        has_good_context = len(response) > 150 and response.count(".") > 3
        factors["context_for_followup"] = has_good_context
        score += 0.15 if has_good_context else 0.05
        
        return {
            "score": round(min(score, 1.0), 2),
            "factors": factors
        }
    
    def _evaluate_coherence(self, response: str) -> Dict:
        """Evaluate writing quality and coherence"""
        
        score = 0.0
        factors = {}
        
        # Grammar and structure check (basic)
        sentences = [s.strip() for s in response.split(".") if s.strip()]
        well_formed_sentences = sum(1 for s in sentences if len(s.split()) > 3)
        factors["well_formed_sentences"] = well_formed_sentences / len(sentences) if sentences else 0
        score += factors["well_formed_sentences"] * 0.3
        
        # Check for logical flow (transitions between ideas)
        transitions = ["therefore", "however", "because", "additionally", "furthermore", "as a result"]
        has_transitions = any(t in response.lower() for t in transitions)
        factors["has_transitions"] = has_transitions
        score += 0.25 if has_transitions else 0.1
        
        # No obvious repetition
        words = response.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        factors["lexical_diversity"] = round(unique_ratio, 2)
        score += min(unique_ratio, 0.45)
        
        # Proper paragraph structure
        paragraphs = [p.strip() for p in response.split("\n") if p.strip()]
        has_structure = len(paragraphs) > 1 or response.count("\n") > 0 or len(response) > 300
        factors["has_structure"] = has_structure
        score += 0.15 if has_structure else 0.05
        
        return {
            "score": round(min(score, 1.0), 2),
            "factors": factors
        }
    
    def _detect_hallucination(self, response: str, context: str) -> Dict:
        """Detect potential hallucinations or made-up information"""
        
        risk_level = "low"
        factors = {}
        confidence = 1.0
        
        # Check for unsupported claims
        risky_patterns = [
            (r"(?:definitely|certainly|undoubtedly|proven)", "too_certain"),
            (r"(?:all|every|always|never)", "overgeneralization"),
            (r"(?:secret|hidden|new discovery)", "extraordinary_claims")
        ]
        
        hallucination_indicators = 0
        for pattern, indicator_type in risky_patterns:
            import re
            if re.search(pattern, response, re.IGNORECASE):
                hallucination_indicators += 1
                factors[indicator_type] = True
        
        # Check if response has specific unsupported details
        response_specifics = self._extract_specific_claims(response)
        context_specifics = self._extract_specific_claims(context)
        unsupported = sum(1 for claim in response_specifics if claim not in context_specifics)
        
        factors["unsupported_claims"] = unsupported
        
        if hallucination_indicators > 0 or unsupported > 2:
            risk_level = "medium"
            confidence = 0.6
        elif hallucination_indicators > 0 or unsupported > 0:
            risk_level = "low-medium"
            confidence = 0.75
        
        return {
            "risk_level": risk_level,
            "confidence": confidence,
            "indicators_found": hallucination_indicators,
            "factors": factors
        }
    
    def _evaluate_citations(self, response: str, context: str) -> Dict:
        """Evaluate quality and density of citations"""
        
        score = 0.5
        factors = {}
        
        citation_markers = [
            "source", "according to", "documented", "evidence shows",
            "research indicates", "studies show", "historically", "archaeologically",
            "the record", "contemporary accounts"
        ]
        
        citation_count = sum(1 for marker in citation_markers if marker.lower() in response.lower())
        factors["citation_count"] = citation_count
        
        # Citation density (relative to response length)
        words = len(response.split())
        citation_density = citation_count / (words / 100) if words > 0 else 0
        factors["citation_density"] = round(citation_density, 2)
        
        if citation_density > 0.5:
            score = 0.9
        elif citation_density > 0.2:
            score = 0.7
        elif citation_density > 0:
            score = 0.5
        else:
            score = 0.2
        
        # Implicit context usage
        context_match = sum(
            1 for word in set(context.lower().split())
            if len(word) > 4 and word in response.lower()
        )
        factors["implicit_context_use"] = context_match
        
        if context_match > 3:
            score = min(score + 0.15, 1.0)
        
        return {
            "score": round(score, 2),
            "factors": factors
        }
    
    def _evaluate_specificity(self, response: str) -> Dict:
        """Check response specificity vs. generality"""
        
        score = 0.0
        factors = {}
        
        # Specific markers: named entities, dates, numbers
        import re
        has_dates = bool(re.search(r'\d{3,4}(?:\s+(?:CE|BCE|AD|BC|century))?', response))
        has_numbers = bool(re.search(r'\d+(?:\s*(?:meters|feet|kilometers|years))?', response))
        has_specific_names = any(char.isupper() for char in response)
        
        factors["has_dates"] = has_dates
        factors["has_measurements"] = has_numbers
        factors["has_named_entities"] = has_specific_names
        
        specificity_count = sum([has_dates, has_numbers, has_specific_names])
        score = specificity_count / 3.0
        
        # Check for generic phrases that indicate lack of specificity
        generic_phrases = ["it is", "this is", "there are", "one can"]
        generic_count = sum(1 for phrase in generic_phrases if phrase in response.lower())
        factors["generic_phrases"] = generic_count
        
        score = max(0, score - (generic_count * 0.05))
        
        return {
            "score": round(min(score, 1.0), 2),
            "factors": factors
        }
    
    def _evaluate_length(self, response: str, query: str) -> Dict:
        """Evaluate if response length is appropriate"""
        
        response_length = len(response)
        query_complexity = len(query.split())
        
        factors = {
            "response_length": response_length,
            "query_complexity": query_complexity
        }
        
        # Simple heuristic: roughly 10-20 words response per word in query
        expected_length_min = query_complexity * 5
        expected_length_max = query_complexity * 30
        
        if response_length < expected_length_min:
            score = 0.4
            factors["assessment"] = "too_short"
        elif response_length > expected_length_max * 2:
            score = 0.6
            factors["assessment"] = "too_long"
        else:
            score = 0.9
            factors["assessment"] = "appropriate"
        
        return {
            "score": round(score, 2),
            "factors": factors
        }
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """Calculate weighted overall quality score"""
        
        weights = {
            "relevance": 0.20,
            "factual_grounding": 0.25,
            "completeness": 0.20,
            "coherence": 0.15,
            "hallucination_risk": 0.10,  # Inverse scoring
            "citation_quality": 0.05,
            "specificity": 0.03,
            "length_appropriateness": 0.02
        }
        
        total_score = 0.0
        
        for metric_name, weight in weights.items():
            if metric_name in metrics:
                metric = metrics[metric_name]
                if metric_name == "hallucination_risk":
                    # Inverse: lower risk = higher score
                    score = 1.0 - (
                        0.0 if metric["risk_level"] == "low" else
                        0.5 if metric["risk_level"] == "low-medium" else
                        1.0
                    )
                else:
                    score = metric.get("score", 0.5)
                
                total_score += score * weight
        
        return round(total_score, 2)
    
    def _rate_quality(self, score: float) -> str:
        """Convert score to quality rating"""
        if score >= 0.85:
            return "excellent"
        elif score >= 0.70:
            return "good"
        elif score >= 0.55:
            return "fair"
        elif score >= 0.40:
            return "poor"
        else:
            return "very_poor"
    
    def _generate_recommendations(self, metrics: Dict) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics.get("relevance", {}).get("score", 1.0) < 0.6:
            recommendations.append("Response may not adequately address the question - consider refocusing")
        
        if metrics.get("factual_grounding", {}).get("score", 1.0) < 0.5:
            recommendations.append("Check factual accuracy - some claims may not be grounded in context")
        
        if metrics.get("hallucination_risk", {}).get("risk_level") in ["medium", "high"]:
            recommendations.append("Potential hallucination detected - verify claims are in context")
        
        if metrics.get("completeness", {}).get("score", 1.0) < 0.5:
            recommendations.append("Response appears incomplete - consider providing more detail")
        
        if metrics.get("coherence", {}).get("score", 1.0) < 0.5:
            recommendations.append("Improve response organization and clarity")
        
        if metrics.get("specificity", {}).get("score", 1.0) < 0.4:
            recommendations.append("Add specific dates, numbers, or named entities for more concrete information")
        
        if not recommendations:
            recommendations.append("Response quality is good - consider minor enhancements for specificity")
        
        return recommendations
    
    # Helper methods
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract main keywords from text"""
        import re
        # Remove common words
        common = {"the", "a", "is", "are", "and", "or", "but", "in", "of", "to", "for"}
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        return [w for w in words if w not in common]
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract factual claims (numbers, dates, proper nouns)"""
        import re
        facts = []
        # Extract dates
        facts.extend(re.findall(r'\d{3,4}\s*(?:CE|BCE|AD|BC)?', text))
        # Extract measurements
        facts.extend(re.findall(r'\d+\s*(?:meters|feet|kilometers|years)', text))
        # Extract capitalized phrases (proper nouns)
        facts.extend(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text))
        return list(set(facts))
    
    def _extract_specific_claims(self, text: str) -> List[str]:
        """Extract specific factual claims"""
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        return sentences[:5]  # Return first 5 claims
    
    def _identify_query_aspects(self, query: str) -> List[str]:
        """Identify different aspects of a query"""
        aspects = []
        aspect_keywords = {
            "when": ["date", "period", "century", "when"],
            "where": ["location", "place", "where"],
            "why": ["reason", "cause", "why", "significance"],
            "what": ["description", "what", "details"],
            "how": ["method", "process", "how"],
            "who": ["person", "name", "who"]
        }
        
        query_lower = query.lower()
        for question_word, keywords in aspect_keywords.items():
            if any(kw in query_lower for kw in keywords):
                aspects.append(question_word)
        
        return aspects if aspects else ["general"]


def main():
    """Demo: Show evaluation in action"""
    
    evaluator = ResponseEvaluator()
    
    print("=" * 70)
    print("RESPONSE QUALITY EVALUATOR DEMO")
    print("=" * 70 + "\n")
    
    # Test case 1: Good response
    query = "Tell me about Sigiriya's historical significance"
    response = """Sigiriya, located in central Sri Lanka, is one of the most remarkable historical sites 
on the island. Built in the 5th century CE during the reign of King Kasyapa I (477-495 CE), 
this 147-meter high rock fortress served as both a royal residence and defensive structure. 

The site is architecturally significant for its sophisticated engineering, featuring an elaborate 
water garden system, decorative frescoes, and a palace complex atop the rock. According to 
archaeological evidence, it remained an important Buddhist monastery after the royal period. 

Sigiriya's historical importance lies in its representation of ancient Sri Lankan civilization's 
engineering capabilities and artistic achievements. Today, it's recognized as a UNESCO World 
Heritage Site and stands as one of Asia's most impressive ancient fortified sites."""
    
    context = """Sigiriya is a massive rock fortress in central Sri Lanka, standing 147 meters above 
the surrounding plains. Constructed in the 5th century CE under King Kasyapa I (around 477-495 CE), 
it originally served as a royal palace and fortress. The site features water gardens, elaborate frescoes, 
stone sculptures, and a royal palace on top. After King Kasyapa's reign, it became a Buddhist monastery 
and remained so for several centuries. The site shows sophisticated ancient engineering and artistic work."""
    
    evaluation = evaluator.evaluate_response(
        user_query=query,
        response=response,
        context=context
    )
    
    print("TEST 1: Good Response")
    print("-" * 70)
    print(f"Overall Score: {evaluation['overall_score']}/1.0")
    print(f"Quality Rating: {evaluation['quality_rating'].upper()}")
    print(f"\nMetrics Breakdown:")
    
    for metric_name, metric_data in evaluation["metrics"].items():
        score = metric_data.get("score", metric_data.get("confidence", "N/A"))
        print(f"  • {metric_name.replace('_', ' ').title()}: {score}")
    
    print(f"\nRecommendations:")
    for rec in evaluation["recommendations"]:
        print(f"  • {rec}")
    
    # Test case 2: Poor response
    print("\n\nTEST 2: Poor Response (No Context)")
    print("-" * 70)
    
    poor_response = "Sigiriya is a rock in Sri Lanka."
    
    evaluation2 = evaluator.evaluate_response(
        user_query=query,
        response=poor_response,
        context=context
    )
    
    print(f"Overall Score: {evaluation2['overall_score']}/1.0")
    print(f"Quality Rating: {evaluation2['quality_rating'].upper()}")
    print(f"\nRecommendations:")
    for rec in evaluation2["recommendations"]:
        print(f"  • {rec}")


if __name__ == "__main__":
    main()
