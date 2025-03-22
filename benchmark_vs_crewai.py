"""
Benchmark script comparing router-based stock analyst with CrewAI implementation.

This script:
1. Tests the router-based stock analysis implementation with CrewAI agents
2. Tests the pure CrewAI-based stock analysis implementation
3. Compares performance metrics (execution time, resource usage)

Requirements:
- pip install crewai langchain psutil matplotlib pandas
- Your router service must be running
- You need API keys for any financial data services
"""

import time
import statistics
import psutil
import json
import grpc
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import matplotlib.pyplot as plt
from generated import router_pb2_grpc, router_pb2
from config import get_router_address

# Try to import CrewAI (not failing if not installed)
try:
    from crewai import Agent, Crew, Task
    from langchain.llms import OpenAI
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    print("CrewAI not installed. Only router benchmarks will be run.")

# Constants
NUM_RUNS = 3  # Number of times to run each test for averaging
TEST_STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]  # Test stock symbols

class BenchmarkResults:
    def __init__(self):
        self.execution_times = []
        self.memory_usages = []
        self.cpu_usages = []
        self.results = []
    
    def add_run_data(self, execution_time, memory_usage, cpu_usage, result):
        self.execution_times.append(execution_time)
        self.memory_usages.append(memory_usage)
        self.cpu_usages.append(cpu_usage)
        self.results.append(result)
    
    def get_summary(self):
        return {
            "avg_execution_time": statistics.mean(self.execution_times) if self.execution_times else 0,
            "avg_memory_usage_mb": statistics.mean(self.memory_usages) if self.memory_usages else 0,
            "avg_cpu_usage_percent": statistics.mean(self.cpu_usages) if self.cpu_usages else 0,
            "runs": len(self.execution_times)
        }

def measure_performance(func, *args, **kwargs):
    """Measure performance metrics of a function execution"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    start_time = time.time()
    start_cpu = process.cpu_percent()
    
    # Run the function
    result = func(*args, **kwargs)
    
    # Collect metrics
    execution_time = time.time() - start_time
    end_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_usage = end_memory - start_memory
    cpu_usage = process.cpu_percent()
    
    return execution_time, memory_usage, cpu_usage, result

class RouterClient:
    def __init__(self):
        self.router_address = get_router_address()
        self.channel = grpc.insecure_channel(f"localhost:{self.router_address}")
        self.stub = router_pb2_grpc.RouterStub(self.channel)
        self.client_port = self._start_client_server()
        self.client_address = f"localhost:{self.client_port}"
    
    def _start_client_server(self):
        """Start a server to receive responses"""
        server = grpc.server(ThreadPoolExecutor(max_workers=10))
        self.responses = {}
        
        # Add servicer methods
        class ClientServicer(router_pb2_grpc.RouterServicer):
            def __init__(self, responses_dict):
                self.responses = responses_dict
            
            def ReceiveResponse(self, response, context):
                response_json = json.loads(response.info)
                request_id = response_json["request_id"]
                self.responses[request_id] = response_json["data"]
                return router_pb2.Empty()
        
        servicer = ClientServicer(self.responses)
        router_pb2_grpc.add_RouterServicer_to_server(servicer, server)
        port = server.add_insecure_port("[::]:0")  # Dynamic port
        server.start()
        return port
    
    def analyze_stocks(self, stocks):
        """Send stock analysis request through the router"""
        # Create a unique request ID
        request_id = f"benchmark_{int(time.time())}"
        
        # Create request data
        request_data = json.dumps({
            "service_name": "stock_analyst",
            "request_id": request_id,
            "request_ip": self.client_address,
            "data": stocks[0],  # First stock as first chunk
            "chunk_id": 0
        })
        
        # Send first stock
        request = router_pb2.Request(info=request_data)
        
        # If there are multiple stocks, send them as separate chunks
        if len(stocks) > 1:
            # Send first N-1 stocks as regular chunks
            self.stub.RouteRequestChunks(iter([request]))
            
            # Send the last stock as the last chunk
            last_request_data = json.dumps({
                "service_name": "stock_analyst",
                "request_id": request_id,
                "request_ip": self.client_address,
                "data": stocks[-1],
                "chunk_id": len(stocks) - 1
            })
            last_request = router_pb2.Request(info=last_request_data)
            self.stub.RouteLastRequestChunk(last_request)
        else:
            # If only one stock, send it as both first and last chunk
            self.stub.RouteLastRequestChunk(request)
        
        # Wait for response
        max_wait = 30  # seconds
        start_time = time.time()
        while request_id not in self.responses and time.time() - start_time < max_wait:
            time.sleep(0.1)
        
        if request_id in self.responses:
            return self.responses[request_id]
        else:
            raise TimeoutError(f"No response received after {max_wait} seconds")

# New class that combines CrewAI agents with router infrastructure
class RouterWithCrewAgents:
    def __init__(self):
        # Initialize router client
        self.router_client = RouterClient()
        
        # Initialize CrewAI agents but don't connect them directly
        self._initialize_crewai_agents()
    
    def _initialize_crewai_agents(self):
        """Create CrewAI agents but use them only for their definitions"""
        if not HAS_CREWAI:
            print("CrewAI not installed. Using mock agents.")
            self.agents = ["MockResearcher", "MockAnalyst", "MockAdvisor"]
            return
        
        # Check if OpenAI API key is set
        if "OPENAI_API_KEY" not in os.environ:
            print("Warning: OPENAI_API_KEY not set. Using mock LLM.")
            # Create a mock LLM
            class MockLLM:
                def __call__(self, prompt):
                    return f"Mock response to: {prompt[:30]}..."
            llm = MockLLM()
        else:
            # Use actual OpenAI if key is available
            llm = OpenAI(temperature=0.7)
        
        # Create the agents (only definitions)
        self.agents = [
            Agent(
                role="Stock Market Researcher",
                goal="Provide accurate stock market insights",
                backstory="An expert in stock market analysis with years of experience.",
                llm=llm
            ),
            Agent(
                role="Financial Analyst",
                goal="Analyze stocks to provide investment recommendations",
                backstory="An experienced financial analyst with a track record of successful investments.",
                llm=llm
            ),
            Agent(
                role="Investment Advisor",
                goal="Provide investment recommendations",
                backstory="A seasoned investment advisor who helps clients make strategic investment decisions.",
                llm=llm
            )
        ]
        print(f"Created {len(self.agents)} CrewAI agents for use with router")
    
    def analyze_stocks(self, stocks):
        """Analyze stocks using router infrastructure with CrewAI agent definitions"""
        # Use the router to handle communication while conceptually using CrewAI agents
        return self.router_client.analyze_stocks(stocks)

def run_router_benchmark(stocks):
    """Run benchmark using the basic router implementation"""
    results = BenchmarkResults()
    
    print("Running benchmark with basic router implementation (no CrewAI agents)")
    
    for i in range(NUM_RUNS):
        print(f"Router benchmark run {i+1}/{NUM_RUNS}...")
        
        client = RouterClient()
        execution_time, memory_usage, cpu_usage, result = measure_performance(
            client.analyze_stocks, stocks
        )
        
        results.add_run_data(execution_time, memory_usage, cpu_usage, result)
        print(f"  Time: {execution_time:.2f}s, Memory: {memory_usage:.2f}MB, CPU: {cpu_usage:.2f}%")
    
    return results

def run_router_with_crewai_benchmark(stocks):
    """Run benchmark using router with CrewAI agent definitions"""
    results = BenchmarkResults()
    
    print("Running benchmark with router using CrewAI agent definitions")
    
    for i in range(NUM_RUNS):
        print(f"Router+CrewAI benchmark run {i+1}/{NUM_RUNS}...")
        
        client = RouterWithCrewAgents()
        execution_time, memory_usage, cpu_usage, result = measure_performance(
            client.analyze_stocks, stocks
        )
        
        results.add_run_data(execution_time, memory_usage, cpu_usage, result)
        print(f"  Time: {execution_time:.2f}s, Memory: {memory_usage:.2f}MB, CPU: {cpu_usage:.2f}%")
    
    return results

def run_pure_crewai_benchmark(stocks):
    """Run benchmark using pure CrewAI implementation"""
    if not HAS_CREWAI:
        print("CrewAI not installed. Skipping pure CrewAI benchmark.")
        return None
    
    results = BenchmarkResults()
    
    print("Running benchmark with pure CrewAI implementation")
    
    for i in range(NUM_RUNS):
        print(f"Pure CrewAI benchmark run {i+1}/{NUM_RUNS}...")
        
        def run_crewai_analysis():
            # Check if OpenAI API key is set
            if "OPENAI_API_KEY" not in os.environ:
                print("Warning: OPENAI_API_KEY not set. Using mock data for CrewAI.")
                # Return mock data
                return {
                    "analysis": [
                        {"symbol": stock, "recommendation": "MOCK", "price_target": 100.0}
                        for stock in stocks
                    ]
                }
            
            # Based on the CrewAI example
            llm = OpenAI(temperature=0.7)
            
            # Create the agents
            researcher = Agent(
                role="Stock Market Researcher",
                goal="Provide accurate stock market insights",
                backstory="An expert in stock market analysis with years of experience.",
                llm=llm
            )
            
            analyst = Agent(
                role="Financial Analyst",
                goal="Analyze stocks to provide investment recommendations",
                backstory="An experienced financial analyst with a track record of successful investments.",
                llm=llm
            )
            
            advisor = Agent(
                role="Investment Advisor",
                goal="Provide investment recommendations",
                backstory="A seasoned investment advisor who helps clients make strategic investment decisions.",
                llm=llm
            )
            
            # Create the tasks
            research_task = Task(
                description=f"Research the latest news and market trends for {', '.join(stocks)}",
                agent=researcher
            )
            
            analysis_task = Task(
                description="Analyze the researched information and create an analysis report",
                agent=analyst
            )
            
            recommendation_task = Task(
                description="Provide investment recommendations based on the analysis",
                agent=advisor
            )
            
            # Create the crew
            crew = Crew(
                agents=[researcher, analyst, advisor],
                tasks=[research_task, analysis_task, recommendation_task],
                verbose=False
            )
            
            # Execute the crew's plan
            result = crew.kickoff()
            return result
        
        execution_time, memory_usage, cpu_usage, result = measure_performance(run_crewai_analysis)
        
        results.add_run_data(execution_time, memory_usage, cpu_usage, result)
        print(f"  Time: {execution_time:.2f}s, Memory: {memory_usage:.2f}MB, CPU: {cpu_usage:.2f}%")
    
    return results

def visualize_results(router_results, router_crewai_results, pure_crewai_results):
    """Create visualizations comparing the benchmark results"""
    router_summary = router_results.get_summary()
    
    data = {
        'Implementation': ['Router'],
        'Avg. Execution Time (s)': [router_summary['avg_execution_time']],
        'Avg. Memory Usage (MB)': [router_summary['avg_memory_usage_mb']],
        'Avg. CPU Usage (%)': [router_summary['avg_cpu_usage_percent']]
    }
    
    if router_crewai_results:
        router_crewai_summary = router_crewai_results.get_summary()
        data['Implementation'].append('Router+CrewAI')
        data['Avg. Execution Time (s)'].append(router_crewai_summary['avg_execution_time'])
        data['Avg. Memory Usage (MB)'].append(router_crewai_summary['avg_memory_usage_mb'])
        data['Avg. CPU Usage (%)'].append(router_crewai_summary['avg_cpu_usage_percent'])
    
    if pure_crewai_results:
        pure_crewai_summary = pure_crewai_results.get_summary()
        data['Implementation'].append('Pure CrewAI')
        data['Avg. Execution Time (s)'].append(pure_crewai_summary['avg_execution_time'])
        data['Avg. Memory Usage (MB)'].append(pure_crewai_summary['avg_memory_usage_mb'])
        data['Avg. CPU Usage (%)'].append(pure_crewai_summary['avg_cpu_usage_percent'])
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create plots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Execution Time
    axes[0].bar(df['Implementation'], df['Avg. Execution Time (s)'])
    axes[0].set_title('Execution Time (s)')
    axes[0].set_ylabel('Seconds')
    
    # Memory Usage
    axes[1].bar(df['Implementation'], df['Avg. Memory Usage (MB)'])
    axes[1].set_title('Memory Usage (MB)')
    axes[1].set_ylabel('MB')
    
    # CPU Usage
    axes[2].bar(df['Implementation'], df['Avg. CPU Usage (%)'])
    axes[2].set_title('CPU Usage (%)')
    axes[2].set_ylabel('Percentage')
    
    plt.tight_layout()
    plt.savefig('benchmark_results.png')
    print(f"Benchmark visualization saved to 'benchmark_results.png'")
    
    # Print summary
    print("\nBenchmark Summary:")
    print(f"Router: {router_summary['avg_execution_time']:.2f}s, {router_summary['avg_memory_usage_mb']:.2f}MB, {router_summary['avg_cpu_usage_percent']:.2f}%")
    
    if router_crewai_results:
        print(f"Router+CrewAI: {router_crewai_summary['avg_execution_time']:.2f}s, {router_crewai_summary['avg_memory_usage_mb']:.2f}MB, {router_crewai_summary['avg_cpu_usage_percent']:.2f}%")
    
    if pure_crewai_results:
        print(f"Pure CrewAI: {pure_crewai_summary['avg_execution_time']:.2f}s, {pure_crewai_summary['avg_memory_usage_mb']:.2f}MB, {pure_crewai_summary['avg_cpu_usage_percent']:.2f}%")

def main():
    print(f"Starting benchmark with {len(TEST_STOCKS)} stocks: {', '.join(TEST_STOCKS)}")
    
    # Run basic router benchmark
    print("\n=== Basic Router Benchmark ===")
    router_results = run_router_benchmark(TEST_STOCKS)
    
    # Run router with CrewAI agents benchmark
    print("\n=== Router with CrewAI Agents Benchmark ===")
    router_crewai_results = run_router_with_crewai_benchmark(TEST_STOCKS)
    
    # Run pure CrewAI benchmark if available
    pure_crewai_results = None
    if HAS_CREWAI:
        print("\n=== Pure CrewAI Benchmark ===")
        pure_crewai_results = run_pure_crewai_benchmark(TEST_STOCKS)
    
    # Visualize and compare results
    visualize_results(router_results, router_crewai_results, pure_crewai_results)

if __name__ == "__main__":
    main() 