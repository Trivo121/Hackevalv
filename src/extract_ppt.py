#Extrct_ppt.py
import logging
import os
from pathlib import Path
import PyPDF2
from functools import reduce as py_reduce

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

class Document:
    """A simple wrapper for document data that provides helper methods."""
    def __init__(self, data: dict):
        self.data = data

    def column_names(self):
        return list(self.data.keys())

    def __getitem__(self, key):
        return self.data[key]

    def __repr__(self):
        return f"Document({self.data})"

    def with_columns(self, **kwargs):
        """Return a new Document with updated columns."""
        new_data = self.data.copy()
        new_data.update(kwargs)
        return Document(new_data)

    def select(self, *cols):
        """Return a new Document containing only the specified columns."""
        selected = {col: self.data.get(col) for col in cols if col in self.data}
        return Document(selected)

    def concat_reindex(self, *others):
        """Concatenate this document with others into a Table."""
        return Table([self] + list(others))

def extract_pdf_content(file_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        logging.info(f"Extracting content from {file_path}")
        text = []
        with file_path.open('rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            logging.info(f"PDF has {len(reader.pages)} pages")
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    text.append(f"Page {page_num}:\n{page_text}")
                else:
                    logging.warning(f"No text extracted from page {page_num}")
        
        result = "\n".join(text)
        logging.info(f"Extracted {len(result)} characters from {file_path}")
        return result
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return ""

def setup_sources():
    """
    Set up data sources by reading all PDF files from the './data' directory.
    Each source is returned as a Document instance.
    """
    pdf_dir = Path("./data")
    
    # Create directory if it doesn't exist
    if not pdf_dir.exists():
        logging.info(f"Creating data directory: {pdf_dir}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Look for files with common presentation extensions
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    all_files = pdf_files
    
    if not all_files:
        logging.warning(f"No presentation files found in directory: {pdf_dir}")
        # List all files in directory for debugging
        all_directory_files = list(pdf_dir.glob("*"))
        if all_directory_files:
            logging.info(f"Other files in directory: {', '.join(str(f) for f in all_directory_files)}")
        else:
            logging.info("Directory is empty")
        return []
    
    sources = []
    for pdf_file in all_files:
        logging.info(f"Processing file: {pdf_file}")
        content = extract_pdf_content(pdf_file)
        
        if not content.strip():
            logging.warning(f"No content extracted from {pdf_file}")
            continue
            
        doc_data = {
            "file_path": str(pdf_file), 
            "text": content,
            "file_name": pdf_file.name,
            "metadata": {"source": pdf_file.name}  # Add metadata for better compatibility
        }
        sources.append(Document(doc_data))
        
    logging.info(f"Processed {len(sources)} files successfully")
    return sources

# Column class to wrap a column of values and provide a .table attribute.
class Column:
    def __init__(self, table, name, values):
        self.table = table
        self.name = name
        self.values = values

    def as_list(self):
        return self.values

    def __repr__(self):
        return f"Column({self.name}, {self.values})"

class Table:
    """A minimal Table class to wrap a list of Document objects."""
    def __init__(self, docs):
        self.docs = docs

    @property
    def _metadata(self):
        # Return an empty dict for each document as metadata.
        return [{} for _ in self.docs]

    @property
    def data(self):
        """
        Return a dictionary mapping column names to Column objects.
        Each Column wraps a list of values from the documents.
        """
        columns = {}
        for doc in self.docs:
            for key, value in doc.data.items():
                columns.setdefault(key, []).append(value)
        # Ensure a 'metadata' column exists.
        if "metadata" not in columns:
            columns["metadata"] = self._metadata
        return { key: Column(self, key, values) for key, values in columns.items() }

    @property
    def text(self):
        """Return the 'text' column as a Column object."""
        return self.data.get("text", Column(self, "text", []))

    @property
    def _pw_embedded_column(self):
        """
        Provide the column to be used for generating embeddings.
        Here, we assume that the "text" column should be embedded.
        """
        return self.text

    def select(self, *cols, **kwargs):
        if cols:
            new_docs = [doc.select(*cols) for doc in self.docs]
        else:
            new_docs = self.docs
        if kwargs:
            new_docs = [doc.with_columns(**kwargs) for doc in new_docs]
        return Table(new_docs)

    def with_columns(self, **kwargs):
        """
        Update each document in the table with new columns.
        Returns a new Table.
        """
        new_docs = [doc.with_columns(**kwargs) for doc in self.docs]
        return Table(new_docs)

    def flatten(self, *args, **kwargs):
        """Accept extra arguments to match expected signature; return self."""
        return self

    def concat_reindex(self, *others):
        new_docs = self.docs[:]
        for other in others:
            if isinstance(other, Table):
                new_docs.extend(other.docs)
            else:
                new_docs.append(other)
        return Table(new_docs)

    def reduce(self, func=lambda values, **kwargs: values, **kwargs):
        """
        Apply a reduction function to each column's list of values.
        The function 'func' should accept a list of values and return an aggregated result.
        If no function is provided, the default returns the list as is.
        Returns a new Document containing the reduced columns.
        """
        reduced = {}
        for key, col in self.data.items():
            reduced[key] = func(col.values, **kwargs)
        return Document(reduced)

    def __add__(self, other):
        if isinstance(other, Table):
            return Table(self.docs + other.docs)
        else:
            raise TypeError("Can only add Table to Table")

    def __iadd__(self, other):
        if isinstance(other, Table):
            self.docs += other.docs
            return self
        else:
            raise TypeError("Can only add Table to Table")

    def __iter__(self):
        return iter(self.docs)

    def __getitem__(self, index):
        return self.docs[index]

    def __repr__(self):
        return f"Table({self.docs})"

if __name__ == "__main__":
    sources = setup_sources()
    # For demonstration, print out each document.
    for doc in sources:
        print(doc)
