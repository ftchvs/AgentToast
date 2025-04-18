import yfinance as yf
from pydantic import BaseModel, Field
import json

class StockInfo(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Company name")
    current_price: float = Field(..., description="Current stock price")
    day_high: float = Field(..., description="Highest price during the day")
    day_low: float = Field(..., description="Lowest price during the day")
    market_cap: float | None = Field(None, description="Market capitalization")
    volume: int | None = Field(None, description="Trading volume")
    previous_close: float | None = Field(None, description="Previous closing price")
    open_price: float | None = Field(None, description="Opening price")
    fifty_two_week_high: float | None = Field(None, description="52-week high price")
    fifty_two_week_low: float | None = Field(None, description="52-week low price")
    summary: str | None = Field(None, description="Company business summary")

def get_stock_info(symbol: str) -> str:
    """
    Fetches stock information for a given ticker symbol from Yahoo Finance.

    Args:
        symbol: The stock ticker symbol (e.g., 'AAPL', 'GOOGL').

    Returns:
        A JSON string containing the stock information, or an error message.
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Extract relevant information, handling potential missing keys
        stock_data = StockInfo(
            symbol=symbol,
            company_name=info.get('longName', 'N/A'),
            # Use currentPrice, fallback to regularMarketPrice or open if needed
            current_price=info.get('currentPrice') or info.get('regularMarketPrice') or info.get('open', 0.0),
            day_high=info.get('dayHigh', 0.0),
            day_low=info.get('dayLow', 0.0),
            market_cap=info.get('marketCap'),
            volume=info.get('volume'),
            previous_close=info.get('previousClose'),
            open_price=info.get('open'),
            fifty_two_week_high=info.get('fiftyTwoWeekHigh'),
            fifty_two_week_low=info.get('fiftyTwoWeekLow'),
            summary=info.get('longBusinessSummary')
        )

        return stock_data.model_dump_json(indent=2)

    except Exception as e:
        # Return error as JSON for consistent interface
        return json.dumps({"error": f"Failed to fetch data for {symbol}: {str(e)}"})

if __name__ == '__main__':
    # Example usage
    ticker_symbol_aapl = "AAPL"
    stock_json_aapl = get_stock_info(ticker_symbol_aapl)
    print(f"--- {ticker_symbol_aapl} ---")
    print(stock_json_aapl)
    print("\n")

    ticker_symbol_invalid = "INVALIDTICKER"
    stock_json_invalid = get_stock_info(ticker_symbol_invalid)
    print(f"--- {ticker_symbol_invalid} ---")
    print(stock_json_invalid) 