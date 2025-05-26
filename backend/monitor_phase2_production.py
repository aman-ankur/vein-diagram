#!/usr/bin/env python3
"""
Phase 2 Production Monitoring Script

This script monitors Phase 2 implementation in production by:
1. Checking logs for Phase 2 activity
2. Analyzing token optimization metrics
3. Tracking biomarker extraction improvements
4. Monitoring chunk-based processing
"""

import os
import sys
import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import glob

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def setup_logging():
    """Setup logging for the monitoring script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('phase2_monitoring.log')
        ]
    )
    return logging.getLogger(__name__)

def check_phase2_configuration():
    """Check if Phase 2 is properly configured"""
    try:
        from app.core.config import DOCUMENT_ANALYZER_CONFIG
        
        config_status = {
            "master_enabled": DOCUMENT_ANALYZER_CONFIG.get("enabled", False),
            "content_optimization_enabled": DOCUMENT_ANALYZER_CONFIG.get("content_optimization", {}).get("enabled", False),
            "token_reduction_target": DOCUMENT_ANALYZER_CONFIG.get("content_optimization", {}).get("token_reduction_target", 0),
            "adaptive_context_enabled": DOCUMENT_ANALYZER_CONFIG.get("adaptive_context", {}).get("enabled", False)
        }
        
        return config_status
    except Exception as e:
        return {"error": str(e)}

def analyze_recent_logs(hours_back: int = 24) -> Dict[str, Any]:
    """Analyze recent logs for Phase 2 activity"""
    logger = logging.getLogger(__name__)
    
    # Look for log files in the logs directory
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        logger.warning(f"Log directory not found: {log_dir}")
        return {"error": "Log directory not found"}
    
    # Get recent log files
    log_files = glob.glob(os.path.join(log_dir, "*.log"))
    
    # Also check for application logs (common locations)
    app_log_locations = [
        "/var/log/app.log",
        "/var/log/biomarker_extraction.log",
        "app.log",
        "biomarker_extraction.log"
    ]
    
    for log_path in app_log_locations:
        if os.path.exists(log_path):
            log_files.append(log_path)
    
    if not log_files:
        logger.warning("No log files found")
        return {"error": "No log files found"}
    
    # Analyze logs for Phase 2 indicators
    phase2_indicators = {
        "content_optimization_used": 0,
        "chunk_based_processing": 0,
        "token_optimization_events": 0,
        "biomarker_extractions": 0,
        "optimization_metrics": [],
        "errors": [],
        "total_documents_processed": 0
    }
    
    # Key log patterns to look for
    patterns = {
        "content_optimization": r"Using enhanced content optimization",
        "chunk_processing": r"Created (\d+) optimized chunks",
        "token_reduction": r"Token optimization: (\d+) -> (\d+) \(([0-9.]+)% reduction\)",
        "biomarker_extraction": r"Extracted (\d+) biomarkers",
        "optimization_metrics": r"OPTIMIZATION METRICS SUMMARY",
        "document_processing": r"Processing document|Starting biomarker extraction",
        "phase2_errors": r"ERROR.*(?:optimization|chunk|token)"
    }
    
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    for log_file in log_files:
        try:
            logger.info(f"Analyzing log file: {log_file}")
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Extract timestamp if present
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            try:
                                log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                                if log_time < cutoff_time:
                                    continue
                            except ValueError:
                                pass  # Continue processing if timestamp parsing fails
                        
                        # Check for Phase 2 patterns
                        if re.search(patterns["content_optimization"], line):
                            phase2_indicators["content_optimization_used"] += 1
                        
                        chunk_match = re.search(patterns["chunk_processing"], line)
                        if chunk_match:
                            phase2_indicators["chunk_based_processing"] += 1
                        
                        token_match = re.search(patterns["token_reduction"], line)
                        if token_match:
                            original_tokens = int(token_match.group(1))
                            optimized_tokens = int(token_match.group(2))
                            reduction_percent = float(token_match.group(3))
                            
                            phase2_indicators["token_optimization_events"] += 1
                            phase2_indicators["optimization_metrics"].append({
                                "original_tokens": original_tokens,
                                "optimized_tokens": optimized_tokens,
                                "reduction_percent": reduction_percent,
                                "timestamp": timestamp_match.group(1) if timestamp_match else "unknown"
                            })
                        
                        biomarker_match = re.search(patterns["biomarker_extraction"], line)
                        if biomarker_match:
                            count = int(biomarker_match.group(1))
                            phase2_indicators["biomarker_extractions"] += count
                        
                        if re.search(patterns["document_processing"], line):
                            phase2_indicators["total_documents_processed"] += 1
                        
                        if re.search(patterns["phase2_errors"], line, re.IGNORECASE):
                            phase2_indicators["errors"].append({
                                "line": line.strip(),
                                "file": log_file,
                                "line_number": line_num
                            })
                    
                    except Exception as line_error:
                        logger.debug(f"Error processing line {line_num} in {log_file}: {str(line_error)}")
                        continue
        
        except Exception as file_error:
            logger.error(f"Error reading log file {log_file}: {str(file_error)}")
            continue
    
    return phase2_indicators

def check_database_metrics() -> Dict[str, Any]:
    """Check database for Phase 2 related metrics"""
    logger = logging.getLogger(__name__)
    
    try:
        # Try to import database components
        from app.database.database import get_db
        from sqlalchemy import text
        
        # Get database session
        db = next(get_db())
        
        # Query for recent extractions with optimization data
        recent_extractions_query = text("""
            SELECT 
                COUNT(*) as total_extractions,
                AVG(CASE WHEN processing_time IS NOT NULL THEN processing_time ELSE NULL END) as avg_processing_time,
                COUNT(CASE WHEN optimization_data IS NOT NULL THEN 1 ELSE NULL END) as optimized_extractions
            FROM biomarker_extractions 
            WHERE created_at >= datetime('now', '-24 hours')
        """)
        
        result = db.execute(recent_extractions_query).fetchone()
        
        metrics = {
            "total_extractions_24h": result[0] if result else 0,
            "avg_processing_time": result[1] if result else None,
            "optimized_extractions": result[2] if result else 0
        }
        
        # Query for biomarker counts
        biomarker_count_query = text("""
            SELECT COUNT(*) as total_biomarkers
            FROM biomarkers 
            WHERE created_at >= datetime('now', '-24 hours')
        """)
        
        biomarker_result = db.execute(biomarker_count_query).fetchone()
        metrics["total_biomarkers_24h"] = biomarker_result[0] if biomarker_result else 0
        
        db.close()
        return metrics
        
    except Exception as e:
        logger.warning(f"Could not query database metrics: {str(e)}")
        return {"error": str(e)}

def generate_phase2_report() -> Dict[str, Any]:
    """Generate a comprehensive Phase 2 status report"""
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Generating Phase 2 Production Status Report")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "configuration": check_phase2_configuration(),
        "log_analysis": analyze_recent_logs(24),
        "database_metrics": check_database_metrics()
    }
    
    # Calculate summary statistics
    log_data = report["log_analysis"]
    if not isinstance(log_data, dict) or "error" in log_data:
        report["summary"] = {"status": "ERROR", "message": "Could not analyze logs"}
    else:
        # Calculate Phase 2 health score
        health_indicators = []
        
        # Check if content optimization is being used
        if log_data.get("content_optimization_used", 0) > 0:
            health_indicators.append("✅ Content optimization active")
        else:
            health_indicators.append("❌ Content optimization not detected")
        
        # Check if chunk processing is working
        if log_data.get("chunk_based_processing", 0) > 0:
            health_indicators.append("✅ Chunk-based processing active")
        else:
            health_indicators.append("❌ Chunk-based processing not detected")
        
        # Check token optimization
        if log_data.get("token_optimization_events", 0) > 0:
            avg_reduction = sum(m["reduction_percent"] for m in log_data.get("optimization_metrics", [])) / len(log_data.get("optimization_metrics", [1]))
            health_indicators.append(f"✅ Token optimization active (avg {avg_reduction:.1f}% reduction)")
        else:
            health_indicators.append("❌ Token optimization not detected")
        
        # Check biomarker extraction
        if log_data.get("biomarker_extractions", 0) > 0:
            health_indicators.append(f"✅ Biomarker extraction active ({log_data['biomarker_extractions']} biomarkers)")
        else:
            health_indicators.append("❌ No biomarker extractions detected")
        
        # Check for errors
        error_count = len(log_data.get("errors", []))
        if error_count == 0:
            health_indicators.append("✅ No Phase 2 errors detected")
        else:
            health_indicators.append(f"⚠️ {error_count} Phase 2 errors detected")
        
        # Overall health score
        positive_indicators = sum(1 for indicator in health_indicators if indicator.startswith("✅"))
        total_indicators = len(health_indicators)
        health_score = (positive_indicators / total_indicators) * 100
        
        report["summary"] = {
            "health_score": health_score,
            "status": "HEALTHY" if health_score >= 80 else "WARNING" if health_score >= 60 else "CRITICAL",
            "indicators": health_indicators,
            "documents_processed": log_data.get("total_documents_processed", 0),
            "optimization_events": log_data.get("token_optimization_events", 0)
        }
    
    return report

def main():
    """Main monitoring function"""
    logger = setup_logging()
    
    logger.info("🚀 Starting Phase 2 Production Monitoring")
    
    # Generate report
    report = generate_phase2_report()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 PHASE 2 PRODUCTION STATUS REPORT")
    print("="*60)
    
    # Configuration status
    config = report["configuration"]
    print(f"\n🔧 Configuration:")
    print(f"   Master Enabled: {'✅' if config.get('master_enabled') else '❌'}")
    print(f"   Content Optimization: {'✅' if config.get('content_optimization_enabled') else '❌'}")
    print(f"   Token Reduction Target: {config.get('token_reduction_target', 0)*100:.0f}%")
    print(f"   Adaptive Context: {'✅' if config.get('adaptive_context_enabled') else '❌'}")
    
    # Summary status
    summary = report.get("summary", {})
    print(f"\n📈 Overall Status: {summary.get('status', 'UNKNOWN')}")
    print(f"   Health Score: {summary.get('health_score', 0):.1f}%")
    print(f"   Documents Processed (24h): {summary.get('documents_processed', 0)}")
    print(f"   Optimization Events (24h): {summary.get('optimization_events', 0)}")
    
    # Health indicators
    print(f"\n🔍 Health Indicators:")
    for indicator in summary.get("indicators", []):
        print(f"   {indicator}")
    
    # Log analysis details
    log_data = report["log_analysis"]
    if isinstance(log_data, dict) and "error" not in log_data:
        print(f"\n📋 Activity Summary (24h):")
        print(f"   Content Optimization Uses: {log_data.get('content_optimization_used', 0)}")
        print(f"   Chunk Processing Events: {log_data.get('chunk_based_processing', 0)}")
        print(f"   Token Optimization Events: {log_data.get('token_optimization_events', 0)}")
        print(f"   Total Biomarkers Extracted: {log_data.get('biomarker_extractions', 0)}")
        print(f"   Errors Detected: {len(log_data.get('errors', []))}")
        
        # Token optimization details
        if log_data.get("optimization_metrics"):
            metrics = log_data["optimization_metrics"]
            avg_reduction = sum(m["reduction_percent"] for m in metrics) / len(metrics)
            total_tokens_saved = sum(m["original_tokens"] - m["optimized_tokens"] for m in metrics)
            print(f"\n💰 Token Optimization:")
            print(f"   Average Reduction: {avg_reduction:.1f}%")
            print(f"   Total Tokens Saved: {total_tokens_saved:,}")
            print(f"   Estimated Cost Savings: ${total_tokens_saved * 0.000003:.4f}")
    
    # Database metrics
    db_metrics = report["database_metrics"]
    if isinstance(db_metrics, dict) and "error" not in db_metrics:
        print(f"\n🗄️ Database Metrics (24h):")
        print(f"   Total Extractions: {db_metrics.get('total_extractions_24h', 0)}")
        print(f"   Optimized Extractions: {db_metrics.get('optimized_extractions', 0)}")
        print(f"   Total Biomarkers: {db_metrics.get('total_biomarkers_24h', 0)}")
        if db_metrics.get('avg_processing_time'):
            print(f"   Avg Processing Time: {db_metrics['avg_processing_time']:.2f}s")
    
    print("\n" + "="*60)
    
    # Save detailed report
    report_file = f"phase2_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"📄 Detailed report saved to: {report_file}")
    except Exception as e:
        logger.error(f"Could not save report: {str(e)}")
    
    # Return exit code based on health
    health_score = summary.get("health_score", 0)
    if health_score >= 80:
        logger.info("✅ Phase 2 is healthy")
        return 0
    elif health_score >= 60:
        logger.warning("⚠️ Phase 2 has some issues")
        return 1
    else:
        logger.error("❌ Phase 2 has critical issues")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 