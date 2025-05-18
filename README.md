# Hackathon PPT Evaluator

![Hackathon PPT Evaluator](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green)

A powerful and intelligent system for evaluating PowerPoint presentations in hackathon settings using Retrieval-Augmented Generation (RAG) with Gemini and Pathway.

## 🚀 Overview

Hackathon PPT Evaluator is a specialized tool designed to automate and standardize the evaluation of hackathon presentations. The application leverages advanced AI and Natural Language Processing (NLP) techniques to analyze presentation content, provide detailed feedback, and generate objective scores based on customizable criteria.

By combining the power of Google's Gemini AI with Pathway's vector processing capabilities, this tool creates a seamless evaluation experience that helps hackathon organizers, judges, and participants alike.

## ✨ Key Features

- **Automated PDF Processing**: Automatically extracts and processes text from PDF presentations
- **Customizable Evaluation Criteria**: Define your own evaluation criteria and scoring weights
- **Intelligent Content Analysis**: Uses AI to understand presentation content and context
- **Detailed Feedback Generation**: Provides comprehensive feedback for each evaluation aspect
- **Intuitive User Interface**: Built with Streamlit for a clean, responsive experience
- **Presentation Ranking**: Automatically ranks presentations by score
- **REST API Integration**: Backend API for integration with other systems

## 🏗️ Architecture

The application follows a modular architecture with these main components:

1. **Data Processing Module (`extract_ppt.py`)**: Handles PDF extraction and document preparation
2. **Evaluation Engine (`evaluate.py`)**: Core evaluation logic using RAG and LLM technologies
3. **Web Service (`main.py`)**: FastAPI backend service for handling evaluation requests
4. **User Interface (`ui.py`)**: Streamlit-based frontend for user interactions

### Technology Stack:

- **Backend**: Python, FastAPI, Pathway, PyPDF2
- **AI/ML**: Google Gemini, Vector Embeddings, RAG (Retrieval Augmented Generation)
- **Frontend**: Streamlit
- **Infrastructure**: Docker-ready, configurable for cloud deployment

## 📋 Prerequisites

- Python 3.8 or higher
- Pathway license key
- Google Gemini API key

## 🔧 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/hackathon-ppt-evaluator.git
cd hackathon-ppt-evaluator
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a `config.py` file with your API keys:

```python
# config.py
GEMINI_API_KEY = "your_gemini_api_key"
PATHWAY_LICENSE_KEY = "your_pathway_license_key"
APP_HOST = "0.0.0.0"
APP_PORT = 8000
```

## 🚦 Usage

### Starting the Backend Server

1. Run the backend server:

```bash
python main.py
```

2. The server will start on the configured host and port (default: http://0.0.0.0:8000)

### Starting the UI

1. In a separate terminal, run the Streamlit UI:

```bash
streamlit run ui.py
```

2. Access the UI in your browser at http://localhost:8501

### Evaluating Presentations

1. Upload PDF presentations using the file uploader in the sidebar
2. Enter your evaluation criteria in the text area
3. Click "Evaluate Presentations"
4. View the ranked results and detailed feedback

### Example Evaluation Criteria

```
Evaluate each presentation on the following aspects:
1. Technical innovation (0-25 points): Assess the novelty of the solution, technical complexity, and use of cutting-edge technologies.
2. Problem clarity (0-20 points): How well the problem statement is defined and whether the solution addresses it directly.
3. Implementation feasibility (0-20 points): Evaluate if the solution can be realistically implemented within a hackathon timeframe.
4. Visual quality (0-15 points): Judge the clarity of diagrams, readability of text, and overall design coherence.
5. Business potential (0-20 points): Assess market opportunity, target audience definition, and potential for scaling.
Provide specific feedback for each criterion and justify the overall score.
```

## 🐳 Docker Support

Build and run the application using Docker:

```bash
# Build the Docker image
docker build -t hackathon-ppt-evaluator .

# Run the container
docker run -p 8000:8000 -p 8501:8501 -v $(pwd)/data:/app/data hackathon-ppt-evaluator
```

## 📂 Project Structure

```
ProjectFolder/
├── data/                # Directory for uploaded presentations
├── src/                 # Additional source files
├── __pycache__/         # Python cache files
├── config.py            # Configuration settings
├── evaluate.py          # Evaluation engine
├── extract_ppt.py       # PDF processing module
├── main.py              # FastAPI backend server
├── ui.py                # Streamlit UI
├── venv/                # Virtual environment
├── app.yaml             # Cloud deployment configuration
├── Dockerfile           # Docker configuration
├── README.md            # This documentation
└── requirements.txt     # Python dependencies
```

## 🔄 API Endpoints

- `POST /v1/evaluate_ppts`: Evaluates presentations based on provided criteria
- `POST /v1/chat`: Allows querying presentation content using natural language

## 🛠️ Customization

### Adjusting Evaluation Parameters

You can modify the RAG and evaluation parameters in `evaluate.py`:

```python
self.rag_app = BaseRAGQuestionAnswerer(
    llm=llm,
    indexer=doc_store,
    search_topk=3,  # Change to retrieve more/fewer chunks
)
```

### Configuring Document Processing

Adjust document chunking in `main.py`:

```python
splitter = splitters.TokenCountSplitter(
    chunk_size=1000,    # Size of each chunk
    chunk_overlap=100,  # Overlap between chunks
    model="models/embedding-001"
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Google Gemini AI](https://deepmind.google/technologies/gemini/) for the language model
- [Pathway](https://pathway.com/) for the vector processing infrastructure.
- [Streamlit](https://streamlit.io/) for the intuitive UI framework.
- [FastAPI](https://fastapi.tiangolo.com/) for the robust API backend.
- [PyPDF2](https://pythonhosted.org/PyPDF2/) for PDF processing capabilities.
