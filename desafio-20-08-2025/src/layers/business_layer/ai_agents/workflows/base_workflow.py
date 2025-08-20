from langchain_core.messages import convert_to_messages
from src.layers.core_logic_layer.logging import logger


class BaseWorkflow:
    @staticmethod
    def _pretty_print_message(message, indent=False):
        pretty_message = message.pretty_repr(html=True)
        if not indent:
            logger.info(pretty_message)
            return

        indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
        logger.info(indented)

    def _pretty_print_messages(self, update, last_message=False):
        is_subgraph = False
        if isinstance(update, tuple):
            ns, update = update
            if len(ns) == 0:
                return

            graph_id = ns[-1].split(":")[0]
            logger.info(f"Update from subgraph {graph_id}:")
            logger.info("\n")
            is_subgraph = True

        for node_name, node_update in update.items():
            update_label = f"Update from node {node_name}:"
            if is_subgraph:
                update_label = "\t" + update_label

            logger.info(update_label)
            logger.info("\n")

            messages = convert_to_messages(node_update["messages"])
            if last_message:
                messages = messages[-1:]

            for m in messages:
                self._pretty_print_message(m, indent=is_subgraph)
            logger.info("\n")
