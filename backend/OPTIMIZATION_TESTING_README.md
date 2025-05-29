# Optimization Testing & Monitoring Tools

This directory contains powerful tools for testing, validating, and monitoring the optimization system performance across different lab report formats.

## Tools Overview

### 🧪 `lab_optimization_tester.py`
Comprehensive testing tool for validating chunking strategies, accuracy metrics, and token optimization across different lab report formats.

### 📊 `optimization_monitor.py`
Real-time monitoring tool for tracking optimization system performance, accuracy, cost savings, and system health.

## Features

### Lab Optimization Tester
- **Multi-Mode Testing**: Test legacy, accuracy, and balanced optimization modes
- **Real PDF Processing**: Process actual lab reports with full optimization pipeline
- **Performance Benchmarking**: Compare optimization across multiple lab formats
- **Detailed Metrics**: Token reduction, accuracy, processing time, and biomarker extraction
- **Comparative Analysis**: Automatic comparison between different optimization modes

### Optimization Monitor  
- **Real-Time Monitoring**: Continuous tracking of optimization performance
- **Historical Analysis**: Analyze trends and patterns over time
- **Health Checks**: System health monitoring and alerts
- **Performance Alerts**: Automatic detection of performance degradation
- **Cost Analysis**: Track cost savings and efficiency metrics

## Quick Start

### Test a Single PDF
```bash
# Test all optimization modes on a PDF
python lab_optimization_tester.py --pdf path/to/lab_report.pdf

# Test only balanced mode
python lab_optimization_tester.py --pdf path/to/lab_report.pdf --mode balanced

# Test with debug logging
python lab_optimization_tester.py --pdf path/to/lab_report.pdf --debug
```

### Benchmark Multiple Lab Formats
```bash
# Benchmark all PDFs in sample_reports directory
python lab_optimization_tester.py --benchmark

# Benchmark with custom directory
python lab_optimization_tester.py --benchmark --sample-dir /path/to/lab_reports
```

### Monitor System Performance
```bash
# Quick system status check
python optimization_monitor.py

# Continuous monitoring (every 60 seconds)
python optimization_monitor.py --mode continuous

# Analyze last 7 days of optimization data
python optimization_monitor.py --analyze-logs --days 7
```

## Detailed Usage

### Lab Optimization Tester

#### Command Line Options
```
--pdf PATH              Path to PDF file to test
--mode MODE             Optimization mode: legacy, accuracy, balanced, all (default: all)
--benchmark             Run benchmark across multiple lab formats  
--sample-dir DIR        Directory containing sample lab reports (default: sample_reports)
--output FILE           Output file for results (default: auto-generated)
--debug                 Enable debug logging
```

#### Example Output
```
🧪 Starting optimization test for: sample_reports/quest_diagnostics.pdf
📊 Test mode: all

📄 Extracting text from PDF...
✅ Extracted text from 3 pages
📏 Total text length: 4,521 characters

🔬 Testing LEGACY mode...
📊 LEGACY Results:
   💰 Token reduction: 0.82%
   🎯 Biomarkers extracted: 8
   📈 Average confidence: 0.945
   ⏱️  Processing time: 12.3s

🔬 Testing ACCURACY mode...
📊 ACCURACY Results:
   💰 Token reduction: 0.82%
   🎯 Biomarkers extracted: 9
   📈 Average confidence: 0.962
   ⏱️  Processing time: 15.1s

🔬 Testing BALANCED mode...
📊 BALANCED Results:
   💰 Token reduction: 28.0%
   🎯 Biomarkers extracted: 8
   📈 Average confidence: 0.941
   ⏱️  Processing time: 11.7s

📋 Test Results Summary:
   LEGACY:
     💰 Token reduction: 0.82%
     🎯 Biomarkers: 8
     📈 Avg confidence: 0.945
   ACCURACY:
     💰 Token reduction: 0.82%
     🎯 Biomarkers: 9
     📈 Avg confidence: 0.962
   BALANCED:
     💰 Token reduction: 28.00%
     🎯 Biomarkers: 8
     📈 Avg confidence: 0.941

💾 Detailed results saved to: logs/lab_optimization_results_20250530_142315.json
```

#### Benchmark Output
```
🏆 Benchmark Results Summary:
   📊 Labs tested: 5
   ✅ Successful: 5
   ❌ Failed: 0
   💰 Avg token reduction: 24.1%
   🎯 Avg accuracy: 0.947

💾 Detailed results saved to: logs/lab_optimization_results_20250530_142845.json
```

### Optimization Monitor

#### Command Line Options
```
--mode MODE             Monitoring mode: continuous, batch, on-demand (default: on-demand)
--interval SECONDS      Monitoring interval for continuous mode (default: 60)
--analyze-logs          Analyze existing log files
--days DAYS             Number of days to analyze (default: 7)
--log-dir DIR           Directory containing log files (default: logs)
```

#### Example Output

**On-Demand Status:**
```
============================================================
🔍 OPTIMIZATION SYSTEM STATUS
============================================================

📊 Current Performance:
   BALANCED:
     💰 Token reduction: 28.0%
     🎯 Accuracy: 0.941
     ⏱️  Processing time: 11.7s

💻 System Resources:
     CPU: 23.4%
     Memory: 45.2%
     Disk: 67.8%

🏥 System Health: HEALTHY
     ✅ log_files: healthy
     ✅ optimization_system: healthy
     ✅ database: healthy
```

**Historical Analysis:**
```
📊 Historical Analysis (7 days):
   📋 Processed: 12 optimization runs
   💰 Avg token reduction: 25.3%
   🎯 Avg accuracy: 0.943
   ⏱️  Avg processing time: 13.2s

💡 Recommendations:
   • System is performing well within expected parameters
```

## Output Files

### Test Results JSON Structure
```json
{
  "pdf_path": "path/to/lab_report.pdf",
  "total_pages": 3,
  "original_text_length": 4521,
  "test_timestamp": "2025-05-30T14:23:15",
  "modes_tested": {
    "balanced": {
      "processing_time": 11.7,
      "chunks_created": 2,
      "token_metrics": {
        "original_tokens": 1250,
        "optimized_tokens": 900,
        "token_reduction_percent": 28.0,
        "tokens_saved": 350
      },
      "biomarker_metrics": {
        "biomarkers_extracted": 8,
        "average_confidence": 0.941,
        "high_confidence_count": 8,
        "api_calls_made": 2
      },
      "chunk_analysis": {
        "avg_chunk_tokens": 450,
        "chunk_sizes": [425, 475]
      }
    }
  },
  "comparison": {
    "best_token_reduction": {"mode": "balanced", "reduction": 28.0},
    "best_accuracy": {"mode": "accuracy", "confidence": 0.962},
    "fastest_processing": {"mode": "balanced", "time": 11.7},
    "most_biomarkers": {"mode": "accuracy", "count": 9}
  }
}
```

## Performance Thresholds

The monitoring system uses these default performance thresholds:

- **Minimum Token Reduction**: 15.0%
- **Minimum Accuracy**: 0.85 (85%)
- **Maximum Processing Time**: 300 seconds
- **Minimum Biomarker Count**: 5 per document

Alerts are generated when performance falls below these thresholds.

## Integration with Existing System

Both tools integrate seamlessly with the existing optimization system:

- **Environment Variables**: Automatically handles `ACCURACY_MODE` and `BALANCED_MODE` settings
- **Existing APIs**: Uses the same PDF processing and biomarker extraction pipeline
- **Database Integration**: Compatible with existing database models and schemas
- **Logging**: Integrates with existing logging infrastructure

## Sample Directory Structure

For benchmarking, organize your lab reports like this:
```
sample_reports/
├── quest_diagnostics.pdf
├── labcorp_report.pdf
├── hospital_lab.pdf
├── local_lab.pdf
└── international_lab.pdf
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the backend directory and the virtual environment is activated
2. **Missing PDFs**: Check that PDF paths are correct and files exist
3. **Permission Errors**: Ensure the scripts have execute permissions (`chmod +x`)
4. **Memory Issues**: For large PDFs, monitor system memory usage

### Debug Mode

Enable debug mode for detailed logging:
```bash
python lab_optimization_tester.py --pdf path/to/report.pdf --debug
```

This provides detailed information about:
- Text extraction process
- Chunk creation and optimization
- Token counting and reduction calculations
- Biomarker extraction details
- API call logs

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Adaptive optimization based on historical performance
- **Web Interface**: Browser-based dashboard for monitoring and testing
- **Automated Alerts**: Email/Slack notifications for performance issues
- **A/B Testing**: Framework for testing new optimization strategies
- **Custom Metrics**: User-defined performance metrics and thresholds

### Contributing

When adding new optimization modes or features:
1. Update both testing and monitoring tools
2. Add appropriate test cases
3. Update performance thresholds if needed
4. Document new features in this README

## Support

For issues or questions about these tools:
1. Check the logs directory for detailed error information
2. Run in debug mode for additional context
3. Verify that all dependencies are installed
4. Ensure the virtual environment is activated

These tools are designed to be the primary way to validate and monitor optimization performance across different lab formats, ensuring the system maintains high accuracy while achieving significant cost savings. 