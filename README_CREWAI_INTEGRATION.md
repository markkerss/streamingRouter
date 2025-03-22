# Integrating CrewAI Agents with Router Infrastructure

This guide explains how to use CrewAI's Agent class with your custom router infrastructure for agent communication and orchestration.

## Architecture Overview

The integration combines:

1. **CrewAI Agents**: Used for agent definitions, goals, and capabilities
2. **Router Infrastructure**: Used for efficient inter-agent communication

![Architecture Diagram](https://mermaid.ink/img/pako:eNp1kV1rwjAUhv9KOBeK4Fp_QKHrZK5QdNSNbW6KF2mOJTRNSFJGEf_7TmtX2MZ2E5LznPOeN6fDP7TEDHOgZccMBk9Wb8-rj0VL29Ja9ohKYsQPEqiZ0gHVJ4mGJz90yN5D4vRNcFBGi8AbZBOHDI-GY6yH_SdlxRlh9X5nNP-DdEXz_ZLvb_5wnl2tLJcKgdFUV1ggx5QKC8xNwIhAMtSt5sZ5iBkm_uHdGGK2a-vfSGvlqb0Hpdk40EoJ3oQjKkBL4tPcmCVrYs3oQjWTxSFr3WMFuuAbkuoO1QQ5NeumUYZuSGXtHrQJBpMm9UmvRCJJXyCOx48_vw7VJA9JXtbhG8y7LtbqnzAY5yCF_iqY58a8J5fj56cP61W8vI0Xl_x-j5dgzE8EUTrtJLsoXz2hIH_IItxuOFz-bCKHyw?type=png)

## Key Components

1. **CrewAI Agent Wrapper (crewai_router_agent.py)**:
   - Wraps CrewAI Agent class to work with the router
   - Handles translation between CrewAI capabilities and router communication
   - Registers with the router automatically at startup

2. **Router Client (clients/stock_client.py)**:
   - Demonstrates how to make requests to agents through the router
   - Creates agents using CrewAI API but communicates through router

3. **Benchmark (benchmark_vs_crewai.py)**:
   - Compares performance of different architectures:
     - Basic Router
     - Router with CrewAI Agents
     - Pure CrewAI

## Getting Started

### Prerequisites

1. Install required dependencies:
   ```bash
   pip install crewai langchain openai grpcio grpcio-tools
   ```

2. Set up your OpenAI API key (required for CrewAI):
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   ```

### Starting the System

1. Start the router:
   ```bash
   python router/router.py
   ```

2. Start CrewAI agent servers:
   ```bash
   python server/crewai_router_agent.py
   ```

3. Run a client request:
   ```bash
   python clients/stock_client.py
   ```

## Running the Benchmark

To compare the performance of the different architectures:

```bash
python benchmark_vs_crewai.py
```

## Implementation Details

### CrewAI Agent Registration with Router

The `CrewAIRouterAgent` class:
1. Initializes a CrewAI Agent with role, goal and backstory
2. Inherits from `ServerTemplate` to integrate with the router
3. Registers itself with the router at startup

```python
def __init__(self, service_name, agent_role, agent_goal, agent_backstory=None):
    # Initialize router connection
    super().__init__(service_name=service_name)
    
    # Initialize CrewAI agent
    self.agent = Agent(
        role=agent_role,
        goal=agent_goal,
        backstory=agent_backstory or f"An expert {agent_role}",
        llm=OpenAI(temperature=0.7)
    )
```

### Request Processing

When a request arrives through the router:

1. `add_query()` processes each incoming chunk
2. `run_query()` combines chunks and executes the agent's task
3. The agent's response is returned to the router

```python
def run_query(self, chunks):
    # Combine chunks into a single input
    input_data = "\n".join(chunks)
    
    # Run the CrewAI agent's task
    result = self._run_agent_task(input_data)
    return json.dumps(result)
```

## Multiple Agents Setup

You can run multiple CrewAI agents as separate services, each connected to the router:

```python
def serve_multi_agents():
    # Start several agent servers in separate threads
    analyst_thread = Thread(target=serve_stock_analyst)
    researcher_thread = Thread(target=serve_market_research)
    advisor_thread = Thread(target=serve_investment_advisor)
    
    analyst_thread.start()
    researcher_thread.start()
    advisor_thread.start()
    
    # Wait for all threads
    analyst_thread.join()
    researcher_thread.join()
    advisor_thread.join()
```

## Benefits of this Architecture

1. **Scalability**: Deploy agents across multiple machines connected by the router
2. **Loose Coupling**: Agents are independent services that can be updated separately
3. **Flexibility**: Use CrewAI's agent capabilities with your custom communication layer
4. **Performance**: Router handles efficient communication while CrewAI handles agent logic

## Limitations

1. CrewAI's built-in collaboration features aren't directly accessible
2. Task chaining requires manual implementation through the router
3. Requires maintaining two systems (CrewAI and router)

## Next Steps

Consider these enhancements:

1. Implement a higher-level orchestration layer that maps CrewAI Crew logic to router communication
2. Add support for CrewAI tools within the router agent implementation
3. Enable agent discovery and capability advertising through the router
4. Create a hybrid execution mode that can switch between direct CrewAI execution and router-based execution 