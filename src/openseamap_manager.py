import os
import requests
from math import floor, ceil, log, tan, radians, cos, pi, atan, sinh
from kivy.network.urlrequest import UrlRequest

class OpenSeaMapManager:
    
    def __init__(self, cache_dir='../assets/openseamap_cache'):
        self.cache_dir = cache_dir
        self.title_servers = [
            "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
            "https://t1.openseamap.org/seamark/{z}/{x}/{y}.png",
        ]
        os.makedirs(self.cache_dir, exist_ok=True)
        
    
    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
        return (xtile, ytile)
    
    def num2deg(self, xtile, ytile, zoom):
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
        lat_deg = lat_rad * 180.0 / pi
        return (lat_deg, lon_deg)
    
    def get_tile_bounds(self, lat1, lon1, lat2, lon2, zoom):
        x1, y1 = self.deg2num(max(lat1, lat2), min(lon1, lon2), zoom)
        x2, y2 = self.deg2num(min(lat1, lat2), max(lon1, lon2), zoom)
        return {
            'x_min': min(x1, x2),
            'x_max': max(x1, x2),
            'y_min': min(y1, y2),
            'y_max': max(y1, y2),
            'zoom': zoom
        }
        
        
    def get_tile_path(self, x, y, z):
        return os.path.join(self.cache_dir, f"{z}_{x}_{y}.png")
    
    def tile_exists(self, x, y, z):
        return os.path.exists(self.get_tile_path(x, y, z))
    
    def download_tile(self, x, y, z, callback=None):
        tile_path = self.get_tile_path(x, y, z)
        
        os.makedirs(os.path.dirname(tile_path), exist_ok=True)
        
        url = self.title_servers[0].format(z=z, x=x, y=y)
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(tile_path, 'wb') as f:
                    f.write(response.content)
                if callback:
                    callback(success=True, path=tile_path)
                return True
        except Exception as e:
            print(f"Error downloading tile {z}/{x}/{y}: {e}")
            
        if callback:
            callback(success=False, path=None)
            return False
    
    def download_area(self, lat1, lon1, lat2, lon2, min_zoom=8, max_zoom=15, progress_callback=None):
        total_tiles = 0
        downloaded_tiles = 0
        
        for zoom in range(min_zoom, max_zoom + 1):
            bounds = self.get_tile_bounds(lat1, lon1, lat2, lon2, zoom)
            tiles_count = (bounds['x_max'] - bounds['x_min'] + 1) * (bounds['y_max'] - bounds['y_min'] + 1)
            total_tiles += tiles_count
            
        print(f"Total tiles to download: {total_tiles}")
        
        for zoom in range(min_zoom, max_zoom + 1):
            bounds = self.get_tile_bounds(lat1, lon1, lat2, lon2, zoom)
            for x in range(bounds['x_min'], bounds['x_max'] + 1):
                for y in range(bounds['y_min'], bounds['y_max'] + 1):
                    if not self.tile_exists(x, y, zoom):
                        success = self.download_tile(x, y, zoom)
                        if success:
                            downloaded_tiles += 1
                    else:
                        downloaded_tiles += 1
                    
                    if progress_callback:
                        progress = downloaded_tiles / total_tiles
                        progress_callback(progress)

        print(f"Download complete. {downloaded_tiles}/{total_tiles} tiles downloaded.")
        return downloaded_tiles
    
    def get_available_areas(self):
        areas = []
        
        if os.path.exists(self.cache_dir):
            for zoom_dir in os.listdir(self.cache_dir):
                zoom_path = os.path.join(self.cache_dir, zoom_dir)
                if os.path.isdir(zoom_path) and zoom_dir.isdigit():
                    zoom_level = int(zoom_dir)
                    x_dirs = [d for d in os.listdir(zoom_path) if os.path.isdir(os.path.join(zoom_path, d))]
                    if x_dirs:
                        areas.append({
                            'zoom': zoom_level,
                            "tiles": len(x_dirs)
                        })
                        
        return areas
    
    def clear_cache(self):
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            print("Cache cleared.")
            
FRANCE_COASTAL_AREAS = {
    "Cote d'Azure": {
        "boundes": (43.4, 6.5, 43.8, 7.4),
        "description": "Area covering the French Riviera including Nice, Cannes, and Monaco."
        },
    "Bretagne Sud": {
        "boundes": (47.0, -5.0, 48.0, -2.5),
        "description": "Area covering the southern part of Brittany including Lorient and Vannes."
        }
    }