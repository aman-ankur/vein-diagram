# Technical Specification: Integrated Document Structure Analysis & API Cost Optimization

## Overview

This specification outlines a comprehensive approach to improving biomarker extraction by combining document structure analysis with API cost optimization. The solution addresses two key challenges:

* Reducing false positive extractions by understanding document structure
* Minimizing Claude API costs while maintaining extraction accuracy

By integrating these objectives into a unified implementation, we can achieve better results with less disruption to the existing pipeline.

## Goals

* Reduce false positive biomarker extractions by 70%+ through structure awareness
* Decrease Claude API token usage by 40%+ through optimized requests
* Maintain or improve biomarker extraction accuracy
* Implement with minimal disruption to existing pipeline
* Allow for phased deployment of improvements

## Technical Design

### Core Architecture: Document Structure Pipeline

The solution introduces a new preprocessing stage that analyzes document structure before biomarker extraction, leveraging this structure to both improve accuracy and reduce API costs.

**New Module: `document_analyzer.py`**
backend/
  app/
    services/
      document_analyzer.py  # New integrated module

This module will contain all functionality for analyzing document structure and optimizing content for extraction.

### Key Components

**1. Structural Analysis Engine**

* **Purpose:** Analyze PDF structure to identify relevant content zones and ignore non-biomarker areas
* **Core Functions:**
    * Table Detection: Identify tabular regions likely to contain structured biomarker data
    * Zone Classification: Categorize page regions (header, footer, content, address blocks)
    * Document Type Recognition: Identify specific lab report formats
* **Integration Point:** Between text extraction and biomarker extraction

**2. Content Optimization Engine**

* **Purpose:** Prepare optimized text chunks for Claude API calls to reduce token usage
* **Core Functions:**
    * Biomarker Pattern Recognition: Identify text patterns that match biomarker data
    * Intelligent Chunking: Split content into optimal segments for API calls
    * Token Optimization: Reduce unnecessary content while preserving context
* **Integration Point:** Before each Claude API call

**3. Context Management System**

* **Purpose:** Maintain extraction context across API calls to reduce redundant instructions
* **Core Functions:**
    * Extraction State Tracking: Monitor already-extracted biomarkers and patterns
    * Adaptive Prompting: Generate optimized prompts based on extraction history
    * Confidence Scoring: Evaluate certainty of biomarker identification
* **Integration Point:** Throughout the extraction process

### Updated Extraction Pipeline

The revised pipeline integrates both structural analysis and cost optimization:

1.  Extract text from PDF (existing `extract_text_from_pdf`)
2.  **NEW:** Analyze document structure (tables, zones, document type)
3.  Extract metadata from initial pages (existing, but with structural context)
4.  **MODIFIED:** Filter relevant pages using structural information
5.  **NEW:** Generate optimized content chunks from relevant pages
6.  **MODIFIED:** Create adaptive prompts for Claude API calls
7.  **MODIFIED:** Extract biomarkers using optimized chunks and prompts
8.  Process and standardize biomarkers (existing)
9.  Store results (existing)

### Data Structures

**Document Structure Context**
```python
document_structure = {
    "document_type": str,                    # E.g., "quest_diagnostics", "labcorp"
    "page_zones": Dict[int, Dict[str, Any]], # Page number -> zone information
    "tables": Dict[int, List[Dict]],         # Page number -> list of tables
    "biomarker_regions": List[Dict],         # Identified biomarker-containing regions
    "confidence": float                      # Overall structure analysis confidence
}
```
### Extraction Context

```python

extraction_context = {
    "known_biomarkers": Dict[str, Dict],     # Biomarkers already identified
    "extraction_patterns": List[str],        # Successful extraction patterns
    "section_context": Dict[str, str],       # Current section information
    "call_count": int,                       # Number of API calls made
    "token_usage": Dict[str, int],           # Tracking token consumption
    "confidence_threshold": float            # Adaptive confidence threshold
}
```

### Content Chunk
```python

content_chunk = {
    "text": str,                             # Optimized text for extraction
    "page_num": int,                         # Source page number
    "region_type": str,                      # E.g., "table", "list", "text"
    "estimated_tokens": int,                 # Estimated token count
    "biomarker_confidence": float,           # Confidence of containing biomarkers
    "context": str                           # Surrounding context information
}
```
###  Design Approaches 

**Approach : Integrated Analysis First Approach (Selected)**
Combine structural analysis and chunk optimization in a single process

* **Pros:** Most efficient analysis, avoids redundant processing, single integration
* **Cons:** More complex initial development, requires careful testing

### Decision Rationale
This Approach  was selected because:

* Document structure naturally informs optimal chunking (tables make natural chunks)
* Single-pass analysis is more efficient (analyze structure once, use for multiple purposes)
* Common underlying logic for both problems (pattern recognition, content classification)
* Minimizes disruption to existing pipeline (single new preprocessing stage)

### 2. System Architecture Changes

#### 2.1 New Module: `document_analyzer.py`

**Purpose:** Central module for document structure analysis and content optimization  
**Location:** `backend/app/services/document_analyzer.py`

**Public Functions:**

```python
analyze_document_structure(pdf_path: str, pages_text_dict: Dict[int, str]) -> DocumentStructure
optimize_content_for_extraction(pages_text_dict: Dict[int, str], document_structure: DocumentStructure) -> List[ContentChunk]
create_adaptive_prompt(chunk: ContentChunk, extraction_context: ExtractionContext) -> str
update_extraction_context(extraction_context: ExtractionContext, chunk: ContentChunk, results: List[Dict]) -> ExtractionContext
```

**Type Definitions:**

- `DocumentStructure`: Class/TypedDict with document analysis results  
- `ContentChunk`: Class/TypedDict for optimized content segments  
- `ExtractionContext`: Class/TypedDict for extraction state management  

---

#### 2.2 Configuration Updates: `config.py`

**Location:** `backend/app/core/config.py`

**New Configuration Section:**

```python
DOCUMENT_ANALYZER_CONFIG = {
    "enabled": True,
    "structure_analysis": { "enabled": True, "fallback_to_legacy": True },
    "content_optimization": { "enabled": True, "token_reduction_target": 0.4 },
    "adaptive_context": { "enabled": True, "confidence_threshold": 0.7 }
}
```

---

#### 2.3 Dependency Additions: `requirements.txt`

**New Dependencies:**

- `pdfplumber>=0.7.0`: For table detection and layout analysis  
- `tiktoken>=0.3.0`: For consistent token counting (optional)  

---

### 3. Detailed API Changes

#### 3.1 Modified Functions: `pdf_service.py`

- **Function:** `process_pdf_background`  
  **Changes:** Add document structure analysis before page filtering  

- **Function:** `filter_relevant_pages`  
  **Signature Change:** Add `document_structure` parameter  
  **Changes:** Use structure information in relevance scoring  

- **Function:** `process_pages_sequentially`  
  **Signature Change:** Add `document_structure` parameter  
  **Changes:** Use optimized chunks instead of whole pages  

---

#### 3.2 Modified Functions: `biomarker_parser.py`

- **Function:** `extract_biomarkers_with_claude`  
  **Signature Change:** Add `extraction_context` parameter, return updated context  
  **Changes:** Use adaptive prompts based on context  

- **Function:** `_process_biomarker`  
  **Changes:** Add structure context for validation  


#### 4. Implementation Phases

#### Phase 1: Foundation (Week 1–2)

**Objective:** Basic document structure analysis with minimal pipeline changes

**Tasks:**

- Create `document_analyzer.py` with basic structure detection  
- Implement table detection using `pdfplumber`  
- Implement basic zone classification (header/footer/content)  
- Add configuration settings in `config.py`  
- Modify `filter_relevant_pages` to use structure information  
- Add feature toggle system  
- Create unit tests for structure detection  
- Document changes and update logging  

**Acceptance Criteria:**

- Structure detection works on 90% of test documents  
- Page filtering uses structural context when available  
- All tests pass  
- Feature can be toggled off without affecting existing flow  

---

#### Phase 2: Content Optimization (Week 3–4)

**Objective:** Optimize content chunks for Claude API calls

**Tasks:**

- Implement content chunking based on structure  
- Add token estimation functionality  
- Modify `process_pages_sequentially` to use chunks  
- Create unit tests for content optimization  
- Add metrics collection for token usage  
- Update logging for chunk processing  
- Implement parallel validation (compare with legacy method)  

**Acceptance Criteria:**

- Content chunking reduces token usage by 30%+  
- No reduction in extraction accuracy  
- All tests pass  
- Performance impact less than 10%  

---

#### Phase 3: Adaptive Context (Week 5–6)

**Objective:** Context-aware extraction across API calls

**Tasks:**

- Implement extraction context management  
- Create adaptive prompt templates  
- Modify `extract_biomarkers_with_claude` to use adaptive prompts  
- Add logic to update context between calls  
- Implement confidence-based validation  
- Create unit tests for context management  
- Update metrics collection for context benefits  

**Acceptance Criteria:**

- Additional 10%+ reduction in token usage  
- Equal or better extraction accuracy  
- All tests pass  
- Context management works across document sections  

---

#### Phase 4: Integration & Validation (Week 7–8)

**Objective:** Complete integration and comprehensive testing

**Tasks:**

- Finalize integration of all components  
- Optimize performance of combined system  
- Create comprehensive test suite  
- Implement A/B testing capability  
- Add detailed performance and accuracy metrics  
- Update documentation  
- Create deployment plan  

**Acceptance Criteria:**

- 40%+ reduction in token usage  
- 70%+ reduction in false positives  
- No more than 2% reduction in true positives  
- All tests pass with 90%+ coverage  
- System can be deployed with minimal disruption  

---

### 5. Module Specifications

#### 5.1 Document Structure Analysis

**Function:** `analyze_document_structure`

**Input:** PDF path, extracted text dictionary

**Operations:**

- Detect tables using `pdfplumber`  
- Identify page zones (header, footer, content)  
- Classify document type using pattern matching  
- Generate confidence scores for analysis  

**Output:** `DocumentStructure` object

**Validation Requirements:**

- Accurately identifies tables in 90%+ of test documents  
- Correctly classifies header/footer zones in 85%+ of cases  
- Handles multi-column layouts  
- Degrades gracefully when structure is unclear  

---

#### 5.2 Content Optimization

**Function:** `optimize_content_for_extraction`

**Input:** Pages text dictionary, document structure

**Operations:**

- Identify biomarker-containing sections  
- Split content into optimal chunks  
- Estimate token count for each chunk  
- Preserve necessary context for extraction  

**Output:** List of `ContentChunk` objects

**Validation Requirements:**

- Reduces total token usage by 30%+  
- Preserves all biomarker data and context  
- Creates chunks that fit within token limits  
- Handles table rows appropriately (doesn't split rows)  

---

#### 5.3 Adaptive Prompting

**Function:** `create_adaptive_prompt`

**Input:** Content chunk, extraction context

**Operations:**

- Select appropriate prompt template based on context  
- Insert chunk-specific instructions  
- Include relevant extraction history  
- Optimize prompt for token efficiency  

**Output:** Optimized prompt string

**Validation Requirements:**

- Reduces instruction tokens by 20%+ after first call  
- Maintains or improves extraction accuracy  
- Adapts appropriately to document type  
- Handles edge cases gracefully  

---

#### 5.4 Context Management

**Function:** `update_extraction_context`

**Input:** Current extraction context, content chunk, extraction results

**Operations:**

- Update known biomarkers list  
- Track successful extraction patterns  
- Update confidence thresholds  
- Track token usage  

**Output:** Updated extraction context

**Validation Requirements:**

- Correctly maintains state across multiple API calls  
- Prevents duplicate extraction efforts  
- Enables progressive optimization  
- Handles extraction failures appropriately  

### 6. Testing Requirements

---

#### 6.1 Unit Tests

| Module              | Test Cases                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Structure Analysis**   | Table detection, zone classification, document type identification, edge cases |
| **Content Optimization** | Chunk creation, token estimation, context preservation, boundary conditions     |
| **Adaptive Prompting**   | Template selection, context integration, token efficiency, prompt correctness    |
| **Context Management**   | State updates, pattern learning, recovery from failures                        |

---

#### 6.2 Integration Tests

| Feature           | Test Cases                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **Combined Pipeline** | End-to-end workflow, feature toggle behavior, fallback mechanisms            |
| **Performance**        | Token usage measurement, processing time, memory usage                      |
| **Accuracy**           | False positive rate, true positive rate, F1 score compared to baseline       |

---

#### 6.3 Test Documents

Create comprehensive test set covering:

- Different lab formats (Quest, LabCorp, etc.)  
- Complex layouts (multi-column, dense tables)  
- Edge cases (handwritten notes, stamps, watermarks)  
- Mixed content (graphs, charts, explanatory text)  


# Integration Strategy

To minimize disruption to the existing pipeline:

* **Wrap-Around Integration:** Integrate new functionality as wrappers around existing functions
* **Feature Toggles:** Add configuration settings to enable/disable new features
* **Parallel Processing:** Run new and old paths simultaneously for validation
* **Incremental Deployment:** Replace components progressively as they're validated

Example feature toggle configuration:

```python
DOCUMENT_ANALYZER_CONFIG = {
    "enabled": True,               # Master toggle for all features
    "structure_analysis": {
        "enabled": True,           # Enable structure analysis
        "fallback_to_legacy": True # Fall back to old method if analysis fails
    },
    "content_optimization": {
        "enabled": True,           # Enable content optimization
        "token_reduction_target": 0.4 # Target 40% token reduction
    },
    "adaptive_context": {
        "enabled": True,           # Enable adaptive context
        "confidence_threshold": 0.7 # Minimum confidence to use adaptive prompts
    }
}
```