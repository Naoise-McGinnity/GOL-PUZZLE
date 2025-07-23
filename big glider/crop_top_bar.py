import os
from PIL import Image

folder = r"c:\Users\Walpha\Desktop\Naoise_Codecrafters\big glider"
crop_height = 32

for filename in os.listdir(folder):
    if filename.lower().endswith('.png'):
        path = os.path.join(folder, filename)
        img = Image.open(path)
        width, height = img.size
        cropped = img.crop((0, crop_height, width, height))
        cropped.save(path)
        print(f"Cropped {filename}")