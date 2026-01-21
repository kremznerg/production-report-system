"""
API Client for fetching production event data.
"""

import requests
import logging
from datetime import date
from typing import List, Dict, Any
from pydantic import ValidationError

from ..config import settings
from ..models import ProductionEvent

logger = logging.getLogger(__name__)

class APIClient:
    """Client for production event API."""
    
    def __init__(self):
        self.base_url = settings.API_BASE_URL
        self.timeout = 10
    
    def fetch_events(self, machine_id: str, target_date: date) -> List[Dict[str, Any]]:
        """
        Fetch production events for a specific machine and date.
        
        Args:
            machine_id: Machine identifier (e.g., 'PM1', 'PM2')
            target_date: Date to fetch data for
            
        Returns:
            List of event dictionaries
            
        Raises:
            requests.HTTPError: On API error
            requests.Timeout: On timeout
        """
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{self.base_url}/events/{machine_id}/{date_str}"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            raise Exception(f"API timeout: {url}")
        except requests.HTTPError as e:
            raise Exception(f"API error: {e.response.status_code} - {url}")
    
    def validate_events(self, raw_events: List[Dict[str, Any]]) -> List[ProductionEvent]:
        """
        Validate raw API data using Pydantic models.
        
        Args:
            raw_events: Raw JSON data from API
            
        Returns:
            List of validated ProductionEvent objects
        """
        validated = []
        for event in raw_events:
            try:
                validated.append(ProductionEvent(**event))
            except ValidationError as e:
                logger.warning(f"Validation error, skipping event: {e}")
        
        return validated
