"""
Query executor for the mini-server.

This module implements a basic query executor that handles queries in the format
defined in client/curl/EXAMPLES.md. It supports:

Phase 1 (Current Implementation):
- Node filtering by type (node_pattern.node_type)
- Edge filtering by relation_type and min_confidence
- Target filtering with field references (target.name, target.node_type)
- Aggregations: count, avg
- Group by single field
- Order by with direction (asc/desc)
- Limit

Phase 2 (Current Implementation):
- Additional operators: in, contains, regex, gt, gte, lt, lte, ne
- Multi-hop path queries with max_hops and avoid_cycles
- Edge queries (find: "edges")
- More aggregations: sum, min, max
- Multiple group_by fields
- Field projections (return_fields)

Phase 3 features are documented in QUERY_EXECUTOR_ROADMAP.md
"""

import logging
import re
from typing import Any, Dict, List

import psycopg2
from langchain_community.embeddings import HuggingFaceEmbeddings

# Initialize embeddings model (lazy loaded)
_embeddings_model = None


def get_embeddings_model():
    global _embeddings_model
    if _embeddings_model is None:
        _embeddings_model = HuggingFaceEmbeddings(
            model_name="microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext", model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True}
        )
    return _embeddings_model


logger = logging.getLogger(__name__)

# Configuration constants
MAX_REGEX_PATTERN_LENGTH = 200  # Maximum length for regex patterns to prevent ReDoS


def execute_query(query: Dict[str, Any], entities: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Execute a query against the synthetic data.

    Args:
        query: Query dictionary in the format from EXAMPLES.md
        entities: Dictionary of entities keyed by entity ID
        relationships: List of relationship dictionaries

    Returns:
        Dictionary with "results" key containing list of result rows

    Query Types:
    - find: "nodes" - Return source nodes (default, Phase 1)
    - find: "edges" or "relationships" - Return relationships (Phase 2)
    - find: "paths" - Return multi-hop paths (Phase 2)
    """
    find_type = query.get("find", "nodes")

    # Route to appropriate query handler
    if find_type in ["edges", "relationships"]:
        return execute_edge_query(query, entities, relationships)
    elif find_type == "paths":
        return execute_path_query(query, entities, relationships)

    # Check for vector search
    if "vector_search" in query:
        return execute_vector_search_query(query)

    else:
        # Default to node query
        return execute_node_query(query, entities, relationships)


def execute_vector_search_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a semantic vector search query using pgvector.

    Query format:
    {
        "vector_search": {
            "text": "query text",
            "top_k": 10,
            "min_similarity": 0.5 (optional)
        },
        "return_fields": ["name", "entity_type", "similarity"] (optional)
    }
    """
    vector_params = query.get("vector_search", {})
    query_text = vector_params.get("text")
    top_k = vector_params.get("top_k", 10)
    min_similarity = vector_params.get("min_similarity", 0.0)
    return_fields = query.get("return_fields", ["name", "entity_type", "similarity"])

    if not query_text:
        return {"results": []}

    # Generate embedding for query text
    try:
        model = get_embeddings_model()
        query_embedding = model.embed_query(query_text)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return {"error": str(e)}

    # Connect to DB and execute vector search
    results = []
    try:
        # Note: This requires the DATABASE_URL env var to be set
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return {"error": "DATABASE_URL not set"}

        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Cosine similarity is 1 - cosine distance (<=>)
                sql = """
                    SELECT
                        id,
                        name,
                        entity_type,
                        properties,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM entities
                    WHERE 1 - (embedding <=> %s::vector) > %s
                    ORDER BY similarity DESC
                    LIMIT %s
                """
                cur.execute(sql, (query_embedding, query_embedding, min_similarity, top_k))

                rows = cur.fetchall()
                for row in rows:
                    # Map to result dict
                    entity = {"id": row[0], "name": row[1], "type": row[2], "properties": row[3], "similarity": float(row[4])}

                    # Filter fields if requested
                    if return_fields:
                        filtered = {}
                        for field in return_fields:
                            # Handle similarity specifically or standard fields
                            if field == "similarity":
                                filtered[field] = entity["similarity"]
                            elif field == "node_type":
                                filtered[field] = entity["type"]
                            elif field in entity:
                                filtered[field] = entity[field]
                            elif field.startswith("properties."):
                                prop_name = field.split(".", 1)[1]
                                filtered[field] = entity["properties"].get(prop_name)
                        results.append(filtered)
                    else:
                        results.append(entity)

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return {"error": str(e), "results": []}

    return {"results": results}


def execute_node_query(query: Dict[str, Any], entities: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Execute a node query (original Phase 1 behavior).

    Query Flow:
    1. Filter source nodes by node_pattern (type, name, etc.)
    2. Filter edges by edge_pattern (relation_type, min_confidence)
    3. Apply filters to target nodes (target.name, target.node_type)
    4. Aggregate results if aggregate is specified
    5. Order results by order_by fields
    6. Apply limit
    7. Apply field projections if return_fields is specified
    """
    # Extract query components
    node_pattern = query.get("node_pattern", {})
    edge_pattern = query.get("edge_pattern", {})
    filters = query.get("filters", [])
    aggregate = query.get("aggregate", {})
    order_by = query.get("order_by", [])
    limit = query.get("limit")
    return_fields = query.get("return_fields")

    # Step 1: Filter source nodes by node_pattern
    source_nodes = filter_nodes_by_pattern(entities, node_pattern)

    # Step 2: Find matching relationships
    matches = []
    for node_id in source_nodes:
        node = entities[node_id]

        # Find relationships where this node is the subject
        for rel in relationships:
            if rel["subject_id"] != node_id:
                continue

            # Check edge_pattern
            if not matches_edge_pattern(rel, edge_pattern):
                continue

            # Get target node
            target_id = rel["object_id"]
            if target_id not in entities:
                continue

            target_node = entities[target_id]

            # Apply filters
            if not matches_filters(node, rel, target_node, filters):
                continue

            # Add match
            matches.append({"source": node, "edge": rel, "target": target_node})

    # Step 3: Aggregate if requested
    if aggregate:
        results = aggregate_results(matches, aggregate, node_pattern)
    else:
        # Return raw matches
        results = []
        for match in matches:
            result = {}
            var_name = node_pattern.get("var", "node")
            result[f"{var_name}.name"] = match["source"]["name"]
            result[f"{var_name}.id"] = match["source"]["id"]
            results.append(result)

    # Step 4: Order results
    if order_by:
        results = order_results(results, order_by)

    # Step 5: Apply limit
    if limit:
        results = results[:limit]

    # Step 6: Apply field projections
    if return_fields:
        results = project_fields(results, return_fields)

    return {"results": results}


def filter_nodes_by_pattern(entities: Dict[str, Dict], node_pattern: Dict[str, Any]) -> List[str]:
    """
    Filter entities by node_pattern.

    Supports:
    - node_type: Filter by entity type (e.g., "drug", "disease")
    - name: Filter by exact name match (case-insensitive)
    - var: Variable name for this node (used in aggregations)

    Returns list of matching entity IDs.
    """
    node_type = node_pattern.get("node_type")
    name = node_pattern.get("name")

    matching_ids = []

    for entity_id, entity in entities.items():
        # Check node type
        if node_type and entity["type"] != node_type:
            continue

        # Check name (case-insensitive)
        if name and entity["name"].lower() != name.lower():
            continue

        matching_ids.append(entity_id)

    return matching_ids


def matches_edge_pattern(rel: Dict[str, Any], edge_pattern: Dict[str, Any]) -> bool:
    """
    Check if a relationship matches the edge_pattern.

    Supports:
    - relation_type: Required relation type (e.g., "TREATS")
    - min_confidence: Minimum confidence threshold
    - direction: "outgoing" or "incoming" (currently only outgoing is supported)
    """
    if not edge_pattern:
        return True

    # Check relation type (case-insensitive)
    relation_type = edge_pattern.get("relation_type")
    if relation_type:
        # Normalize both to uppercase for comparison
        if rel["predicate"].upper() != relation_type.upper():
            return False

    # Check min_confidence
    min_confidence = edge_pattern.get("min_confidence")
    if min_confidence is not None:
        if rel.get("confidence", 0.0) < min_confidence:
            return False

    return True


def matches_filters(source: Dict, edge: Dict, target: Dict, filters: List[Dict]) -> bool:
    """
    Check if a match satisfies all filters.

    Supports field references:
    - source.* (from node_pattern var, e.g., drug.name)
    - target.* (target node fields)
    - edge.* (relationship fields)

    Operators:
    - eq: Equality (case-insensitive for strings)
    - ne: Not equal (case-insensitive for strings)
    - in: Field value in a list
    - contains: String contains substring (case-insensitive)
    - regex: Regular expression matching
    - gt/gte/lt/lte: Numeric and string comparisons
    """
    for filter_spec in filters:
        field = filter_spec.get("field", "")
        operator = filter_spec.get("operator", "eq")
        value = filter_spec.get("value")

        # Parse field reference (e.g., "target.name", "target.node_type")
        if "." in field:
            parts = field.split(".", 1)
            context = parts[0]
            field_name = parts[1]

            # Map context to data with alias support
            # Using a mapping approach for maintainability
            context_mapping = {
                "target": target,
                "object": target,  # Alias for target
                "source": source,
                "subject": source,  # Alias for source
                "edge": edge,
            }

            data = context_mapping.get(context)
            if data is None:
                # Assume it's the variable name from node_pattern
                data = source

            # Handle node_type as alias for type
            if field_name == "node_type" and (data is source or data is target):
                field_name = "type"

            actual_value = data.get(field_name)
        else:
            # Field without context, check all
            actual_value = target.get(field) or edge.get(field) or source.get(field)

        # Apply operator
        if not apply_operator(actual_value, operator, value):
            return False

    return True


def apply_operator(actual_value: Any, operator: str, expected_value: Any) -> bool:
    """
    Apply a filter operator to compare actual_value with expected_value.

    Supported operators:
    - eq: Equality (case-insensitive for strings)
    - ne: Not equal (case-insensitive for strings)
    - in: Field value in a list
    - contains: String contains substring (case-insensitive)
    - regex: Regular expression matching
    - gt: Greater than
    - gte: Greater than or equal
    - lt: Less than
    - lte: Less than or equal
    """
    if operator == "eq":
        # Case-insensitive comparison for strings
        if isinstance(actual_value, str) and isinstance(expected_value, str):
            return actual_value.lower() == expected_value.lower()
        else:
            return actual_value == expected_value

    elif operator == "ne":
        # Not equal (case-insensitive for strings)
        if isinstance(actual_value, str) and isinstance(expected_value, str):
            return actual_value.lower() != expected_value.lower()
        else:
            return actual_value != expected_value

    elif operator == "in":
        # Field value in a list
        if not isinstance(expected_value, list):
            return False
        # Case-insensitive comparison for strings
        if isinstance(actual_value, str):
            return any(actual_value.lower() == str(v).lower() for v in expected_value)
        else:
            return actual_value in expected_value

    elif operator == "contains":
        # String contains substring (case-insensitive)
        if not isinstance(actual_value, str) or not isinstance(expected_value, str):
            return False
        return expected_value.lower() in actual_value.lower()

    elif operator == "regex":
        # Regular expression matching
        # Note: For production use, consider adding pattern complexity validation
        # or timeouts to prevent ReDoS attacks
        if not isinstance(actual_value, str) or not isinstance(expected_value, str):
            return False
        # Basic protection: limit pattern length
        if len(expected_value) > MAX_REGEX_PATTERN_LENGTH:
            return False
        try:
            return bool(re.search(expected_value, actual_value, re.IGNORECASE))
        except re.error:
            return False

    elif operator == "gt":
        # Greater than
        if actual_value is None or expected_value is None:
            return False
        try:
            return actual_value > expected_value
        except TypeError:
            return False

    elif operator == "gte":
        # Greater than or equal
        if actual_value is None or expected_value is None:
            return False
        try:
            return actual_value >= expected_value
        except TypeError:
            return False

    elif operator == "lt":
        # Less than
        if actual_value is None or expected_value is None:
            return False
        try:
            return actual_value < expected_value
        except TypeError:
            return False

    elif operator == "lte":
        # Less than or equal
        if actual_value is None or expected_value is None:
            return False
        try:
            return actual_value <= expected_value
        except TypeError:
            return False

    else:
        # Unsupported operator - fail the filter
        return False


def aggregate_results(matches: List[Dict], aggregate: Dict[str, Any], node_pattern: Dict[str, Any]) -> List[Dict]:
    """
    Aggregate matches by group_by fields and compute aggregations.

    Supports:
    - group_by: List of field references to group by (e.g., ["drug.name"])
    - aggregations: Dict of aggregation functions
        - count: Count occurrences
        - avg: Average of numeric values
        - sum: Sum numeric values
        - min: Minimum value
        - max: Maximum value

    Returns list of aggregated result rows.
    """
    group_by = aggregate.get("group_by", [])
    aggregations = aggregate.get("aggregations", {})

    # Group matches
    groups = {}
    for match in matches:
        # Build group key
        key_parts = []
        for field_ref in group_by:
            value = get_field_value(match, field_ref, node_pattern)
            key_parts.append(str(value))

        key = tuple(key_parts)

        if key not in groups:
            groups[key] = []
        groups[key].append(match)

    # Compute aggregations for each group
    results = []
    for key, group_matches in groups.items():
        result = {}

        # Add group_by fields to result
        for i, field_ref in enumerate(group_by):
            result[field_ref] = key[i]

        # Compute aggregations
        for agg_name, agg_spec in aggregations.items():
            if isinstance(agg_spec, list) and len(agg_spec) >= 2:
                agg_func = agg_spec[0]
                agg_field = agg_spec[1]

                if agg_func == "count":
                    result[agg_name] = compute_count(group_matches, agg_field, node_pattern)
                elif agg_func == "avg":
                    result[agg_name] = compute_avg(group_matches, agg_field, node_pattern)
                elif agg_func == "sum":
                    result[agg_name] = compute_sum(group_matches, agg_field, node_pattern)
                elif agg_func == "min":
                    result[agg_name] = compute_min(group_matches, agg_field, node_pattern)
                elif agg_func == "max":
                    result[agg_name] = compute_max(group_matches, agg_field, node_pattern)

        results.append(result)

    return results


def get_field_value(match: Dict, field_ref: str, node_pattern: Dict[str, Any]) -> Any:
    """
    Get a field value from a match using a field reference.

    Field references can be:
    - var_name.field (e.g., "drug.name")
    - target.field (e.g., "target.name")
    - edge_var.field (e.g., "treatment.confidence")
    """
    if "." not in field_ref:
        return None

    parts = field_ref.split(".", 1)
    context = parts[0]
    field_name = parts[1]

    # Get the variable name from node_pattern
    var_name = node_pattern.get("var", "node")

    if context == var_name:
        data = match["source"]
    elif context == "target":
        data = match["target"]
    else:
        # Assume it's an edge variable
        data = match["edge"]

    return data.get(field_name)


def compute_count(matches: List[Dict], field_ref: str, node_pattern: Dict[str, Any]) -> int:
    """
    Count occurrences in matches.

    For fields like "treatment.evidence.paper_id", count unique paper IDs.
    For "treatment.evidence", count total evidence items.
    For other fields, count matches.
    """
    # Handle evidence.paper_id - count unique papers
    if "evidence.paper_id" in field_ref or ("evidence" in field_ref and "paper" in field_ref):
        # Count total papers across all matches
        total_papers = 0
        for match in matches:
            edge = match["edge"]
            # Use the papers list length
            total_papers += len(edge.get("papers", []))
        return total_papers

    # Handle evidence counting (total evidence)
    if field_ref.endswith(".evidence"):
        total = 0
        for match in matches:
            edge = match["edge"]
            # Count evidence items (evidence_count field)
            total += edge.get("evidence_count", 1)
        return total

    # For other fields, count matches
    return len(matches)


def compute_avg(matches: List[Dict], field_ref: str, node_pattern: Dict[str, Any]) -> float:
    """
    Compute average of a numeric field across matches.
    """
    values = []
    for match in matches:
        value = get_field_value(match, field_ref, node_pattern)
        if value is not None and isinstance(value, (int, float)):
            values.append(value)

    if not values:
        return 0.0

    return round(sum(values) / len(values), 2)


def compute_sum(matches: List[Dict], field_ref: str, node_pattern: Dict[str, Any]) -> float:
    """
    Compute sum of a numeric field across matches.
    """
    total = 0.0
    for match in matches:
        value = get_field_value(match, field_ref, node_pattern)
        if value is not None and isinstance(value, (int, float)):
            total += value

    return round(total, 2)


def compute_min(matches: List[Dict], field_ref: str, node_pattern: Dict[str, Any]) -> Any:
    """
    Compute minimum value of a field across matches.
    """
    values = []
    for match in matches:
        value = get_field_value(match, field_ref, node_pattern)
        if value is not None:
            values.append(value)

    if not values:
        return None

    return min(values)


def compute_max(matches: List[Dict], field_ref: str, node_pattern: Dict[str, Any]) -> Any:
    """
    Compute maximum value of a field across matches.
    """
    values = []
    for match in matches:
        value = get_field_value(match, field_ref, node_pattern)
        if value is not None:
            values.append(value)

    if not values:
        return None

    return max(values)


def order_results(results: List[Dict], order_by: List[List]) -> List[Dict]:
    """
    Order results by specified fields.

    order_by is a list of [field, direction] pairs, e.g.:
    [["paper_count", "desc"], ["avg_confidence", "desc"]]
    """
    if not order_by:
        return results

    # Build sort key function
    def sort_key(item):
        keys = []
        for field_spec in order_by:
            field = field_spec[0]
            direction = field_spec[1] if len(field_spec) > 1 else "asc"

            value = item.get(field, 0)
            # Convert to sortable value
            if value is None:
                value = 0

            # Reverse for descending
            if direction == "desc":
                # For numeric values, negate
                if isinstance(value, (int, float)):
                    value = -value
                # For strings, we'll handle separately

            keys.append(value)

        return tuple(keys)

    return sorted(results, key=sort_key)


def execute_edge_query(query: Dict[str, Any], entities: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Execute an edge/relationship query.

    Returns relationships instead of nodes, with source and target information.

    Query Flow:
    1. Filter relationships by edge_pattern
    2. Apply filters to source, edge, and target
    3. Order results
    4. Apply limit
    5. Apply field projections if return_fields is specified
    """
    edge_pattern = query.get("edge_pattern", {})
    filters = query.get("filters", [])
    order_by = query.get("order_by", [])
    limit = query.get("limit")
    return_fields = query.get("return_fields")

    # Find matching relationships
    results = []
    for rel in relationships:
        # Check edge_pattern
        if not matches_edge_pattern(rel, edge_pattern):
            continue

        # Get source and target nodes
        source_id = rel["subject_id"]
        target_id = rel["object_id"]

        if source_id not in entities or target_id not in entities:
            continue

        source_node = entities[source_id]
        target_node = entities[target_id]

        # Apply filters
        if not matches_filters(source_node, rel, target_node, filters):
            continue

        # Build result row with edge and node information
        result = {
            "subject.name": source_node["name"],
            "subject.id": source_node["id"],
            "subject.type": source_node["type"],
            "predicate": rel["predicate"],
            "object.name": target_node["name"],
            "object.id": target_node["id"],
            "object.type": target_node["type"],
            "confidence": rel.get("confidence", 0.0),
            "evidence_count": rel.get("evidence_count", 0),
            "papers": rel.get("papers", []),
        }

        results.append(result)

    # Order results
    if order_by:
        results = order_results(results, order_by)

    # Apply limit
    if limit:
        results = results[:limit]

    # Apply field projections
    if return_fields:
        results = project_fields(results, return_fields)

    return {"results": results}


def execute_path_query(query: Dict[str, Any], entities: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Execute a multi-hop path query.

    Traverses relationships to find paths from start node through specified edge patterns.

    Query Flow:
    1. Find start nodes matching path_pattern.start
    2. Traverse edges according to path_pattern.edges
    3. Apply filters
    4. Respect max_hops and avoid_cycles settings
    5. Order results
    6. Apply limit
    7. Apply field projections if return_fields is specified
    """
    path_pattern = query.get("path_pattern", {})
    filters = query.get("filters", [])
    order_by = query.get("order_by", [])
    limit = query.get("limit")
    return_fields = query.get("return_fields")

    if not path_pattern:
        return {"results": []}

    start_spec = path_pattern.get("start", {})
    edge_specs = path_pattern.get("edges", [])
    max_hops = path_pattern.get("max_hops", len(edge_specs))
    avoid_cycles = path_pattern.get("avoid_cycles", True)

    # Find start nodes
    start_nodes = filter_nodes_by_pattern(entities, start_spec)

    # Traverse paths
    paths = []
    for start_id in start_nodes:
        start_node = entities[start_id]
        # Start traversal with empty path
        traverse_paths(start_node, [], [], edge_specs, 0, max_hops, avoid_cycles, entities, relationships, paths)

    # Convert paths to result format
    results = []
    for path in paths:
        result = build_path_result(path, start_spec, edge_specs)
        results.append(result)

    # Apply filters to path results
    if filters:
        results = [r for r in results if matches_path_filters(r, filters)]

    # Order results
    if order_by:
        results = order_results(results, order_by)

    # Apply limit
    if limit:
        results = results[:limit]

    # Apply field projections
    if return_fields:
        results = project_fields(results, return_fields)

    return {"results": results}


def is_valid_edge_spec(edge_spec_item: Any) -> bool:
    """
    Validate that an edge_spec item has exactly 2 elements.

    Args:
        edge_spec_item: Item from edge_specs list to validate

    Returns:
        True if valid (list/tuple with exactly 2 elements), False otherwise
    """
    return isinstance(edge_spec_item, (list, tuple)) and len(edge_spec_item) == 2


def traverse_paths(
    current_node: Dict,
    current_path_nodes: List[Dict],
    current_path_edges: List[Dict],
    edge_specs: List[List],
    hop_index: int,
    max_hops: int,
    avoid_cycles: bool,
    entities: Dict[str, Dict],
    relationships: List[Dict],
    collected_paths: List,
):
    """
    Recursively traverse paths through the graph.

    Args:
        current_node: Current node in traversal
        current_path_nodes: Nodes visited so far in this path
        current_path_edges: Edges traversed so far in this path
        edge_specs: Edge specifications from path_pattern.edges
        hop_index: Current hop index (0-based)
        max_hops: Maximum number of hops allowed
        avoid_cycles: Whether to prevent revisiting nodes
        entities: All entities in the graph
        relationships: All relationships in the graph
        collected_paths: Output list to collect completed paths
    """
    # Add current node to path
    path_nodes = current_path_nodes + [current_node]

    # Check if we've completed all specified hops
    if hop_index >= len(edge_specs) or hop_index >= max_hops:
        # Path complete
        collected_paths.append({"nodes": path_nodes, "edges": current_path_edges})
        return

    # Get the edge specification for this hop
    # Validate edge_spec structure - must be exactly 2 elements
    if not is_valid_edge_spec(edge_specs[hop_index]):
        # Invalid edge spec, skip
        return

    edge_spec, target_spec = edge_specs[hop_index]

    # Find matching edges from current node
    for rel in relationships:
        if rel["subject_id"] != current_node["id"]:
            continue

        # Check if edge matches the edge_spec
        if not matches_edge_spec(rel, edge_spec):
            continue

        # Get target node
        target_id = rel["object_id"]
        if target_id not in entities:
            continue

        target_node = entities[target_id]

        # Check if target matches target_spec
        if not matches_node_spec(target_node, target_spec):
            continue

        # Check for cycles if needed
        if avoid_cycles and any(n["id"] == target_id for n in path_nodes):
            continue

        # Continue traversal
        path_edges = current_path_edges + [rel]
        traverse_paths(target_node, path_nodes, path_edges, edge_specs, hop_index + 1, max_hops, avoid_cycles, entities, relationships, collected_paths)


def matches_edge_spec(rel: Dict, edge_spec: Dict) -> bool:
    """Check if a relationship matches an edge specification from path_pattern."""
    # Check relation_type
    relation_type = edge_spec.get("relation_type")
    relation_types = edge_spec.get("relation_types", [])

    if relation_type:
        if rel["predicate"].upper() != relation_type.upper():
            return False

    if relation_types:
        if not any(rel["predicate"].upper() == rt.upper() for rt in relation_types):
            return False

    # Check min_confidence
    min_confidence = edge_spec.get("min_confidence")
    if min_confidence is not None:
        if rel.get("confidence", 0) < min_confidence:
            return False

    return True


def matches_node_spec(node: Dict, node_spec: Dict) -> bool:
    """Check if a node matches a node specification from path_pattern."""
    # Check node_type
    node_type = node_spec.get("node_type")
    node_types = node_spec.get("node_types", [])

    if node_type and node["type"] != node_type:
        return False

    if node_types and node["type"] not in node_types:
        return False

    # Check name if specified
    name = node_spec.get("name")
    if name and node["name"].lower() != name.lower():
        return False

    return True


def build_path_result(path: Dict, start_spec: Dict, edge_specs: List[List]) -> Dict:
    """
    Build a result dictionary from a path.

    Includes fields from nodes and edges based on variable names.
    For each node, includes all its fields prefixed with the variable name.
    For each edge, includes all its fields prefixed with the edge variable name.
    """
    nodes = path["nodes"]
    edges = path["edges"]

    result = {}

    # Add start node fields - include ALL fields from the node
    start_var = start_spec.get("var", "start")
    if nodes:
        start_node = nodes[0]
        for field_name, field_value in start_node.items():
            # Skip internal fields that shouldn't be exposed
            if field_name not in ["type", "canonical_id", "mentions", "aliases", "description"]:
                result[f"{start_var}.{field_name}"] = field_value

    # Add intermediate nodes and edges
    for i, edge_pair in enumerate(edge_specs):
        # Validate structure - must be exactly 2 elements
        if not is_valid_edge_spec(edge_pair):
            continue

        edge_spec, target_spec = edge_pair

        if i < len(edges):
            edge = edges[i]
            edge_var = edge_spec.get("var", f"edge{i}")
            # Add all edge fields, including metadata
            result[f"{edge_var}.relation_type"] = edge["predicate"]
            result[f"{edge_var}.confidence"] = edge.get("confidence", 0.0)
            # Include metadata fields directly at the edge variable level
            metadata = edge.get("metadata", {})
            for meta_key, meta_value in metadata.items():
                result[f"{edge_var}.{meta_key}"] = meta_value

        if i + 1 < len(nodes):
            node = nodes[i + 1]
            node_var = target_spec.get("var", f"node{i + 1}")
            # Add ALL fields from the node
            for field_name, field_value in node.items():
                # Skip internal fields that shouldn't be exposed
                if field_name not in ["type", "canonical_id", "mentions", "aliases", "description"]:
                    result[f"{node_var}.{field_name}"] = field_value

    return result


def matches_path_filters(path_result: Dict, filters: List[Dict]) -> bool:
    """
    Check if a path result matches filters.

    This is a simplified version that checks if filter fields exist in the result.
    """
    for filter_spec in filters:
        field = filter_spec.get("field", "")
        operator = filter_spec.get("operator", "eq")
        value = filter_spec.get("value")

        # Get the actual value from the path result
        actual_value = path_result.get(field)

        # Apply operator
        if not apply_operator(actual_value, operator, value):
            return False

    return True


def project_fields(results: List[Dict], return_fields: List[str]) -> List[Dict]:
    """
    Project only specified fields from results.

    Args:
        results: List of result dictionaries
        return_fields: List of field names to include

    Returns:
        List of results with only the specified fields
    """
    projected = []
    for result in results:
        projected_result = {}
        for field in return_fields:
            if field in result:
                projected_result[field] = result[field]
        projected.append(projected_result)

    return projected


class SQLQueryExecutor:
    """
    Translates JSON graph queries into PostgreSQL SQL and executes them.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url

    def get_connection(self):
        return psycopg2.connect(self.database_url)

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against PostgreSQL."""
        find_type = query.get("find", "nodes")

        if find_type in ["edges", "relationships"]:
            return self.execute_edge_query(query)
        elif find_type == "paths":
            return self.execute_path_query(query)
        else:
            return self.execute_node_query(query)

    def execute_node_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Translate and execute a node query."""
        node_pattern = query.get("node_pattern", {})
        edge_pattern = query.get("edge_pattern", {})
        filters = query.get("filters", [])
        aggregate = query.get("aggregate", {})
        order_by = query.get("order_by", [])
        limit = query.get("limit")
        return_fields = query.get("return_fields")

        var_name = node_pattern.get("var", "node")

        # Build SQL parts
        if return_fields:
            select_cols = []
            for rf in return_fields:
                select_cols.append(f'{self._translate_field(rf, var_name)} as "{rf}"')
            select_clause = "SELECT " + ", ".join(select_cols)
        else:
            select_clause = f'SELECT {var_name}.name as "{var_name}.name", {var_name}.id as "{var_name}.id"'
        from_clause = "FROM entities " + var_name
        where_clauses = []
        params = []

        # Node pattern filters
        if node_pattern.get("node_type"):
            where_clauses.append(f"{var_name}.entity_type = %s")
            params.append(node_pattern["node_type"])
        if node_pattern.get("name"):
            where_clauses.append(f"LOWER({var_name}.name) = LOWER(%s)")
            params.append(node_pattern["name"])

        # Vector similarity search (pgvector)
        if node_pattern.get("vector_search"):
            vector = node_pattern["vector_search"]
            # Format vector as PostgreSQL vector string: '[1,2,3]'
            if isinstance(vector, list):
                vector_str = "[" + ",".join(str(x) for x in vector) + "]"
            else:
                vector_str = str(vector)
            # pgvector uses <=> for cosine distance
            # Similarity = 1 - Distance
            # Cast both column and parameter to vector(768) type
            select_clause += f", (1 - ({var_name}.embedding::vector(768) <=> %s::vector(768))) as similarity"

            threshold = node_pattern.get("similarity_threshold")
            if threshold:
                where_clauses.append(f"({var_name}.embedding::vector(768) <=> %s::vector(768)) <= %s")
                params.append(vector_str)
                params.append(1.0 - threshold)

            # If no other order_by is specified, order by similarity
            if not order_by:
                order_by = [["similarity", "desc"]]
            params.insert(0, vector_str)

        # Edge pattern filters (requires JOIN)
        if edge_pattern:
            from_clause += f" JOIN relationships rel ON {var_name}.id = rel.subject_id"
            from_clause += " JOIN entities target ON rel.object_id = target.id"

            if edge_pattern.get("relation_type"):
                where_clauses.append("rel.predicate = %s")
                params.append(edge_pattern["relation_type"])
            if edge_pattern.get("min_confidence"):
                where_clauses.append("rel.confidence >= %s")
                params.append(edge_pattern["min_confidence"])

        # Additional filters
        for f in filters:
            sql, p = self._translate_filter(f, var_name)
            if sql:
                where_clauses.append(sql)
                params.extend(p)

        # Aggregations
        if aggregate:
            group_by = aggregate.get("group_by", [])
            aggregations = aggregate.get("aggregations", {})

            agg_selects = []
            for field in group_by:
                agg_selects.append(self._translate_field(field, var_name))

            for agg_name, agg_spec in aggregations.items():
                func, field = agg_spec[0], agg_spec[1]
                sql_func = self._map_agg_func(func)
                field_sql = self._translate_field(field, var_name)
                agg_selects.append(f"{sql_func}({field_sql}) as {agg_name}")

            select_clause = "SELECT " + ", ".join(agg_selects)

        sql = select_clause + " " + from_clause
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if aggregate and aggregate.get("group_by"):
            sql += " GROUP BY " + ", ".join([self._translate_field(f, var_name) for f in aggregate["group_by"]])

        # Order by
        if order_by:
            order_parts = []
            for spec in order_by:
                field = spec[0]
                direction = "DESC" if len(spec) > 1 and spec[1].lower() == "desc" else "ASC"
                order_parts.append(f"{self._translate_field(field, var_name)} {direction}")
            sql += " ORDER BY " + ", ".join(order_parts)

        if limit:
            sql += f" LIMIT {int(limit)}"

        results = self._run_sql(sql, params)
        return {"results": results}

    def execute_edge_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Translate and execute an edge query."""
        # Simple implementation for now
        sql = """
            SELECT
                s.name as "subject.name", s.id as "subject.id", s.entity_type as "subject.type",
                r.predicate as "predicate",
                o.name as "object.name", o.id as "object.id", o.entity_type as "object.type",
                r.confidence as "confidence"
            FROM relationships r
            JOIN entities s ON r.subject_id = s.id
            JOIN entities o ON r.object_id = o.id
        """
        params = []
        where_clauses = []

        edge_pattern = query.get("edge_pattern", {})
        if edge_pattern.get("relation_type"):
            where_clauses.append("r.predicate = %s")
            params.append(edge_pattern["relation_type"])

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        limit = query.get("limit")
        if limit:
            sql += f" LIMIT {int(limit)}"

        results = self._run_sql(sql, params)
        return {"results": results}

    def execute_path_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Translate and execute a multi-hop path query using sequential JOINs."""
        path_pattern = query.get("path_pattern", {})
        if not path_pattern:
            return {"results": []}

        start_spec = path_pattern.get("start", {})
        edge_specs = path_pattern.get("edges", [])
        return_fields = query.get("return_fields")
        limit = query.get("limit")

        # Start building the SQL
        start_var = start_spec.get("var", "node")
        from_clause = f"FROM entities {start_var}"
        where_clauses = []
        params = []

        if start_spec.get("node_type"):
            where_clauses.append(f"{start_var}.entity_type = %s")
            params.append(start_spec["node_type"])
        if start_spec.get("name"):
            where_clauses.append(f"LOWER({start_var}.name) = LOWER(%s)")
            params.append(start_spec["name"])
        elif start_spec.get("name_pattern"):
            where_clauses.append(f"{start_var}.name ~* %s")
            params.append(start_spec["name_pattern"])

        # Loop through edges and nodes for joins
        prev_node_var = start_var
        for i, hop in enumerate(edge_specs):
            edge_pattern = hop.get("edge", {})
            node_pattern = hop.get("node", {})

            edge_var = edge_pattern.get("var", f"rel_{i}")
            node_var = node_pattern.get("var", f"node_{i}")

            from_clause += f" JOIN relationships {edge_var} ON {prev_node_var}.id = {edge_var}.subject_id"
            from_clause += f" JOIN entities {node_var} ON {edge_var}.object_id = {node_var}.id"

            if edge_pattern.get("relation_type"):
                where_clauses.append(f"{edge_var}.predicate = %s")
                params.append(edge_pattern["relation_type"])
            elif edge_pattern.get("relation_types"):
                where_clauses.append(f"{edge_var}.predicate = ANY(%s)")
                params.append(edge_pattern["relation_types"])
            if edge_pattern.get("min_confidence"):
                where_clauses.append(f"{edge_var}.confidence >= %s")
                params.append(edge_pattern["min_confidence"])

            if node_pattern.get("node_type"):
                where_clauses.append(f"{node_var}.entity_type = %s")
                params.append(node_pattern["node_type"])
            elif node_pattern.get("node_types"):
                where_clauses.append(f"{node_var}.entity_type = ANY(%s)")
                params.append(node_pattern["node_types"])

            prev_node_var = node_var

        # Build SELECT clause
        if return_fields:
            select_parts = []
            for rf in return_fields:
                select_parts.append(f'{self._translate_field(rf, start_var)} as "{rf}"')
            select_clause = "SELECT " + ", ".join(select_parts)
        else:
            # Default: return names of all nodes in path
            select_parts = [f'{start_var}.name as "{start_var}.name"']
            for i, hop in enumerate(edge_specs):
                node_var = hop.get("node", {}).get("var", f"node_{i}")
                select_parts.append(f'{node_var}.name as "{node_var}.name"')
            select_clause = "SELECT " + ", ".join(select_parts)

        sql = f"{select_clause} {from_clause}"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if limit:
            sql += f" LIMIT {int(limit)}"

        results = self._run_sql(sql, params)
        return {"results": results}
        #     SELECT * FROM graph_path WHERE hop_count = %s
        # """
        # params = []
        # if start_spec.get("node_type"):
        #     params.append(start_spec["node_type"])
        # if start_spec.get("name"):
        #     params.append(start_spec["name"])
        # params.append(max_hops + 1)  # hop_count is 1-based start
        # params.append(max_hops + 1)

        # Note: This is a simplified path query. Real implementation would be more complex
        # to match specific edge types at each hop.

        # results = self._run_sql(sql_template, params)
        # return {"results": results}
        return {"results": [], "error": "Path queries not fully implemented in SQL yet"}

    def _translate_filter(self, filter_spec: Dict, var_name: str) -> tuple:
        field = filter_spec.get("field", "")
        operator = filter_spec.get("operator", "eq")
        value = filter_spec.get("value")

        field_sql = self._translate_field(field, var_name)

        if operator == "eq":
            return f"{field_sql} = %s", [value]
        elif operator == "ne":
            return f"{field_sql} != %s", [value]
        elif operator == "in":
            return f"{field_sql} = ANY(%s)", [value]
        elif operator == "gt":
            return f"{field_sql} > %s", [value]
        elif operator == "contains":
            return f"{field_sql} ILIKE %s", [f"%{value}%"]

        return None, []

    def _translate_field(self, field_ref: str, default_var: str) -> str:
        if "." not in field_ref:
            if field_ref == "similarity":
                return "similarity"
            return f"{default_var}.{field_ref}"

        parts = field_ref.split(".", 1)
        var = parts[0]
        field = parts[1]

        if var == "node":
            var = default_var
        if field == "node_type":
            field = "entity_type"

        return f"{var}.{field}"

    def _map_agg_func(self, func: str) -> str:
        mapping = {"count": "COUNT", "avg": "AVG", "sum": "SUM", "min": "MIN", "max": "MAX"}
        return mapping.get(func, "COUNT")

    def _run_sql(self, sql: str, params: list) -> List[Dict]:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    colnames = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()
                    return [dict(zip(colnames, row)) for row in rows]
        except Exception as e:
            logger.error(f"SQL error: {e}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Params: {params}")
            raise
