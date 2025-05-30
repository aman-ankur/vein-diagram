# 🧪 PDF Biomarker Extraction Testing Guide

This guide explains how to use the comprehensive PDF testing script to evaluate biomarker extraction performance with detailed analytics.

## 🚀 Quick Start

### Prerequisites

1. **Virtual Environment**: Always activate the virtual environment first:
   ```bash
   source vein-d/bin/activate
   ```

2. **Environment Variables**: Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your_api_key_here"
   ```

### Basic Usage

```bash
# Test a single PDF
python test_real_pdf_extraction.py path/to/your/lab_report.pdf

# Specify custom output directory
python test_real_pdf_extraction.py path/to/your/lab_report.pdf --output-dir my_test_results
```

## 📊 What the Script Tests

The script runs the **complete biomarker extraction pipeline** including:

### Phase 1: Smart Chunk Skipping ✅
- **Purpose**: Skip chunks with minimal biomarker potential
- **Metrics Tracked**:
  - Total chunks created vs processed
  - Chunks skipped and reasons why
  - Tokens saved through skipping
  - Skip rate efficiency

### Phase 2: Biomarker Caching ✅  
- **Purpose**: Use cache for common biomarkers (no LLM calls needed)
- **Metrics Tracked**:
  - Cache hits vs misses
  - Biomarkers found via cache vs LLM
  - LLM calls saved
  - Cache learning updates

### Core Pipeline
- **Document Structure Analysis**: Table detection, page zones
- **Page Filtering**: Relevance scoring and filtering
- **Token Optimization**: Content chunking and optimization
- **Biomarker Extraction**: LLM-based extraction with confidence scoring

## 📈 Generated Reports

The script generates **5 comprehensive reports**:

### 1. 📝 Summary Report (`*_summary.txt`)
```
================================================================================
BIOMARKER EXTRACTION TEST REPORT
Run ID: lab_report_20241201_143052
PDF: lab_report
Timestamp: 2024-12-01T14:30:52
================================================================================

📋 PDF INFORMATION
----------------------------------------
File Size: 2.34 MB
Total Pages: 8
Relevant Pages: 3
Pages Filtered Out: 5
Filter Efficiency: 62.5%

🧬 EXTRACTION RESULTS
----------------------------------------
Total Biomarkers Extracted: 15
Pages Processed: 3
Average Confidence: 0.923
High Confidence (≥0.8): 14/15

📊 PERFORMANCE METRICS
----------------------------------------
Original Tokens: 12,450
Optimized Tokens: 8,920
Token Reduction: 28.4%
Estimated Cost Savings: $0.028
API Calls Made: 4
Total Tokens Used: 8,920
Average Tokens per Call: 2,230.0

⏭️ SMART CHUNK SKIPPING
----------------------------------------
Total Chunks: 12
Chunks Skipped: 7
Chunks Processed: 5
Tokens Saved: 3,200
Skip Rate: 58.3%

🧠 BIOMARKER CACHE PERFORMANCE
----------------------------------------
Cache Hits: 8
Cache Misses: 4
Cache Hit Rate: 66.7%
LLM Calls Saved: 8
New Cache Hits: 3
```

### 2. 🔬 Biomarkers Table (`*_biomarkers_table.html`)
Interactive HTML table with:
- **Color-coded confidence levels** (high/medium/low)
- **Abnormal values highlighted**
- **Complete biomarker details**: name, value, unit, reference range
- **Extraction method**: cache vs LLM
- **Page source information**

### 3. 📈 Performance Dashboard (`*_performance_dashboard.html`)
Visual dashboard with:
- **Key metrics cards** (biomarkers, token reduction, cost savings)
- **Page processing statistics**
- **Smart skipping performance**
- **Cache performance details**

### 4. 💾 Complete Results JSON (`*_complete_results.json`)
Full machine-readable results including:
- All raw data and metrics
- Individual biomarker details
- Processing timestamps
- Configuration settings used

### 5. 🔍 Detailed Metrics Report (`*_detailed_metrics.json`)
Comprehensive technical metrics:
- Token usage per API call
- Chunk-by-chunk processing details
- Optimization performance data
- Cache interaction logs

## 🎯 Key Metrics Explained

### Token Efficiency
- **Original Tokens**: Raw text token count
- **Optimized Tokens**: After smart chunking and skipping
- **Token Reduction %**: Percentage saved through optimization
- **Cost Savings**: Estimated $ saved on API calls

### Cache Performance
- **Cache Hit Rate**: % of biomarkers found without LLM calls
- **LLM Calls Saved**: Number of API calls avoided
- **Cache Learning**: New patterns learned from LLM results

### Smart Skipping
- **Skip Rate**: % of chunks skipped
- **Tokens Saved**: API tokens not used due to skipping
- **Biomarker Safety**: Ensures no biomarkers missed

### Extraction Quality
- **Average Confidence**: Overall extraction confidence
- **High Confidence Rate**: % of biomarkers with confidence ≥ 0.8
- **Abnormal Detection**: Properly flagged abnormal values

## 🔧 Advanced Usage

### Test Multiple PDFs
```bash
# Test all PDFs in a directory
for pdf in lab_reports/*.pdf; do
    python test_real_pdf_extraction.py "$pdf" --output-dir "batch_results/$(basename "$pdf" .pdf)"
done
```

### Compare Configurations
```bash
# Test with different optimization levels
BALANCED_MODE=true python test_real_pdf_extraction.py sample.pdf --output-dir balanced_test
ACCURACY_MODE=true python test_real_pdf_extraction.py sample.pdf --output-dir accuracy_test
```

### Debug Mode
```bash
# Enable extra debug logging
DEBUG_TOKEN_METRICS=1 python test_real_pdf_extraction.py sample.pdf
```

## 📁 Output Structure

```
extraction_results/
├── lab_report_20241201_143052_summary.txt              # Human-readable summary
├── lab_report_20241201_143052_biomarkers_table.html    # Interactive biomarkers table
├── lab_report_20241201_143052_performance_dashboard.html # Visual dashboard
├── lab_report_20241201_143052_complete_results.json    # Complete raw data
├── lab_report_20241201_143052_detailed_metrics.json    # Technical metrics
└── lab_report_20241201_143052_extraction.log           # Detailed processing log
```

## 🎉 Success Indicators

### Excellent Performance
- ✅ **Token Reduction**: 25-40%
- ✅ **Cache Hit Rate**: >60%
- ✅ **Average Confidence**: >0.9
- ✅ **High Confidence Rate**: >90%

### Good Performance  
- ✅ **Token Reduction**: 15-25%
- ✅ **Cache Hit Rate**: >40%
- ✅ **Average Confidence**: >0.8
- ✅ **High Confidence Rate**: >80%

### Needs Investigation
- ⚠️ **Token Reduction**: <15%
- ⚠️ **Cache Hit Rate**: <30%
- ⚠️ **Average Confidence**: <0.7
- ⚠️ **High Confidence Rate**: <70%

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the backend directory
   cd backend
   source vein-d/bin/activate
   ```

2. **Missing API Key**
   ```bash
   export ANTHROPIC_API_KEY="your_key_here"
   ```

3. **Permission Errors**
   ```bash
   chmod +x test_real_pdf_extraction.py
   ```

4. **PDF Not Found**
   ```bash
   # Use absolute path
   python test_real_pdf_extraction.py /full/path/to/your.pdf
   ```

### Debug Tips

1. **Check logs**: Always review the `*_extraction.log` file for detailed processing information

2. **Validate results**: Open the HTML reports in your browser for visual validation

3. **Compare baselines**: Run the same PDF multiple times to ensure consistent results

4. **Monitor cache**: Check if cache is learning and improving over time

## 📋 Test Checklist

Before running production tests:

- [ ] Virtual environment activated (`source vein-d/bin/activate`)
- [ ] API key configured (`echo $ANTHROPIC_API_KEY`)
- [ ] PDF file exists and is readable
- [ ] Output directory has write permissions
- [ ] Test with a small PDF first
- [ ] Review generated reports for sanity

## 🎯 Interpreting Results

### What to Look For

1. **Token Optimization**: Are we achieving 20%+ reduction?
2. **Cache Effectiveness**: Is cache hit rate improving with more tests?
3. **Extraction Quality**: Are confidence scores consistently high?
4. **Processing Speed**: Are optimizations actually faster?
5. **Biomarker Accuracy**: Do extracted values match visual inspection?

### Red Flags

- ❌ **Zero cache hits**: Cache may not be working
- ❌ **Low confidence scores**: Extraction quality issues
- ❌ **High skip rates with missed biomarkers**: Skipping too aggressively
- ❌ **No token reduction**: Optimization not working

This testing framework provides comprehensive validation of all the extraction improvements from `extraction_v2.md` and ensures production readiness! 🚀 