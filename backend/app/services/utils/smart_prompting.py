"""
Smart Prompt Engineering Module

This module implements advanced prompt engineering techniques for biomarker extraction:
- Dynamic prompt adaptation based on extraction context
- Template-based prompts for different document types
- Context-aware prompt optimization
- Progressive prompt refinement based on success patterns
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import json
import re
from enum import Enum
from dataclasses import dataclass


class DocumentType(Enum):
    """Supported document types for prompt specialization."""
    QUEST_DIAGNOSTICS = "quest_diagnostics"
    LABCORP = "labcorp"
    GENERIC_LAB = "generic_lab"
    HOSPITAL_REPORT = "hospital_report"
    UNKNOWN = "unknown"


class PromptStrategy(Enum):
    """Different prompting strategies based on context."""
    INITIAL_COMPREHENSIVE = "initial_comprehensive"  # First call, detailed instructions
    CONTINUATION_FOCUSED = "continuation_focused"   # Subsequent calls, focused on new items
    PATTERN_GUIDED = "pattern_guided"              # Based on successful patterns
    REFINEMENT_MODE = "refinement_mode"            # High precision mode for edge cases


@dataclass
class PromptTemplate:
    """Template for generating context-aware prompts."""
    strategy: PromptStrategy
    document_type: DocumentType
    base_template: str
    context_instructions: str
    examples: Optional[List[str]] = None
    token_optimization_level: int = 1  # 1=low, 2=medium, 3=high


class SmartPromptEngine:
    """Advanced prompt engineering engine for biomarker extraction."""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.success_patterns = {}  # Track successful extraction patterns
        self.failure_patterns = {}  # Track failed patterns for avoidance
        
    def _initialize_templates(self) -> Dict[Tuple[PromptStrategy, DocumentType], PromptTemplate]:
        """Initialize prompt templates for different strategies and document types."""
        templates = {}
        
        # Initial Comprehensive Templates
        templates[(PromptStrategy.INITIAL_COMPREHENSIVE, DocumentType.QUEST_DIAGNOSTICS)] = PromptTemplate(
            strategy=PromptStrategy.INITIAL_COMPREHENSIVE,
            document_type=DocumentType.QUEST_DIAGNOSTICS,
            base_template="""Extract biomarkers from this Quest Diagnostics lab report page {page_num}.

QUEST DIAGNOSTICS SPECIFIC INSTRUCTIONS:
- Look for test names in the leftmost column
- Values are typically in the middle columns
- Reference ranges are in the rightmost column
- Flag indicators (H/L/A) appear next to values
- Units are typically after the value or in a separate column

{context_instructions}

EXTRACTION FORMAT:
Return a JSON list of biomarker objects with these fields:
- name: Test/biomarker name (exact as shown)
- value: Numeric value only
- unit: Measurement unit (mg/dL, ng/mL, etc.)
- reference_range: Normal range if available
- flag: H (high), L (low), A (abnormal), or null
- confidence: Your confidence in this extraction (0.0-1.0)

{specific_instructions}

TEXT FROM PAGE {page_num}:
{chunk_text}""",
            context_instructions="Look for table structures with clear columns for test names, values, and reference ranges.",
            examples=["Glucose: 95 mg/dL (70-99)", "Cholesterol, Total: 180 mg/dL (< 200)"]
        )
        
        templates[(PromptStrategy.INITIAL_COMPREHENSIVE, DocumentType.LABCORP)] = PromptTemplate(
            strategy=PromptStrategy.INITIAL_COMPREHENSIVE,
            document_type=DocumentType.LABCORP,
            base_template="""Extract biomarkers from this LabCorp report page {page_num}.

LABCORP SPECIFIC INSTRUCTIONS:
- Test names may be bold or separated by spacing
- Values often follow test names on the same line
- Reference ranges appear in parentheses or after "Ref:"
- Status indicators may be asterisks (*) or text flags

{context_instructions}

EXTRACTION FORMAT:
Return a JSON list of biomarker objects with these fields:
- name: Test/biomarker name
- value: Numeric value only  
- unit: Measurement unit
- reference_range: Normal range if available
- flag: Status indicator if present
- confidence: Your confidence (0.0-1.0)

{specific_instructions}

TEXT FROM PAGE {page_num}:
{chunk_text}""",
            context_instructions="Focus on clear test-value pairs and parenthetical reference ranges.",
            examples=["TSH: 2.1 mIU/L (0.4-4.0)", "Hemoglobin A1c: 5.6% (<5.7)"]
        )
        
        templates[(PromptStrategy.INITIAL_COMPREHENSIVE, DocumentType.GENERIC_LAB)] = PromptTemplate(
            strategy=PromptStrategy.INITIAL_COMPREHENSIVE,
            document_type=DocumentType.GENERIC_LAB,
            base_template="""Extract biomarkers from this medical lab report page {page_num}.

{context_instructions}

For each biomarker, return:
- name: Official biomarker name
- value: Measured numeric value 
- unit: Unit of measurement
- reference_range: Normal range (if provided)
- flag: "normal", "high", "low", or null
- confidence: NUMERIC confidence score 0.0-1.0 (NOT text like "high")

Return JSON array format only:
{{"biomarkers": [{{"name": "example", "value": 100, "unit": "mg/dL", "reference_range": "70-100", "flag": "normal", "confidence": 0.95}}]}}

PAGE {page_num}:
{chunk_text}""",
            context_instructions="Extract all biomarkers with high accuracy.",
            token_optimization_level=1
        )
        
        # Continuation Focused Templates (optimized for token efficiency)
        templates[(PromptStrategy.CONTINUATION_FOCUSED, DocumentType.QUEST_DIAGNOSTICS)] = PromptTemplate(
            strategy=PromptStrategy.CONTINUATION_FOCUSED,
            document_type=DocumentType.QUEST_DIAGNOSTICS,
            base_template="""Continue extracting NEW biomarkers from Quest page {page_num}.

{context_instructions}
{known_biomarker_context}

Extract only NEW biomarkers not in the above list. Use the same JSON format.

PAGE {page_num} TEXT:
{chunk_text}""",
            context_instructions="Focus on Quest table format: test name | value | unit | range | flag.",
            token_optimization_level=3
        )
        
        templates[(PromptStrategy.CONTINUATION_FOCUSED, DocumentType.GENERIC_LAB)] = PromptTemplate(
            strategy=PromptStrategy.CONTINUATION_FOCUSED,
            document_type=DocumentType.GENERIC_LAB,
            base_template="""Continue extracting NEW biomarkers from page {page_num}. Avoid duplicates.

{known_biomarker_context}

{context_instructions}

Find NEW biomarkers only. Return JSON with:
- name, value, unit, reference_range, flag
- confidence: NUMERIC 0.0-1.0 (NOT "high", "medium", etc.)

Format: {{"biomarkers": [...]}}

PAGE {page_num}:
{chunk_text}""",
            context_instructions="Continue with established patterns.",
            token_optimization_level=3
        )
        
        # Pattern Guided Templates (use successful patterns)
        templates[(PromptStrategy.PATTERN_GUIDED, DocumentType.QUEST_DIAGNOSTICS)] = PromptTemplate(
            strategy=PromptStrategy.PATTERN_GUIDED,
            document_type=DocumentType.QUEST_DIAGNOSTICS,
            base_template="""Extract biomarkers from Quest page {page_num} using these successful patterns:

{successful_patterns}

{context_instructions}

Use identical extraction approach. JSON format: name, value, unit, reference_range, flag, confidence.

PAGE {page_num}:
{chunk_text}""",
            context_instructions="Apply proven patterns from previous successful extractions.",
            token_optimization_level=2
        )
        
        return templates
    
    def create_adaptive_prompt(
        self,
        chunk_text: str,
        page_num: int,
        extraction_context: Dict[str, Any],
        document_type: Optional[str] = None,
        optimization_level: int = 1
    ) -> str:
        """
        Create an adaptive prompt based on extraction context and document type.
        
        Args:
            chunk_text: Text content to extract from
            page_num: Page number of the chunk
            extraction_context: Current extraction context with call history
            document_type: Detected document type (e.g., "quest_diagnostics")
            optimization_level: Token optimization level (1=low, 2=medium, 3=high)
            
        Returns:
            Optimized prompt string for Claude API
        """
        # Determine document type
        doc_type = self._map_document_type(document_type)
        
        # Determine strategy based on context
        strategy = self._determine_strategy(extraction_context, optimization_level)
        
        # Get appropriate template
        template = self._get_template(strategy, doc_type)
        
        # Build context-specific instructions
        context_instructions = self._build_context_instructions(
            extraction_context, strategy, optimization_level
        )
        
        # Build specific instructions based on known patterns
        specific_instructions = self._build_specific_instructions(
            extraction_context, strategy, doc_type
        )
        
        # Generate the final prompt
        prompt = template.base_template.format(
            page_num=page_num,
            chunk_text=chunk_text,
            context_instructions=context_instructions,
            specific_instructions=specific_instructions,
            known_biomarker_context=self._build_known_biomarker_context(
                extraction_context, optimization_level
            ),
            successful_patterns=self._build_successful_patterns_context(
                extraction_context, doc_type
            )
        )
        
        return prompt
    
    def _map_document_type(self, document_type: Optional[str]) -> DocumentType:
        """Map string document type to enum."""
        if not document_type:
            return DocumentType.UNKNOWN
        
        type_mapping = {
            "quest_diagnostics": DocumentType.QUEST_DIAGNOSTICS,
            "labcorp": DocumentType.LABCORP,
            "generic_lab": DocumentType.GENERIC_LAB,
            "hospital_report": DocumentType.HOSPITAL_REPORT
        }
        
        return type_mapping.get(document_type.lower(), DocumentType.GENERIC_LAB)
    
    def _determine_strategy(
        self, 
        extraction_context: Dict[str, Any], 
        optimization_level: int
    ) -> PromptStrategy:
        """Determine the best prompting strategy based on context."""
        call_count = extraction_context.get("call_count", 0)
        known_biomarkers_count = len(extraction_context.get("known_biomarkers", {}))
        
        # First call - use comprehensive approach
        if call_count == 0:
            return PromptStrategy.INITIAL_COMPREHENSIVE
        
        # If we have many successful patterns, use pattern-guided approach
        successful_patterns = extraction_context.get("extraction_patterns", [])
        if len(successful_patterns) >= 3 and optimization_level >= 2:
            return PromptStrategy.PATTERN_GUIDED
        
        # If we've found many biomarkers and want high optimization, use focused approach
        if known_biomarkers_count >= 5 and optimization_level >= 2:
            return PromptStrategy.CONTINUATION_FOCUSED
        
        # Default to continuation focused for subsequent calls
        return PromptStrategy.CONTINUATION_FOCUSED
    
    def _get_template(
        self, 
        strategy: PromptStrategy, 
        doc_type: DocumentType
    ) -> PromptTemplate:
        """Get the appropriate template for strategy and document type."""
        # Try exact match first
        if (strategy, doc_type) in self.templates:
            return self.templates[(strategy, doc_type)]
        
        # Fall back to generic template for the strategy
        generic_key = (strategy, DocumentType.GENERIC_LAB)
        if generic_key in self.templates:
            return self.templates[generic_key]
        
        # Final fallback to initial comprehensive generic
        fallback_key = (PromptStrategy.INITIAL_COMPREHENSIVE, DocumentType.GENERIC_LAB)
        return self.templates[fallback_key]
    
    def _build_context_instructions(
        self,
        extraction_context: Dict[str, Any],
        strategy: PromptStrategy,
        optimization_level: int
    ) -> str:
        """Build context-specific instructions based on previous extractions."""
        instructions = []
        
        # Add section context if available
        section_context = extraction_context.get("section_context", {})
        if section_context and optimization_level <= 2:
            context_info = []
            if "chunks_processed" in section_context:
                context_info.append(f"Processed {section_context['chunks_processed']} chunks")
            if "avg_biomarkers_per_chunk" in section_context:
                avg = section_context["avg_biomarkers_per_chunk"]
                context_info.append(f"avg {avg:.1f} biomarkers/chunk")
            
            if context_info:
                instructions.append(f"Context: {', '.join(context_info)}.")
        
        # Add pattern guidance for continuation strategies
        if strategy in [PromptStrategy.CONTINUATION_FOCUSED, PromptStrategy.PATTERN_GUIDED]:
            patterns = extraction_context.get("extraction_patterns", [])
            if patterns and optimization_level <= 2:
                recent_patterns = patterns[-2:]  # Use last 2 successful patterns
                instructions.append(f"Follow patterns like: {'; '.join(recent_patterns)}")
        
        return " ".join(instructions) if instructions else ""
    
    def _build_specific_instructions(
        self,
        extraction_context: Dict[str, Any],
        strategy: PromptStrategy,
        doc_type: DocumentType
    ) -> str:
        """Build specific instructions based on extraction history and document type."""
        instructions = []
        
        # Add document type specific guidance
        if doc_type == DocumentType.QUEST_DIAGNOSTICS:
            instructions.append("Quest format: focus on table columns with clear test|value|unit|range structure.")
        elif doc_type == DocumentType.LABCORP:
            instructions.append("LabCorp format: look for test-value pairs with parenthetical ranges.")
        
        # Add guidance based on token usage efficiency
        token_usage = extraction_context.get("token_usage", {})
        if token_usage:
            total_tokens = token_usage.get("input", 0) + token_usage.get("output", 0)
            biomarker_count = len(extraction_context.get("known_biomarkers", {}))
            
            if biomarker_count > 0:
                tokens_per_biomarker = total_tokens / biomarker_count
                if tokens_per_biomarker > 300:  # High token usage per biomarker
                    instructions.append("Be concise - focus only on clear, confident extractions.")
        
        return " ".join(instructions) if instructions else ""
    
    def _build_known_biomarker_context(
        self,
        extraction_context: Dict[str, Any],
        optimization_level: int
    ) -> str:
        """Build context about already known biomarkers."""
        known_biomarkers = extraction_context.get("known_biomarkers", {})
        
        if not known_biomarkers:
            return ""
        
        if optimization_level >= 3:  # High optimization - minimal context
            sample_names = list(known_biomarkers.keys())[:3]
            return f"Already extracted: {', '.join(sample_names)}. Skip these."
        
        elif optimization_level == 2:  # Medium optimization - moderate context
            biomarker_list = []
            for name, data in list(known_biomarkers.items())[:5]:
                value = data.get("value", "")
                unit = data.get("unit", "")
                biomarker_list.append(f"{name} ({value} {unit})")
            return f"Previously extracted: {', '.join(biomarker_list)}. Extract only NEW biomarkers."
        
        else:  # Low optimization - full context
            biomarker_details = []
            for name, data in list(known_biomarkers.items())[:8]:
                value = data.get("value", "")
                unit = data.get("unit", "")
                page = data.get("page", "")
                biomarker_details.append(f"{name}: {value} {unit} (page {page})")
            
            if biomarker_details:
                return f"Already extracted biomarkers:\n{chr(10).join(biomarker_details)}\n\nExtract only NEW biomarkers not in this list."
            
        return ""
    
    def _build_successful_patterns_context(
        self,
        extraction_context: Dict[str, Any],
        doc_type: DocumentType
    ) -> str:
        """Build context about successful extraction patterns."""
        patterns = extraction_context.get("extraction_patterns", [])
        
        if not patterns:
            return "No established patterns yet."
        
        # Use the most recent successful patterns
        recent_patterns = patterns[-3:] if len(patterns) >= 3 else patterns
        
        pattern_examples = []
        for pattern in recent_patterns:
            pattern_examples.append(f"✓ {pattern}")
        
        return "\n".join(pattern_examples)
    
    def update_patterns_from_results(
        self,
        extraction_context: Dict[str, Any],
        biomarkers: List[Dict[str, Any]],
        chunk_text: str,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Update success/failure patterns based on extraction results.
        
        Args:
            extraction_context: Current extraction context
            biomarkers: Extracted biomarkers
            chunk_text: Original chunk text
            success: Whether the extraction was successful
            
        Returns:
            Updated extraction context with pattern information
        """
        updated_context = extraction_context.copy()
        
        if success and biomarkers:
            # Record successful patterns
            for biomarker in biomarkers:
                if biomarker.get("confidence", 0) >= 0.8:  # Only high-confidence extractions
                    pattern = self._extract_pattern_from_biomarker(biomarker, chunk_text)
                    if pattern and pattern not in updated_context.get("extraction_patterns", []):
                        if "extraction_patterns" not in updated_context:
                            updated_context["extraction_patterns"] = []
                        updated_context["extraction_patterns"].append(pattern)
                        
                        # Keep only the most recent 10 patterns for efficiency
                        if len(updated_context["extraction_patterns"]) > 10:
                            updated_context["extraction_patterns"] = updated_context["extraction_patterns"][-10:]
        
        return updated_context
    
    def _extract_pattern_from_biomarker(
        self,
        biomarker: Dict[str, Any],
        chunk_text: str
    ) -> Optional[str]:
        """Extract the text pattern that led to successful biomarker extraction."""
        name = biomarker.get("name", "")
        value = biomarker.get("value", "")
        unit = biomarker.get("unit", "")
        
        if not all([name, value, unit]):
            return None
        
        # Try to find the pattern in the text
        # Look for various common patterns
        patterns_to_try = [
            rf"{re.escape(name)}\s*[:\-]\s*{re.escape(str(value))}\s*{re.escape(unit)}",
            rf"{re.escape(name)}\s+{re.escape(str(value))}\s*{re.escape(unit)}",
            rf"{re.escape(name)}.*?{re.escape(str(value))}\s*{re.escape(unit)}"
        ]
        
        for pattern in patterns_to_try:
            match = re.search(pattern, chunk_text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        # Fallback to simple pattern
        return f"{name}: {value} {unit}"


# Global instance for use across the application
smart_prompt_engine = SmartPromptEngine() 