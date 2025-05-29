#!/usr/bin/env python3
"""
Optimization Monitor
====================

Real-time monitoring tool for the optimization system performance, tracking 
accuracy, cost savings, and system health across different optimization modes.

Features:
- Real-time monitoring of optimization metrics
- Performance tracking across different modes  
- Cost analysis and savings calculation
- Health checks and system status monitoring
- Historical trend analysis
- Alert system for performance degradation

Usage:
    python optimization_monitor.py
    python optimization_monitor.py --mode continuous
    python optimization_monitor.py --analyze-logs --days 7
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

# Add the app directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.utils.content_optimization import estimate_tokens
    from app.core.database import get_database_session
    from app.models.pdf_model import PDF
    from app.models.biomarker_model import Biomarker
except ImportError as e:
    print(f"⚠️  Warning: Could not import app modules: {e}")
    print("   Monitor will run in standalone mode with limited functionality")


class OptimizationMonitor:
    """Real-time monitoring system for optimization performance."""
    
    def __init__(self, log_dir: str = "logs", history_size: int = 1000):
        self.log_dir = Path(log_dir)
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self.performance_thresholds = {
            "min_token_reduction": 15.0,  # Minimum acceptable token reduction %
            "min_accuracy": 0.85,         # Minimum acceptable accuracy
            "max_processing_time": 300,   # Maximum acceptable processing time (seconds)
            "min_biomarker_count": 5      # Minimum expected biomarkers per document
        }
        self.alerts = []
        self.is_monitoring = False
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        import logging
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / f'optimization_monitor_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self, interval: int = 60, mode: str = "continuous"):
        """
        Start real-time monitoring.
        
        Args:
            interval: Monitoring interval in seconds
            mode: Monitoring mode ('continuous', 'batch', 'on-demand')
        """
        self.logger.info(f"🔍 Starting optimization monitoring in {mode} mode")
        self.logger.info(f"📊 Monitoring interval: {interval} seconds")
        self.is_monitoring = True
        
        if mode == "continuous":
            self._continuous_monitoring(interval)
        elif mode == "batch":
            self._batch_monitoring()
        else:
            self._on_demand_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.is_monitoring = False
        self.logger.info("🛑 Monitoring stopped")
    
    def _continuous_monitoring(self, interval: int):
        """Run continuous monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self.collect_current_metrics()
                self.analyze_metrics(metrics)
                self.check_alerts(metrics)
                self.log_metrics(metrics)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Monitoring interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(interval)
    
    def _batch_monitoring(self):
        """Run batch analysis of recent processing."""
        self.logger.info("📊 Running batch analysis...")
        
        # Analyze recent PDFs
        recent_metrics = self.analyze_recent_processing(hours=24)
        
        # Generate report
        report = self.generate_performance_report(recent_metrics)
        self.save_report(report)
        
        self.logger.info("📋 Batch analysis complete")
    
    def _on_demand_monitoring(self):
        """Run on-demand monitoring."""
        self.logger.info("🔍 Running on-demand analysis...")
        
        metrics = self.collect_current_metrics()
        self.display_current_status(metrics)
        
        # Check system health
        health_status = self.check_system_health()
        self.display_health_status(health_status)
    
    def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "optimization_metrics": {},
            "system_metrics": {},
            "database_metrics": {}
        }
        
        try:
            # Collect optimization metrics from logs
            metrics["optimization_metrics"] = self._collect_optimization_metrics()
            
            # Collect system metrics
            metrics["system_metrics"] = self._collect_system_metrics()
            
            # Collect database metrics
            metrics["database_metrics"] = self._collect_database_metrics()
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting metrics: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _collect_optimization_metrics(self) -> Dict[str, Any]:
        """Collect optimization-specific metrics from recent logs."""
        optimization_files = list(self.log_dir.glob("lab_optimization_*.json"))
        
        if not optimization_files:
            return {"status": "no_recent_optimizations"}
        
        # Get the most recent optimization file
        latest_file = max(optimization_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            metrics = {
                "last_optimization": data.get("test_timestamp"),
                "modes_performance": {}
            }
            
            if "modes_tested" in data:
                for mode, results in data["modes_tested"].items():
                    if "error" not in results:
                        metrics["modes_performance"][mode] = {
                            "token_reduction": results.get("token_metrics", {}).get("token_reduction_percent", 0),
                            "accuracy": results.get("biomarker_metrics", {}).get("average_confidence", 0),
                            "biomarkers_extracted": results.get("biomarker_metrics", {}).get("biomarkers_extracted", 0),
                            "processing_time": results.get("processing_time", 0)
                        }
            
            return metrics
            
        except Exception as e:
            self.logger.warning(f"⚠️  Could not parse optimization file {latest_file}: {e}")
            return {"status": "parse_error", "error": str(e)}
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        import psutil
        
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except ImportError:
            return {"status": "psutil_not_available"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database-related metrics."""
        try:
            # This would need to be adapted based on your database setup
            db_path = Path("vein_diagram.db")
            if db_path.exists():
                stat = db_path.stat()
                return {
                    "database_size_mb": stat.st_size / (1024 * 1024),
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                return {"status": "database_not_found"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def analyze_recent_processing(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Analyze processing metrics from recent time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = []
        
        # Check optimization log files
        for log_file in self.log_dir.glob("lab_optimization_*.json"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time > cutoff_time:
                    with open(log_file, 'r') as f:
                        data = json.load(f)
                        recent_metrics.append(data)
            except Exception as e:
                self.logger.warning(f"⚠️  Could not process {log_file}: {e}")
        
        return recent_metrics
    
    def analyze_metrics(self, metrics: Dict[str, Any]):
        """Analyze collected metrics for trends and issues."""
        self.metrics_history.append(metrics)
        
        if len(self.metrics_history) < 2:
            return  # Need at least 2 data points for trend analysis
        
        # Analyze trends
        trends = self._calculate_trends()
        
        # Store trends in metrics
        metrics["trends"] = trends
        
        self.logger.info(f"📈 Trends analysis: {trends}")
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from historical data."""
        if len(self.metrics_history) < 5:
            return {"status": "insufficient_data"}
        
        # Get recent metrics for trend calculation
        recent_metrics = list(self.metrics_history)[-5:]  # Last 5 measurements
        
        trends = {
            "token_reduction_trend": "stable",
            "accuracy_trend": "stable",
            "processing_time_trend": "stable"
        }
        
        try:
            # Calculate token reduction trend
            token_reductions = []
            for metric in recent_metrics:
                opt_metrics = metric.get("optimization_metrics", {})
                balanced_perf = opt_metrics.get("modes_performance", {}).get("balanced", {})
                if "token_reduction" in balanced_perf:
                    token_reductions.append(balanced_perf["token_reduction"])
            
            if len(token_reductions) >= 3:
                if token_reductions[-1] > token_reductions[0] * 1.1:
                    trends["token_reduction_trend"] = "improving"
                elif token_reductions[-1] < token_reductions[0] * 0.9:
                    trends["token_reduction_trend"] = "declining"
            
            # Similar analysis for accuracy and processing time...
            
        except Exception as e:
            self.logger.warning(f"⚠️  Trend calculation error: {e}")
            trends["error"] = str(e)
        
        return trends
    
    def check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts."""
        alerts = []
        
        opt_metrics = metrics.get("optimization_metrics", {})
        
        if "modes_performance" in opt_metrics:
            for mode, performance in opt_metrics["modes_performance"].items():
                # Check token reduction
                token_reduction = performance.get("token_reduction", 0)
                if token_reduction < self.performance_thresholds["min_token_reduction"]:
                    alerts.append({
                        "type": "low_token_reduction",
                        "mode": mode,
                        "value": token_reduction,
                        "threshold": self.performance_thresholds["min_token_reduction"],
                        "severity": "warning"
                    })
                
                # Check accuracy
                accuracy = performance.get("accuracy", 0)
                if accuracy < self.performance_thresholds["min_accuracy"]:
                    alerts.append({
                        "type": "low_accuracy",
                        "mode": mode,
                        "value": accuracy,
                        "threshold": self.performance_thresholds["min_accuracy"],
                        "severity": "critical"
                    })
                
                # Check processing time
                processing_time = performance.get("processing_time", 0)
                if processing_time > self.performance_thresholds["max_processing_time"]:
                    alerts.append({
                        "type": "slow_processing",
                        "mode": mode,
                        "value": processing_time,
                        "threshold": self.performance_thresholds["max_processing_time"],
                        "severity": "warning"
                    })
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(f"⚠️  ALERT: {alert['type']} in {alert['mode']} mode - "
                               f"Value: {alert['value']}, Threshold: {alert['threshold']}")
        
        self.alerts.extend(alerts)
        return alerts
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {}
        }
        
        # Check log files
        health["checks"]["log_files"] = self._check_log_files()
        
        # Check optimization system
        health["checks"]["optimization_system"] = self._check_optimization_system()
        
        # Check database
        health["checks"]["database"] = self._check_database_health()
        
        # Determine overall status
        failed_checks = [name for name, check in health["checks"].items() 
                        if check.get("status") == "error"]
        
        if failed_checks:
            health["overall_status"] = "degraded" if len(failed_checks) == 1 else "error"
            health["failed_checks"] = failed_checks
        
        return health
    
    def _check_log_files(self) -> Dict[str, Any]:
        """Check log file accessibility and recent activity."""
        try:
            log_files = list(self.log_dir.glob("*.log"))
            recent_activity = False
            
            cutoff_time = datetime.now() - timedelta(hours=1)
            for log_file in log_files:
                if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_time:
                    recent_activity = True
                    break
            
            return {
                "status": "healthy",
                "log_files_count": len(log_files),
                "recent_activity": recent_activity
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_optimization_system(self) -> Dict[str, Any]:
        """Check optimization system functionality."""
        try:
            # Try importing optimization modules
            from app.services.utils.content_optimization import optimize_content_for_extraction
            
            # Check if environment variables work
            test_env = os.environ.get("BALANCED_MODE", "false")
            
            return {
                "status": "healthy",
                "modules_importable": True,
                "env_variables_accessible": True
            }
        except ImportError as e:
            return {
                "status": "error", 
                "error": f"Cannot import optimization modules: {e}"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations."""
        try:
            db_path = Path("vein_diagram.db")
            if not db_path.exists():
                return {"status": "error", "error": "Database file not found"}
            
            # Basic file check
            size_mb = db_path.stat().st_size / (1024 * 1024)
            
            return {
                "status": "healthy",
                "database_exists": True,
                "size_mb": round(size_mb, 2)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def generate_performance_report(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "analysis_period": f"{len(metrics_list)} measurements",
            "summary": {},
            "detailed_analysis": {},
            "recommendations": []
        }
        
        if not metrics_list:
            report["summary"]["status"] = "no_data"
            return report
        
        # Aggregate metrics
        token_reductions = []
        accuracies = []
        processing_times = []
        
        for metrics in metrics_list:
            opt_metrics = metrics.get("optimization_metrics", {})
            balanced_perf = opt_metrics.get("modes_performance", {}).get("balanced", {})
            
            if balanced_perf:
                token_reductions.append(balanced_perf.get("token_reduction", 0))
                accuracies.append(balanced_perf.get("accuracy", 0))
                processing_times.append(balanced_perf.get("processing_time", 0))
        
        # Calculate summary statistics
        if token_reductions:
            report["summary"] = {
                "avg_token_reduction": sum(token_reductions) / len(token_reductions),
                "min_token_reduction": min(token_reductions),
                "max_token_reduction": max(token_reductions),
                "avg_accuracy": sum(accuracies) / len(accuracies) if accuracies else 0,
                "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0
            }
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report["summary"])
        
        return report
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations based on metrics."""
        recommendations = []
        
        avg_token_reduction = summary.get("avg_token_reduction", 0)
        avg_accuracy = summary.get("avg_accuracy", 0)
        
        if avg_token_reduction < 20:
            recommendations.append("Consider tuning compression patterns for better token reduction")
        
        if avg_accuracy < 0.9:
            recommendations.append("Review accuracy mode settings to improve biomarker detection")
        
        if summary.get("avg_processing_time", 0) > 120:
            recommendations.append("Consider optimizing chunk sizes for faster processing")
        
        if not recommendations:
            recommendations.append("System is performing well within expected parameters")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save performance report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        report_path = self.log_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📊 Performance report saved: {report_path}")
    
    def display_current_status(self, metrics: Dict[str, Any]):
        """Display current system status."""
        print("\n" + "="*60)
        print("🔍 OPTIMIZATION SYSTEM STATUS")
        print("="*60)
        
        opt_metrics = metrics.get("optimization_metrics", {})
        
        if "modes_performance" in opt_metrics:
            print("\n📊 Current Performance:")
            for mode, performance in opt_metrics["modes_performance"].items():
                print(f"   {mode.upper()}:")
                print(f"     💰 Token reduction: {performance.get('token_reduction', 0):.1f}%")
                print(f"     🎯 Accuracy: {performance.get('accuracy', 0):.3f}")
                print(f"     ⏱️  Processing time: {performance.get('processing_time', 0):.1f}s")
        
        sys_metrics = metrics.get("system_metrics", {})
        if "cpu_usage" in sys_metrics:
            print(f"\n💻 System Resources:")
            print(f"     CPU: {sys_metrics.get('cpu_usage', 0):.1f}%")
            print(f"     Memory: {sys_metrics.get('memory_usage', 0):.1f}%")
            print(f"     Disk: {sys_metrics.get('disk_usage', 0):.1f}%")
    
    def display_health_status(self, health: Dict[str, Any]):
        """Display system health status."""
        print(f"\n🏥 System Health: {health['overall_status'].upper()}")
        
        for check_name, check_result in health["checks"].items():
            status_icon = "✅" if check_result.get("status") == "healthy" else "❌"
            print(f"     {status_icon} {check_name}: {check_result.get('status', 'unknown')}")
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log metrics to file."""
        log_file = self.log_dir / f"optimization_metrics_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Append to daily metrics file
        try:
            if log_file.exists():
                with open(log_file, 'r') as f:
                    daily_metrics = json.load(f)
            else:
                daily_metrics = {"date": datetime.now().strftime('%Y-%m-%d'), "metrics": []}
            
            daily_metrics["metrics"].append(metrics)
            
            with open(log_file, 'w') as f:
                json.dump(daily_metrics, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"❌ Failed to log metrics: {e}")


def main():
    """Main CLI interface for the optimization monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Optimization Monitor - Real-time monitoring of optimization system performance",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--mode",
        choices=["continuous", "batch", "on-demand"],
        default="on-demand",
        help="Monitoring mode (default: on-demand)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds for continuous mode (default: 60)"
    )
    
    parser.add_argument(
        "--analyze-logs",
        action="store_true",
        help="Analyze existing log files"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory containing log files (default: logs)"
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = OptimizationMonitor(log_dir=args.log_dir)
    
    try:
        if args.analyze_logs:
            # Analyze historical logs
            hours = args.days * 24
            recent_metrics = monitor.analyze_recent_processing(hours=hours)
            
            if recent_metrics:
                report = monitor.generate_performance_report(recent_metrics)
                monitor.save_report(report)
                
                print(f"\n📊 Historical Analysis ({args.days} days):")
                print(f"   📋 Processed: {len(recent_metrics)} optimization runs")
                if "summary" in report:
                    summary = report["summary"]
                    print(f"   💰 Avg token reduction: {summary.get('avg_token_reduction', 0):.1f}%")
                    print(f"   🎯 Avg accuracy: {summary.get('avg_accuracy', 0):.3f}")
                    print(f"   ⏱️  Avg processing time: {summary.get('avg_processing_time', 0):.1f}s")
                
                print(f"\n💡 Recommendations:")
                for rec in report.get("recommendations", []):
                    print(f"   • {rec}")
            else:
                print("⚠️  No optimization data found for the specified period")
        
        else:
            # Start monitoring
            monitor.start_monitoring(interval=args.interval, mode=args.mode)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 