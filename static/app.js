// API Configuration
// const API_URL = 'http://localhost:8000';
const API_URL = window.location.origin;

// State
let currentStock = null;
let apiStatus = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    loadStocks();
    setupEventListeners();
});

// Check API Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_URL}/api/status`);
        const data = await response.json();
        apiStatus = data;
        updateStatusIndicator(true, data.bot_initialized);
    } catch (error) {
        updateStatusIndicator(false, false);
        console.error('API connection failed:', error);
    }
}

// Update status indicator
function updateStatusIndicator(online, botInitialized) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');

    // If neither element exists (status box removed), nothing to update
    if (!statusDot && !statusText) return;

    if (online) {
        if (statusDot) {
            statusDot.classList.add('online');
            statusDot.classList.remove('offline');
        }

        if (statusText) {
            if (botInitialized) {
                // Show a simple online message when bot is initialized
                statusText.textContent = 'API Online';
            } else {
                statusText.textContent = '⚠️ API Online | RAG Bot Not Initialized';
            }
        }
    } else {
        if (statusDot) {
            statusDot.classList.add('offline');
            statusDot.classList.remove('online');
        }
        if (statusText) {
            statusText.textContent = '❌ API Offline';
        }
    }
}

// Load stocks
async function loadStocks() {
    const select = document.getElementById('stock-select');
    if (!select) return;
    select.innerHTML = '<option value="">Loading stocks...</option>';

    // First try the API
    try {
        const response = await fetch(`${API_URL}/stocks`);
        if (response.ok) {
            const data = await response.json();
            if (data && Array.isArray(data.symbols) && data.symbols.length) {
                select.innerHTML = '<option value="">Select a stock...</option>';
                data.symbols.forEach(stock => {
                    const option = document.createElement('option');
                    option.value = stock;
                    option.textContent = stock;
                    select.appendChild(option);
                });
                return;
            }
        }
    } catch (err) {
        console.warn('API /stocks fetch failed, will try local CSV fallback:', err);
    }

    // Fallback: try loading local CSV (useful when API isn't running)
    try {
        const csvResp = await fetch('data/processed/stock_data_with_indicators.csv');
        if (!csvResp.ok) throw new Error('CSV not found');
        const text = await csvResp.text();
        const lines = text.split(/\r?\n/).filter(Boolean);
        if (lines.length < 2) throw new Error('CSV empty');

        const header = lines[0].split(',').map(h => h.trim().toLowerCase());
        const symbolIdx = header.indexOf('symbol');
        if (symbolIdx === -1) throw new Error('symbol column not found in CSV');

        const set = new Set();
        const input = document.getElementById('stock-select');
        const datalist = document.getElementById('stock-options');
        
        for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',');
            const sym = (cols[symbolIdx] || '').trim();
            if (sym) set.add(sym.toUpperCase());
        }

        const symbols = Array.from(set).sort();
        if (symbols.length) {
            input.placeholder = "Type or select a stock...";
            datalist.innerHTML = ''; // Clear any existing options
            symbols.forEach(stock => {
                const option = document.createElement('option');
                option.value = stock;
                datalist.appendChild(option);
            });
            return;
        }
    } catch (err) {
        console.error('Local CSV fallback failed:', err);
    }

    // If we reached here nothing worked
    input.placeholder = "No stocks available";
    datalist.innerHTML = ''; // Clear any existing options
    showError('Failed to load stock list. Start the API or ensure data CSV exists.');
}

// Setup event listeners
function setupEventListeners() {
    const stockSelect = document.getElementById('stock-select');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    stockSelect.addEventListener('change', (e) => {
        currentStock = e.target.value;
        if (currentStock) {
            loadStockInfo(currentStock);
        }
    });
    
    analyzeBtn.addEventListener('click', () => {
        if (currentStock) {
            analyzeStock();
        } else {
            showError('Please select a stock first');
        }
    });
}

// Load stock info
async function loadStockInfo(symbol) {
    try {
        const response = await fetch(`${API_URL}/stocks/${symbol}`);
        const data = await response.json();
        
        displayStockMetrics(data);
    } catch (error) {
        console.error('Failed to load stock info:', error);
    }
}

// Display stock metrics
function displayStockMetrics(data) {
    const metricsDiv = document.getElementById('stock-metrics');
    metricsDiv.style.display = 'grid';
    
    document.getElementById('metric-close').textContent = `Rs. ${data.close.toFixed(2)}`;
    
    const changeElem = document.getElementById('metric-change');
    const changePercent = data.diff_percent.toFixed(2);
    changeElem.textContent = `${changePercent}%`;
    changeElem.className = 'metric-change ' + (data.diff_percent >= 0 ? 'positive' : 'negative');
    
    document.getElementById('metric-volume').textContent = data.volume.toLocaleString();
    
    document.getElementById('metric-rsi').textContent = data.rsi.toFixed(2);
    
    const rsiStatus = document.getElementById('metric-rsi-status');
    if (data.rsi > 70) {
        rsiStatus.textContent = 'Overbought';
        rsiStatus.style.color = '#f44336';
    } else if (data.rsi < 30) {
        rsiStatus.textContent = 'Oversold';
        rsiStatus.style.color = '#4caf50';
    } else {
        rsiStatus.textContent = 'Neutral';
        rsiStatus.style.color = '#ff9800';
    }
    
    document.getElementById('metric-52w').textContent = `Rs. ${data.week_52_high.toFixed(2)}`;
}

// Analyze stock
async function analyzeStock() {
    if (!apiStatus || !apiStatus.bot_initialized) {
        showError('RAG Bot is not initialized. Please set GOOGLE_API_KEY and restart the API.');
        return;
    }
    
    const stockSelect = document.getElementById('stock-select');
    const strategy = document.getElementById('strategy-select').value;
    
    // Update the analyzed stock name
    document.getElementById('analyzed-stock-name').textContent = stockSelect.options[stockSelect.selectedIndex].text;
    
    // Show loading state
    showLoading();
    
    try {
        // Get indicators
        const indicatorsResponse = await fetch(`${API_URL}/stocks/${currentStock}/indicators`);
        const indicators = await indicatorsResponse.json();
        
        // Get AI analysis
        const analysisResponse = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: currentStock,
                strategy: strategy
            })
        });
        
        const analysisData = await analysisResponse.json();
        
        if (analysisData.success) {
            displayResults(indicators, analysisData.analysis);
        } else {
            showError(analysisData.error || 'Analysis failed');
        }
    } catch (error) {
        console.error('Analysis failed:', error);
        showError('Failed to get analysis. Please try again.');
    }
}

// Show loading state
function showLoading() {
    document.getElementById('loading-state').style.display = 'block';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('results-container').style.display = 'none';
}

// Show error
function showError(message) {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'block';
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('error-message').textContent = message;
}

// Display results
function displayResults(indicators, analysis) {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('results-container').style.display = 'block';
    
    // Display indicators
    displayIndicators(indicators);
    
    // Display AI analysis
    displayAnalysis(analysis);
}

// Display indicators
function displayIndicators(indicators) {
    // Moving Averages & Price
    document.getElementById('ind-ma20').textContent = `Rs. ${indicators.moving_averages.ma20.toFixed(2)}`;
    document.getElementById('ind-ma50').textContent = `Rs. ${indicators.moving_averages.ma50.toFixed(2)}`;
    document.getElementById('ind-close').textContent = `Rs. ${indicators.price.close.toFixed(2)}`;
    document.getElementById('ind-vwap').textContent = `Rs. ${indicators.price.vwap.toFixed(2)}`;
    document.getElementById('ind-change').textContent = `${indicators.change_percent.toFixed(2)}%`;
    
    // Momentum
    const rsi = indicators.momentum.rsi;
    let rsiSignal = ' Neutral';
    if (rsi > 70) rsiSignal = ' Overbought';
    else if (rsi < 30) rsiSignal = ' Oversold';
    
    document.getElementById('ind-rsi').textContent = `${rsi.toFixed(2)} (${rsiSignal})`;
    document.getElementById('ind-macd').textContent = indicators.momentum.macd.toFixed(2);
    document.getElementById('ind-signal').textContent = indicators.momentum.macd_signal.toFixed(2);
    
    const macdHist = indicators.momentum.macd - indicators.momentum.macd_signal;
    const macdTrend = macdHist > 0 ? ' Bullish' : ' Bearish';
    document.getElementById('ind-trend').textContent = macdTrend;
    
    // Bollinger Bands
    document.getElementById('ind-bb-upper').textContent = `Rs. ${indicators.bollinger_bands.upper.toFixed(2)}`;
    document.getElementById('ind-bb-middle').textContent = `Rs. ${indicators.bollinger_bands.middle.toFixed(2)}`;
    document.getElementById('ind-bb-lower').textContent = `Rs. ${indicators.bollinger_bands.lower.toFixed(2)}`;
    
    const close = indicators.price.close;
    const bbUpper = indicators.bollinger_bands.upper;
    const bbLower = indicators.bollinger_bands.lower;
    
    let bbPos = ' Within Bands (Normal)';
    if (close > bbUpper) bbPos = ' Above Upper (Overbought)';
    else if (close < bbLower) bbPos = ' Below Lower (Oversold)';
    
    document.getElementById('ind-bb-pos').textContent = bbPos;
}

// Display AI analysis
function displayAnalysis(analysis) {
    const content = document.getElementById('ai-analysis-content');
    
    // Convert markdown-style formatting to HTML
    let html = analysis
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^- (.*$)/gim, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/<li>/g, '<ul><li>')
        .replace(/<\/li>(?![\s\S]*<li>)/g, '</li></ul>');
    
    content.innerHTML = `<p>${html}</p>`;
}

