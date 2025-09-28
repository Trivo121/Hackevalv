#main.py
import os
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.udfs import ExponentialBackoffRetryStrategy
import logging
from extract_ppt import setup_sources
from evaluate import setup_evaluator
import config

def init_logging():
    """Initialize logging configuration""" 
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

def setup_gemini():
    """Set up and configure Gemini API"""
    os.environ["GEMINI_API_KEY"] = config.GEMINI_API_KEY
    os.environ["LITELLM_LOG"] = "DEBUG"  # Help with debugging

def setup_pathway():
    """Set up Pathway license"""
    pw.set_license_key(config.PATHWAY_LICENSE_KEY)

def setup_embedder():
    """Set up the document embedder"""
    return embedders.GeminiEmbedder(
        model="models/embedding-001",
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6, backoff_factor=2.5),
    )

def setup_llm():
    """Set up the language model for chat"""
    return llms.LiteLLMChat(
        model="gemini/gemini-1.5-flash",
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6, backoff_factor=2.5),
        temperature=0.0,
    )

def setup_parser():
    """Set up the document parser using the updated parser interface."""
    return parsers.ParseUnstructured() 

def setup_document_store(sources, embedder, parser):
    """Set up the document store"""
    # Changed initialization to match the API expected by your Pathway version
    # Use default initialization without extra parameters
    splitter = splitters.TokenCountSplitter()
    
    # Print information about sources and their content
    logging.info(f"Processing {len(sources)} sources from data folder")
    
    if sources:
        for i, source in enumerate(sources[:min(3, len(sources))]):
            logging.info(f"Source {i+1} sample: {source.data.get('file_path', 'unknown')}")
            logging.info(f"Source {i+1} text length: {len(source.data.get('text', ''))}")
    else:
        logging.warning("No sources found! Check data folder.")
    
    return pw.xpacks.llm.vector_store.VectorStoreServer(
        *sources,
        embedder=embedder,
        splitter=splitter,
        parser=parser,
    )

def main():
    """Main function to set up and run the RAG application"""
    # Initialize logging and configurations
    init_logging()
    logging.info("Starting PPT Evaluator application")
    
    # Create data directory if it doesn't exist
    data_dir = "./data"
    if not os.path.exists(data_dir):
        logging.info(f"Creating data directory: {data_dir}")
        os.makedirs(data_dir)
    else:
        logging.info(f"Data directory exists: {data_dir}")
        # List files in data directory
        files = os.listdir(data_dir)
        if files:
            logging.info(f"Files in data directory: {files}")
        else:
            logging.warning("No files found in data directory!")
    
    setup_gemini()
    setup_pathway()
    
    # Set up components
    embedder = setup_embedder()
    chat = setup_llm()
    parser = setup_parser()
    
    # Set up data sources 
    sources = setup_sources()
    if not sources:
        logging.error("No sources found! Make sure to add PDF files to the data folder.")
    
    # Create document store
    doc_store = setup_document_store(sources, embedder, parser)
    
    # Create the evaluator application
    app = setup_evaluator(chat, doc_store)
    
    # Build and run the server
    app_host = config.APP_HOST
    app_port = config.APP_PORT
    app.build_server(host=app_host, port=app_port)
    
    logging.info(f"Server running at http://{app_host}:{app_port}")
    app.run_server()

if __name__ == "__main__":
    main()
