from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List

from ultralytics import YOLO
from fastapi import WebSocket

from backend.config.settings import HISTORY_MAX, HEATMAP_POINTS_MAX, PATH_HISTORY_MAX

loaded_models:     Dict[str, YOLO]            = {}
latest_results:    Dict[str, dict]            = {}
detection_history: Dict[str, deque]           = defaultdict(lambda: deque(maxlen=HISTORY_MAX))
heatmap_points:    Dict[str, list]            = defaultdict(list)
path_history:      Dict[str, deque]           = defaultdict(lambda: deque(maxlen=PATH_HISTORY_MAX))
ws_clients:        Dict[str, List[WebSocket]] = defaultdict(list)
processor_status:  Dict[str, str]             = {}
alert_history:     list                       = []
alert_cooldowns:   Dict[str, datetime]        = {}
complaints:        list                       = []
