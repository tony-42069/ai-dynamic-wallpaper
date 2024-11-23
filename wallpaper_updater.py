import os
import sys
import time
import requests
import schedule
from datetime import datetime
import platform
import random
import ctypes
from pathlib import Path
import json
import traceback
import torch
from PIL import Image
from io import BytesIO
import base64

# Add immediate debugging
debug_log_path = Path(r"C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App\debug.log")
with open(debug_log_path, 'a', encoding='utf-8') as f:
    f.write(f"\n[{datetime.now()}] Script started\n")

class UnsplashWallpaperManager:
    def __init__(self):
        try:
            self.base_path = Path(r"C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App")
            self.config_path = self.base_path / "config.json"
            self.images_path = self.base_path / "generated_images"
            self.logs_path = self.base_path / "logs"
            self.last_update_file = self.base_path / "last_update.txt"
            self.prompt_log_file = self.images_path / "image_prompts.txt"
            
            # Create directories
            self.images_path.mkdir(parents=True, exist_ok=True)
            self.logs_path.mkdir(parents=True, exist_ok=True)
            
            # Setup logging
            self.log_file = self.logs_path / f"wallpaper_log_{datetime.now().strftime('%Y%m%d')}.txt"
            
            # Load config
            self.load_config()
            
            # API endpoint for FLUX through Hugging Face
            self.api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
            self.headers = {
                "Authorization": f"Bearer {self.config['api_settings']['api_key']}"
            }
            
            self.prompt_styles = [
                "a breathtaking mountain vista at golden hour, volumetric god rays, ultra detailed landscape photography, award winning, 8k",
                "a serene Japanese garden with cherry blossoms, morning mist, masterful composition, professional photography",
                "a futuristic cityscape at night, neon lights reflecting off glass buildings, cinematic atmosphere, ultra detailed",
                "an ethereal cosmic scene with nebulas and galaxies, stunning colors, astronomical photography"
            ]
            
            self.negative_prompt = "ugly, blurry, low quality, distorted, disfigured, bad anatomy, watermark, signature, text"
            
            self.log_event("Wallpaper Manager initialized successfully")
            
        except Exception as e:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] Error initializing WallpaperManager: {str(e)}")
            raise

    def log_prompt(self, image_filename, prompt):
        """Log the prompt used for each image"""
        try:
            with open(self.prompt_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{image_filename}: {prompt}\n")
        except Exception as e:
            self.log_event(f"Error logging prompt: {str(e)}")

    def log_event(self, message):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            print(log_entry.strip())  # Console output
            
            # Ensure log directory exists
            self.logs_path.mkdir(parents=True, exist_ok=True)
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
                
            # Also write to debug log
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging: {str(e)}")
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] Logging Error: {str(e)}\n{traceback.format_exc()}\n")

    def load_config(self):
        try:
            if not self.config_path.exists():
                default_config = {
                    "schedule": {
                        "daily_update_time": "00:00"
                    },
                    "api_settings": {
                        "api_key": "YOUR_API_KEY",
                        "width": 3840,
                        "height": 2160
                    }
                }
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                self.config = default_config
            else:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except Exception as e:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] Config Load Error: {str(e)}")
            raise

    def get_last_update(self):
        try:
            if not self.last_update_file.exists():
                return None
            with open(self.last_update_file, 'r', encoding='utf-8') as f:
                date_str = f.read().strip()
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            self.log_event(f"Error reading last update: {str(e)}")
            return None

    def update_last_update_time(self):
        try:
            with open(self.last_update_file, 'w', encoding='utf-8') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            self.log_event(f"Error updating last update time: {str(e)}")

    def should_update_wallpaper(self):
        """Determine if we should update the wallpaper"""
        try:
            # Force update for testing
            return True
            
            last_update = self.get_last_update()
            now = datetime.now()
            
            if last_update is None:
                self.log_event("No previous update found - updating now")
                return True
                
            if last_update.date() < now.date():
                self.log_event("Last update was yesterday or earlier - updating now")
                return True
                
            scheduled_time = datetime.strptime(self.config['schedule']['daily_update_time'], '%H:%M').time()
            if last_update.date() == now.date() and now.time() >= scheduled_time and last_update.time() < scheduled_time:
                self.log_event("Past scheduled time for today - updating now")
                return True
                
            self.log_event(f"Last update was at {last_update}")
            return False
        except Exception as e:
            self.log_event(f"Error checking update status: {str(e)}")
            return True

    def generate_image(self, prompt):
        """Generate image using FLUX through Hugging Face API"""
        try:
            self.log_event(f"Starting image generation with prompt: {prompt}")
            self.log_event(f"Using API URL: {self.api_url}")
            
            # FLUX uses a simpler parameter set
            payload = {
                "inputs": prompt,
                "parameters": {
                    "guidance_scale": 3.5,
                    "num_inference_steps": 50,
                    "max_sequence_length": 512
                }
            }
            
            self.log_event(f"Sending request with payload: {json.dumps(payload, indent=2)}")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            self.log_event(f"Response status code: {response.status_code}")
            self.log_event(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                self.log_event(f"Error response content: {response.text}")
                # Add retry logic for model loading
                if response.status_code == 503 and "is currently loading" in response.text:
                    self.log_event("Model is loading, waiting 30 seconds...")
                    time.sleep(30)
                    self.log_event("Retrying request after wait...")
                    response = requests.post(self.api_url, headers=self.headers, json=payload)
                    self.log_event(f"Retry response status: {response.status_code}")
                    if response.status_code != 200:
                        self.log_event(f"Error from API after retry: {response.status_code} - {response.text}")
                        return None
                else:
                    return None
            
            try:
                # Hugging Face returns the image directly in the response content
                image = Image.open(BytesIO(response.content))
                self.log_event(f"Successfully created image of size: {image.size}")
                return image
            except Exception as img_error:
                self.log_event(f"Error processing image data: {str(img_error)}")
                self.log_event(f"Response content type: {type(response.content)}")
                self.log_event(f"First 100 bytes of response: {response.content[:100]}")
                return None
            
        except Exception as e:
            self.log_event(f"Error generating image: {str(e)}\n{traceback.format_exc()}")
            return None

    def update_wallpaper(self):
        """Main function to generate and set new wallpaper"""
        try:
            if not self.should_update_wallpaper():
                return False

            self.log_event("Starting wallpaper update process")
            
            # Generate prompt
            prompt = random.choice(self.prompt_styles)
            self.log_event(f"Generated prompt: {prompt}")
            
            # Generate image
            self.log_event("Calling image generation...")
            image = self.generate_image(prompt)
            
            if image is None:
                self.log_event("Image generation failed")
                return False
            
            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"wallpaper_{timestamp}.png"
            image_path = self.images_path / image_filename
            
            self.log_event(f"Saving image to {image_path}")
            image.save(image_path)
            
            # Log the prompt used for this image
            self.log_prompt(image_filename, prompt)
            
            # Set as wallpaper
            self.log_event("Setting as wallpaper")
            ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 0)
            
            # Update last update time
            self.update_last_update_time()
            
            self.log_event("Wallpaper updated successfully")
            return True
            
        except Exception as e:
            self.log_event(f"Error updating wallpaper: {str(e)}")
            return False

def main():
    try:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] Main function started\n")
        
        manager = UnsplashWallpaperManager()
        
        # Single update and exit - better for Task Scheduler
        manager.update_wallpaper()
        
    except Exception as e:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] Critical Error: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now()}] Fatal Error: {str(e)}\n{traceback.format_exc()}")