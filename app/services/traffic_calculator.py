from typing import List, Tuple, Optional
import logging
from datetime import datetime

class TrafficCalculator:
    """
    ATCS Core Algorithm - Adaptive Traffic Light Timing Calculator
    
    Implements intelligent traffic timing calculation algorithm that
    dynamically adjusts green light durations based on real-time vehicle counts.
    
    Algorithm Logic:
    1. Count total vehicles across all 4 lanes
    2. Determine cycle time: 120s base, +10s per 10 vehicles over 100, max 180s
    3. For each lane: ≤15 vehicles = 15s green time, else proportional allocation
    4. Calculate remaining time for adjustable lanes
    5. Cap at 90s max per lane with redistribution
    6. Round to whole seconds and balance total
    """
    
    def __init__(self, min_time: int = 15, max_time: int = 90, base_cycle_time: int = 120, db_service=None):
        """
        Initialize traffic calculator with timing constraints
        
        Args:
            min_time (int): Minimum green time per lane in seconds
            max_time (int): Maximum green time per lane in seconds  
            base_cycle_time (int): Base cycle time in seconds
            db_service: Database service instance for logging (optional)
        """
        self.min_time = min_time
        self.max_time = max_time
        self.base_cycle_time = base_cycle_time
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    async def calculate_green_times(self, lane_counts: List[int], junction_id: Optional[int] = None) -> Tuple[List[int], int]:
        """
        Calculate optimal green times for each lane based on vehicle counts
        
        Algorithm Steps:
        1. Validate input data
        2. Calculate total vehicles and cycle time
        3. Identify fixed lanes (≤15 vehicles) and adjustable lanes
        4. Proportionally allocate time to adjustable lanes
        5. Enforce maximum time constraints with redistribution
        6. Round to whole seconds and balance total
        
        Args:
            lane_counts (List[int]): Vehicle count [lane1, lane2, lane3, lane4]
            junction_id (Optional[int]): Junction ID for database logging
            
        Returns:
            Tuple[List[int], int]: (green_times_per_lane, total_cycle_time)
            
        Raises:
            ValueError: If input validation fails
        """
        start_time = datetime.now()
        
        # Step 1: Input validation
        if len(lane_counts) != 4:
            raise ValueError("Lane counts must contain exactly 4 values")
        
        if any(count < 0 for count in lane_counts):
            raise ValueError("Lane counts cannot be negative")
            
        num_lanes = 4
        total_cars = sum(lane_counts)
        
        self.logger.info(f"Calculating green times for lane counts: {lane_counts}, total vehicles: {total_cars}")
        
        # Step 2: Calculate cycle time based on total vehicles
        if total_cars <= 100:
            cycle_time = self.base_cycle_time
        else:
            # Correct increment calculation: for every 10 vehicles over 100, add 10s
            excess_vehicles = total_cars - 100
            increments = (excess_vehicles + 9) // 10  # Ceiling division
            cycle_time = self.base_cycle_time + increments * 10
            cycle_time = min(cycle_time, 180)  # Maximum 180 seconds
        
        self.logger.debug(f"Calculated cycle time: {cycle_time}s for {total_cars} vehicles")
        
        # Step 3: Identify fixed and adjustable lanes
        fixed_lanes = []
        adjustable_lanes = []
        green_times = [0] * num_lanes
        
        # Set minimum times for all lanes first
        for idx, count in enumerate(lane_counts):
            if count <= 15:
                green_times[idx] = self.min_time
                fixed_lanes.append(idx)
                self.logger.debug(f"Lane {idx+1}: Fixed at {self.min_time}s ({count} vehicles)")
            else:
                green_times[idx] = self.min_time  # Start with minimum
                adjustable_lanes.append(idx)
                self.logger.debug(f"Lane {idx+1}: Adjustable from {self.min_time}s ({count} vehicles)")
        
        # Special case: If all lanes have ≤15 vehicles, use minimum cycle time
        if not adjustable_lanes:
            final_cycle_time = num_lanes * self.min_time  # 4 × 15 = 60s
            green_times_rounded = [self.min_time] * num_lanes
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"All lanes ≤15 vehicles: using minimum cycle time {final_cycle_time}s")
            self.logger.info(f"Final green times: {green_times_rounded}, cycle time: {final_cycle_time}, execution time: {execution_time:.2f}ms")
            return green_times_rounded, final_cycle_time
        
        # Step 4: Calculate remaining time to distribute
        total_fixed_time = len(fixed_lanes) * self.min_time
        total_adjustable_base = len(adjustable_lanes) * self.min_time
        remaining_time = cycle_time - total_fixed_time - total_adjustable_base
        
        # Step 5: Distribute remaining time proportionally among adjustable lanes
        if adjustable_lanes and remaining_time > 0:
            adjustable_counts = [lane_counts[i] for i in adjustable_lanes]
            total_adjustable_vehicles = sum(adjustable_counts)
            
            if total_adjustable_vehicles > 0:
                for i, lane_idx in enumerate(adjustable_lanes):
                    # Proportional allocation based on vehicle count
                    proportion = adjustable_counts[i] / total_adjustable_vehicles
                    additional_time = remaining_time * proportion
                    green_times[lane_idx] = self.min_time + additional_time
                    self.logger.debug(f"Lane {lane_idx+1}: {self.min_time} + {additional_time:.2f} = {green_times[lane_idx]:.2f}s")
        
        # Step 6: Enforce maximum time constraints with redistribution
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            excess_time = 0
            over_max_lanes = []
            under_max_lanes = []
            
            for i in adjustable_lanes:
                if green_times[i] > self.max_time:
                    excess_time += green_times[i] - self.max_time
                    over_max_lanes.append(i)
                elif green_times[i] < self.max_time:
                    under_max_lanes.append(i)
            
            if excess_time > 0:
                # Cap over-max lanes
                for i in over_max_lanes:
                    green_times[i] = self.max_time
                
                # Redistribute excess among under-max adjustable lanes
                if under_max_lanes:
                    # Only distribute to adjustable lanes that can accept more time
                    eligible_lanes = [i for i in under_max_lanes if lane_counts[i] > 15]
                    
                    if eligible_lanes:
                        total_eligible_vehicles = sum(lane_counts[i] for i in eligible_lanes)
                        for i in eligible_lanes:
                            if total_eligible_vehicles > 0:
                                proportion = lane_counts[i] / total_eligible_vehicles
                                additional = excess_time * proportion
                                green_times[i] = min(green_times[i] + additional, self.max_time)
                    else:
                        # No eligible lanes, distribute evenly among all under-max lanes
                        for i in under_max_lanes:
                            green_times[i] = min(green_times[i] + excess_time / len(under_max_lanes), self.max_time)
                
                self.logger.debug(f"Iteration {iteration}: Redistributed {excess_time:.2f}s excess time")
                iteration += 1
            else:
                break
        
        # Step 7: Handle case where excess time cannot be redistributed
        # Check if we still have violations after redistribution attempts
        final_excess = 0
        for i in range(num_lanes):
            if green_times[i] > self.max_time:
                final_excess += green_times[i] - self.max_time
                green_times[i] = self.max_time
        
        if final_excess > 0:
            # Reduce cycle time if we can't redistribute excess
            cycle_time = cycle_time - int(final_excess)
            self.logger.debug(f"Reduced cycle time by {int(final_excess)}s due to max constraint violations")
        
        # Step 8: Final rounding and balancing
        green_times_rounded = [round(t) for t in green_times]
        current_total = sum(green_times_rounded)
        diff = cycle_time - current_total
        
        # Balance the difference intelligently
        if diff != 0:
            if diff > 0:
                # Need to add time - add to lane with most vehicles that's not at max
                for _ in range(abs(diff)):
                    best_lane = -1
                    best_score = -1
                    for i in range(num_lanes):
                        if green_times_rounded[i] < self.max_time:
                            score = lane_counts[i] * (1 - green_times_rounded[i] / self.max_time)
                            if score > best_score:
                                best_score = score
                                best_lane = i
                    if best_lane != -1:
                        green_times_rounded[best_lane] += 1
            else:
                # Need to remove time - remove from lane with fewest vehicles that's above min
                for _ in range(abs(diff)):
                    best_lane = -1
                    best_score = float('inf')
                    for i in range(num_lanes):
                        if green_times_rounded[i] > self.min_time:
                            score = lane_counts[i] + green_times_rounded[i]
                            if score < best_score:
                                best_score = score
                                best_lane = i
                    if best_lane != -1:
                        green_times_rounded[best_lane] -= 1
            
            self.logger.debug(f"Balanced {diff}s difference through intelligent adjustment")
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        self.logger.info(f"Final green times: {green_times_rounded}, cycle time: {cycle_time}, execution time: {execution_time:.2f}ms")
        
        # Log to database if service and junction_id provided
        if self.db_service and junction_id:
            try:
                await self.db_service.log_traffic_cycle(
                    junction_id=junction_id,
                    lane_counts=lane_counts,
                    green_times=green_times_rounded,
                    cycle_time=cycle_time,
                    calculation_time_ms=int(execution_time)
                )
                self.logger.debug(f"Traffic cycle logged to database for junction {junction_id}")
            except Exception as e:
                self.logger.error(f"Failed to log traffic cycle to database: {str(e)}")
        
        return green_times_rounded, cycle_time
    
    def validate_calculation(self, lane_counts: List[int], green_times: List[int], cycle_time: int) -> bool:
        """
        Validate that calculated times meet all constraints
        
        Args:
            lane_counts (List[int]): Input vehicle counts
            green_times (List[int]): Calculated green times
            cycle_time (int): Calculated cycle time
            
        Returns:
            bool: True if all constraints are satisfied
        """
        # Check bounds
        if any(time < self.min_time or time > self.max_time for time in green_times):
            self.logger.error(f"Green times {green_times} violate bounds [{self.min_time}, {self.max_time}]")
            return False
        
        # Check total equals cycle time
        if sum(green_times) != cycle_time:
            self.logger.error(f"Green times sum {sum(green_times)} != cycle time {cycle_time}")
            return False
            
        # Check proportionality (allow 2s rounding difference)
        for i in range(len(lane_counts)):
            for j in range(i + 1, len(lane_counts)):
                if lane_counts[i] > lane_counts[j] and green_times[i] < green_times[j]:
                    if green_times[j] - green_times[i] > 2:
                        self.logger.warning(f"Proportionality issue: Lane {i+1} ({lane_counts[i]} cars, {green_times[i]}s) vs Lane {j+1} ({lane_counts[j]} cars, {green_times[j]}s)")
                        return False
        
        self.logger.debug("Validation passed: All constraints satisfied")
        return True
    
    def get_algorithm_info(self) -> dict:
        """
        Get algorithm configuration information
        
        Returns:
            dict: Algorithm parameters and metadata
        """
        return {
            "algorithm_version": "v1.0",
            "min_green_time": self.min_time,
            "max_green_time": self.max_time,
            "base_cycle_time": self.base_cycle_time,
            "max_cycle_time": 180,
            "description": "ATCS Adaptive Traffic Light Timing Calculator",
            "author": "FlexTraff Team"
        }