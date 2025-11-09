import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from rag_data_loader import stock_to_text_chunks
from dotenv import load_dotenv
load_dotenv()

def build_vector_store(data_path="data/processed/stock_data_with_indicators.csv", 
                       vector_store_path="vectorstore/faiss_index",
                       last_n_days=60):
    """
    Build and save FAISS vector store from stock data.
    
    Args:
        data_path: Path to the CSV file with stock data and indicators
        vector_store_path: Path to save the FAISS index
        last_n_days: Number of recent days to include per stock
    """
    
    # Load and convert stock data to documents
    docs = stock_to_text_chunks(data_path, last_n_days=last_n_days)
    
    if not docs:
        print("❌ No documents found. Please check your data file.")
        return
    

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Create FAISS vector store
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
 
    vectorstore.save_local(vector_store_path)
   

if __name__ == "__main__":
    build_vector_store()

