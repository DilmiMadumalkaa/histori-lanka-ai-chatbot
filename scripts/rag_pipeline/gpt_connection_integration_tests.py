"""
GPT Connection Integration Tests
================================

Comprehensive testing for GPT + RAG integration.
Validates end-to-end chatbot functionality and response improvement signals.
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GPTConnectionTestSuite:
    """Comprehensive test suite for GPT connection and response quality improvement."""
    
    def __init__(self, use_mock: bool = True):
        """Initialize test suite"""
        self.use_mock = use_mock
        self.test_results = []
        self.logger = logger
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize required components"""
        try:
            if self.use_mock:
                # Use mock generator when in mock mode
                from chat_interface import MockGPTGenerator
                self.generator = MockGPTGenerator()
                logger.info("[+] GPT Response Generator available (MOCK)")
            else:
                from gpt41_mini_response_generator import ResponseGenerator
                self.generator = ResponseGenerator()
                logger.info("[+] GPT Response Generator available")
        except Exception as e:
            logger.warning(f"[-] GPT Generator not available: {e}")
            self.generator = None
        
        try:
            if self.use_mock:
                from rag_evaluation_simulator import MockRetriever
                self.retriever = MockRetriever()
            else:
                from pinecone_retrieval import PineconeRetrieverWithReranking
                self.retriever = PineconeRetrieverWithReranking()
            logger.info("[+] Retriever available")
        except Exception as e:
            logger.warning(f"[-] Retriever not available: {e}")
            self.retriever = None
        
        try:
            from response_evaluator import ResponseEvaluator
            self.evaluator = ResponseEvaluator()
            logger.info("[+] Response Evaluator available")
        except Exception as e:
            logger.warning(f"[-] Evaluator not available: {e}")
            self.evaluator = None
    
    def run_all_tests(self) -> Dict:
        """Run all test categories"""
        
        print("\n" + "=" * 70)
        print("GPT CONNECTION INTEGRATION TEST SUITE")
        print("=" * 70 + "\n")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_categories": {}
        }
        
        # Test 1: Component Availability
        results["test_categories"]["component_availability"] = self.test_component_availability()
        
        # Test 2: Response Generation
        if self.generator:
            results["test_categories"]["response_generation"] = self.test_response_generation()
        
        # Test 3: Retrieval Quality
        if self.retriever:
            results["test_categories"]["retrieval_quality"] = self.test_retrieval_quality()
        
        # Test 4: End-to-End Pipeline
        if self.generator and self.retriever:
            results["test_categories"]["end_to_end"] = self.test_end_to_end_pipeline()
        
        # Test 5: Response Quality
        if self.evaluator:
            results["test_categories"]["response_quality"] = self.test_response_quality()

        # Test 6: Improvement Recommendations
        if self.evaluator and self.generator:
            results["test_categories"]["improvement_recommendations"] = self.test_improvement_recommendations()
        
        # Test 7: Error Handling
        results["test_categories"]["error_handling"] = self.test_error_handling()
        
        # Test 8: Performance
        if self.generator and self.retriever:
            results["test_categories"]["performance"] = self.test_performance()
        
        # Summary
        results["summary"] = self._generate_summary(results["test_categories"])
        
        return results
    
    def test_component_availability(self) -> Dict:
        """Test 1: Verify all components are available"""
        
        logger.info("\n[TEST 1] Component Availability Check")
        print("-" * 70)
        
        tests = {
            "Generator Available": self.generator is not None,
            "Retriever Available": self.retriever is not None,
            "Evaluator Available": self.evaluator is not None,
        }
        
        results = {
            "category": "component_availability",
            "tests": tests,
            "passed": sum(tests.values()),
            "total": len(tests)
        }
        
        for test_name, passed in tests.items():
            status = "[+]" if passed else "[-]"
            print(f"{status} {test_name}")
        
        return results
    
    def test_response_generation(self) -> Dict:
        """Test 2: Verify response generation works"""
        
        logger.info("\n[TEST 2] Response Generation")
        print("-" * 70)
        
        test_queries = [
            "Tell me about Sigiriya",
            "What is the historical significance of Anuradhapura?",
            "Describe the architecture at Polonnaruwa"
        ]
        
        results = {
            "category": "response_generation",
            "tests": {},
            "queries_tested": 0
        }
        
        for query in test_queries:
            try:
                # Generate response with mock context
                context = f"Information about the query: {query}"
                response = self.generator.call_gpt_with_rag_context(
                    user_query=query,
                    rag_context=context,
                    instructions="Answer only from provided context.",
                    temperature=0.5,
                    max_tokens=200
                )
                
                # Verify response
                passed = (
                    response.get("success", False) and
                    len(response.get("response", "")) > 30 and
                    response.get("tokens_used", 0) > 0
                )
                
                results["tests"][query[:30]] = {
                    "passed": passed,
                    "response_length": len(response.get("response", "")),
                    "tokens": response.get("tokens_used", 0)
                }
                
                status = "[+]" if passed else "[-]"
                print(f"{status} Query: {query[:40]}...")
                results["queries_tested"] += 1
                
            except Exception as e:
                logger.error(f"Error testing query: {e}")
                results["tests"][query[:30]] = {"passed": False, "error": str(e)}
        
        results["passed"] = sum(1 for t in results["tests"].values() if t.get("passed", False))
        results["total"] = len(test_queries)
        
        return results
    
    def test_retrieval_quality(self) -> Dict:
        """Test 3: Verify retrieval quality"""
        
        logger.info("\n[TEST 3] Retrieval Quality")
        print("-" * 70)
        
        test_queries = [
            "Sigiriya fortress",
            "Buddhist temples Sri Lanka",
            "ancient kingdoms"
        ]
        
        results = {
            "category": "retrieval_quality",
            "tests": {},
            "queries_tested": 0
        }
        
        for query in test_queries:
            try:
                context = self.retriever.retrieve_formatted_context(query, top_k=3)
                
                # Verify retrievals
                passed = (
                    len(context) > 0 and
                    "Source" in context or "Category" in context
                )
                
                results["tests"][query[:30]] = {
                    "passed": passed,
                    "context_length": len(context),
                    "has_metadata": "Category" in context
                }
                
                status = "[+]" if passed else "[-]"
                print(f"{status} Retrieved {len(context)} chars for: {query[:30]}...")
                results["queries_tested"] += 1
                
            except Exception as e:
                logger.error(f"Error retrieving: {e}")
                results["tests"][query[:30]] = {"passed": False, "error": str(e)}
        
        results["passed"] = sum(1 for t in results["tests"].values() if t.get("passed", False))
        results["total"] = len(test_queries)
        
        return results
    
    def test_end_to_end_pipeline(self) -> Dict:
        """Test 4: Verify full pipeline works"""
        
        logger.info("\n[TEST 4] End-to-End Pipeline")
        print("-" * 70)
        
        test_queries = [
            "What can you tell me about Sigiriya?",
            "Describe Anuradhapura",
            "Tell me about historical temples in Sri Lanka"
        ]
        
        results = {
            "category": "end_to_end",
            "tests": {},
            "queries_tested": 0
        }
        
        for query in test_queries:
            try:
                start_time = time.time()
                
                # Step 1: Retrieve
                context = self.retriever.retrieve_formatted_context(query, top_k=3)
                
                # Step 2: Generate
                response = self.generator.call_gpt_with_rag_context(
                    user_query=query,
                    rag_context=context,
                    instructions="Use only retrieved context and mention uncertainty when needed.",
                    temperature=0.7
                )
                
                elapsed = time.time() - start_time
                
                # Verify complete pipeline
                passed = (
                    len(context) > 0 and
                    response.get("success", False) and
                    len(response.get("response", "")) > 50 and
                    elapsed < 30  # Should complete in < 30 seconds
                )
                
                results["tests"][query[:30]] = {
                    "passed": passed,
                    "elapsed_seconds": round(elapsed, 2),
                    "context_length": len(context),
                    "response_length": len(response.get("response", ""))
                }
                
                status = "[+]" if passed else "[-]"
                print(f"{status} End-to-end for: {query[:35]}... ({elapsed:.2f}s)")
                results["queries_tested"] += 1
                
            except Exception as e:
                logger.error(f"Error in pipeline: {e}")
                results["tests"][query[:30]] = {"passed": False, "error": str(e)}
        
        results["passed"] = sum(1 for t in results["tests"].values() if t.get("passed", False))
        results["total"] = len(test_queries)
        
        return results
    
    def test_response_quality(self) -> Dict:
        """Test 5: Verify response quality assessment"""
        
        logger.info("\n[TEST 5] Response Quality Assessment")
        print("-" * 70)
        
        # Use a fixed good response
        query = "When was Sigiriya built?"
        context = """Sigiriya was constructed in the 5th century CE during the reign of 
        King Kasyapa I (approximately 477-495 CE). The site stands 147 meters tall."""
        response = """Sigiriya was built in the 5th century CE, specifically during the reign 
        of King Kasyapa I around 477-495 CE. This 147-meter-high rock fortress was constructed 
        as a royal residence and defensive structure."""
        
        results = {
            "category": "response_quality",
            "tests": {}
        }
        
        try:
            evaluation = self.evaluator.evaluate_response(
                user_query=query,
                response=response,
                context=context
            )
            
            # Verify evaluation
            passed = (
                "overall_score" in evaluation and
                "quality_rating" in evaluation and
                evaluation["overall_score"] > 0.5
            )
            
            results["tests"]["Quality Assessment"] = {
                "passed": passed,
                "overall_score": evaluation.get("overall_score", 0),
                "rating": evaluation.get("quality_rating", "unknown"),
                "metrics_count": len(evaluation.get("metrics", {}))
            }
            
            status = "[+]" if passed else "[-]"
            print(f"{status} Score: {evaluation.get('overall_score', 0)}/1.0 ({evaluation.get('quality_rating', 'N/A')})")
            
            results["passed"] = 1 if passed else 0
            results["total"] = 1
            
        except Exception as e:
            logger.error(f"Error evaluating: {e}")
            results["tests"]["Quality Assessment"] = {"passed": False, "error": str(e)}
            results["passed"] = 0
            results["total"] = 1
        
        return results

    def test_improvement_recommendations(self) -> Dict:
        """Test 6: Verify improvement recommendations are produced for weak responses."""

        logger.info("\n[TEST 6] Improvement Recommendations")
        print("-" * 70)

        query = "Tell me about Sigiriya's exact architectural plan and dimensions"
        context = "Sigiriya is a historical site in Sri Lanka. It was built in the 5th century."
        weak_response = "Sigiriya is old and important."

        results = {
            "category": "improvement_recommendations",
            "tests": {}
        }

        try:
            evaluation = self.evaluator.evaluate_response(
                user_query=query,
                response=weak_response,
                context=context,
            )

            recommendations = evaluation.get("recommendations", [])
            passed = len(recommendations) > 0

            results["tests"]["Recommendations Generated"] = {
                "passed": passed,
                "recommendation_count": len(recommendations),
                "overall_score": evaluation.get("overall_score", 0),
            }

            status = "[+]" if passed else "[-]"
            print(f"{status} Recommendations generated: {len(recommendations)}")

            results["passed"] = 1 if passed else 0
            results["total"] = 1
        except Exception as e:
            logger.error("Error generating improvement recommendations: %s", e)
            results["tests"]["Recommendations Generated"] = {"passed": False, "error": str(e)}
            results["passed"] = 0
            results["total"] = 1

        return results
    
    def test_error_handling(self) -> Dict:
        """Test 6: Verify proper error handling"""
        
        logger.info("\n[TEST 6] Error Handling")
        print("-" * 70)
        
        results = {
            "category": "error_handling",
            "tests": {}
        }
        
        # Test 1: Empty query
        try:
            if self.generator:
                response = self.generator.generate_response("", "", temperature=0.5)
                passed = not response.get("success", True)
                results["tests"]["Empty Query Handling"] = {"passed": passed}
                status = "[+]" if passed else "[-]"
                print(f"{status} Empty query properly handled")
        except Exception as e:
            print(f"[-] Empty query test failed: {e}")
            results["tests"]["Empty Query Handling"] = {"passed": False}
        
        # Test 2: Very long query
        try:
            if self.generator:
                long_query = "test " * 1000
                response = self.generator.generate_response(long_query, "context", temperature=0.5)
                passed = True  # Should not crash
                results["tests"]["Long Query Handling"] = {"passed": passed}
                status = "[+]" if passed else "[-]"
                print(f"{status} Long query handled gracefully")
        except Exception as e:
            print(f"[-] Long query test error: {e}")
            results["tests"]["Long Query Handling"] = {"passed": False}
        
        # Test 3: No context retrieval
        try:
            if self.generator and self.retriever:
                query = "Very specific unknown local site in XYZ location"
                context = ""
                response = self.generator.call_gpt_with_rag_context(
                    user_query=query,
                    rag_context=context or "No context available",
                    instructions="If context is missing, say information is unavailable.",
                    temperature=0.5,
                )
                passed = response.get("success", False)
                results["tests"]["No Context Handling"] = {"passed": passed}
                status = "[+]" if passed else "[-]"
                print(f"{status} No context scenario handled")
        except Exception as e:
            print(f"[-] No context test failed: {e}")
            results["tests"]["No Context Handling"] = {"passed": False}
        
        results["passed"] = sum(1 for t in results["tests"].values() if t.get("passed", False))
        results["total"] = len(results["tests"])
        
        return results
    
    def test_performance(self) -> Dict:
        """Test 7: Verify performance metrics"""
        
        logger.info("\n[TEST 7] Performance Metrics")
        print("-" * 70)
        
        results = {
            "category": "performance",
            "tests": {},
            "performance_metrics": {}
        }
        
        queries = [
            "Sigiriya fortress",
            "Anuradhapura Buddhist monastery",
            "Polonnaruwa ancient temples"
        ]
        
        latencies = []
        
        for query in queries:
            try:
                start = time.time()
                
                # Full pipeline
                context = self.retriever.retrieve_formatted_context(query, top_k=3)
                response = self.generator.call_gpt_with_rag_context(
                    user_query=query,
                    rag_context=context,
                    instructions="Respond with grounded facts from context.",
                    max_tokens=500
                )
                
                latency = time.time() - start
                latencies.append(latency)
                
                # Check if meets performance target (< 10 seconds for full pipeline)
                passed = latency < 10
                results["tests"][query] = {
                    "passed": passed,
                    "latency_seconds": round(latency, 2)
                }
                
                status = "[+]" if passed else "[-]"
                print(f"{status} {query}: {latency:.2f}s")
                
            except Exception as e:
                logger.error(f"Performance test error: {e}")
                results["tests"][query] = {"passed": False, "error": str(e)}
        
        # Performance statistics
        if latencies:
            results["performance_metrics"] = {
                "avg_latency": round(sum(latencies) / len(latencies), 2),
                "min_latency": round(min(latencies), 2),
                "max_latency": round(max(latencies), 2),
                "target_latency": 10  # seconds
            }
            print(f"\nPerformance Summary:")
            print(f"  Avg: {results['performance_metrics']['avg_latency']}s")
            print(f"  Min: {results['performance_metrics']['min_latency']}s")
            print(f"  Max: {results['performance_metrics']['max_latency']}s")
        
        results["passed"] = sum(1 for t in results["tests"].values() if t.get("passed", False))
        results["total"] = len(queries)
        
        return results
    
    def _generate_summary(self, test_categories: Dict) -> Dict:
        """Generate overall test summary"""
        
        summary = {
            "total_tests": 0,
            "total_passed": 0,
            "pass_rate": 0.0,
            "categories": {}
        }
        
        for category_name, category_results in test_categories.items():
            if not category_results or "total" not in category_results:
                continue
            
            passed = category_results.get("passed", 0)
            total = category_results.get("total", 0)
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            summary["categories"][category_name] = {
                "passed": passed,
                "total": total,
                "pass_rate": round(pass_rate, 1)
            }
            
            summary["total_tests"] += total
            summary["total_passed"] += passed
        
        summary["pass_rate"] = round(summary["total_passed"] / summary["total_tests"] * 100, 1) if summary["total_tests"] > 0 else 0
        
        return summary
    
    def print_summary(self, results: Dict):
        """Print test summary"""
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        summary = results.get("summary", {})
        print(f"\nOverall Results: {summary.get('total_passed', 0)}/{summary.get('total_tests', 0)} passed ({summary.get('pass_rate', 0)}%)")
        
        print("\nCategory Breakdown:")
        for category, details in summary.get("categories", {}).items():
            print(f"  {category}: {details['passed']}/{details['total']} ({details['pass_rate']}%)")
        
        print("\n" + "=" * 70)
    
    def export_results(self, results: Dict, filename: str = None) -> str:
        """Export test results to JSON"""
        
        if not filename:
            filename = f"gpt_connection_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"[+] Results exported to {filename}")
        return filename


def main():
    """Run test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT Connection Integration Tests")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock retriever")
    parser.add_argument("--real", action="store_true", help="Use real Pinecone retriever")
    parser.add_argument("--export", action="store_true", help="Export results to file")
    
    args = parser.parse_args()
    
    # Run tests
    suite = GPTConnectionTestSuite(use_mock=not args.real)
    results = suite.run_all_tests()
    
    # Print summary
    suite.print_summary(results)
    
    # Export if requested
    if args.export:
        suite.export_results(results)


if __name__ == "__main__":
    main()
