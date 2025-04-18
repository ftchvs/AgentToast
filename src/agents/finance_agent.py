import json
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from src.agents.base_agent import BaseAgent, InputT, OutputT # Use existing base
from src.tools.finance_tool import get_stock_info, StockInfo # Import the tool and its model
from src.config import get_logger

class FinanceInput(BaseModel):
    symbol: str = Field(..., description="The stock ticker symbol to fetch information for.")

# Output model could be the StockInfo model itself or a wrapper
class FinanceOutput(StockInfo):
    pass # Inherit directly or add agent-specific fields if needed

# Custom output for errors
class FinanceErrorOutput(BaseModel):
    error: str
    symbol: str

class FinanceAgent(BaseAgent[FinanceInput, FinanceOutput]):
    """Agent responsible for fetching financial data for a stock symbol."""

    def __init__(
        self,
        model: str | None = None, # Model might not be strictly needed if not using LLM part
        temperature: Optional[float] = None,
        verbose: bool = False
    ):
        super().__init__(
            name="FinanceAgent",
            instructions="Fetch stock information using the provided tool.", # Basic instructions
            tools=[], # No LLM tools needed for direct function call
            model=model or "", # Pass model if needed, else empty
            temperature=temperature,
            verbose=verbose
        )
        # Override logger specifically for this agent
        self.logger = get_logger("agent.finance")

    # Override run_sync as we are not using the LLM runner for this agent
    def run_sync(self, input_data: FinanceInput) -> FinanceOutput | FinanceErrorOutput:
        """Fetches stock info directly using the tool."""
        self.logger.info(f"Fetching finance data for symbol: {input_data.symbol}")
        try:
            # Call the finance tool directly
            stock_json = get_stock_info(input_data.symbol)
            stock_data = json.loads(stock_json)

            if "error" in stock_data:
                self.logger.error(f"Error fetching data for {input_data.symbol}: {stock_data['error']}")
                return FinanceErrorOutput(error=stock_data["error"], symbol=input_data.symbol)
            else:
                # Use the StockInfo model for parsing and validation
                parsed_output = FinanceOutput(**stock_data)
                self.logger.info(f"Successfully fetched data for {input_data.symbol}")
                if self.verbose:
                    self.logger.debug(f"Data: {parsed_output.model_dump_json(indent=2)}")
                return parsed_output

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response for {input_data.symbol}: {e}")
            return FinanceErrorOutput(error="Failed to parse finance tool response", symbol=input_data.symbol)
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred fetching data for {input_data.symbol}: {e}")
            return FinanceErrorOutput(error=f"An unexpected error occurred: {str(e)}", symbol=input_data.symbol)

    # Implement abstract methods from BaseAgent, even if not used by run_sync
    def _prepare_input(self, input_data: FinanceInput) -> str:
        # This won't be called by our overridden run_sync
        return input_data.model_dump_json()

    def _process_output(self, output: str) -> FinanceOutput:
        # This won't be called by our overridden run_sync
        # If it were, it would parse the LLM string output into the Pydantic model
        try:
            data = json.loads(output)
            return FinanceOutput(**data)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Failed to process LLM output into FinanceOutput: {e}")
            # Raise or return a default/error state depending on desired behavior
            raise ValueError(f"Could not parse LLM output: {output}") from e

# Example Usage (Optional)
if __name__ == '__main__':
    agent = FinanceAgent(verbose=True)
    
    # Test with valid symbol
    print("\n--- Testing AAPL ---")
    input_aapl = FinanceInput(symbol="AAPL")
    result_aapl = agent.run_sync(input_aapl)
    if isinstance(result_aapl, FinanceErrorOutput):
        print(f"Error: {result_aapl.error}")
    else:
        print(result_aapl.model_dump_json(indent=2))
    
    # Test with invalid symbol
    print("\n--- Testing INVALID ---")
    input_invalid = FinanceInput(symbol="INVALIDTICKER")
    result_invalid = agent.run_sync(input_invalid)
    if isinstance(result_invalid, FinanceErrorOutput):
        print(f"Error: {result_invalid.error}")
    else:
        # This part likely won't be reached for an invalid symbol
        print(result_invalid.model_dump_json(indent=2)) 