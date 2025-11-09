NEPSE Trading Bot

This is an AI-powered stock analysis system for the Nepal Stock Exchange (NEPSE), built as part of my internship assignment under Ashish Sir at Brand Builder. The bot provides actionable trading recommendations using RAG (Retrieval-Augmented Generation) and technical analysis.

Features

Data-Driven Insights: Uses 60 days of NEPSE stock data across all sectors.

Technical Indicators: MA20/MA50, RSI, MACD, Bollinger Bands, VWAP, and more.

AI-Powered Recommendations: Generates BUY/SELL/HOLD actions with confidence scores using Google Gemini-2.0-flash-exp.

Vector Database: Data is chunked, embedded with HuggingFace Sentence Transformers, and stored in FAISS for efficient retrieval.

Interactive Frontend: Built using HTML, CSS, and JavaScript.

API Backend: Implemented with FastAPI for serving real-time recommendations.

How It Works

Data Collection & Preprocessing: Fetches the last 60 days of NEPSE stock data and prepares it for analysis.

Embedding & Storage: Chunked data is embedded and stored in a FAISS vectorstore.

Recommendation Generation: A large language model (Google Gemini-2.0-flash-exp) reads the data and outputs structured recommendations including:

Technical indicator analysis

Actionable advice (BUY/SELL/HOLD)

Confidence levels

Risk factors and action plan

Frontend & API: Users can interact with the bot through the web interface or via the FastAPI endpoints.


Tech Stack

Backend: FastAPI, Python

Frontend: HTML, CSS, JavaScript

AI/ML: Google Gemini-2.0-flash-exp, HuggingFace Transformers

Vector Database: FAISS

demo:https://nepse-trading-bot-7.onrender.com/
