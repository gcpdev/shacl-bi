import config
from functions.virtuoso_service import execute_sparql_update
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("clear_vkg")

def clear_violation_kg():
    """
    Clears the Violation Knowledge Graph in Virtuoso by executing a
    SPARQL CLEAR GRAPH query.
    """
    vkg_graph_uri = config.VIOLATION_KG_GRAPH
    if not vkg_graph_uri:
        logger.error("VIOLATION_KG_GRAPH URI is not defined in the configuration.")
        return

    logger.info(f"Preparing to clear graph: {vkg_graph_uri}")

    query = f"CLEAR GRAPH <{vkg_graph_uri}>"

    try:
        logger.info(f"Executing SPARQL update query:\n{query}")
        execute_sparql_update(query)
        logger.info(f"Successfully cleared graph: {vkg_graph_uri}")
    except Exception as e:
        logger.error(f"An error occurred while trying to clear the graph: {e}", exc_info=True)

if __name__ == "__main__":
    clear_violation_kg()
