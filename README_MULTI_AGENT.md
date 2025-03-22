# Multi-Agent Investment System with CrewAI and Router

This is a research prototype that demonstrates using CrewAI agents with a custom router infrastructure for distributed agent communication.

## Overview

The system consists of three specialist agents:

1. **Stock Analyst**: Analyzes stocks and provides investment recommendations
2. **Market Researcher**: Researches market trends and conditions
3. **Investment Advisor**: Provides investment advice based on input from other agents

Each agent:
- Runs as a separate server process
- Uses CrewAI's Agent class for its capabilities
- Communicates with other agents through the router

## Requirements

- Python 3.8+
- Router infrastructure (already set up in your codebase)
- CrewAI and dependencies:
  ```
  pip install crewai langchain openai
  ```
- Set your OpenAI API key:
  ```
  export OPENAI_API_KEY=your_api_key_here
  ```

## Running the System

### 1. Start the Router

First, make sure your router is running:

```bash
python router/router.py
```

### 2. Launch the Agents

Use the launcher script to start all agent servers:

```bash
python launch_agents.py
```

This will start each agent in a separate process and display their log outputs.

### 3. Run the Client

Use the multi-agent client to interact with the system:

```bash
python clients/multi_agent_client.py
```

By default, this runs a complete investment workflow that:
1. Gets market research
2. Analyzes stocks
3. Provides investment advice

### Client Options

The client supports different operation modes:

```bash
# Run stock analysis only
python clients/multi_agent_client.py --mode analysis --stocks "AAPL,MSFT,GOOGL"

# Run market research only
python clients/multi_agent_client.py --mode research --stocks "AAPL,MSFT,GOOGL"

# Get investment advice only
python clients/multi_agent_client.py --mode advice --request "Recommend a growth portfolio" --stocks "AAPL,TSLA,NVDA"

# Full workflow with custom request
python clients/multi_agent_client.py --mode workflow --request "Build a low-risk retirement portfolio" --stocks "MSFT,GOOGL,AMZN"
```

## Architecture

The system uses a distributed architecture:

1. **Router**: Central communication hub that routes messages between agents
2. **Agent Servers**: Independent servers that register with the router
3. **Client**: Orchestrates the workflow and collects results

### Inter-Agent Communication

Agents can communicate with each other through the router:

- The Stock Analyst can request market data from the Market Researcher
- The Investment Advisor can request analyses from both other agents
- Each agent handles requests asynchronously through the router

### CrewAI Integration

Each agent uses CrewAI's Agent class to define:
- Role and goal
- Backstory and expertise
- Reasoning capabilities (via LLM)

The router infrastructure handles:
- Agent discovery and registration
- Message routing
- Response collection

## Adding New Agents

To add a new agent:

1. Create a new file in the `server/` directory based on the existing templates
2. Define the agent's role, goal, and capabilities using CrewAI's Agent class
3. Implement the `add_query` and `run_query` methods
4. Add the agent to the `AGENTS` list in `launch_agents.py`

## Benefits of This Approach

- **Scalability**: Agents run as separate processes and can be distributed across machines
- **Modularity**: Each agent has a specific role and can be updated independently
- **Flexibility**: New agents can be added without modifying existing ones
- **Reusability**: CrewAI's agent definitions provide rich capabilities 