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

Phase 2/3 features are documented in QUERY_EXECUTOR_ROADMAP.md
"""

from typing import Any, Dict, List


def execute_query(query: Dict[str, Any], entities: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
    """
    Execute a query against the synthetic data.

    Args:
        query: Query dictionary in the format from EXAMPLES.md
        entities: Dictionary of entities keyed by entity ID
        relationships: List of relationship dictionaries

    Returns:
        Dictionary with "results" key containing list of result rows

    Query Flow:
    1. Filter source nodes by node_pattern (type, name, etc.)
    2. Filter edges by edge_pattern (relation_type, min_confidence)
    3. Apply filters to target nodes (target.name, target.node_type)
    4. Aggregate results if aggregate is specified
    5. Order results by order_by fields
    6. Apply limit
    """
    # Extract query components
    node_pattern = query.get("node_pattern", {})
    edge_pattern = query.get("edge_pattern", {})
    filters = query.get("filters", [])
    aggregate = query.get("aggregate", {})
    order_by = query.get("order_by", [])
    limit = query.get("limit")

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

    # Check relation type
    relation_type = edge_pattern.get("relation_type")
    if relation_type:
        # Case-insensitive comparison
        if rel["predicate"].upper() != relation_type.upper():
            return False

    # Check min_confidence
    min_confidence = edge_pattern.get("min_confidence")
    if min_confidence is not None:
        if rel["confidence"] < min_confidence:
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

            # Map context to data
            if context == "target":
                data = target
                # Handle node_type as alias for type
                if field_name == "node_type":
                    field_name = "type"
            elif context == "source":
                data = source
                if field_name == "node_type":
                    field_name = "type"
            else:
                # Assume it's the variable name from node_pattern
                data = source
                if field_name == "node_type":
                    field_name = "type"

            actual_value = data.get(field_name)
        else:
            # Field without context, check all
            actual_value = target.get(field) or edge.get(field) or source.get(field)

        # Apply operator
        if operator == "eq":
            # Case-insensitive comparison for strings
            if isinstance(actual_value, str) and isinstance(value, str):
                if actual_value.lower() != value.lower():
                    return False
            else:
                if actual_value != value:
                    return False
        else:
            # Unsupported operator
            return False

    return True


def aggregate_results(matches: List[Dict], aggregate: Dict[str, Any], node_pattern: Dict[str, Any]) -> List[Dict]:
    """
    Aggregate matches by group_by fields and compute aggregations.

    Supports:
    - group_by: List of field references to group by (e.g., ["drug.name"])
    - aggregations: Dict of aggregation functions
        - count: Count occurrences
        - avg: Average of numeric values

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
    if "evidence.paper_id" in field_ref or "evidence" in field_ref and "paper" in field_ref:
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
