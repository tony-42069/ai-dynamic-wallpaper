import torch
from diffusers import FluxPipeline
from huggingface_hub import login, snapshot_download
import os
from pathlib import Path

# Set up cache directory in OneDrive
cache_dir = Path(os.path.expanduser("~/OneDrive/AI Models Cache"))
cache_dir.mkdir(parents=True, exist_ok=True)

# Set environment variables for caching
os.environ["HF_HOME"] = str(cache_dir)
os.environ["TRANSFORMERS_CACHE"] = str(cache_dir / "transformers")
os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_dir / "hub")

# Login to Hugging Face
login(token="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")

print(f"Using cache directory: {cache_dir}")
print("Starting model download (this may take a while)...")

# Download model files sequentially with specific cache directory
model_path = snapshot_download(
    "black-forest-labs/FLUX.1-dev",
    local_files_only=False,
    resume_download=True,
    max_workers=1,  # Download sequentially
    cache_dir=str(cache_dir / "hub")
)

print(f"Model downloaded to: {model_path}")
print("Initializing pipeline...")

# Initialize pipeline with float16 instead of bfloat16
pipe = FluxPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    local_files_only=True,
    cache_dir=str(cache_dir / "hub")
)
pipe.enable_model_cpu_offload()

print("Model loaded successfully!")

# Test with the example prompt
prompt = "A cat holding a sign that says hello world"
print(f"Generating image with prompt: {prompt}")

image = pipe(
    prompt,
    height=1024,
    width=1024,
    guidance_scale=3.5,
    num_inference_steps=50,
    max_sequence_length=512,
    generator=torch.Generator("cpu").manual_seed(0)
).images[0]

image.save("flux-test.png")
print("Image generated and saved as flux-test.png!")
