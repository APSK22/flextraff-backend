#!/usr/bin/env python3
"""
Debug script for maximum constraint enforcement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.traffic_calculator import TrafficCalculator
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_max_constraint():
    calculator = TrafficCalculator()
    lane_counts = [100, 5, 5, 5]  # One lane with very high traffic
    
    print(f"Input: {lane_counts}")
    print(f"Total vehicles: {sum(lane_counts)}")
    
    green_times, cycle_time = calculator.calculate_green_times(lane_counts)
    
    print(f"Output: {green_times}")
    print(f"Cycle time: {cycle_time}")
    print(f"Lane 1 green time: {green_times[0]} (should be ≤90)")
    print(f"Validation: {calculator.validate_calculation(lane_counts, green_times, cycle_time)}")

if __name__ == "__main__":
    debug_max_constraint()