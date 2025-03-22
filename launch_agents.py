#!/usr/bin/env python3
"""
Agent Launcher Script

This script launches all the agent servers needed for the investment workflow.
Each agent is started in its own process.
"""

import subprocess
import sys
import time
import os
import signal
from concurrent.futures import ThreadPoolExecutor

# Define agent scripts
AGENTS = [
    {
        "name": "Stock Analyst",
        "script": "server/stock_analyst_agent.py",
        "description": "Analyzes stocks and provides investment recommendations"
    },
    {
        "name": "Market Researcher",
        "script": "server/market_researcher_agent.py",
        "description": "Researches market trends and conditions"
    },
    {
        "name": "Investment Advisor",
        "script": "server/investment_advisor_agent.py",
        "description": "Provides personalized investment advice"
    }
]

# Track running processes
processes = []

def start_agent(agent):
    """Start an agent in a separate process"""
    print(f"Starting {agent['name']} agent...")
    
    try:
        # Start the agent process
        process = subprocess.Popen(
            [sys.executable, agent["script"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Store the process for later cleanup
        processes.append(process)
        
        print(f"{agent['name']} agent started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Error starting {agent['name']} agent: {str(e)}")
        return None

def monitor_output(process, agent_name):
    """Monitor and print agent output"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"[{agent_name}] {output.strip()}")
    
    # Check for errors
    if process.returncode != 0:
        print(f"[{agent_name}] Process exited with code {process.returncode}")
        for line in process.stderr.readlines():
            print(f"[{agent_name} ERROR] {line.strip()}")

def cleanup():
    """Clean up all agent processes"""
    print("\nShutting down agents...")
    for process in processes:
        if process.poll() is None:  # If process is still running
            try:
                # Send SIGTERM first
                process.terminate()
                time.sleep(0.5)
                
                # If still running, force kill
                if process.poll() is None:
                    process.kill()
            except Exception as e:
                print(f"Error stopping process {process.pid}: {str(e)}")
    
    print("All agents shut down")

def main():
    """Start all agents and monitor their output"""
    print("===== Starting Agent System =====")
    
    # Register cleanup handler
    def signal_handler(sig, frame):
        print("\nReceived shutdown signal")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if router is running
    print("Make sure the router is running before starting agents!")
    input("Press Enter to start the agents...")
    
    # Start all agents
    with ThreadPoolExecutor(max_workers=len(AGENTS)) as executor:
        for agent in AGENTS:
            process = start_agent(agent)
            if process:
                # Monitor the agent output in a separate thread
                executor.submit(monitor_output, process, agent["name"])
    
    # Wait for user to stop the agents
    print("\nAll agents have been started.")
    print("Press Ctrl+C to stop all agents")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main() 