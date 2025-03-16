#!/bin/bash
# Script to monitor application logs in real-time for debugging

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to display usage info
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -a, --all      Monitor all log files"
    echo "  -b, --biomarker Monitor biomarker parser logs"
    echo "  -p, --pdf      Monitor PDF service logs"
    echo "  -e, --error    Show only ERROR level logs"
    echo "  -h, --help     Show this help message"
    exit 1
}

# Default values
monitor_biomarker=false
monitor_pdf=false
error_only=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            monitor_biomarker=true
            monitor_pdf=true
            shift
            ;;
        -b|--biomarker)
            monitor_biomarker=true
            shift
            ;;
        -p|--pdf)
            monitor_pdf=true
            shift
            ;;
        -e|--error)
            error_only=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# If no specific log was chosen, monitor all
if [[ "$monitor_biomarker" == "false" && "$monitor_pdf" == "false" ]]; then
    monitor_biomarker=true
    monitor_pdf=true
fi

# Build the command
command=""

if [[ "$monitor_biomarker" == "true" ]]; then
    if [[ "$error_only" == "true" ]]; then
        command="tail -f logs/biomarker_parser.log | grep ERROR"
    else
        command="tail -f logs/biomarker_parser.log"
    fi
fi

if [[ "$monitor_pdf" == "true" ]]; then
    if [[ -n "$command" ]]; then
        if [[ "$error_only" == "true" ]]; then
            command="$command & tail -f logs/pdf_service.log | grep ERROR"
        else
            command="$command & tail -f logs/pdf_service.log"
        fi
    else
        if [[ "$error_only" == "true" ]]; then
            command="tail -f logs/pdf_service.log | grep ERROR"
        else
            command="tail -f logs/pdf_service.log"
        fi
    fi
fi

# Set up color indicators for log levels
if [[ "$error_only" == "false" ]]; then
    command="$command | grep --color=always -E '^|ERROR|WARNING|INFO|DEBUG'"
fi

echo "Monitoring logs in real-time. Press Ctrl+C to exit."
echo "-----------------------------------------------"

# Execute the command
eval $command 