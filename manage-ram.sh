#!/bin/bash

echo "=========================================="
echo "       System Memory Status Monitor       "
echo "=========================================="
echo ""
echo "[1] Current Memory Usage:"
free -h
echo ""

echo "[2] Top 10 Memory Consuming Processes:"
# List top 10 processes by memory usage
ps aux --sort=-%mem | awk 'NR<=11{print $0}' | cut -c 1-100
echo "..."
echo ""

if [ "$1" == "--clean" ]; then
    echo "[3] Attempting to clean RAM..."
    if [ "$EUID" -ne 0 ]; then
        echo "Error: Please run with 'sudo' to clean RAM cache."
        echo "Usage: sudo ./manage-ram.sh --clean"
        exit 1
    fi
    
    echo "Syncing filesystem..."
    sync
    
    # Drop caches: 
    # 1 = Page cache
    # 2 = dentries and inodes
    # 3 = Page cache, dentries, and inodes
    echo "Dropping caches (echo 3 > /proc/sys/vm/drop_caches)..."
    echo 3 > /proc/sys/vm/drop_caches
    
    echo "Done."
    echo ""
    echo "[4] Memory Usage After Cleanup:"
    free -h
else
    echo "Tip: To clear cached RAM (buffers/cache), run this script with 'sudo' and '--clean':"
    echo "     sudo ./manage-ram.sh --clean"
fi
echo "=========================================="
