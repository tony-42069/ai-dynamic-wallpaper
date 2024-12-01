import os
import sys
import time
from datetime import datetime
import platform
import random
import ctypes
from pathlib import Path
import torch
from diffusers import FluxPipeline
from PIL import Image
from huggingface_hub import login

# Login to Hugging Face
login(token="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")

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
            
            # Create directories if they don't exist
            self.images_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize FLUX pipeline exactly as in example
            self.log_event("Initializing FLUX pipeline...")
            self.pipe = FluxPipeline.from_pretrained(
                "black-forest-labs/FLUX.1-dev", 
                torch_dtype=torch.bfloat16,
                use_auth_token="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"
            )
            self.pipe.enable_model_cpu_offload()
            self.log_event("FLUX pipeline initialized successfully")
            
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

    def generate_image(self, prompt):
        """Generate an image using FLUX"""
        try:
            self.log_event(f"Starting image generation with prompt: {prompt}")
            
            # Generate image with FLUX exactly as in example
            image = self.pipe(
                prompt,
                height=1080,  # Changed for wallpaper aspect ratio
                width=1920,   # Changed for wallpaper aspect ratio
                guidance_scale=3.5,
                num_inference_steps=50,
                max_sequence_length=512,
                generator=torch.Generator("cpu").manual_seed(random.randint(0, 1000000))
            ).images[0]
            
            # Save the image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"wallpaper_{timestamp}.png"
            image_path = self.images_path / image_filename
            
            image.save(image_path)
            self.log_event(f"Successfully saved image to {image_path}")
            
            return image_path
            
        except Exception as e:
            self.log_event(f"Error generating image: {str(e)}")
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

    def set_wallpaper(self, image_path=None):
        """Set the wallpaper"""
        try:
            if image_path is None:
                image_path = self.get_most_recent_image()
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

def main():
    print("Starting wallpaper updater...")
    try:
        manager = WallpaperManager()
        print("Manager initialized successfully")
        
        print("Generating new wallpaper...")
        prompts = [
            "a cyberpunk cityscape at dusk, neon-lit skyscrapers reflecting in rain puddles, holographic advertisements floating in the air, flying vehicles with light trails, cinematic, ultra detailed",
            "solarpunk utopia, bioluminescent crystal towers, floating gardens with exotic plants, clean energy tech integrated with nature, ethereal lighting",
            "synthwave dreamscape, digital grid horizon, chrome mountains, neon sun setting behind geometric shapes, retro-futuristic aesthetic",
            "neo-tokyo street scene, cherry blossom petals floating through neon rain, holographic shop signs, cyberpunk fashion, moody atmospheric lighting",
            "vaporwave paradise, ancient statues with neon outlines, digital waterfalls, chrome spheres floating in pink sky, retro-future aesthetic"
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