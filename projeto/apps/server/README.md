from typing import Dict, Any, List
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from your_tools_module import CalculateSquareTool # Make sure to import your tool class

def custom_tools_node_with_list(state: Dict[str, Any], tools: List[BaseTool]) -> Dict[str, Any]:
"""
A custom node that executes tool calls from the last message using a provided list of tools.
"""
last_message = state["messages"][-1]
new_messages = []

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state

    for tool_call in last_message.tool_calls:
        tool_name = tool_call.name
        tool_args = tool_call.args
        tool_call_id = tool_call.id

        tool_to_run = next((t for t in tools if t.name == tool_name), None)

        if tool_to_run:
            try:
                # 🎯 The new logic starts here
                # Check if the tool is an instance of CalculateSquareTool
                if isinstance(tool_to_run, CalculateSquareTool):
                    # Check if 'number' is in the state
                    if "number" in state:
                        number_from_state = state["number"]
                        # Run the tool using the number from the state
                        tool_output = tool_to_run.run(number=number_from_state)
                    else:
                        tool_output = "Error: 'number' not found in state for CalculateSquareTool."
                else:
                    # For all other tools, run them with their original arguments
                    tool_output = tool_to_run.run(**tool_args, tool_call_id=tool_call_id)
                # 🎯 The new logic ends here

                new_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call_id))
            except Exception as e:
                new_messages.append(ToolMessage(content=f"Error executing tool {tool_name}: {e}", tool_call_id=tool_call_id))
        else:
            new_messages.append(ToolMessage(content=f"Tool not found: {tool_name}", tool_call_id=tool_call_id))

    return {"messages": state["messages"] + new_messages}
