from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
import json

from langchain_core.messages import BaseMessage

from src.layers.core_logic_layer.logging import logger


class BaseAgent:
    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        tools: list[BaseTool],
        prompt: str,
    ):
        self.name: str = name
        self.llm: BaseChatModel = llm
        self.tools: list[BaseTool] = tools
        self.prompt: str = prompt

    def robust_json_parser(
        self, message: BaseMessage, resources: list[str]
    ) -> dict[str, str]:
        """
        Parse a BaseMessage's content into a dictionary with a 'next' key.

        Args:
            message: BaseMessage containing the content to parse.
            resources: List of valid resource names for routing.

        Returns:
            Dict with 'next' key pointing to a resource name or 'FINISH'.
        """
        content = message.content.strip()
        try:
            parsed = json.loads(content)
            if (
                isinstance(parsed, dict)
                and "next" in parsed
                and parsed["next"] in resources + ["FINISH"]
            ):
                logger.debug(f"Successfully parsed JSON: {parsed}")
                return parsed
            logger.warning(f"Invalid JSON structure or 'next' value: {content}")
        except json.JSONDecodeError as error:
            logger.debug(f"Direct JSON parsing failed: {error}")

        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                parsed = json.loads(json_str)
                if (
                    isinstance(parsed, dict)
                    and "next" in parsed
                    and parsed["next"] in resources + ["FINISH"]
                ):
                    logger.debug(f"Successfully parsed JSON substring: {parsed}")
                    return parsed
                logger.warning(
                    f"Invalid JSON substring structure or 'next' value: {json_str}"
                )
        except json.JSONDecodeError as error:
            logger.debug(f"JSON substring parsing failed: {error}")

        for resource in resources + ["FINISH"]:
            if resource.lower() in content.lower():
                logger.info(f"Fallback to resource name match: {resource}")
                return {"next": resource}

        logger.warning(f"Could not parse content, defaulting to FINISH: {content}")
        return {"next": "FINISH"}
