from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseService:
    """
    Supabase Database Service for FlexTraff ATCS Backend
    Handles all database operations without authentication requirements
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError("Missing Supabase credentials. Please check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file")
        
        self.supabase: Client = create_client(
            self.supabase_url,
            self.supabase_service_key
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Database service initialized successfully")
    
    async def log_vehicle_detection(
        self, 
        junction_id: int, 
        lane_number: int, 
        fastag_id: str, 
        vehicle_type: str = "car"
    ) -> Dict[str, Any]:
        """
        Log vehicle detection to Supabase
        
        Args:
            junction_id (int): ID of the traffic junction
            lane_number (int): Lane number (1-4)
            fastag_id (str): FastTag ID of the vehicle
            vehicle_type (str): Type of vehicle (car, truck, bike, etc.)
            
        Returns:
            Dict[str, Any]: Inserted record data
        """
        try:
            detection_data = {
                'junction_id': junction_id,
                'lane_number': lane_number,
                'fastag_id': fastag_id,
                'vehicle_type': vehicle_type,
                'detection_timestamp': datetime.now().isoformat(),
                'processing_status': 'processed'
            }
            
            result = self.supabase.table('vehicle_detections').insert(detection_data).execute()
            
            if result.data:
                self.logger.info(f"Vehicle detection logged: {fastag_id} on lane {lane_number} at junction {junction_id}")
                return result.data[0]
            else:
                raise Exception("No data returned from insert operation")
            
        except Exception as e:
            self.logger.error(f"Failed to log vehicle detection: {str(e)}")
            raise
    
    async def log_traffic_cycle(
        self,
        junction_id: int,
        lane_counts: List[int],
        green_times: List[int],
        cycle_time: int,
        calculation_time_ms: int
    ) -> Dict[str, Any]:
        """
        Log calculated traffic cycle to Supabase
        
        Args:
            junction_id (int): ID of the traffic junction
            lane_counts (List[int]): Vehicle counts per lane [lane1, lane2, lane3, lane4]
            green_times (List[int]): Calculated green times [lane1, lane2, lane3, lane4]
            cycle_time (int): Total cycle time in seconds
            calculation_time_ms (int): Algorithm execution time in milliseconds
            
        Returns:
            Dict[str, Any]: Inserted traffic cycle record
        """
        try:
            cycle_data = {
                'junction_id': junction_id,
                'cycle_start_time': datetime.now().isoformat(),
                'total_cycle_time': cycle_time,
                'lane_1_green_time': green_times[0],
                'lane_2_green_time': green_times[1],
                'lane_3_green_time': green_times[2],
                'lane_4_green_time': green_times[3],
                'lane_1_vehicle_count': lane_counts[0],
                'lane_2_vehicle_count': lane_counts[1],
                'lane_3_vehicle_count': lane_counts[2],
                'lane_4_vehicle_count': lane_counts[3],
                'total_vehicles_detected': sum(lane_counts),
                'algorithm_version': 'v1.0',
                'calculation_time_ms': calculation_time_ms
            }
            
            result = self.supabase.table('traffic_cycles').insert(cycle_data).execute()
            
            if result.data:
                cycle_id = result.data[0]['id']
                self.logger.info(f"Traffic cycle logged: ID {cycle_id}, junction {junction_id}, cycle time {cycle_time}s")
                return result.data[0]
            else:
                raise Exception("No data returned from insert operation")
            
        except Exception as e:
            self.logger.error(f"Failed to log traffic cycle: {str(e)}")
            raise
    
    async def get_current_lane_counts(self, junction_id: int, time_window_minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get current vehicle counts per lane for a junction within specified time window
        
        Args:
            junction_id (int): ID of the traffic junction
            time_window_minutes (int): Time window in minutes to look back
            
        Returns:
            List[Dict[str, Any]]: Lane counts with metadata
        """
        try:
            # Calculate time threshold
            time_threshold = (datetime.now() - timedelta(minutes=time_window_minutes)).isoformat()
            
            # Query vehicle detections within time window
            result = self.supabase.table('vehicle_detections') \
                .select('lane_number') \
                .eq('junction_id', junction_id) \
                .gte('detection_timestamp', time_threshold) \
                .execute()
            
            # Count vehicles per lane
            lane_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            lane_names = {1: "North", 2: "South", 3: "East", 4: "West"}
            
            for detection in result.data:
                lane_number = detection['lane_number']
                if lane_number in lane_counts:
                    lane_counts[lane_number] += 1
            
            # Format response
            lane_data = []
            for lane_num in range(1, 5):
                lane_data.append({
                    "lane": lane_names[lane_num],
                    "lane_number": lane_num,
                    "count": lane_counts[lane_num]
                })
            
            self.logger.debug(f"Current lane counts for junction {junction_id}: {lane_counts}")
            return lane_data
            
        except Exception as e:
            self.logger.error(f"Failed to get current lane counts: {str(e)}")
            return []
    
    async def get_vehicles_count_by_date(self, junction_id: int, target_date: date) -> int:
        """
        Get total vehicle count for a specific date
        
        Args:
            junction_id (int): ID of the traffic junction
            target_date (date): Date to query
            
        Returns:
            int: Total vehicle count for the date
        """
        try:
            start_date = target_date.isoformat()
            end_date = (target_date + timedelta(days=1)).isoformat()
            
            result = self.supabase.table('vehicle_detections') \
                .select('id', count='exact') \
                .eq('junction_id', junction_id) \
                .gte('detection_timestamp', start_date) \
                .lt('detection_timestamp', end_date) \
                .execute()
            
            count = result.count if result.count else 0
            self.logger.debug(f"Vehicle count for junction {junction_id} on {target_date}: {count}")
            return count
            
        except Exception as e:
            self.logger.error(f"Failed to get vehicles count by date: {str(e)}")
            return 0
    
    async def get_current_traffic_cycle(self, junction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent traffic cycle for a junction
        
        Args:
            junction_id (int): ID of the traffic junction
            
        Returns:
            Optional[Dict[str, Any]]: Most recent traffic cycle data or None
        """
        try:
            result = self.supabase.table('traffic_cycles') \
                .select('*') \
                .eq('junction_id', junction_id) \
                .order('cycle_start_time', desc=True) \
                .limit(1) \
                .execute()
            
            if result.data:
                self.logger.debug(f"Retrieved current traffic cycle for junction {junction_id}")
                return result.data[0]
            else:
                self.logger.debug(f"No traffic cycles found for junction {junction_id}")
                return None
            
        except Exception as e:
            self.logger.error(f"Failed to get current traffic cycle: {str(e)}")
            return None
    
    async def get_recent_detections_with_signals(
        self, 
        junction_id: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent vehicle detections with simulated signal status
        
        Args:
            junction_id (int): ID of the traffic junction
            limit (int): Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Recent detection logs with signal status
        """
        try:
            result = self.supabase.table('vehicle_detections') \
                .select('*') \
                .eq('junction_id', junction_id) \
                .order('detection_timestamp', desc=True) \
                .limit(limit) \
                .execute()
            
            enhanced_logs = []
            for detection in result.data:
                # Simulate signal status based on lane and time
                signal_status = self._simulate_signal_status(detection['lane_number'])
                
                enhanced_logs.append({
                    **detection,
                    'signal_status': signal_status,
                    'vehicle_count': 1,
                    'lane_name': self._get_lane_name(detection['lane_number'])
                })
            
            self.logger.debug(f"Retrieved {len(enhanced_logs)} recent detections for junction {junction_id}")
            return enhanced_logs
            
        except Exception as e:
            self.logger.error(f"Failed to get recent detections: {str(e)}")
            return []
    
    async def get_junction_info(self, junction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get traffic junction information
        
        Args:
            junction_id (int): ID of the traffic junction
            
        Returns:
            Optional[Dict[str, Any]]: Junction information or None
        """
        try:
            result = self.supabase.table('traffic_junctions') \
                .select('*') \
                .eq('id', junction_id) \
                .execute()
            
            if result.data:
                self.logger.debug(f"Retrieved junction info for ID {junction_id}")
                return result.data[0]
            else:
                self.logger.warning(f"Junction {junction_id} not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get junction info: {str(e)}")
            return None
    
    async def get_all_junctions(self) -> List[Dict[str, Any]]:
        """
        Get all traffic junctions
        
        Returns:
            List[Dict[str, Any]]: List of all junctions
        """
        try:
            result = self.supabase.table('traffic_junctions') \
                .select('*') \
                .eq('status', 'active') \
                .order('junction_name') \
                .execute()
            
            self.logger.debug(f"Retrieved {len(result.data)} active junctions")
            return result.data
            
        except Exception as e:
            self.logger.error(f"Failed to get all junctions: {str(e)}")
            return []
    
    async def batch_insert_vehicle_detections(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Batch insert vehicle detections for high-volume processing
        
        Args:
            detections (List[Dict[str, Any]]): List of detection records
            
        Returns:
            Dict[str, Any]: Operation result
        """
        try:
            result = self.supabase.table('vehicle_detections').insert(detections).execute()
            
            inserted_count = len(result.data) if result.data else 0
            self.logger.info(f"Batch inserted {inserted_count} vehicle detections")
            
            return {
                "success": True,
                "inserted_count": inserted_count,
                "message": f"Successfully inserted {inserted_count} detections"
            }
            
        except Exception as e:
            self.logger.error(f"Batch insert failed: {str(e)}")
            return {
                "success": False,
                "inserted_count": 0,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Supabase database connection health
        
        Returns:
            Dict[str, Any]: Health check result
        """
        try:
            # Simple query to test connection
            result = self.supabase.table('traffic_junctions') \
                .select('id') \
                .limit(1) \
                .execute()
            
            return {
                "database_connected": True,
                "connection_status": "healthy",
                "message": "Database connection successful",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return {
                "database_connected": False,
                "connection_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _simulate_signal_status(self, lane_number: int) -> str:
        """
        Simulate signal status for demo purposes
        
        Args:
            lane_number (int): Lane number
            
        Returns:
            str: Signal status (Green, Red, Yellow)
        """
        import random
        # Simple simulation based on lane number and randomness
        statuses = ['Green', 'Red', 'Yellow']
        weights = [0.3, 0.6, 0.1]  # More likely to be Red
        return random.choices(statuses, weights=weights)[0]
    
    def _get_lane_name(self, lane_number: int) -> str:
        """
        Convert lane number to descriptive name
        
        Args:
            lane_number (int): Lane number (1-4)
            
        Returns:
            str: Lane name
        """
        lane_names = {1: "North", 2: "South", 3: "East", 4: "West"}
        return lane_names.get(lane_number, f"Lane {lane_number}")
    
    def get_connection_info(self) -> Dict[str, str]:
        """
        Get database connection information (for debugging)
        
        Returns:
            Dict[str, str]: Connection details
        """
        return {
            "supabase_url": self.supabase_url,
            "service_key_configured": "Yes" if self.supabase_service_key else "No",
            "client_initialized": "Yes" if self.supabase else "No"
        }