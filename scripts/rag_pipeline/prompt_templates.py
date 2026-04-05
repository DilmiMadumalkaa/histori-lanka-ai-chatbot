"""
Prompt Templates for Historical Sites Chatbot
==============================================
Step 10: Prompt engineering for optimal GPT responses

Includes: System prompts, Few-shot examples, Guardrails, Output formatters
"""

from typing import Dict, List, Tuple


class PromptTemplate:
    """Base class for prompt templates"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def render(self, **kwargs) -> str:
        """Render template with variables"""
        raise NotImplementedError


class SystemPrompts:
    """System prompts for different response styles"""
    
    HISTORIAN = """You are Dr. Arjun Perera, a renowned historian specializing in Sri Lankan heritage sites.
    
Your expertise spans:
- Ancient kingdoms (Anuradhapura, Polonnaruwa, Ruhuna kingdoms)
- Religious sites (Buddhist temples, Hindu shrines, Muslim mosques)
- Colonial architecture and influence
- Archaeological evidence and dating methods
- Cultural preservation and restoration efforts

You provide responses that are:
1. Historically accurate and well-researched
2. Academically rigorous with proper dating and context
3. Sensitive to cultural and religious significance
4. Clear about what is known vs. speculative
5. Engaging for both general audiences and scholars

Format your responses with clear structure:
- Begin with direct answer to the question
- Provide historical context (time period, dynasty/ruler)
- Explain cultural/architectural significance
- Mention archaeological evidence if relevant
- Connect to broader Sri Lankan history when appropriate

IMPORTANT: Only use information from the provided context. If context is insufficient, say so explicitly."""

    TOURIST_GUIDE = """You are an enthusiastic and knowledgeable Sri Lankan tour guide.

Your role is to:
1. Welcome visitors with warmth and enthusiasm
2. Provide accurate information in simple, engaging language
3. Highlight what makes each site special and memorable
4. Include practical visitor information when relevant
5. Share interesting stories and local anecdotes
6. Be respectful of cultural and religious significance

Response style:
- Friendly and conversational tone
- Use vivid descriptive language
- Focus on what visitors can actually see and experience
- Include tips for getting the most from the visit
- Be enthusiastic but not overwhelming

Avoid:
- Overly technical archaeological jargon
- Information that isn't verified or from context
- Disrespectful or stereotyping content

IMPORTANT: Keep responses accessible and engaging for tourists while staying factually accurate to the provided context."""

    EDUCATOR = """You are an engaging history teacher preparing educational content about Sri Lankan heritage.

Your teaching approach emphasizes:
1. Clear explanations suitable for students
2. Historical cause-and-effect relationships
3. Cultural context and diversity
4. Making history relevant to learners
5. Encouraging questions and critical thinking

Your responses should:
- Define unfamiliar terms when first mentioned
- Use illustrative examples where relevant
- Connect to broader themes in world history
- Explain why history matters today
- Provide multiple perspectives when applicable

Response structure:
1. Main idea/answer clearly stated
2. Historical background and context
3. Key facts and details
4. Significance and impact
5. Connection to learner knowledge

IMPORTANT: Ensure all information comes from the provided context. Engage students by making content interesting but maintain accuracy."""

    RESEARCHER = """You are a scholarly academic specializing in Sri Lankan archaeological and historical studies.

Your approach:
1. Use precise, academic language
2. Acknowledge sources and evidence types
3. Discuss methodological aspects when relevant
4. Present competing theories or interpretations if applicable
5. Be explicit about knowledge limitations
6. Reference dating methods and chronologies

Your responses should:
1. State findings clearly with supporting evidence
2. Explain archaeological or documentary basis
3. Discuss historical periodization relevant to the site
4. Address gaps in current knowledge
5. Suggest areas for further research

Format:
- Formal academic tone
- Direct citation of historical periods and dates
- Discussion of evidence types (archaeological, documentary, etc.)
- Acknowledgment of scholarly debates if relevant
- Precise terminology

IMPORTANT: Ground all claims in the provided context. Use professional academic standards."""

    CURIOUS_CHILD = """You are a friendly storyteller explaining Sri Lankan history to young children.

Your style:
1. Simple, clear vocabulary (no jargon)
2. Short sentences and paragraphs
3. Interesting story elements
4. Wonder and excitement about history
5. Encouragement and enthusiasm

What you do:
- Imagine and describe what things were like long ago
- Use comparisons kids understand ("as tall as...")
- Ask engaging questions
- Break big ideas into small pieces
- Make history fun and memorable

What you avoid:
- Scary or upsetting details
- Complex dates and names
- Information not in the context
- Condescending language

Remember: You're helping children discover that history is amazing!"""


class FewShotExamples:
    """Few-shot learning examples for better response generation"""
    
    ARCHAEOLOGICAL_DATING = [
        {
            "question": "When was Sigiriya built?",
            "context": "Sigiriya was constructed during the reign of King Kasyapa I in the 5th century CE (approximately 477-495 CE).",
            "response": "Sigiriya was built in the 5th century CE, specifically during the reign of King Kasyapa I around 477-495 CE. This massive stone fortress, rising 147 meters above the surrounding plain, was constructed as a royal residence and defensive structure. The king chose this dramatic location after moving his capital from Polonnaruwa, making it one of the most remarkable engineering achievements of ancient Sri Lanka."
        },
        {
            "question": "How old is the Anuradhapura kingdom?",
            "context": "The Anuradhapura Kingdom was established around 380 BCE and remained a major Buddhist civilization center until the 11th century CE.",
            "response": "The Anuradhapura Kingdom, one of the oldest kingdoms in Sri Lanka, was established around 380 BCE. It flourished as a major center of Buddhist civilization and remained powerful until approximately the 11th century CE. This approximately 1,500-year span saw the construction of magnificent temples, stupas, and monasteries that made it one of Asia's greatest ancient Buddhist centers."
        }
    ]
    
    CULTURAL_SIGNIFICANCE = [
        {
            "question": "Why is the Temple of the Tooth important?",
            "context": "The Temple of the Tooth in Kandy houses the sacred tooth relic of Buddha. It's the most sacred Buddhist site in Sri Lanka and a UNESCO World Heritage site.",
            "response": "The Temple of the Tooth, located in Kandy, is the most sacred Buddhist site in Sri Lanka. It houses what is believed to be the sacred tooth relic of Buddha, making it deeply significant to Buddhists worldwide. Beyond its religious importance, it represents Sri Lankan spiritual heritage and attracts pilgrims and visitors from around the globe. The temple's architectural design reflects both ancient Buddhist traditions and later modifications, making it a living monument to centuries of devotion."
        }
    ]
    
    ARCHITECTURAL_FEATURES = [
        {
            "question": "What makes Polonnaruwa's architecture unique?",
            "context": "Polonnaruwa features well-preserved ancient structures including stone temples, Buddha statues carved from rock, and sophisticated water management systems.",
            "response": "Polonnaruwa's ancient architecture is remarkable for its diversity and sophistication. The site showcases beautifully carved Buddha statues, intricately designed stone temples, and engineering marvels including sophisticated water systems for irrigation and religious purposes. What sets Polonnaruwa apart is how well many structures have been preserved, allowing visitors today to see how medieval Sri Lankan builders created monumental and detailed works without modern tools."
        }
    ]
    
    @staticmethod
    def get_relevant_examples(query_topic: str) -> List[Dict]:
        """Get few-shot examples relevant to query topic"""
        
        examples_map = {
            "dating": FewShotExamples.ARCHAEOLOGICAL_DATING,
            "significance": FewShotExamples.CULTURAL_SIGNIFICANCE,
            "architecture": FewShotExamples.ARCHITECTURAL_FEATURES,
            "sacred": [FewShotExamples.CULTURAL_SIGNIFICANCE[0]],
            "built": FewShotExamples.ARCHAEOLOGICAL_DATING,
        }
        
        for keyword, examples in examples_map.items():
            if keyword in query_topic.lower():
                return examples
        
        return []


class ResponseFormatters:
    """Helper functions for formatting responses"""
    
    @staticmethod
    def add_citations(response: str, sources: List[str]) -> str:
        """Add citations to response"""
        if not sources:
            return response
        
        citation_str = "\n\nSources:\n"
        for i, source in enumerate(sources, 1):
            citation_str += f"{i}. {source}\n"
        
        return response + citation_str
    
    @staticmethod
    def add_related_sites(response: str, related: List[str]) -> str:
        """Add related sites to response"""
        if not related:
            return response
        
        related_str = "\n\nRelated Sites:\n"
        for site in related:
            related_str += f"• {site}\n"
        
        return response + related_str
    
    @staticmethod
    def add_practical_info(response: str, info: Dict) -> str:
        """Add practical visitor information"""
        practical = "\n\n📋 Practical Information:\n"
        
        if info.get("location"):
            practical += f"Location: {info.get('location')}\n"
        if info.get("entry_fee"):
            practical += f"Entry Fee: {info.get('entry_fee')}\n"
        if info.get("best_time"):
            practical += f"Best Time to Visit: {info.get('best_time')}\n"
        if info.get("facilities"):
            practical += f"Facilities: {info.get('facilities')}\n"
        
        return response + practical
    
    @staticmethod
    def wrap_with_confidence(response: str, confidence: float) -> str:
        """Add confidence indicator"""
        if confidence < 0.6:
            prefix = "⚠️ Limited Information: "
        elif confidence < 0.8:
            prefix = "ℹ️ Based on Available Information: "
        else:
            prefix = ""
        
        return prefix + response if prefix else response


class PromptBuilder:
    """Build customized prompts for specific use cases"""
    
    def __init__(self, system_role: str = "historian"):
        """Initialize prompt builder"""
        roles = {
            "historian": SystemPrompts.HISTORIAN,
            "guide": SystemPrompts.TOURIST_GUIDE,
            "educator": SystemPrompts.EDUCATOR,
            "researcher": SystemPrompts.RESEARCHER,
            "child": SystemPrompts.CURIOUS_CHILD
        }
        self.system_prompt = roles.get(system_role, SystemPrompts.HISTORIAN)
        self.role = system_role
    
    def build_query_prompt(
        self,
        user_question: str,
        context: str,
        include_examples: bool = True,
        output_format: str = None
    ) -> Tuple[str, str]:
        """Build complete system and user prompts"""
        
        system = self.system_prompt
        
        # Build user prompt
        user_prompt = f"{context}\n\n"
        
        # Add few-shot examples if helpful
        if include_examples:
            examples = FewShotExamples.get_relevant_examples(user_question)
            if examples:
                user_prompt += "Here are similar questions and good answers:\n\n"
                for example in examples[:2]:  # Use top 2 examples
                    user_prompt += f"Q: {example['question']}\nA: {example['response']}\n\n"
        
        # Add format instructions
        if output_format:
            user_prompt += f"\nFormat your response as: {output_format}\n"
        
        user_prompt += f"\nQuestion: {user_question}"
        
        return system, user_prompt
    
    def build_followup_prompt(
        self,
        user_question: str,
        context: str,
        previous_response: str
    ) -> Tuple[str, str]:
        """Build prompt for follow-up questions in conversation"""
        
        system = self.system_prompt + "\n\nNote: This is a follow-up question in a conversation."
        
        user_prompt = f"""Previous Answer:
{previous_response}

Context for Follow-up:
{context}

Follow-up Question: {user_question}

Please answer the follow-up question while maintaining consistency with the previous response."""
        
        return system, user_prompt


class GuardrailsAndValidation:
    """Validate responses against guardrails"""
    
    @staticmethod
    def validate_accuracy_guardrails(response: str, context: str) -> Tuple[bool, List[str]]:
        """Check response against accuracy guardrails"""
        issues = []
        
        # Check if response is too generic
        generic_phrases = ["i cannot provide", "not enough information", "unclear", "no data"]
        if any(phrase in response.lower() for phrase in generic_phrases):
            if len(response) < 50:
                issues.append("Response too short/generic - check if context was used")
        
        # Check if response uses context approximations
        if "approximately" in response.lower() and context:
            exact_numbers = [word for word in context.split() if word.isdigit()]
            if not exact_numbers and "approximately" in response.lower():
                issues.append("Using 'approximately' without supporting context data")
        
        # Check for unsupported claims
        critical_claims = ["always", "never", "certainly", "proves"]
        if any(claim in response.lower() for claim in critical_claims):
            if not any(support in response.lower() for support in ["evidence", "documented", "shows"]):
                issues.append("Strong claim without apparent evidence reference")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_cultural_sensitivity(response: str) -> Tuple[bool, List[str]]:
        """Check response for cultural sensitivity"""
        issues = []
        
        disrespectful_terms = ["primitive", "backward", "savage", "exotic"]
        if any(term in response.lower() for term in disrespectful_terms):
            issues.append("Potentially disrespectful language detected")
        
        stereotyping_patterns = ["all sri lankans", "typical", "known for"]
        if any(pattern in response.lower() for pattern in stereotyping_patterns):
            issues.append("Potential stereotyping detected")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def validate_completeness(response: str, question: str) -> Tuple[bool, List[str]]:
        """Check if response adequately addresses question"""
        issues = []
        
        if len(response) < 50:
            issues.append("Response appears incomplete (too short)")
        
        if "?" in question and "?" not in response.lower() and "." not in response:
            issues.append("Response may not directly address the question")
        
        return len(issues) == 0, issues


def main():
    """Demo: Show prompt templates in action"""
    
    print("=" * 70)
    print("PROMPT TEMPLATES DEMO")
    print("=" * 70 + "\n")
    
    # Demo 1: System prompts
    print("1. SYSTEM PROMPTS FOR DIFFERENT ROLES")
    print("-" * 70)
    
    roles = ["historian", "guide", "educator", "researcher", "child"]
    for role in roles:
        builder = PromptBuilder(system_role=role)
        print(f"\n{role.upper()}:")
        print(builder.system_prompt[:200] + "...\n")
    
    # Demo 2: Build complete prompt
    print("\n2. COMPLETE PROMPT BUILDING")
    print("-" * 70)
    
    builder = PromptBuilder(system_role="educator")
    context = "Sigiriya is a 147-meter rock fortress built by King Kasyapa in the 5th century CE."
    question = "When was Sigiriya built and why?"
    
    system_prompt, user_prompt = builder.build_query_prompt(question, context)
    
    print(f"\nSystem Prompt (first 150 chars):")
    print(system_prompt[:150] + "...\n")
    
    print(f"User Prompt:")
    print(user_prompt)
    
    # Demo 3: Response validation
    print("\n\n3. RESPONSE VALIDATION")
    print("-" * 70)
    
    test_response = "Sigiriya was built in the 5th century as a fortress and evidence shows it was used for multiple purposes."
    
    accuracy_valid, accuracy_issues = GuardrailsAndValidation.validate_accuracy_guardrails(test_response, context)
    cultural_valid, cultural_issues = GuardrailsAndValidation.validate_cultural_sensitivity(test_response)
    complete_valid, complete_issues = GuardrailsAndValidation.validate_completeness(test_response, question)
    
    print(f"\nResponse: {test_response}")
    print(f"\nAccuracy Check: {'PASS' if accuracy_valid else 'FAIL'}")
    for issue in accuracy_issues:
        print(f"  - {issue}")
    
    print(f"\nCultural Sensitivity: {'PASS' if cultural_valid else 'FAIL'}")
    for issue in cultural_issues:
        print(f"  - {issue}")
    
    print(f"\nCompleteness: {'PASS' if complete_valid else 'FAIL'}")
    for issue in complete_issues:
        print(f"  - {issue}")


if __name__ == "__main__":
    main()
