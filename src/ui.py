#ui.py 
import streamlit as st
import requests
import json
import logging
import config
import time
import os
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_streamlit_ui():
    """Set up the Streamlit UI for the PPT evaluator"""
    st.set_page_config(
        page_title="Hackathon PPT Evaluator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 Hackathon PPT Evaluator")
    st.subheader("Evaluate PowerPoint presentations using Gemini and Pathway")
    
    # Sidebar for additional information and controls
    with st.sidebar:
        st.header("About")
        st.info(
            """
            This application uses Retrieval-Augmented Generation (RAG) to evaluate 
            PowerPoint presentations for hackathons. Upload your presentations to 
            the 'data' folder, and they will be automatically evaluated based on 
            your criteria.
            """
        )
        
        st.header("How to use")
        st.markdown(
            """
            1. Upload presentations using the form below
            2. Enter your evaluation criteria in the text box
            3. Click 'Evaluate Presentations'
            4. View the ranked list of presentations
            """
        )
        
        # Upload files to data directory
        st.header("Upload Presentations")
        uploaded_files = st.file_uploader("Upload PDF presentations", type=['pdf'], accept_multiple_files=True)
        
        if uploaded_files:
            data_dir = Path("./data")
            data_dir.mkdir(exist_ok=True)
            
            for uploaded_file in uploaded_files:
                file_path = data_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Saved {uploaded_file.name}")
            
            # Option to restart server after upload
            if st.button("Restart Server to Process New Files"):
                st.info("Attempting to restart the server...")
                try:
                    # This is a very simplified approach - in a real app you'd use a more robust method
                    subprocess.Popen(["python", "main.py"])
                    st.success("Server restart initiated. Please wait a few moments.")
                    time.sleep(5)  # Give the server time to start
                except Exception as e:
                    st.error(f"Failed to restart server: {str(e)}")

def check_server_status():
    """Check if the backend server is running"""
    try:
        response = requests.get(
            f"http://{config.APP_HOST}:{config.APP_PORT}/docs",  # FastAPI automatic docs endpoint
            timeout=2
        )
        return response.status_code == 200
    except:
        return False

def fetch_rankings(criteria):
    """Fetch rankings from the evaluation API"""
    try:
        server_url = f"http://{config.APP_HOST}:{config.APP_PORT}/v1/evaluate_ppts"
        logging.info(f"Sending request to: {server_url}")
        
        response = requests.post(
            server_url,
            json={"criteria": criteria},
            timeout=60  # Longer timeout for evaluation
        )
        
        logging.info(f"Response status code: {response.status_code}")
        
        # Check if the response is successful
        if response.status_code != 200:
            logging.error(f"API error: {response.status_code} - {response.text}")
            return {"error": f"API returned status {response.status_code}: {response.text}"}
        
        # Try to parse the response
        try:
            result = response.json()
            logging.info(f"Response type: {type(result)}")
            
            # Debug: log the first part of the response
            log_result = str(result)[:500] + "..." if len(str(result)) > 500 else str(result)
            logging.info(f"Response data: {log_result}")
            
            # Handle various response formats
            if isinstance(result, dict) and "error" in result:
                return {"error": result["error"]}
            
            if isinstance(result, str):
                # Try to parse string as JSON
                try:
                    parsed = json.loads(result)
                    return parsed if isinstance(parsed, list) else [parsed]
                except:
                    return [{"overview": result, "explanation": "", "score": 0, "file_name": "Unknown"}]
            
            if not isinstance(result, list):
                return [result] if result else []
                
            return result
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {str(e)}")
            # Try to return the raw text
            return [{"overview": response.text, "explanation": "Could not parse server response", "score": 0, "file_name": "Response parsing error"}]
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error calling evaluation API: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        logging.error(f"Unexpected error in fetch_rankings: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

def check_data_directory():
    """Check if there are PDF files in the data directory"""
    data_dir = Path("./data")
    if not data_dir.exists():
        return "Data directory does not exist"
    
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        return "No PDF files found in data directory"
    
    return f"Found {len(pdf_files)} PDF files in data directory: {', '.join(f.name for f in pdf_files)}"

def display_results(results):
    """Display evaluation results in a structured format"""
    if not results:
        st.info("No presentations evaluated. Click 'Evaluate Presentations' to start.")
        return
        
    # Check if results is an error message
    if isinstance(results, dict) and "error" in results:
        st.error(f"Error: {results['error']}")
        return
        
    st.write("## Ranked Presentations")
    
    # Create a summary table
    summary_data = {
        "Presentation": [],
        "Score": [],
        "Overview": []
    }
    
    for item in results:
        if not isinstance(item, dict):
            st.error(f"Invalid result format: {item}")
            continue
            
        # Safely extract data with fallbacks
        filename = item.get("file_name", "Unknown")
        score = item.get("score", 0)
        overview = item.get("overview", "Not available")
        
        # Truncate overview for the summary table
        short_overview = overview[:100] + "..." if len(overview) > 100 else overview
        
        summary_data["Presentation"].append(filename)
        summary_data["Score"].append(f"{score}/100")
        summary_data["Overview"].append(short_overview)
    
    st.dataframe(summary_data, use_container_width=True)
    
    # Display detailed results
    st.write("## Detailed Evaluations")
    for item in results:
        if not isinstance(item, dict):
            st.error(f"Invalid result format: {item}")
            continue
            
        filename = item.get("file_name", "Unknown")
        score = item.get("score", 0)
        
        with st.expander(f"{filename} - Score: {score}/100"):
            st.write(f"**Overview**")
            st.write(item.get("overview", "Not available"))
            
            st.write(f"**Evaluation**")
            st.write(item.get("explanation", "Not available"))
            
            if "file_id" in item:
                st.write(f"**File ID**: {item.get('file_id', 'Unknown')}")

def main():
    """Main function for the Streamlit UI"""
    setup_streamlit_ui()
    
    # Initialize session state
    if "criteria" not in st.session_state:
        st.session_state.criteria = ""
    if "results" not in st.session_state:
        st.session_state.results = []
    
    # Display server status
    server_status = check_server_status()
    if server_status:
        st.success("✅ Backend server is running")
    else:
        st.error("❌ Backend server is not running. Please start the server using 'python main.py'")
        
    # Check data directory
    data_status = check_data_directory()
    st.info(data_status)
    
    # Input for evaluation criteria
    criteria = st.text_area(
        "Enter evaluation criteria:",
        value=st.session_state.criteria,
        height=200,
        placeholder="""Example: Evaluate each presentation on technical innovation (0-25 points), problem clarity (0-20 points), implementation feasibility (0-20 points), visual quality (0-15 points), and business potential (0-20 points)."""
    )
    
    # Evaluation buttons
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        evaluate_button = st.button("Evaluate Presentations", type="primary", disabled=not server_status)
    
    with col2:
        refresh_button = st.button("Refresh Results", disabled=not server_status)
        
    with col3:
        if st.button("Clear Results"):
            st.session_state.results = []
            st.experimental_rerun()
    
    # Handle button clicks
    if evaluate_button and server_status:
        if criteria:
            with st.spinner("Evaluating presentations... This may take a minute or two."):
                st.session_state.criteria = criteria
                st.session_state.results = fetch_rankings(criteria)
        else:
            st.warning("Please enter evaluation criteria first.")
    
    if refresh_button and server_status:
        if st.session_state.criteria:
            with st.spinner("Refreshing results..."):
                st.session_state.results = fetch_rankings(st.session_state.criteria)
        else:
            st.warning("Please enter criteria before refreshing.")
    
    # Display results
    display_results(st.session_state.results)
    
    # Show debugging information in an expander
    with st.expander("Debug Information"):
        st.write("### Server Configuration")
        st.write(f"Host: {config.APP_HOST}")
        st.write(f"Port: {config.APP_PORT}")
        st.write(f"Server URL: http://{config.APP_HOST}:{config.APP_PORT}")
        
        st.write("### Current Session State")
        st.write(f"Criteria length: {len(st.session_state.criteria)} characters")
        st.write(f"Results count: {len(st.session_state.results) if isinstance(st.session_state.results, list) else 'N/A'}")
        
        # Display the data directory content
        st.write("### Data Directory Content")
        data_dir = Path("./data")
        if data_dir.exists():
            files = list(data_dir.glob("*"))
            if files:
                for file in files:
                    st.write(f"- {file.name} ({file.stat().st_size} bytes)")
            else:
                st.write("No files in data directory")
        else:
            st.write("Data directory does not exist")

if __name__ == "__main__":
    main()