import os
import time
import requests
import schedule
from datetime import datetime
import platform
import random
import ctypes
from pathlib import Path
import json

class FluxWallpaperManager:
    def __init__(self):
        """Initialize the wallpaper manager with configuration"""
        self.base_path = Path(r"C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App")
        self.config_path = self.base_path / "config.json"
        self.images_path = self.base_path / "generated_images"
        self.logs_path = self.base_path / "logs"
        self.last_update_file = self.base_path / "last_update.txt"
        
        # Load configuration
        self.load_config()
        
        # API endpoints
        self.generation_endpoint = "https://api.bfl.ml/v1/flux-pro-1.1"
        self.result_endpoint = "https://api.bfl.ml/v1/get_result"
        
        # Create necessary directories
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.log_file = self.logs_path / f"wallpaper_log_{datetime.now().strftime('%Y%m%d')}.txt"

    def get_last_update_date(self):
        """Get the date of the last wallpaper update"""
        if self.last_update_file.exists():
            try:
                with open(self.last_update_file, 'r') as f:
                    return datetime.strptime(f.read().strip(), '%Y-%m-%d').date()
            except:
                return None
        return None

    def update_last_update_date(self):
        """Update the last update date to today"""
        with open(self.last_update_file, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))

    def should_update_today(self):
        """Check if we should update the wallpaper today"""
        last_update = self.get_last_update_date()
        today = datetime.now().date()
        
        if last_update is None or last_update < today:
            scheduled_time = datetime.strptime(self.config['schedule']['daily_update_time'], '%H:%M').time()
            current_time = datetime.now().time()
            
            # Update if it's past the scheduled time
            if current_time >= scheduled_time:
                self.log_event("Time for daily wallpaper update")
                return True
            else:
                self.log_event(f"Waiting for scheduled time: {self.config['schedule']['daily_update_time']}")
                return False
        else:
            self.log_event("Wallpaper already updated today")
            return False

    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "api_settings": {
                "api_key": "8188616a-0587-4268-9816-48189620b1dd",
                "width": 1440,
                "height": 896
            },
            "schedule": {
                "daily_update_time": "00:00"
            },
            "storage": {
                "keep_images_days": 7
            },
            "prompts": {
                "scenes": [
                    "a majestic mountain range at sunset with dramatic clouds",
                    "an ethereal forest with bioluminescent plants and floating lights",
                    "a futuristic cityscape with neon lights reflecting off glass buildings",
                    "an abstract cosmic scene with swirling galaxies and nebulas",
                    "a serene Japanese garden with cherry blossoms and a stone path"
                ],
                "styles": [
                    "in a cinematic style with dramatic lighting",
                    "with volumetric fog and ray tracing",
                    "rendered in stunning 8K detail",
                    "with hyperrealistic textures",
                    "in an ethereal dreamlike style"
                ]
            },
            "custom_prompts": []
        }

        if not self.config_path.exists():
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            self.config = default_config
        else:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def generate_prompt(self):
        """Generate a random prompt using configuration"""
        if self.config['custom_prompts'] and random.random() < 0.3:
            prompt = random.choice(self.config['custom_prompts'])
        else:
            scene = random.choice(self.config['prompts']['scenes'])
            style = random.choice(self.config['prompts']['styles'])
            prompt = f"{scene}, {style}, masterpiece quality, perfect for desktop wallpaper"
        
        self.log_event(f"Generated prompt: {prompt}")
        return prompt

    def log_event(self, message):
        """Log events with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        print(log_entry.strip())
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def update_wallpaper(self):
        """Main function to generate and set new wallpaper"""
        if not self.should_update_today():
            return

        self.log_event("Starting wallpaper update process")
        
        try:
            # Generate image
            headers = {
                'accept': 'application/json',
                'x-key': self.config['api_settings']['api_key'],
                'Content-Type': 'application/json',
            }
            
            payload = {
                'prompt': self.generate_prompt(),
                'width': self.config['api_settings']['width'],
                'height': self.config['api_settings']['height'],
            }
            
            # Submit generation request
            self.log_event("Submitting generation request to Flux API...")
            response = requests.post(
                self.generation_endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                self.log_event(f"Error submitting request: {response.status_code} - {response.text}")
                return
            
            request_id = response.json()["id"]
            self.log_event(f"Generation request submitted successfully. ID: {request_id}")
            
            # Poll for results
            while True:
                time.sleep(5)
                result = requests.get(
                    self.result_endpoint,
                    headers={'accept': 'application/json', 'x-key': self.config['api_settings']['api_key']},
                    params={'id': request_id},
                ).json()
                
                if result["status"] == "Ready":
                    image_url = result['result']['sample']
                    self.log_event("Image generated successfully")
                    
                    # Download and save image
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_path = self.images_path / f"wallpaper_{timestamp}.png"
                        
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        
                        # Set as wallpaper
                        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 3)
                        self.log_event("Wallpaper set successfully")
                        
                        # Update last update date
                        self.update_last_update_date()
                        
                        self.log_event("Wallpaper update completed successfully")
                        break
                
                self.log_event(f"Generation status: {result['status']}")
                
        except Exception as e:
            self.log_event(f"Error during wallpaper update: {str(e)}")

def main():
    manager = FluxWallpaperManager()
    
    # Schedule daily check
    schedule.every(1).minutes.do(manager.update_wallpaper)
    
    # Run initial check
    manager.update_wallpaper()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
    