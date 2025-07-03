import json
import pathway as pw
from pathway.xpacks.llm.llms import LiteLLMChat
from pathway.xpacks.llm.vector_store import VectorStoreServer
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
import logging
from typing import Dict, List, Any
from fastapi import FastAPI, Request
import uvicorn
import time
import asyncio

class PresentationEvaluator:
    """A wrapper class for evaluating presentations using RAG"""
    
    def __init__(self, llm, doc_store):
        self.llm = llm
        self.doc_store = doc_store
        self.rag_app = BaseRAGQuestionAnswerer(
            llm=llm,
            indexer=doc_store,
            search_topk=3,  # Retrieve top 3 most relevant chunks
        )
        self.app = FastAPI(title="Presentation Evaluator API")
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up the FastAPI routes"""
        
        @self.app.post("/v1/evaluate_ppts")
        async def evaluate_ppts_endpoint(request: Request):
            try:
                data = await request.json()
                criteria = data.get("criteria", "")
                
                # Get all documents from the document store
                all_documents = self._get_all_documents()
                
                logging.info(f"Found {len(all_documents)} documents to evaluate")
                
                # Evaluate each document
                results = []
                for doc in all_documents:
                    evaluation = await self.evaluate_ppt_async(criteria, doc)
                    
                    # Add document metadata
                    file_path = doc.get("file_path", "unknown")
                    evaluation["file_id"] = file_path
                    evaluation["file_name"] = file_path.split("/")[-1] if file_path else "unknown"
                    
                    results.append(evaluation)
                    logging.info(f"Evaluated {evaluation['file_name']} with score: {evaluation['score']}")
                    
                # Sort by score in descending order
                results.sort(key=lambda x: x["score"], reverse=True)
                
                return results
            except Exception as e:
                logging.error(f"Error in evaluate_ppts_endpoint: {str(e)}")
                return {"error": str(e)}
                
        @self.app.post("/v1/chat")
        async def chat_endpoint(request: Request):
            """Endpoint for querying the presentations"""
            try:
                data = await request.json()
                query = data.get("query", "")
                
                # Use the RAG app to answer the query
                response = await self.rag_app.answer_async(query)
                
                return {
                    "answer": response.answer,
                    "sources": response.sources
                }
            except Exception as e:
                logging.error(f"Error in chat_endpoint: {str(e)}")
                return {"error": str(e)}
    
    def _get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents from the document store"""
        docs = []
        try:
            # Access documents directly from document store
            if hasattr(self.doc_store, 'docs'):
                for doc in self.doc_store.docs:
                    docs.append(doc.data)
            # Try alternative attribute names
            elif hasattr(self.doc_store, 'documents'):
                for doc in self.doc_store.documents:
                    docs.append(doc.data)
            # If all else fails, use a simple fallback approach
            else:
                logging.warning("Could not find documents in doc_store. Using fallback approach.")
                # Loop through data directory and return metadata
                import os
                from pathlib import Path
                data_dir = Path("./data")
                for file_path in data_dir.glob("*.pdf"):
                    with open(file_path, 'rb') as f:
                        # Just read first 100 bytes to check if file is valid
                        sample = f.read(100)
                    docs.append({
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "text": f"Content from {file_path.name}"
                    })
        except Exception as e:
            logging.error(f"Error accessing documents: {str(e)}")
        
        logging.info(f"Retrieved {len(docs)} documents")
        return docs
        
    async def evaluate_ppt_async(self, criteria: str, ppt: dict) -> dict:
        """
        Evaluate a PPT based on given criteria, returning an overview, explanation, and score.
        
        Args:
            criteria (str): User-defined evaluation criteria.
            ppt (dict): Dictionary containing PPT details (e.g., 'id', 'text').
        
        Returns:
            dict: Contains 'overview', 'explanation', and 'score' for the PPT.
        """
        # Extract text from the presentation
        text = ppt.get("text", "No content available for this presentation.")
        filename = ppt.get("file_name", "Unknown Presentation")
        
        logging.info(f"Evaluating {filename} with {len(text)} characters of text")
        
        try:
            # Use a fragment of the presentation text for context
            context = text[:3000]  # Limit to first 3000 chars to avoid token limits
            
            # Construct the system prompt
            system_message = """
            You are an expert presentation evaluator for hackathon projects. Your job is to evaluate 
            presentations based on given criteria and provide detailed, constructive feedback.
            Format your response as a JSON object with the following structure:
            {
                "overview": "Brief summary of the presentation content",
                "explanation": "Detailed evaluation with specific points for each criterion",
                "score": numeric_score_from_0_to_100
            }
            """
            
            # Construct the user prompt
            user_message = f"""
            Based on the following criteria:
            
            {criteria}
            
            Evaluate this presentation: {filename}
            
            Here is the presentation content:
            {context}
            
            Provide a JSON object with your evaluation.
            """
            
            # Different approach: Use a direct string prompt format that works with Pathway
            prompt = f"{system_message}\n\n{user_message}"
            
            # Create a direct call to the LLM
            try:
                # Use a manual approach to call LLM
                import os
                import google.generativeai as genai
                from litellm import completion
                
                # Make sure we have an API key
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    from config import GEMINI_API_KEY
                    api_key = GEMINI_API_KEY
                    os.environ["GEMINI_API_KEY"] = api_key
                
                # Initialize Gemini API
                genai.configure(api_key=api_key)
                
                # Create a direct model call
                response = completion(
                    model="gemini/gemini-1.5-flash",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1
                )
                
                # Extract the response text
                response_text = response.choices[0].message.content
                logging.info(f"Got response from LLM for {filename}")
                
                # Parse the JSON response
                try:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```|({[\s\S]*})', response_text)
                    
                    if json_match:
                        json_str = json_match.group(1) or json_match.group(2)
                        evaluation = json.loads(json_str)
                    else:
                        # Try to parse the whole response
                        evaluation = json.loads(response_text)
                    
                    overview = evaluation.get("overview", "Overview not available")
                    explanation = evaluation.get("explanation", "Explanation not available")
                    score = int(evaluation.get("score", 0))
                    
                    logging.info(f"Successfully parsed JSON for {filename}")
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error for {filename}: {str(e)}")
                    logging.error(f"Response was: {response_text[:200]}...")
                    
                    # Fallback to pattern matching
                    lines = response_text.strip().split('\n')
                    overview_line = next((line for line in lines if "overview" in line.lower()), None)
                    explanation_line = next((line for line in lines if "explanation" in line.lower()), None)
                    score_line = next((line for line in lines if "score" in line.lower()), None)
                    
                    overview = overview_line.split(":", 1)[1].strip() if overview_line else "Overview not available"
                    explanation = explanation_line.split(":", 1)[1].strip() if explanation_line else "Explanation not available"
                    
                    # Try to extract score
                    try:
                        score = int(''.join(filter(str.isdigit, score_line))) if score_line else 0
                    except:
                        score = 0
            except Exception as e:
                logging.error(f"Error during LLM API call for {filename}: {str(e)}")
                overview = f"Error calling LLM API: {str(e)}"
                explanation = "Unable to complete evaluation"
                score = 0
                
        except Exception as e:
            logging.error(f"Error in evaluate_ppt_async for {filename}: {str(e)}")
            overview = f"Error during evaluation: {str(e)}"
            explanation = "Unable to complete evaluation"
            score = 0
        
        return {
            "overview": overview,
            "explanation": explanation,
            "score": score
        }
    
    def build_server(self, host="0.0.0.0", port=8000):
        """Store server configuration"""
        self.host = host
        self.port = port
    
    def run_server(self):
        """Run the FastAPI server"""
        uvicorn.run(self.app, host=self.host, port=self.port)


def setup_evaluator(llm, doc_store):
    """Setup the RAG-based presentation evaluator"""
    
    logging.info("Setting up presentation evaluator")
    
    # Create the evaluator
    evaluator = PresentationEvaluator(llm, doc_store)
    
    logging.info("Evaluator setup complete")
    return evaluator
