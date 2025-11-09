# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# import pandas as pd
# import os
# import sys
# from pathlib import Path
# from typing import Optional, List
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Add the app directory to the Python path
# sys.path.insert(0, str(Path(__file__).parent))

# from rag_trading_bot import create_rag_bot, analyze_stock

# # Lifespan event handler
# from contextlib import asynccontextmanager

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Initialize the RAG bot and load stock data on startup"""
#     global qa_bot, stock_data

#     try:
#         # Check API key
#         if not os.getenv("GOOGLE_API_KEY"):
#             print("⚠️  Warning: GOOGLE_API_KEY not set!")
#         else:
#             qa_bot = create_rag_bot()

#         # Load stock data
#         stock_data = pd.read_csv("data/processed/stock_data_with_indicators.csv")
#         stock_data['tradedate'] = pd.to_datetime(stock_data['tradedate'])
#         print(f"✅ Loaded {len(stock_data)} records for {stock_data['symbol'].nunique()} symbols")

#     except Exception as e:
#         print(f"❌ Error during startup: {str(e)}")

#     yield

#     # Cleanup on shutdown
#     print("👋 Shutting down...")

# # Initialize FastAPI app
# app = FastAPI(
#     title="NEPSE Trading Bot API",
#     description="AI-Powered Stock Analysis API for Nepal Stock Exchange",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for development
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Mount static files
# static_path = Path(__file__).parent.parent / "static"
# if static_path.exists():
#     app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# # Global variables
# qa_bot = None
# stock_data = None

# # Pydantic models
# class AnalysisRequest(BaseModel):
#     symbol: str
#     strategy: Optional[str] = "multi-strategy"

# class AnalysisResponse(BaseModel):
#     symbol: str
#     strategy: str
#     analysis: str
#     success: bool
#     error: Optional[str] = None

# class StockInfo(BaseModel):
#     symbol: str
#     close: float
#     volume: int
#     rsi: float
#     ma20: float
#     ma50: float
#     diff_percent: float
#     week_52_high: float

# class StockListResponse(BaseModel):
#     symbols: List[str]
#     count: int

# # Serve HTML frontend
# @app.get("/")
# async def serve_frontend():
#     """Serve the HTML frontend"""
#     static_path = Path(__file__).parent.parent / "static" / "index.html"
#     if static_path.exists():
#         return FileResponse(str(static_path))
#     return {
#         "status": "online",
#         "message": "NEPSE Trading Bot API is running",
#         "bot_initialized": qa_bot is not None,
#         "data_loaded": stock_data is not None
#     }

# # Health check endpoint
# @app.get("/api/status")
# async def api_status():
#     """API status endpoint"""
#     return {
#         "status": "online",
#         "message": "NEPSE Trading Bot API is running",
#         "bot_initialized": qa_bot is not None,
#         "data_loaded": stock_data is not None
#     }

# # Get all stock symbols
# @app.get("/stocks", response_model=StockListResponse)
# async def get_stocks():
#     """Get list of all available stock symbols"""
#     if stock_data is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")
    
#     symbols = sorted(stock_data['symbol'].unique().tolist())
#     return StockListResponse(symbols=symbols, count=len(symbols))

# # Get stock information
# @app.get("/stocks/{symbol}", response_model=StockInfo)
# async def get_stock_info(symbol: str):
#     """Get latest information for a specific stock"""
#     if stock_data is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")

#     symbol = symbol.upper()
#     stock_df = stock_data[stock_data['symbol'] == symbol]

#     if stock_df.empty:
#         raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

#     latest = stock_df.sort_values('tradedate').iloc[-1]

#     # Helper function to convert NaN to 0 for required fields
#     def safe_float(val, default=0.0):
#         return default if pd.isna(val) else float(val)

#     def safe_int(val, default=0):
#         return default if pd.isna(val) else int(val)

#     return StockInfo(
#         symbol=latest['symbol'],
#         close=safe_float(latest['close']),
#         volume=safe_int(latest['vol']),
#         rsi=safe_float(latest['RSI']),
#         ma20=safe_float(latest['MA20']),
#         ma50=safe_float(latest['MA50']),
#         diff_percent=safe_float(latest['diff %']),
#         week_52_high=safe_float(latest['52 weeks high'])
#     )

# # Analyze stock endpoint
# @app.post("/analyze", response_model=AnalysisResponse)
# async def analyze(request: AnalysisRequest):
#     """Analyze a stock and get AI-powered trading recommendation"""
#     if qa_bot is None:
#         raise HTTPException(
#             status_code=503, 
#             detail="RAG bot not initialized. Please set GOOGLE_API_KEY environment variable."
#         )
    
#     if stock_data is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")
    
#     symbol = request.symbol.upper()
    
#     # Check if stock exists
#     if symbol not in stock_data['symbol'].values:
#         raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
#     try:
#         # Perform analysis
#         analysis_result = analyze_stock(qa_bot, symbol, request.strategy)
        
#         return AnalysisResponse(
#             symbol=symbol,
#             strategy=request.strategy,
#             analysis=analysis_result,
#             success=True
#         )
    
#     except Exception as e:
#         return AnalysisResponse(
#             symbol=symbol,
#             strategy=request.strategy,
#             analysis="",
#             success=False,
#             error=str(e)
#         )

# # Get technical indicators
# @app.get("/stocks/{symbol}/indicators")
# async def get_indicators(symbol: str):
#     """Get latest technical indicators for a stock"""
#     if stock_data is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")

#     symbol = symbol.upper()
#     stock_df = stock_data[stock_data['symbol'] == symbol]

#     if stock_df.empty:
#         raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

#     latest = stock_df.sort_values('tradedate').iloc[-1]

#     # Helper function to convert NaN to None
#     def safe_float(val):
#         return None if pd.isna(val) else float(val)

#     def safe_int(val):
#         return None if pd.isna(val) else int(val)

#     return {
#         "symbol": symbol,
#         "date": latest['tradedate'].strftime('%Y-%m-%d'),
#         "price": {
#             "close": safe_float(latest['close']),
#             "open": safe_float(latest['open']),
#             "high": safe_float(latest['high']),
#             "low": safe_float(latest['low']),
#             "vwap": safe_float(latest['vwap'])
#         },
#         "moving_averages": {
#             "ma20": safe_float(latest['MA20']),
#             "ma50": safe_float(latest['MA50'])
#         },
#         "momentum": {
#             "rsi": safe_float(latest['RSI']),
#             "macd": safe_float(latest['MACD']),
#             "macd_signal": safe_float(latest['MACD_Signal']),
#             "macd_histogram": safe_float(latest['MACD_Hist'])
#         },
#         "bollinger_bands": {
#             "upper": safe_float(latest['BB_UPPER']),
#             "middle": safe_float(latest['BB_MID']),
#             "lower": safe_float(latest['BB_LOWER'])
#         },
#         "volume": safe_int(latest['vol']),
#         "change_percent": safe_float(latest['diff %'])
#     }

# # if __name__ == "__main__":
# #     import uvicorn
# #     uvicorn.run(app, host="0.0.0.0", port=8000)
# if __name__ == "__main__":
#     import uvicorn
#     import os


# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# import pandas as pd
# import os
# import sys
# from pathlib import Path
# from typing import Optional, List
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Add the app directory to the Python path
# sys.path.insert(0, str(Path(__file__).parent))

# from rag_trading_bot import create_rag_bot, analyze_stock

# # -----------------------------
# # Global variables
# # -----------------------------
# qa_bot: Optional[any] = None
# stock_data: Optional[pd.DataFrame] = None

# # -----------------------------
# # FastAPI initialization
# # -----------------------------
# app = FastAPI(
#     title="NEPSE Trading Bot API",
#     description="AI-Powered Stock Analysis API for Nepal Stock Exchange",
#     version="1.0.0",
# )

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for development
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Mount static files
# static_path = Path(__file__).parent.parent / "static"
# if static_path.exists():
#     app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# # -----------------------------
# # Helper functions for lazy loading
# # -----------------------------
# def get_qa_bot():
#     global qa_bot
#     if qa_bot is None:
#         if not os.getenv("GOOGLE_API_KEY"):
#             print("⚠️  Warning: GOOGLE_API_KEY not set!")
#         else:
#             qa_bot = create_rag_bot()
#             print("✅ RAG bot initialized")
#     return qa_bot

# def get_stock_data():
#     global stock_data
#     if stock_data is None:
#         try:
#             stock_data = pd.read_csv("data/processed/stock_data_with_indicators.csv")
#             stock_data['tradedate'] = pd.to_datetime(stock_data['tradedate'])
#             print(f"✅ Loaded {len(stock_data)} records for {stock_data['symbol'].nunique()} symbols")
#         except Exception as e:
#             print(f"❌ Failed to load stock data: {e}")
#     return stock_data

# # -----------------------------
# # Pydantic models
# # -----------------------------
# class AnalysisRequest(BaseModel):
#     symbol: str
#     strategy: Optional[str] = "multi-strategy"

# class AnalysisResponse(BaseModel):
#     symbol: str
#     strategy: str
#     analysis: str
#     success: bool
#     error: Optional[str] = None

# class StockInfo(BaseModel):
#     symbol: str
#     close: float
#     volume: int
#     rsi: float
#     ma20: float
#     ma50: float
#     diff_percent: float
#     week_52_high: float

# class StockListResponse(BaseModel):
#     symbols: List[str]
#     count: int

# # -----------------------------
# # Endpoints
# # -----------------------------
# @app.get("/")
# async def serve_frontend():
#     """Serve the HTML frontend"""
#     index_file = Path(__file__).parent.parent / "static" / "index.html"
#     if index_file.exists():
#         return FileResponse(str(index_file))
#     return {
#         "status": "online",
#         "message": "NEPSE Trading Bot API is running",
#         "bot_initialized": qa_bot is not None,
#         "data_loaded": stock_data is not None
#     }

# @app.get("/api/status")
# async def api_status():
#     """API status endpoint"""
#     return {
#         "status": "online",
#         "message": "NEPSE Trading Bot API is running",
#         "bot_initialized": qa_bot is not None,
#         "data_loaded": stock_data is not None
#     }

# @app.get("/stocks", response_model=StockListResponse)
# async def get_stocks():
#     df = get_stock_data()
#     if df is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")
#     symbols = sorted(df['symbol'].unique().tolist())
#     return StockListResponse(symbols=symbols, count=len(symbols))

# @app.get("/stocks/{symbol}", response_model=StockInfo)
# async def get_stock_info(symbol: str):
#     df = get_stock_data()
#     if df is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")

#     symbol = symbol.upper()
#     stock_df = df[df['symbol'] == symbol]
#     if stock_df.empty:
#         raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
#     latest = stock_df.sort_values('tradedate').iloc[-1]

#     def safe_float(val, default=0.0): return default if pd.isna(val) else float(val)
#     def safe_int(val, default=0): return default if pd.isna(val) else int(val)

#     return StockInfo(
#         symbol=latest['symbol'],
#         close=safe_float(latest['close']),
#         volume=safe_int(latest['vol']),
#         rsi=safe_float(latest['RSI']),
#         ma20=safe_float(latest['MA20']),
#         ma50=safe_float(latest['MA50']),
#         diff_percent=safe_float(latest['diff %']),
#         week_52_high=safe_float(latest['52 weeks high'])
#     )

# @app.post("/analyze", response_model=AnalysisResponse)
# async def analyze(request: AnalysisRequest):
#     bot = get_qa_bot()
#     df = get_stock_data()
    
#     if bot is None:
#         raise HTTPException(status_code=503, detail="RAG bot not initialized")
#     if df is None:
#         raise HTTPException(status_code=503, detail="Stock data not loaded")

#     symbol = request.symbol.upper()
#     if symbol not in df['symbol'].values:
#         raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

#     try:
#         analysis_result = analyze_stock(bot, symbol, request.strategy)
#         return AnalysisResponse(symbol=symbol, strategy=request.strategy, analysis=analysis_result, success=True)
#     except Exception as e:
#         return AnalysisResponse(symbol=symbol, strategy=request.strategy, analysis="", success=False, error=str(e))

# # -----------------------------
# # Run app
# # -----------------------------
# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))  # <-- Render-compatible port
#     uvicorn.run(app, host="0.0.0.0", port=port)





# ============================================================================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
import sys
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from rag_trading_bot import create_rag_bot, analyze_stock

# -----------------------------
# Global variables
# -----------------------------
qa_bot: Optional[any] = None
stock_data: Optional[pd.DataFrame] = None

# -----------------------------
# FastAPI initialization
# -----------------------------
app = FastAPI(
    title="NEPSE Trading Bot API",
    description="AI-Powered Stock Analysis API for Nepal Stock Exchange",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# -----------------------------
# Helper functions for lazy loading
# -----------------------------
def get_qa_bot():
    global qa_bot
    if qa_bot is None:
        if not os.getenv("GOOGLE_API_KEY"):
            print("⚠️  Warning: GOOGLE_API_KEY not set!")
        else:
            qa_bot = create_rag_bot()
            print("✅ RAG bot initialized")
    return qa_bot

def get_stock_data():
    global stock_data
    if stock_data is None:
        try:
            # Use relative path for portability
            data_file = Path(__file__).parent.parent / "data/processed/stock_data_with_indicators.csv"
            stock_data = pd.read_csv(data_file)
            stock_data['tradedate'] = pd.to_datetime(stock_data['tradedate'])
            print(f"✅ Loaded {len(stock_data)} records for {stock_data['symbol'].nunique()} symbols")
        except Exception as e:
            print(f"❌ Failed to load stock data: {e}")
    return stock_data

# -----------------------------
# Pydantic models
# -----------------------------
class AnalysisRequest(BaseModel):
    symbol: str
    strategy: Optional[str] = "multi-strategy"

class AnalysisResponse(BaseModel):
    symbol: str
    strategy: str
    analysis: str
    success: bool
    error: Optional[str] = None

class StockInfo(BaseModel):
    symbol: str
    close: float
    volume: int
    rsi: float
    ma20: float
    ma50: float
    diff_percent: float
    week_52_high: float

class StockListResponse(BaseModel):
    symbols: List[str]
    count: int

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
async def serve_frontend():
    """Serve the HTML frontend"""
    index_file = Path(__file__).parent.parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "status": "online",
        "message": "NEPSE Trading Bot API is running",
        "bot_initialized": qa_bot is not None,
        "data_loaded": stock_data is not None
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "online",
        "message": "NEPSE Trading Bot API is running",
        "bot_initialized": qa_bot is not None,
        "data_loaded": stock_data is not None
    }

@app.get("/stocks", response_model=StockListResponse)
async def get_stocks():
    df = get_stock_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Stock data not loaded")
    symbols = sorted(df['symbol'].unique().tolist())
    return StockListResponse(symbols=symbols, count=len(symbols))

@app.get("/stocks/{symbol}", response_model=StockInfo)
async def get_stock_info(symbol: str):
    df = get_stock_data()
    if df is None:
        raise HTTPException(status_code=503, detail="Stock data not loaded")

    symbol = symbol.upper()
    stock_df = df[df['symbol'] == symbol]
    if stock_df.empty:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    latest = stock_df.sort_values('tradedate').iloc[-1]

    def safe_float(val, default=0.0): return default if pd.isna(val) else float(val)
    def safe_int(val, default=0): return default if pd.isna(val) else int(val)

    return StockInfo(
        symbol=latest['symbol'],
        close=safe_float(latest['close']),
        volume=safe_int(latest['vol']),
        rsi=safe_float(latest['RSI']),
        ma20=safe_float(latest['MA20']),
        ma50=safe_float(latest['MA50']),
        diff_percent=safe_float(latest['diff %']),
        week_52_high=safe_float(latest['52 weeks high'])
    )

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    bot = get_qa_bot()
    df = get_stock_data()
    
    if bot is None:
        raise HTTPException(status_code=503, detail="RAG bot not initialized")
    if df is None:
        raise HTTPException(status_code=503, detail="Stock data not loaded")

    symbol = request.symbol.upper()
    if symbol not in df['symbol'].values:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    try:
        analysis_result = analyze_stock(bot, symbol, request.strategy)
        return AnalysisResponse(symbol=symbol, strategy=request.strategy, analysis=analysis_result, success=True)
    except Exception as e:
        return AnalysisResponse(symbol=symbol, strategy=request.strategy, analysis="", success=False, error=str(e))

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # <-- Render-compatible port
    uvicorn.run(app, host="0.0.0.0", port=port)


#     port = int(os.environ.get("PORT", 8000))  # <-- ✅ this line changed
#     uvicorn.run(app, host="0.0.0.0", port=port)


