# Router vs CrewAI Benchmark

This benchmark compares different approaches to agent-based stock analysis:

1. **Basic Router**: Using your custom router infrastructure with a stock analyst server
2. **Router with CrewAI Agents**: Using CrewAI's Agent class for agent definitions while leveraging your router for communication
3. **Pure CrewAI**: Using the standard CrewAI framework with its built-in agent communication

## Overview

The benchmark measures and compares:
- Execution time
- Memory usage
- CPU usage
- Result quality (subjective analysis)

## Prerequisites

1. Make sure your router service is running:
   ```
   # From the router directory
   python router/router.py
   ```

2. Install required dependencies:
   ```
   pip install crewai langchain openai matplotlib pandas psutil
   ```

3. Set up your API keys for OpenAI (for CrewAI) and any financial APIs used in your stock analysis:
   ```
   export OPENAI_API_KEY=your_openai_api_key
   ```

4. Make sure your `StockAnalystServer` is properly configured in `server/stockAnalystAgent.py`.

## Running the Benchmark

1. Start your Stock Analyst server:
   ```
   # From the router directory
   python server/stockAnalystAgent.py
   ```

2. In a separate terminal, run the benchmark script:
   ```
   # From the router directory
   python benchmark_vs_crewai.py
   ```

3. The benchmark will run multiple iterations of each implementation and display the results.

## Understanding the Results

The benchmark will:
1. Output timing and resource usage for each run
2. Generate a visual comparison saved as `benchmark_results.png`
3. Print a summary of average performance metrics

## Implementation Approaches

### 1. Basic Router
This implementation uses your custom router infrastructure with a basic stock analyst server. The server processes stock symbols and returns analysis results through the router.

### 2. Router with CrewAI Agents
This hybrid approach uses:
- CrewAI's Agent class to define the agents and their roles
- Your router infrastructure for inter-agent communication
- Stock analysis processing handled by your server

This demonstrates how to integrate CrewAI's agent definitions with your custom router infrastructure.

### 3. Pure CrewAI
This is the standard CrewAI implementation that uses:
- CrewAI's Agent class for agent definitions
- CrewAI's built-in communication between agents
- CrewAI's Task and Crew for orchestration

## Customizing the Benchmark

You can modify the benchmark parameters in `benchmark_vs_crewai.py`:

- `NUM_RUNS`: Number of iterations for each implementation (default: 3)
- `TEST_STOCKS`: List of stock symbols to analyze (default: ["AAPL", "MSFT", "GOOGL", "AMZN", "META"])

## Expected Differences

When comparing the implementations, you can expect to see:

1. **Router vs Router+CrewAI**:
   - Performance: Similar performance as both use the same communication infrastructure
   - Implementation complexity: Router+CrewAI provides better agent definition structure

2. **Router+CrewAI vs Pure CrewAI**:
   - Communication overhead: Router may have lower overhead for simple tasks
   - Flexibility: Pure CrewAI provides built-in collaboration mechanisms
   - Memory usage: Router may use less memory without CrewAI's orchestration layer

## Using the Client

To test the stock analyst functionality with the CrewAI agents through the router, use the client script:

```
python clients/stock_client.py
```

This client demonstrates how to:
1. Define agents using CrewAI's Agent class
2. Use the router for communication
3. Process and display analysis results

## Next Steps

Consider these improvements for further development:

1. **More Agent Types**: Implement additional specialized agents through your router
2. **Custom Tools**: Add support for specialized tools in your router infrastructure
3. **Dynamic Agent Discovery**: Enable agents to discover and communicate with each other based on capabilities
4. **Hybrid Runtime**: Dynamically switch between using router communication and CrewAI's built-in communication based on task complexity

## Troubleshooting

- If the router benchmark fails, ensure your router service is running and accessible
- If the CrewAI benchmark fails, check your OpenAI API key and ensure CrewAI is properly installed
- For "connection refused" errors, verify that all services are running on the expected ports

## Additional Tests

For a more comprehensive benchmark, consider adding:
- Stress testing with larger lists of stocks
- Measuring throughput (requests per second)
- Testing fault tolerance and recovery 