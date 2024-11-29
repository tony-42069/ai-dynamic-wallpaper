import os
import sys
import time
from datetime import datetime
import platform
import random
import ctypes
from pathlib import Path
import json
import requests
from PIL import Image
from io import BytesIO

# Add immediate debugging
debug_log_path = Path(r"C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App\debug.log")
with open(debug_log_path, 'a', encoding='utf-8') as f:
    f.write(f"\n[{datetime.now()}] Script started\n")

class WallpaperManager:
    def __init__(self):
        try:
            self.base_path = Path(r"C:\Users\dsade\OneDrive\Desktop\Business\AI\Wallpaper App")
            self.images_path = self.base_path / "images"
            self.last_update_file = self.base_path / "last_update.txt"
            self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            self.headers = {"Authorization": "Bearer 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"}
            self.config = {
                "api_settings": {
                    "width": 1920,
                    "height": 1080
                }
            }
            
            # Create directories if they don't exist
            self.images_path.mkdir(parents=True, exist_ok=True)
            
            self.log_event("Wallpaper Manager initialized successfully")
            
        except Exception as e:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] Error initializing WallpaperManager: {str(e)}")
            raise

    def log_event(self, message):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            print(log_entry.strip())
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging: {str(e)}")

    def get_random_image(self):
        """Get a random image from the images folder"""
        try:
            image_files = [f for f in self.images_path.glob("*") if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
            if not image_files:
                self.log_event("No images found in images folder")
                return None
            return random.choice(image_files)
        except Exception as e:
            self.log_event(f"Error getting random image: {str(e)}")
            return None

    def set_wallpaper(self, image_path=None):
        """Set the wallpaper"""
        try:
            if image_path is None:
                image_path = self.get_random_image()
                if image_path is None:
                    return False
            
            if platform.system() == "Windows":
                ctypes.windll.user32.SystemParametersInfoW(20, 0, str(image_path), 3)
                self.log_event(f"Wallpaper set successfully to {image_path}")
                return True
            return False
        except Exception as e:
            self.log_event(f"Error setting wallpaper: {str(e)}")
            return False

    def update_wallpaper(self):
        """Main function to update the wallpaper"""
        try:
            self.log_event("Starting wallpaper update process")
            if self.set_wallpaper():
                self.log_event("Wallpaper update completed successfully")
                # Update last update time
                with open(self.last_update_file, "w") as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self.log_event("Failed to update wallpaper")
        except Exception as e:
            self.log_event(f"Error in update_wallpaper: {str(e)}")

    def generate_image(self, prompt):
        """Generate an image using the Hugging Face API"""
        max_retries = 5  # Increased retries
        retry_delay = 20  # Increased delay between retries
        
        self.log_event(f"Starting image generation with prompt: {prompt}")
        
        for attempt in range(max_retries):
            try:
                self.log_event(f"Attempt {attempt + 1} of {max_retries}")
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "width": self.config['api_settings']['width'],
                        "height": self.config['api_settings']['height'],
                        "num_inference_steps": 30,  # Reduced steps for faster generation
                        "guidance_scale": 7.5
                    }
                }
                
                self.log_event(f"Sending request to {self.api_url}")
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=180)  # Increased timeout
                self.log_event(f"Received response with status code: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        image_bytes = response.content
                        image = Image.open(BytesIO(image_bytes))
                        
                        # Save the image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        image_filename = f"wallpaper_{timestamp}.png"
                        image_path = self.images_path / image_filename
                        
                        image.save(image_path)
                        self.log_event(f"Successfully saved image to {image_path}")
                        self.log_prompt(image_filename, prompt)
                        
                        return image_path
                    except Exception as e:
                        self.log_event(f"Error processing image response: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        
                elif response.status_code in [503, 429, 500, 502, 504]:
                    self.log_event(f"Service error (attempt {attempt + 1}): {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = retry_delay * (attempt + 1)
                        self.log_event(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                else:
                    # If we get an unexpected error, try to use the most recent image
                    self.log_event(f"Error from API: {response.status_code} - {response.text}")
                    return self.get_most_recent_image()
                    
            except Exception as e:
                self.log_event(f"Request error: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    self.log_event(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                return self.get_most_recent_image()
        
        self.log_event("Max retries exceeded, using most recent image")
        return self.get_most_recent_image()

    def get_most_recent_image(self):
        """Get the most recently generated image"""
        try:
            image_files = list(self.images_path.glob("*.png"))
            if not image_files:
                self.log_event("No existing wallpaper images found")
                return None
            return max(image_files, key=os.path.getctime)
        except Exception as e:
            self.log_event(f"Error getting recent image: {str(e)}")
            return None

    def log_prompt(self, image_filename, prompt):
        try:
            with open(self.base_path / "prompts.log", "a", encoding='utf-8') as f:
                f.write(f"{image_filename}: {prompt}\n")
        except Exception as e:
            self.log_event(f"Error logging prompt: {str(e)}")

def main():
    print("Starting wallpaper updater...")
    try:
        manager = WallpaperManager()
        print("Manager initialized successfully")
        
        print("Generating new wallpaper...")
        prompts = [
            "cyberpunk cityscape at night, neon lights, holographic displays, flying cars, ultra detailed, synthwave colors, neo-optimistic future, 8k resolution, cinematic lighting --ar 16:9 --q 2",
            "solarpunk utopia, bioluminescent plants, clean energy technology, crystal spires, neon accents, hopeful future, ultra detailed, 8k resolution --ar 16:9 --q 2",
            "synthwave sunset over cyber city, retrowave aesthetics, neon grid, digital horizon, vibrant purple and blue, ultra detailed, 8k resolution --ar 16:9 --q 2",
            "neo-tokyo cityscape, cherry blossoms with neon lights, cyberpunk aesthetic, floating holograms, optimistic future, ultra detailed, 8k resolution --ar 16:9 --q 2",
            "digital dreamscape, vaporwave aesthetics, geometric patterns, neon synthwave sun, chrome and glass structures, ultra detailed, 8k resolution --ar 16:9 --q 2"
        ]
        
        prompt = random.choice(prompts)
        print(f"Selected prompt: {prompt}")
        image_path = manager.generate_image(prompt)
        
        if image_path:
            print("Setting new wallpaper...")
            if manager.set_wallpaper(image_path):
                print("Wallpaper updated successfully!")
            else:
                print("Failed to set wallpaper")
        else:
            print("Using previous wallpaper...")
            if manager.set_wallpaper():
                print("Previous wallpaper set successfully")
            else:
                print("Failed to set wallpaper")
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {str(e)}")