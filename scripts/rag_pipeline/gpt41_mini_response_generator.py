"""
Phase 4: GPT Response Generation
=================================
Connect retrieval system with Azure OpenAI GPT for chatbot responses
Steps 10-11: Response generation and quality testing
"""

import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generate historical sites responses using GPT with RAG context"""
    
    def __init__(self):
        """Initialize GPT connection"""
        try:
            from openai import AzureOpenAI
        except ImportError:
            logger.error("OpenAI not installed. Run: pip install openai")
            raise
        
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = self._normalize_azure_endpoint(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        if not self.api_key or not self.endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found in .env")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

        self.chat_deployments = self._get_chat_deployments()
        self.model = self.chat_deployments[0]
        logger.info(f"[+] GPT client initialized (deployment candidates: {self.chat_deployments})")

    def _normalize_azure_endpoint(self, endpoint: str) -> str:
        """Normalize Azure endpoint to base resource URL if a full API path is provided."""
        if not endpoint:
            return endpoint
        parsed = urlparse(endpoint)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return endpoint

    def _get_chat_deployments(self) -> List[str]:
        """Build prioritized list of Azure chat deployment names to try."""
        candidates = [
            os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
            os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            os.getenv("AZURE_OPENAI_MODEL"),
            "gpt-4.1-mini",
            "gpt-4",
            "gpt-4o",
            "gpt-35-turbo",
        ]
        deployments: List[str] = []
        for item in candidates:
            if item and item not in deployments:
                deployments.append(item)
        return deployments

    def _create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ):
        """Try multiple deployment names and return first successful completion."""
        last_error: Optional[Exception] = None
        for deployment in self.chat_deployments:
            try:
                response = self.client.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95,
                )
                self.model = deployment
                return response
            except Exception as exc:
                last_error = exc
                logger.warning("Deployment '%s' failed: %s", deployment, exc)

        if last_error:
            raise last_error
        raise RuntimeError("No Azure OpenAI chat deployment candidates configured")
    
    def generate_response(
        self,
        user_query: str,
        context: str,
        instructions: Optional[str] = None,
        style: str = "informative",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate response using GPT with retrieved context
        
        Args:
            user_query: User's question
            context: Retrieved context from RAG system
            style: Response style (informative, concise, detailed, academic)
            max_tokens: Maximum response length
            temperature: Creativity (0=deterministic, 1=creative)
        
        Returns:
            Dictionary with response, metadata, and quality indicators
        """

        if not user_query or not user_query.strip():
            return {
                "success": False,
                "user_query": user_query,
                "error": "Query cannot be empty",
                "timestamp": datetime.now().isoformat(),
            }
        
        # Get system prompt based on style
        system_prompt = self._get_system_prompt(style)
        if instructions:
            system_prompt = f"{system_prompt}\n\nAdditional Instructions:\n{instructions}"
        
        # Build user message
        user_message = f"""{context}

User Question: {user_query}

Please provide a response based on the context above."""
        
        try:
            logger.info(f"Generating response: {user_query[:50]}...")
            
            # Call GPT with deployment fallback
            response = self._create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response
            answer = response.choices[0].message.content
            
            # Prepare result
            result = {
                "success": True,
                "user_query": user_query,
                "response": answer,
                "response_length": len(answer),
                "tokens_used": response.usage.total_tokens,
                "model": self.model,
                "timestamp": datetime.now().isoformat(),
                "style": style,
                "temperature": temperature
            }
            
            # Extract quality metrics
            result["quality"] = self._assess_quality(answer)
            
            return result
            
        except Exception as e:
            logger.error(f"GPT call failed: {e}")
            return {
                "success": False,
                "user_query": user_query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def call_gpt_with_rag_context(
        self,
        user_query: str,
        rag_context: str,
        instructions: Optional[str] = None,
        style: str = "informative",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict:
        """Step 9: Call GPT using query + retrieved RAG context + explicit instructions."""
        return self.generate_response(
            user_query=user_query,
            context=rag_context,
            instructions=instructions,
            style=style,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def _get_system_prompt(self, style: str) -> str:
        """Get system prompt based on response style"""
        
        prompts = {
            "informative": """You are an expert on Sri Lankan historical sites and tourism.
Your role is to provide accurate, informative responses about historical sites, 
their cultural significance, and historical importance.

Guidelines:
1. Base your response ONLY on the provided context
2. If the context doesn't contain the information, say so clearly
3. If the context sources describe a different site than the user asked about, explicitly state that no matching source was retrieved and do not answer for the other site
3. Provide specific details (dates, names, locations) when available
4. Explain historical significance and cultural context
5. Use accurate terminology
6. Be professional and educational in tone""",
            
            "concise": """You are a helpful tourist information assistant focused on Sri Lankan sites.
Provide accurate, brief answers about historical sites.

Guidelines:
1. Keep responses short and to the point (2-3 sentences max)
2. Use only information from the provided context
3. If the retrieved context does not match the requested site, say matching data is not available
3. Lead with the most important fact
4. Mention key historical periods or dates if relevant
5. Be direct and clear""",
            
            "detailed": """You are a comprehensive historian specializing in Sri Lankan heritage.
Provide in-depth, scholarly responses about historical sites.

Guidelines:
1. Explore multiple aspects: history, culture, architecture, significance
2. Use context information extensively
3. Never transfer facts from one site to another; when site mismatch occurs, report missing matching context instead
3. Connect different time periods and events
4. Explain why each site matters to Sri Lankan history
5. Include architectural or cultural details
6. Be thorough and analytical""",
            
            "academic": """You are an academic researcher in historical studies.
Provide responses suitable for academic/research purposes.

Guidelines:
1. Use formal, scholarly language
2. Cite context sources implicitly ("According to historical records...")
        3. Do not infer or reassign facts when the retrieved sources are about a different place than the query
3. Provide historical period and dating information
4. Explain research/archaeological significance
5. Discuss methodological aspects when relevant
6. Be precise and evidence-based"""
        }
        
        return prompts.get(style, prompts["informative"])
    
    def _assess_quality(self, response: str) -> Dict:
        """Assess response quality based on heuristics"""
        
        quality_factors = {
            "length_adequate": 50 < len(response) < 10000,
            "has_specifics": any(word in response.lower() for word in ["century", "year", "date", "period", "dynasty"]),
            "well_structured": response.count(".") > 2 and response.count("\n") > 0,
            "uses_context": len(response) > 100,
            "no_placeholder": "context" not in response.lower() or "placeholder" not in response.lower()
        }
        
        quality_score = sum(quality_factors.values()) / len(quality_factors)
        
        return {
            "overall_score": round(quality_score, 2),
            "factors": quality_factors,
            "rating": "excellent" if quality_score > 0.8 else "good" if quality_score > 0.6 else "fair"
        }
    
    def generate_with_retrieval(
        self,
        user_query: str,
        retriever=None,
        instructions: Optional[str] = None,
        style: str = "informative",
        top_k: int = 3
    ) -> Dict:
        """
        End-to-end: Retrieve context and generate response
        
        Args:
            user_query: User's question
            retriever: RAG retriever object (PineconeRetrieverWithReranking)
            style: Response style
            top_k: Number of chunks to retrieve
        
        Returns:
            Full result with context and response
        """
        
        if not retriever:
            raise ValueError("Retriever object required")
        
        logger.info(f"[*] Processing query: {user_query}")
        
        # Step 1: Retrieve context
        logger.info("[1/3] Retrieving context from vector database...")
        context = retriever.retrieve_formatted_context(user_query, top_k=top_k)
        
        # Step 2: Generate response
        logger.info("[2/3] Generating response with GPT...")
        result = self.generate_response(
            user_query=user_query,
            context=context,
            instructions=instructions,
            style=style,
        )
        
        # Step 3: Add retrieval information
        logger.info("[3/3] Compiling final result...")
        result["retrieval_method"] = "Pinecone + Custom Reranking"
        result["context_length"] = len(context)
        result["retrieved_sites_count"] = top_k
        
        return result


class ConversationManager:
    """Manage multi-turn conversations with context preservation"""
    
    def __init__(self, retriever=None):
        """Initialize conversation manager"""
        self.generator = ResponseGenerator()
        self.retriever = retriever
        self.conversation_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_user_message(self, user_query: str) -> Dict:
        """Process and respond to user message"""
        
        # Generate response with retrieval
        result = self.generator.generate_with_retrieval(
            user_query=user_query,
            retriever=self.retriever,
            style="informative"
        )
        
        # Store in conversation history
        self.conversation_history.append({
            "type": "user",
            "message": user_query,
            "timestamp": datetime.now().isoformat()
        })
        
        if result.get("success"):
            self.conversation_history.append({
                "type": "assistant",
                "message": result["response"],
                "timestamp": datetime.now().isoformat(),
                "quality": result.get("quality"),
                "tokens": result.get("tokens_used")
            })
        
        return result
    
    def get_conversation_summary(self) -> Dict:
        """Get conversation summary and statistics"""
        
        user_messages = [m for m in self.conversation_history if m["type"] == "user"]
        assistant_messages = [m for m in self.conversation_history if m["type"] == "assistant"]
        
        total_tokens = sum(m.get("tokens", 0) for m in assistant_messages)
        quality_scores = [m.get("quality", {}).get("overall_score", 0.5) for m in assistant_messages]
        
        return {
            "session_id": self.session_id,
            "turn_count": len(user_messages),
            "total_messages": len(self.conversation_history),
            "total_tokens_used": total_tokens,
            "average_quality": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0,
            "conversation_length": sum(len(m["message"]) for m in self.conversation_history)
        }
    
    def export_conversation(self, output_file: str = None) -> str:
        """Export conversation to JSON"""
        
        if not output_file:
            output_file = f"conversation_{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "history": self.conversation_history,
            "summary": self.get_conversation_summary()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"[+] Conversation exported to {output_file}")
        return output_file


def main():
    """Example usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 4: GPT Response Generation")
    parser.add_argument("--query", type=str, help="User query")
    parser.add_argument("--style", default="informative", help="Response style")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    
    args = parser.parse_args()
    
    # Initialize
    logger.info("=" * 70)
    logger.info("PHASE 4: GPT RESPONSE GENERATION")
    logger.info("=" * 70 + "\n")
    
    try:
        generator = ResponseGenerator()
        
        if args.demo or not args.query:
            # Demo mode
            logger.info("Running demo with sample query...")
            
            context = """
📍 Source 1: Sigiriya
Category: Ancient Fortresses
Relevance Score: 89.2%

Sigiriya is a large rock fortress located in central Sri Lanka. 
Built by King Kasyapa in the 5th century, it stands 147 meters tall 
and features remarkable stone sculptures and frescoes. The site includes 
an ancient moat, water gardens, and a royal palace on top. It was 
originally designed as a fortress but later served as a Buddhist monastery.
            """
            
            query = "Tell me about Sigiriya and its historical significance"
        else:
            context = "" # Would come from retriever
            query = args.query
        
        # Generate response
        result = generator.generate_response(
            user_query=query,
            context=context,
            style=args.style,
            temperature=0.7
        )
        
        # Print result
        print("\n" + "=" * 70)
        print("RESPONSE RESULT")
        print("=" * 70)
        print(f"Query: {result['user_query']}")
        print(f"Style: {result['style']}")
        print(f"Tokens Used: {result.get('tokens_used', 'N/A')}")
        print(f"Quality: {result.get('quality', {}).get('rating', 'N/A')}")
        print("\nResponse:")
        print("-" * 70)
        print(result['response'])
        print("-" * 70)
        
        if result.get("quality"):
            print(f"\nQuality Assessment:")
            for factor, value in result["quality"]["factors"].items():
                status = "✓" if value else "✗"
                print(f"  {status} {factor}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
