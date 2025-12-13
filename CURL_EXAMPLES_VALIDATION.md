# Curl Examples Validation Report

## Summary

This report documents the validation of curl examples in `client/curl/EXAMPLES.md` against the schema and their coverage of features introduced in Pull Request #3.

**Date:** 2025-12-13
**Status:** ✅ All issues resolved and PR #3 features covered

---

## Issues Found and Fixed

### 1. Schema Compliance Issues

#### Invalid Relationship Types (Fixed)

Three invalid relationship types were found and corrected:

1. **Example 7 (Differential Diagnosis):**
   - **Invalid:** `symptom_of` 
   - **Fixed:** Changed to `causes` with `direction: "incoming"`
   - **Reasoning:** The schema uses `causes` for Disease → Symptom relationships. To query from Symptom → Disease, we use the incoming direction.

2. **Example 11 (Drug-Drug Interactions):**
   - **Invalid:** `potentiates`, `antagonizes`
   - **Fixed:** Changed to use only `interacts_with`
   - **Reasoning:** These are not defined as separate relationship types in the schema. The `interacts_with` relationship includes an `interaction_type` property that can be set to "synergistic", "antagonistic", or "additive".

### 2. Missing Coverage

#### PR #3 Features (Added)

Pull Request #3 introduced comprehensive ontology support for scientific methodology. The following examples were added:

**New Entity Types Covered:**
- `hypothesis` - Example 13, 14, 17, 22
- `study_design` - Example 20
- `statistical_method` - Example 21
- `evidence_line` - Example 16, 18

**New Relationship Types Covered:**
- `predicts` - Example 17
- `refutes` - Example 22
- `tested_by` - Example 13
- `generates` - Example 18

**New Evidence Fields:**
- `eco_type` - Examples 14, 15, 16
- `obi_study_design` - Examples 13, 14
- `stato_methods` - Example 15

**Additional Coverage:**
- `protein` entity type - Example 19

---

## New Examples Added

### Example 13: Track Hypothesis Evolution
Shows how to query papers that test hypotheses and retrieve test outcomes with study design information.

### Example 14: Query by Study Design Quality
Demonstrates filtering treatment evidence by high-quality study designs (RCTs) using OBI and ECO ontology references.

### Example 15: Statistical Methods Analysis
Shows how to find studies using specific statistical methods (STATO ontology) for a given treatment.

### Example 16: Evidence Line Tracking
Demonstrates querying evidence lines that support hypotheses using SEPIO framework.

### Example 17: Hypothesis Predictions
Shows how to query what outcomes a hypothesis predicts.

### Example 18: Find Papers that Generate Evidence
Demonstrates finding papers that generate evidence lines with quality scores.

### Example 19: Protein-Centric Query
Shows how to query proteins targeted by FDA-approved drugs.

### Example 20: Study Design Quality Filter
Demonstrates querying by formal study design classification (OBI).

### Example 21: Statistical Method Classification
Shows how to query statistical methods by type (STATO).

### Example 22: Evidence Refuting Hypotheses
Demonstrates finding papers that refute hypotheses with refutation strength.

---

## Automated Testing

A comprehensive test suite has been created at `tests/test_curl_examples.py` with the following test coverage:

### Schema Compliance Tests (✅ All Passing)

1. **`test_all_queries_are_valid_json`** - Validates all curl examples contain syntactically correct JSON
2. **`test_node_types_are_valid`** - Ensures all entity types used match the schema
3. **`test_relation_types_are_valid`** - Ensures all relationship types used match the schema
4. **`test_examples_cover_basic_entity_types`** - Verifies coverage of core entities (drug, disease, gene, protein)
5. **`test_examples_cover_pr3_features`** - Verifies coverage of all PR #3 additions

### Integration Tests (Skipped - Require Running Server)

6. **`test_server_is_reachable`** - Checks if server is available
7. **`test_query_execution`** - Executes queries against live server

### Running the Tests

```bash
# Run all schema compliance tests
pytest tests/test_curl_examples.py::TestCurlExamplesSchemaCompliance -v

# Run all tests including integration (requires MEDGRAPH_SERVER env var)
MEDGRAPH_SERVER=http://localhost:8000 pytest tests/test_curl_examples.py -v

# Run only integration tests
pytest tests/test_curl_examples.py::TestCurlExamplesExecution -v -m integration
```

---

## Validation Results

### Before Fixes
- ❌ 3 invalid relationship types
- ❌ Missing protein entity coverage
- ❌ 0/4 PR #3 entity types covered
- ❌ 0/4 PR #3 relationship types covered

### After Fixes
- ✅ All relationship types valid
- ✅ All core entity types covered (drug, disease, gene, protein)
- ✅ 4/4 PR #3 entity types covered (hypothesis, study_design, statistical_method, evidence_line)
- ✅ 4/4 PR #3 relationship types covered (predicts, refutes, tested_by, generates)
- ✅ All examples use valid JSON syntax
- ✅ 22 total examples (up from 12)

---

## PR #3 Feature Summary

Pull Request #3 added ontology-based scientific methodology support:

### New Ontologies Integrated
1. **ECO** (Evidence & Conclusion Ontology) - Evidence type classification
2. **OBI** (Ontology for Biomedical Investigations) - Study designs
3. **STATO** (Statistics Ontology) - Statistical methods
4. **IAO** (Information Artifact Ontology) - Hypotheses
5. **SEPIO** (Scientific Evidence and Provenance Information Ontology) - Evidence chains

### New Schema Elements

**Entity Types:**
- `Hypothesis` - Scientific hypotheses tracked across literature
- `StudyDesign` - Formal study design classifications
- `StatisticalMethod` - Statistical methods used in analysis
- `EvidenceLine` - Structured evidence chains (SEPIO)

**Relationship Types:**
- `PREDICTS` - Hypothesis predicting outcomes
- `REFUTES` - Evidence refuting hypotheses
- `TESTED_BY` - Hypotheses tested by studies
- `GENERATES` - Studies generating evidence

**Enhanced Evidence Fields:**
- `eco_type` - ECO evidence type identifier
- `obi_study_design` - OBI study design identifier
- `stato_methods` - List of STATO statistical method identifiers

---

## Recommendations

1. **For New Examples:** Always validate against the schema before adding to EXAMPLES.md
2. **For Schema Changes:** Update `test_curl_examples.py` to validate new entity/relationship types
3. **For Documentation:** Keep EXAMPLES.md in sync with schema additions
4. **For Testing:** Run `pytest tests/test_curl_examples.py` before committing changes to examples

---

## Files Modified

1. `client/curl/EXAMPLES.md` - Fixed 3 invalid relationships, added 10 new examples
2. `tests/test_curl_examples.py` - New comprehensive test suite (370+ lines)
3. `CURL_EXAMPLES_VALIDATION.md` - This report

---

## Conclusion

All curl examples in `client/curl/EXAMPLES.md` are now:
- ✅ Schema-compliant
- ✅ Covering all core entity types
- ✅ Covering all PR #3 features
- ✅ Automatically validated via pytest
- ✅ Properly documented with expected responses

The examples can be used with confidence for API documentation, client development, and user education.
