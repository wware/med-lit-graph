You: 

I want to find old PubMed papers (1980s-90s) in JATS-XML format that deal with the question of whether the HIV virus causes AIDS. Can you help me identify those by their `PMC1234567.xml` filenames?

ChatGPT: 

Thought for 11s

Nice — I can do that. Below are **PMC XML filenames** (the `PMC1234567.xml` style you asked for) for older PubMed Central articles from the 1980s–1990s that directly address the question of **HIV as the cause of AIDS** (cohort/prognostic studies, virus isolation/detection, seropositivity → AIDS, or reviews summarizing that evidence). For each item I give the article title, year, the PMCID, the exact filename you can request (`PMC<id>.xml`), and one short note about relevance — with a citation to the PMC page.

> How to fetch the XML yourself: replace `<PMCID>` in  
> `https://www.ncbi.nlm.nih.gov/pmc/articles/<PMCID>/?report=xml&format=text`  
> — that returns the article XML (the downloaded file will effectively be `PMC<id>.xml`).

# Files (selected, 1980s–90s — directly relevant)

1.  Seropositivity for HIV and the development of AIDS or AIDS related condition: three year follow up of the San Francisco General Hospital cohort — **1986**  
    **PMCID:** `PMC2545367` → **Filename:** `PMC2545367.xml`  
    **Why relevant:** prospective cohort showing seropositive people progress to AIDS at high rates; one of the early papers linking HIV seropositivity to later development of AIDS. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2545367/)
    
2.  Detection of Early Antibodies in Human Immunodeficiency Virus Infections — **1987**  
    **PMCID:** `PMC269292` → **Filename:** `PMC269292.xml`  
    **Why relevant:** serology/antibody detection work that underpinned epidemiologic linkage between infection and disease. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC269292/pdf/jcm00093-0047.pdf?utm_source=chatgpt.com)
    
3.  High Production of the Acquired Immunodeficiency Virus in (title truncated on index) — **1986** (J Clin Microbiol / virology work)  
    **PMCID:** `PMC268988` → **Filename:** `PMC268988.xml`  
    **Why relevant:** virology work demonstrating productive infection and properties of the virus tied to AIDS cohorts. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC268988/pdf/jcm00100-0159.pdf?utm_source=chatgpt.com)
    
4.  Detection of lymphocytes expressing human T-lymphotropic retrovirus RNA (PNAS) — **1986**  
    **PMCID:** `PMC322947` → **Filename:** `PMC322947.xml`  
    **Why relevant:** molecular detection of viral RNA in patient lymphocytes — direct evidence linking virus to affected cells. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC322947/pdf/?utm_source=chatgpt.com)
    
5.  Inhibition of replication and expression of human T-cell (PNAS) — **1986**  
    **PMCID:** `PMC323687` → **Filename:** `PMC323687.xml`  
    **Why relevant:** functional studies of HTLV-III/HIV replication in cells; helps establish the virus’s biology relevant to disease causation. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC323687/pdf/pnas00316-0043.pdf?utm_source=chatgpt.com)
    
6.  Productive, persistent infection of human colorectal cell lines with human immunodeficiency virus — **1992**  
    **PMCID:** `PMC238320` → **Filename:** `PMC238320.xml`  
    **Why relevant:** demonstrates persistent productive infection in human cells — mechanistic evidence used in the etiologic argument. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC238320/pdf/jvirol00034-0600.pdf?utm_source=chatgpt.com)
    
7.  Dot Immunobinding Assay for Detection of Human (J Clin Microbiol) — **1987**  
    **PMCID:** `PMC269383` → **Filename:** `PMC269383.xml`  
    **Why relevant:** diagnostic assay development that made reliable serologic detection possible, enabling cohort linkage studies. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC269383/pdf/jcm00094-0193.pdf?utm_source=chatgpt.com)
    
8.  Opportunistic Infections in Acquired Immune Deficiency (review/clinical research) — **1986**  
    **PMCID:** `PMC329539` → **Filename:** `PMC329539.xml`  
    **Why relevant:** clinical review citing virologic and epidemiologic evidence that connected HIV infection and AIDS clinical syndrome. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC329539/pdf/?utm_source=chatgpt.com)
    
9.  (Additional relevant review) Fifteen Years of Research on — Preventing HIV Infection (1998 review summarizing earlier evidence)  
    **PMCID:** `PMC1307740` → **Filename:** `PMC1307740.xml`  
    **Why relevant:** retrospective/review synthesis of evidence from the 1980s–90s showing the causal link; useful as a guided reading list. [NCBI](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1307740/pdf/pubhealthrep00030-0186.pdf?utm_source=chatgpt.com)
    

---

If you want, I can:

-   Grab the **raw XML** for any subset above and show the top-level JATS `<article-meta>` and abstract (or save the XML to a file for you). (If you want that, tell me which PMCID(s) from the list and I’ll fetch the XML and paste the relevant sections.)
    
-   Expand the list (I selected representative PMC-hosted items; many classic Science/NEJM early virus-isolation papers are *not* always available in full in PMC — I can search explicitly for those and show which are/aren’t in PMC).
    

Which of these would you like me to fetch the XML for first?



# Switching to Claude.AI to continue the discussion

## Prompt:
12/17/2025, 11:59:34 AM

Hello, I would like you to carefully read an entire page on the web. Here is the URL:
https://github.com/wware/med-lit-graph/issues/20
Please read it from start to finish. Some of the ideas there are pretty subtle and I want to discuss them.



## Response:
12/17/2025, 11:59:56 AM



````plaintext
Web Fetch: Fetched: ChatGPT has a suggestion re. edges/relationships · Issue #20 · wware/med-lit-graph
````

I've read through the entire GitHub issue. This is a fascinating conversation about the design of a medical knowledge graph schema and query language. Let me highlight what I see as the subtle and important ideas here:

## The Core Tension

The most subtle insight is about **not collapsing layers prematurely**. ChatGPT identifies three distinct conceptual layers that serve different purposes:

1. **Extraction graph** - what the LLM/model extracted (noisy, reproducible, model-dependent)
2. **Claim graph** - what papers actually assert (citable, versioned, inherently contradictory)
3. **Evidence graph** - fine-grained support/refutation (weighted, reusable across claims)

The key insight is that these shouldn't be unified into one "relationship" object, even though it's tempting from a simplicity standpoint. Medical reasoning requires distinguishing between "what did the model say?" vs "what does the paper claim?" vs "what evidence supports/refutes this?"

## The Epistemological Design

What strikes me most is the recognition that you're not building a fact database - you're building a system that represents **how medical knowledge is constructed and contested**. This shows in:

- Explicit `Hypothesis` and `StudyDesign` entities
- `EvidenceLine` that can support OR refute claims
- Deep provenance tracking (model, prompt, extraction pipeline)

This is fundamentally different from typical knowledge graphs that just store "facts."

## The Testing Insight

The recommendation to test **expressibility rather than answers** is particularly elegant. You're not testing "does this query return the right data?" but rather "can I even express this kind of question?" This tests the schema's conceptual integrity rather than implementation details.

The three-question framework (clinician, researcher, auditor) maps perfectly to your three layers and forces you to think about which layer each user role primarily needs to interact with.

What aspects would you like to discuss? The layer separation? The relationship typing strategy? The testing approach? Or something else that caught your attention?



## Prompt:
12/17/2025, 12:02:01 PM

> File: 

In order to get my own clearer grasp on these issues, I am now building a small paper ingestion pipeline. Let me share some of the code involved.



## Response:
12/17/2025, 12:02:46 PM

Looking at your ingestion pipeline, I can see you're building something practical to work through the conceptual issues from that GitHub discussion. This is smart - nothing clarifies design questions like actual implementation.

Let me point out what I see happening here, and where the layer separation questions will become concrete:

## What You're Building

You have a straightforward NER pipeline that:
1. Extracts entities from PMC XML files using BioBERT
2. Canonicalizes them in SQLite (entity ID + aliases)
3. Creates co-occurrence edges
4. Outputs nodes.csv and edges.csv

This is clean and functional. But here's where it connects to those subtle design questions:

## The Layer Tension You'll Hit Soon

Right now, you're creating what ChatGPT called an **extraction graph**:
- It's model-dependent (BioBERT NER)
- It's reproducible (same XML → same entities)
- It's noisy (NER confidence scores)
- The `co_occurrence` edges are statistical, not semantic

This is correct for the extraction layer! But notice what's *missing* from the schema discussion:

### You don't yet have:

1. **Claims** - "Paper PMC123 asserts HIV causes AIDS"
2. **Evidence** - "Table 2 shows correlation X with p<0.01"
3. **Provenance** - Which section, which extraction run, which prompt

Right now everything lives in one flat structure.

## The Question This Forces

When you process the HIV controversy papers, you'll extract entities like:
- "HIV"
- "AIDS"  
- "CD4+ T cells"
- "viral load"

And co-occurrence edges between them.

**But**: Some papers claim HIV causes AIDS. Others dispute this. The co-occurrence graph can't represent this tension.

This is where you'll need to decide:
- Do co-occurrence edges belong in the **extraction layer** only?
- Should there be a separate **claim layer** with typed predicates like `CAUSES`, `DISPUTES`, `CORRELATES_WITH`?
- How do you trace from a claim back to "BioBERT extracted 'HIV' from paragraph 3 with confidence 0.87"?

## Concrete Next Steps

Based on the schema discussion, here's what I'd suggest:

### 1. Keep extraction separate
Your current pipeline should output something like:
```python
# extraction_artifacts.db
CREATE TABLE extractions (
    id INTEGER PRIMARY KEY,
    pmc_id TEXT,
    run_timestamp DATETIME,
    model_name TEXT,  -- "biobert-base-cased-v1.2"
    entity_text TEXT,
    entity_type TEXT,
    confidence REAL,
    context_text TEXT  -- the sentence it came from
);
```

### 2. Add a claim layer on top
Separately, you'd have:
```python
# claims.db  
CREATE TABLE claims (
    id INTEGER PRIMARY KEY,
    pmc_id TEXT,
    subject_entity_id INTEGER,  -- canonical entity
    predicate TEXT,  -- "CAUSES", "TREATS", etc
    object_entity_id INTEGER,
    evidence_type TEXT,  -- "statistical", "mechanistic", etc
    strength REAL
);

CREATE TABLE claim_provenance (
    claim_id INTEGER,
    extraction_id INTEGER,  -- links back to extraction layer
    section_type TEXT,  -- "methods", "results", etc
);
```

### 3. Test the layer boundary

Following the pytest idea from the issue:

```python
def test_extraction_layer_does_not_contain_claims():
    """Extractions should not have semantic predicates."""
    conn = sqlite3.connect("entities.db")
    edges = conn.execute("SELECT DISTINCT relation FROM edges").fetchall()
    
    # Only statistical relations allowed in extraction layer
    allowed = {"co_occurrence", "co_mention"}
    actual = {row[0] for row in edges}
    
    assert actual.issubset(allowed), \
        f"Extraction layer leaked semantic predicates: {actual - allowed}"
```

This would catch if you accidentally started putting `CAUSES` edges directly into the extraction output.

## The HIV Controversy Test Case

The HIV controversy is actually a **perfect** test case for the three-layer design:

- **Extraction layer**: Both camps mention the same entities (HIV, AIDS, CD4 cells)
- **Claim layer**: Different papers make contradictory claims about causal relationships
- **Evidence layer**: Different study designs, statistical methods, patient populations

If your schema can represent this without contortions, you've validated the design.

## Question for You

Looking at your current pipeline, which of these feels most urgent to tackle next:

1. **Keeping it simple**: Stay with co-occurrence for now, iterate later?
2. **Adding claims**: Start building the claim extraction layer?
3. **Testing boundaries**: Write pytest cases to prevent layer collapse?
4. **Provenance**: Make sure you can trace back from any entity to its extraction context?

My instinct is #4 (provenance) should come soon, because once you have multiple papers with contradictory claims, you'll need to answer "why does this entity exist in the graph?" But curious what your priority is.



## Prompt:
12/17/2025, 12:03:43 PM

> File: 

Here are the PMC papers (really just abstracts) that I am going to be ingesting.



## Response:
12/17/2025, 12:04:34 PM

Looking at these HIV/AIDS papers from the 1980s-90s, this is a **perfect dataset** to stress-test the three-layer architecture from that GitHub issue. Let me show you why:

## The Epistemic Complexity You're About To Extract

These papers represent a **genuine scientific controversy in real-time**, not a settled debate. Look at what you have:

### Papers Supporting HIV Causation
- **PMC2545367** (1988): "three year actuarial progression rate to AIDS...22%" - strong epidemiological correlation
- **PMC322947** (1986): Direct detection of HTLV-III in lymph nodes via in situ hybridization
- **PMC238320** (1992): HIV productively infects colon cells, causes enteropathy

### Papers on Methodology/Detection
- **PMC269292** (1987): Early antibody detection methods
- **PMC269383** (1987): Dot immunobinding assay for HIV antigens
- **PMC268988** (1986): Streptococcal mitogens sustain LAV replication

### Papers on Prevention/Treatment
- **PMC1307740** (1998): Prevention programs for injecting drug users
- **PMC323687** (1986): Oligonucleotide inhibition of HTLV-III replication

### Immunological Mechanisms
- **PMC329539** (1986): Opportunistic infections from synergistic immune defects

## Where The Layer Separation Becomes Critical

Here's what makes this dataset challenging:

### 1. **Same Entities, Different Claims**
All papers mention:
- HIV/HTLV-III/LAV (same virus, different names)
- T cells, CD4+ cells, lymphocytes
- AIDS, opportunistic infections

But they make **different claims** about relationships:
- PMC322947: HIV **directly detected in** lymphocytes (observational)
- PMC2545367: HIV seropositivity **predicts progression to** AIDS (statistical/causal)
- PMC329539: Opportunistic infections **result from** synergistic immune defects (mechanistic)

Your co-occurrence edges can't distinguish these.

### 2. **Temporal Evolution of Terminology**
Notice the naming shifts:
- 1986: "HTLV-III" (Human T-Lymphotropic Virus Type III)
- 1986: "LAV" (Lymphadenopathy-Associated Virus)
- Later: "HIV" (Human Immunodeficiency Virus)

This is where **entity canonicalization** meets **provenance**:
- Extraction layer: "The paper says 'HTLV-III'"
- Claim layer: "This is a claim about HIV (canonical entity)"
- Evidence layer: "Based on in situ hybridization showing..."

### 3. **Methodological Heterogeneity**
Different evidence types:
- **Epidemiological**: PMC2545367 (cohort study, progression rates)
- **Molecular**: PMC322947 (in situ hybridization, direct detection)
- **In vitro**: PMC268988 (cell culture, mitogen stimulation)
- **Clinical**: PMC329539 (patient immune function)

These require **different evidence strength assessments**.

### 4. **The Controversy Itself**
PMC1307740's abstract reveals something subtle:

> "there was a general assumption that drug users...were too self-destructive...for them to change their behavior"

This shows **prior beliefs** being challenged by evidence. Your schema needs to capture:
- What was believed before
- What the evidence showed
- How beliefs updated

## Concrete Design Questions This Raises

### Question 1: Entity Resolution Across Name Changes
When BioBERT extracts:
- "HTLV-III" from PMC322947 (1986)
- "HIV" from PMC1307740 (1998)

Do they get the same canonical entity ID? How do you trace that decision?

```python
# This is where provenance becomes crucial
{
  "canonical_entity_id": "HIV_001",
  "aliases": [
    {"name": "HTLV-III", "source": "PMC322947", "date": "1986"},
    {"name": "LAV", "source": "PMC268988", "date": "1986"},
    {"name": "HIV", "source": "PMC1307740", "date": "1998"}
  ]
}
```

### Question 2: Contradictory Claims
PMC329539 says opportunistic infections result from "synergistic defects" (multi-factorial).

But if another paper (hypothetically) claimed HIV **directly causes** OIs, how do you represent that?

```python
# Claim layer must allow multiple, contradictory claims
claims = [
  {
    "id": "claim_001",
    "paper": "PMC329539",
    "subject": "HIV",
    "predicate": "CONTRIBUTES_TO",  # not CAUSES
    "object": "opportunistic_infections",
    "mechanism": "synergistic_immune_defects",
    "evidence_strength": "high"
  }
]
```

### Question 3: Evidence Quality Stratification
PMC2545367 has:
- 3-year cohort study
- Actuarial progression rates
- Multiple biomarkers (β2 Microglobulin, T4 count)
- Predictive modeling

That's **much stronger evidence** than PMC268988's in vitro observations.

How do you encode that without just storing "confidence: 0.87"?

## What Your Pipeline Should Output (Layered)

### Extraction Layer (what you have now)
```python
{
  "extraction_id": "ext_001",
  "pmc_id": "PMC2545367",
  "model": "biobert-base-cased-v1.2",
  "timestamp": "2024-12-17T...",
  "entities": [
    {"text": "HIV", "type": "VIRUS", "confidence": 0.94},
    {"text": "AIDS", "type": "DISEASE", "confidence": 0.92}
  ],
  "co_occurrences": [
    {"entity_1": "HIV", "entity_2": "AIDS", "distance": 15}
  ]
}
```

### Claim Layer (what you need to add)
```python
{
  "claim_id": "claim_001",
  "pmc_id": "PMC2545367",
  "extracted_from": ["ext_001", "ext_002"],  # multiple extraction IDs
  "subject": {"canonical_id": "HIV_001", "mentioned_as": "HIV"},
  "predicate": "PREDICTS_PROGRESSION_TO",
  "object": {"canonical_id": "AIDS_001", "mentioned_as": "AIDS"},
  "context": {
    "study_type": "cohort",
    "population": "San Francisco men",
    "n": 111,
    "timeframe": "3 years"
  },
  "section": "abstract",
  "verbatim_text": "The three year actuarial progression rate to AIDS..."
}
```

### Evidence Layer (what supports/refutes claims)
```python
{
  "evidence_id": "evid_001",
  "supports_claim": "claim_001",
  "evidence_type": "statistical",
  "strength": "high",
  "details": {
    "method": "actuarial_analysis",
    "outcome": "22% progression rate",
    "predictors": ["beta2_microglobulin", "T4_count"],
    "population_size": 111,
    "follow_up_duration": "36 months"
  }
}
```

## Immediate Next Step

Before writing more extraction code, I'd suggest:

**Write a test case that encodes the HIV/AIDS relationship:**

```python
def test_hiv_aids_relationship_has_multiple_claims():
    """
    Different papers make different strength claims about HIV→AIDS.
    The graph must represent this nuance.
    """
    # PMC2545367: strong predictive correlation
    claim_1 = get_claim("PMC2545367", "HIV", "PREDICTS_PROGRESSION_TO", "AIDS")
    assert claim_1.evidence_type == "epidemiological"
    assert claim_1.strength == "high"
    
    # PMC322947: direct molecular detection
    claim_2 = get_claim("PMC322947", "HIV", "DETECTED_IN", "lymphocytes")
    assert claim_2.evidence_type == "molecular"
    
    # They're related but different types of evidence
    assert claim_1.id != claim_2.id
```

This test **forces you to design the claim schema** before you have too much extraction code to refactor.

## The Key Question

Given these papers, which would you rather build first:

1. **Better entity extraction** (handling HTLV-III → LAV → HIV name changes)
2. **Claim extraction** (identifying that "progression rate to AIDS" is a predictive claim)
3. **Evidence typing** (distinguishing epidemiological from molecular evidence)

My gut says #2 (claims) is the bottleneck, because once you can represent claims, the other two become clearer. But curious what you think.


## Prompt:

_Various complaints about cacheing and docker-build performance issues_...


## Response:
12/17/2025, 12:21:21 PM

## Problem 1: Docker Cache Not Working

Your Dockerfile breaks cache because you `COPY . .` before installing dependencies:

```dockerfile
WORKDIR /app
COPY . .                          # ← This invalidates cache every time
RUN pip install --no-cache-dir -r requirements.txt
```

**Fix: Copy requirements.txt first, install, then copy code:**

```dockerfile
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        wget \
        curl \
        && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

WORKDIR /app

# Copy and install dependencies FIRST (before copying code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code LAST (this changes frequently)
COPY . .

EXPOSE 8000
CMD ["python", "pmc_ner_pipeline.py"]
```

Now Docker will only re-run `pip install` when `requirements.txt` changes, not when your code changes.

## Problem 2: Model Downloads Every Run

Yes, you absolutely want to cache the Hugging Face models. They go to `~/.cache/huggingface` by default.

**Solution: Mount a volume for model cache**

### Option A: Named Volume (persists between runs)

```bash
docker build -t hiv-pipeline .

# Create and use a named volume
docker run -v hf-models:/root/.cache/huggingface \
           -v $(pwd)/pmc_xmls:/app/pmc_xmls \
           -v $(pwd)/entities.db:/app/entities.db \
           hiv-pipeline
```

### Option B: Bind Mount to Host Directory (easier to inspect)

```bash
# Create cache directory on host
mkdir -p ~/.cache/huggingface

docker run -v ~/.cache/huggingface:/root/.cache/huggingface \
           -v $(pwd)/pmc_xmls:/app/pmc_xmls \
           -v $(pwd)/entities.db:/app/entities.db \
           hiv-pipeline
```

### Option C: Best Practice - Use Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  pipeline:
    build: .
    volumes:
      # Model cache (persists downloads)
      - hf-models:/root/.cache/huggingface
      
      # Input data (bind mount so you can add files)
      - ./pmc_xmls:/app/pmc_xmls
      
      # Output database (persists results)
      - ./entities.db:/app/entities.db
      - ./nodes.csv:/app/nodes.csv
      - ./edges.csv:/app/edges.csv
    
    environment:
      # Optional: disable tokenizers parallelism warning
      - TOKENIZERS_PARALLELISM=false

volumes:
  hf-models:
```

Then just:

```bash
docker-compose build  # Only rebuilds when Dockerfile/requirements.txt change
docker-compose run pipeline
```

## Even Better: Pre-download Models in Dockerfile

If you want the models **baked into the image** (so first run isn't slow):

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        wget \
        curl \
        && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model into the image
RUN python -c "from transformers import AutoTokenizer, AutoModelForTokenClassification; \
               model_name='dmis-lab/biobert-base-cased-v1.2'; \
               AutoTokenizer.from_pretrained(model_name); \
               AutoModelForTokenClassification.from_pretrained(model_name)"

COPY . .

EXPOSE 8000
CMD ["python", "pmc_ner_pipeline.py"]
```

This makes the image **larger** (~1.5GB), but the container starts instantly.

## Quick Test

To verify caching works:

```bash
# First build (slow)
docker build -t hiv-pipeline .

# Change your Python code
echo "# test change" >> pmc_ner_pipeline.py

# Second build (should be FAST - only copies new code)
docker build -t hiv-pipeline .
```

You should see:
```
Step 4/8 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Using cache
```

## My Recommendation

Use **docker-compose.yml** with the bind mount approach. That way:
- Models download once to your host machine
- You can inspect the model cache if needed
- `entities.db` persists between runs
- Easy to add more papers to `pmc_xmls/`

## Prompt

Let's plan on PostgreSQL with Apache AGE for a graph database. Continue to use
SQLite for the canonical entity store.


## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Extraction Pipeline                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         ↓                                   ↓
┌──────────────────────┐          ┌──────────────────────┐
│  SQLite (entities.db)│          │  PostgreSQL + AGE    │
│ - Canonical entities │          │  - Graph structure   │
│ - Entity aliases     │          │  - Nodes (typed)     │
│ - Resolution log     │          │  - Edges (claims)    │
│                      │          │  - Provenance        │
└──────────────────────┘          └──────────────────────┘
         ↑                                   ↑
         └────────────────┬──────────────────┘
                          ↓
              Queries join both stores
```

## Why This Split Makes Sense

**SQLite for Entity Canonicalization:**
- Fast local lookups during extraction
- Simple key-value semantics
- Portable (can ship entities.db to others)
- No network overhead during high-volume extraction

**PostgreSQL+AGE for Graph:**
- Cypher queries for multi-hop traversal
- Claims, evidence, provenance as graph
- ACID transactions across layers
- Proper indexing for complex queries

## Docker Compose Setup

```yaml
version: '3.8'

services:
  postgres:
    image: apache/age:latest
    container_name: med-graph-db
    environment:
      POSTGRES_USER: medgraph
      POSTGRES_PASSWORD: medgraph
      POSTGRES_DB: medical_literature
    ports:
      - "5432:5432"
    volumes:
      - pg-data:/var/lib/postgresql/data
      - ./init-age.sql:/docker-entrypoint-initdb.d/init-age.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medgraph"]
      interval: 5s
      timeout: 5s
      retries: 5

  pipeline:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - hf-models:/root/.cache/huggingface
      - ./pmc_xmls:/app/pmc_xmls
      - ./entities.db:/app/entities.db  # SQLite stays local
      - ./nodes.csv:/app/nodes.csv
      - ./edges.csv:/app/edges.csv
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=medgraph
      - POSTGRES_PASSWORD=medgraph
      - POSTGRES_DB=medical_literature
      - TOKENIZERS_PARALLELISM=false

volumes:
  pg-data:
  hf-models:
```

## AGE Initialization Script

`init-age.sql`:

```sql
-- Enable AGE extension
CREATE EXTENSION IF NOT EXISTS age;

-- Load AGE into search path
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- Create the graph
SELECT create_graph('medical_literature_graph');

-- Create indexes on commonly queried properties
-- (AGE stores graph data in ag_catalog tables)
```

## Updated requirements.txt

```txt
torch>=2.1.0
transformers>=4.36.0
pandas>=2.0.3
scikit-learn>=1.3.0
lxml>=4.9.3
psycopg2-binary>=2.9.9  # PostgreSQL driver
apache-age-python>=0.0.6  # AGE Python client
```

## Revised Pipeline Architecture

```python
# pmc_ner_pipeline.py
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import pandas as pd
from lxml import etree
from pathlib import Path
import sqlite3
from datetime import datetime
import psycopg2
import age

# ------------------------------
# Setup NER pipeline (unchanged)
# ------------------------------
model_name = "dmis-lab/biobert-base-cased-v1.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)
ner_pipeline = pipeline(
    "ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple"
)

# ------------------------------
# SQLite: Canonical Entity Store
# ------------------------------
sqlite_conn = sqlite3.connect("entities.db")
sqlite_conn.execute("PRAGMA foreign_keys = ON;")

# Existing entity tables (unchanged)
sqlite_conn.execute("""
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT UNIQUE,
    type TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
""")
sqlite_conn.execute("""
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    name TEXT UNIQUE,
    source TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
sqlite_conn.commit()

def get_or_create_entity(name, entity_type="GENERIC", source=None, confidence=None):
    """Returns canonical entity_id - stores in SQLite only"""
    cursor = sqlite_conn.execute("SELECT entity_id FROM aliases WHERE name=?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor = sqlite_conn.execute(
        "INSERT OR IGNORE INTO entities (canonical_name, type) VALUES (?, ?)",
        (name, entity_type)
    )
    entity_id = cursor.lastrowid
    if entity_id == 0:
        cursor = sqlite_conn.execute("SELECT id FROM entities WHERE canonical_name=?", (name,))
        entity_id = cursor.fetchone()[0]

    sqlite_conn.execute(
        "INSERT OR IGNORE INTO aliases (entity_id, name, source, confidence) VALUES (?, ?, ?, ?)",
        (entity_id, name, source, confidence)
    )
    sqlite_conn.commit()
    return entity_id

# ------------------------------
# PostgreSQL + AGE: Graph Store
# ------------------------------
import os

PG_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'user': os.getenv('POSTGRES_USER', 'medgraph'),
    'password': os.getenv('POSTGRES_PASSWORD', 'medgraph'),
    'database': os.getenv('POSTGRES_DB', 'medical_literature')
}

def get_pg_connection():
    conn = psycopg2.connect(**PG_CONFIG)
    return conn

def create_extraction_node(pg_conn, pmc_id, entity_id, entity_name, entity_type, confidence):
    """
    Create a node in the extraction layer of the graph.
    Links to canonical entity via entity_id.
    """
    with pg_conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM cypher('medical_literature_graph', $$
                CREATE (e:Extraction {
                    pmc_id: $pmc_id,
                    entity_id: $entity_id,
                    entity_name: $entity_name,
                    entity_type: $entity_type,
                    confidence: $confidence,
                    extracted_at: timestamp()
                })
                RETURN e
            $$) as (extraction agtype);
        """, {
            'pmc_id': pmc_id,
            'entity_id': entity_id,
            'entity_name': entity_name,
            'entity_type': entity_type,
            'confidence': confidence
        })
        pg_conn.commit()

def create_cooccurrence_edge(pg_conn, pmc_id, entity_id_1, entity_id_2):
    """
    Create a co-occurrence edge in the extraction layer.
    """
    with pg_conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM cypher('medical_literature_graph', $$
                MATCH (e1:Extraction {pmc_id: $pmc_id, entity_id: $entity_id_1})
                MATCH (e2:Extraction {pmc_id: $pmc_id, entity_id: $entity_id_2})
                MERGE (e1)-[r:CO_OCCURS_WITH {pmc_id: $pmc_id}]->(e2)
                RETURN r
            $$) as (edge agtype);
        """, {
            'pmc_id': pmc_id,
            'entity_id_1': entity_id_1,
            'entity_id_2': entity_id_2
        })
        pg_conn.commit()

# ------------------------------
# Process PMC XMLs
# ------------------------------
input_dir = Path("./pmc_xmls")
pg_conn = get_pg_connection()

for xml_file in input_dir.glob("PMC*.xml"):
    pmc_id = xml_file.stem
    tree = etree.parse(str(xml_file))
    root = tree.getroot()

    # Extract text
    text_chunks = [p.text for p in root.findall(".//abstract//p") if p.text]
    if not text_chunks:
        text_chunks = [p.text for p in root.findall(".//body//p") if p.text]
    if not text_chunks:
        continue
    full_text = " ".join(text_chunks)

    # Run NER
    entities = ner_pipeline(full_text)
    entity_ids_in_paper = []

    for ent in entities:
        name = ent["word"]
        label = ent.get("entity_group", "GENERIC")
        confidence = ent.get("score", None)

        # Step 1: Get canonical entity_id from SQLite
        entity_id = get_or_create_entity(
            name=name,
            entity_type=label,
            source=pmc_id,
            confidence=confidence
        )

        # Step 2: Create extraction node in graph (PostgreSQL+AGE)
        create_extraction_node(
            pg_conn, pmc_id, entity_id, name, label, confidence
        )

        entity_ids_in_paper.append(entity_id)

    # Step 3: Create co-occurrence edges in graph
    for i in range(len(entity_ids_in_paper)):
        for j in range(i + 1, len(entity_ids_in_paper)):
            create_cooccurrence_edge(
                pg_conn,
                pmc_id,
                entity_ids_in_paper[i],
                entity_ids_in_paper[j]
            )

    print(f"Processed {pmc_id}: {len(entity_ids_in_paper)} entities")

pg_conn.close()
sqlite_conn.close()

print(f"Processed {len(list(input_dir.glob('PMC*.xml')))} XML files.")
```

## Key Design Patterns

### 1. Entity Resolution Workflow
```
Extract "HTLV-III" → SQLite lookup → Get entity_id=42 
                                   ↓
                   Create Extraction node with entity_id=42 in AGE
```

### 2. Layer Separation in the Graph
```cypher
// Extraction layer - what BioBERT said
(:Extraction {pmc_id, entity_id, confidence})

// Claim layer - what paper asserts (add later)
(:Claim {pmc_id, subject_id, predicate, object_id})

// Evidence layer - what supports claims (add later)
(:Evidence {claim_id, type, strength})
```

### 3. Querying Across Both Stores

```python
# Get canonical name from SQLite
cursor = sqlite_conn.execute(
    "SELECT canonical_name FROM entities WHERE id=?", (entity_id,)
)
canonical_name = cursor.fetchone()[0]

# Query graph in AGE
with pg_conn.cursor() as cursor:
    cursor.execute("""
        SELECT * FROM cypher('medical_literature_graph', $$
            MATCH (e:Extraction {entity_id: $entity_id})
            RETURN e.pmc_id, e.confidence
        $$) as (pmc_id agtype, confidence agtype);
    """, {'entity_id': entity_id})
```

## Testing the Layer Boundary

```python
def test_extraction_layer_uses_canonical_ids():
    """Extraction nodes must reference canonical entity IDs from SQLite."""
    # Get an extraction node
    with pg_conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM cypher('medical_literature_graph', $$
                MATCH (e:Extraction)
                RETURN e.entity_id
                LIMIT 1
            $$) as (entity_id agtype);
        """)
        entity_id = cursor.fetchone()[0]
    
    # Verify it exists in SQLite
    cursor = sqlite_conn.execute(
        "SELECT id FROM entities WHERE id=?", (entity_id,)
    )
    assert cursor.fetchone() is not None, \
        "Extraction references non-existent canonical entity"
```

## Next Steps

1. **Get it running**: Use docker-compose to stand up both databases
2. **Add claim extraction**: Later, add logic to create `:Claim` nodes
3. **Add evidence layer**: Create `:Evidence` nodes that link to claims

Want me to help you:
- Debug the AGE connection?
- Write the claim extraction logic?
- Design the Cypher queries for multi-hop traversal?

This architecture gives you the best of both worlds: fast local entity resolution + powerful graph queries.
