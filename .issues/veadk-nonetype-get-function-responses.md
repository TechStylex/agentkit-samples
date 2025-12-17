# [Bug] NoneType object has no attribute 'get_function_responses' in runner.py

## Summary

When running agents with complex tool chains (especially MCP tools), the application crashes with `AttributeError: 'NoneType' object has no attribute 'get_function_responses'`. This occurs because the `intercept_new_message` decorator in `veadk/runner.py` doesn't perform null checks on event objects before accessing their methods.

## Environment

- **veadk-python version**: (check with `pip show veadk-python`)
- **Python version**: 3.12
- **OS**: macOS / Linux

## Error Message

```
AttributeError: 'NoneType' object has no attribute 'get_function_responses'
```

## Steps to Reproduce

1. Create an agent that uses MCP tools (e.g., video-clip-mcp)
2. Run the agent with a complex multi-tool workflow
3. If any tool times out or returns an unexpected response, the error occurs

Example agent configuration (`video_gen/agent.py`):

```python
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    StdioServerParameters,
)
from veadk import Runner
from veadk.agent_builder import AgentBuilder

server_parameters = StdioServerParameters(
    command="npx",
    args=["@pickstar-2002/video-clip-mcp@latest"],
)
mcpTool = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=server_parameters, timeout=600.0
    ),
    errlog=None,
)

agent = agent_builder.build(path="agent.yaml")
agent.tools.append(mcpTool)

runner = Runner(agent=agent, app_name="storyvideo")
# Run the agent...
```

## Root Cause Analysis

The issue is located in `veadk/runner.py`, lines 141-157, within the `intercept_new_message` decorator:

```python
# veadk/runner.py - intercept_new_message decorator

async for event in func(
    user_id=user_id,
    session_id=session_id,
    new_message=new_message,
    **kwargs,
):
    yield event
    event_metadata = f"| agent_name: {event.author} , user_id: {user_id} , session_id: {session_id} , invocation_id: {event.invocation_id}"
    if event.get_function_calls():  # ← Crashes here if event is None
        for function_call in event.get_function_calls():
            logger.debug(f"Function call: {function_call} {event_metadata}")
    elif event.get_function_responses():  # ← Or crashes here
        for function_response in event.get_function_responses():
            logger.debug(
                f"Function response: {function_response} {event_metadata}"
            )
    # ...
```

**Problem**: The code accesses `event.author`, `event.get_function_calls()`, and `event.get_function_responses()` without first checking if `event` is `None`.

**When does event become None?**
- MCP tool connection timeouts
- Upstream generator yielding None on edge cases (connection closed, errors)
- Certain error conditions in the ADK event stream

## Expected Behavior

The runner should gracefully handle `None` events by skipping them instead of crashing.

## Proposed Fix

Add null check before accessing event properties:

```python
# veadk/runner.py - intercept_new_message decorator (lines 134-159)

async for event in func(
    user_id=user_id,
    session_id=session_id,
    new_message=new_message,
    **kwargs,
):
    yield event
    
    # Add null check to prevent AttributeError
    if event is None:
        logger.warning("Received None event from generator, skipping...")
        continue
    
    event_metadata = f"| agent_name: {event.author} , user_id: {user_id} , session_id: {session_id} , invocation_id: {event.invocation_id}"
    if event.get_function_calls():
        for function_call in event.get_function_calls():
            logger.debug(f"Function call: {function_call} {event_metadata}")
    elif event.get_function_responses():
        for function_response in event.get_function_responses():
            logger.debug(
                f"Function response: {function_response} {event_metadata}"
            )
    elif (
        event.content is not None
        and event.content.parts
        and event.content.parts[0].text is not None
        and len(event.content.parts[0].text.strip()) > 0
    ):
        final_output = event.content.parts[0].text
        logger.debug(f"Event output: {final_output} {event_metadata}")
```

## Additional Context

### Related Code Locations That May Also Need Fixes

1. **`google/adk/flows/llm_flows/contents.py`** (line 145):
   ```python
   function_responses = events[-1].get_function_responses()
   ```
   Should add check: `if events and events[-1] is not None:`

2. **`google/adk/flows/llm_flows/base_llm_flow.py`** (line 160):
   ```python
   if event.get_function_responses():
   ```
   Should add null check before this line.

### Affected Use Cases

- `02-use-cases/video_gen` - Video generation with MCP tools
- Any agent using long-running tools or external service integrations
- Agents with complex multi-tool workflows

## Workaround (Temporary)

Until this is fixed in veadk, users can wrap their agent execution in try-catch:

```python
try:
    async for event in runner.run_async(...):
        if event is not None:
            # Process event
            pass
except AttributeError as e:
    if "'NoneType' object has no attribute 'get_function_responses'" in str(e):
        logger.warning("Encountered None event, gracefully handling...")
    else:
        raise
```

## Labels

- `bug`
- `runner`
- `null-safety`

## Priority

**High** - This causes complete application crashes and affects production environments using complex tool chains.
