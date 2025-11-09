
import os
import re
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_output(text):
    """
    Post-process the LLM output to ensure proper formatting.
    """
    # Fix numbered lists that are in paragraphs
    # Pattern: "1. Title: text 2. Title:" -> "1. Title:\n   text\n\n2. Title:"
    text = re.sub(r'(\d+)\.\s+([^:]+):\s+([^0-9]+?)(?=\d+\.|\n##|\Z)', 
                  r'\1. **\2:**\n   \3\n\n', text)
    
    # Ensure proper spacing after headers
    text = re.sub(r'(##[^#\n]+)\n(?!\n)', r'\1\n\n', text)
    text = re.sub(r'(###[^#\n]+)\n(?!\n)', r'\1\n\n', text)
    
    # Ensure double line breaks before major sections
    text = re.sub(r'(?<!\n)\n(## [🎯📊💡⚠️🎯🧠])', r'\n\n\1', text)
    
    # Fix bullet points spacing
    text = re.sub(r'\*\*([^:]+):\*\*(?!\n)', r'**\1:**\n', text)
    
    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def create_rag_bot():
    """
    Create a RAG-based trading bot using FAISS and Google Gemini.
    
    Returns:
        RetrievalQA chain for answering queries
    """
   
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    # Load FAISS vector store
    db = FAISS.load_local("vectorstore/faiss_index", embeddings, allow_dangerous_deserialization=True)
    
    # Create retriever
    retriever = db.as_retriever(search_kwargs={"k": 5})
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.2,  # Lower temperature for more consistent formatting
    )
    
    # Create prompt template with strict formatting
    prompt = ChatPromptTemplate.from_template("""
You are an expert NEPSE (Nepal Stock Exchange) trading analyst.

Context: {context}

Question: {question}

Provide analysis in this EXACT format. Each numbered point MUST start on a new line:



##  RECOMMENDATION

**Action:** [BUY/SELL/HOLD]

**Confidence Level:** [X%]



##  TECHNICAL INDICATOR ANALYSIS

### 1️⃣ Moving Averages (MA20, MA50)

1. **Current Values:** [State MA20 and MA50 values clearly]

2. **Trend Direction:** [Describe if uptrend, downtrend, or sideways]

3. **Signal:** [State Golden Cross, Death Cross, or No Signal]

4. **Decision Support:** [Explain how this supports your BUY/SELL/HOLD decision]

### 2️⃣ RSI (Relative Strength Index)

1. **Current RSI:** [State the exact RSI value]

2. **Interpretation:** [State Overbought (>70), Oversold (<30), or Neutral (30-70)]

3. **Market Condition:** [Describe the current market strength]

4. **Decision Support:** [Explain how this supports your BUY/SELL/HOLD decision]

### 3️⃣ MACD (Moving Average Convergence Divergence)

1. **MACD Position:** [State if MACD is above or below signal line]

2. **Crossover:** [State Bullish Crossover, Bearish Crossover, or No Crossover]

3. **Momentum:** [Describe if momentum is strengthening or weakening]

4. **Decision Support:** [Explain how this supports your BUY/SELL/HOLD decision]

### 4️⃣ Bollinger Bands

1. **Volatility:** [Describe current volatility - expanding, contracting, or normal]

2. **Breakout Potential:** [State if high, medium, or low breakout potential]

3. **Decision Support:** [Explain how this supports your BUY/SELL/HOLD decision]



##  WHY BUY / SELL / HOLD?

1. **[Title]:**
   [Explanation - write this on a new line]

2. **[Title]:**
   [Explanation - write this on a new line]

3. **[Title]:**
   [Explanation - write this on a new line]

4. **[Title]:**
   [Explanation - write this on a new line]



##  RISK FACTORS

1. **[Risk]:**
   [Description - write this on a new line]

2. **[Risk]:**
   [Description - write this on a new line]

3. **[Risk]:**
   [Description - write this on a new line]

4. **[Risk]:**
   [Description - write this on a new line]



##  ACTION PLAN

1. **Entry Price:** [Price]

2. **Stop Loss Level:** [Price]

3. **Target Price:** [Price]

4. **Time Horizon:** [Timeframe]



##  FINAL INSIGHT

[2-3 sentences summary]



CRITICAL: Each numbered item (1., 2., 3., etc.) MUST be on its own line. Never write "1. X 2. Y" in same paragraph.

Answer:
""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Create RAG chain with post-processing
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
        | format_output  # Add post-processing here
    )

    return rag_chain

def analyze_stock(rag_chain, symbol, strategy="multi-strategy"):
    """
    Analyze a stock using the RAG bot.
    """
    question = f"""
Analyze stock {symbol} for Buy, Sell, or Hold recommendation using a {strategy} approach.

Consider these strategies:
- **Trend-Following**: MA20, MA50 crossovers, MACD trends
- **Mean Reversion**: RSI overbought/oversold, Bollinger Band touches
- **Swing Trading**: Momentum shifts, volume patterns
- **Breakout/Pullback**: Support/resistance levels

Provide:
1. Recommendation (Buy/Sell/Hold) with confidence
2. Detailed technical explanation for each indicator
3. Clear reasoning with 4-5 points
4. Risk factors (4 points)
5. Action plan with entry/exit points
"""

    result = rag_chain.invoke(question)
    return result

if __name__ == "__main__":
    rag_chain = create_rag_bot()
    
   