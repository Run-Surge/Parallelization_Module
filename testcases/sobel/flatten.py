import cv2
from glob import glob
import csv
import numpy as np

# ================= Configuration =================
IMAGE_SIZE = 32  # Change to 64, 128, etc. if needed
# =================================================

image_paths = sorted(glob("*.png"))
data = []

for img_path in image_paths:
    img = cv2.imread(img_path)
    if img is None:
        print(f"Skipping unreadable image: {img_path}")
        continue

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize to IMAGE_SIZE x IMAGE_SIZE
    resized = cv2.resize(gray, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_AREA)

    # Overwrite original with resized grayscale image
    cv2.imwrite(img_path, resized)

    # Flatten and collect
    flat = resized.flatten()
    data.append(flat)

# Prepare CSV header: p1 to pN
header = [f"p{i + 1}" for i in range(IMAGE_SIZE * IMAGE_SIZE)]

# Save to pixels.csv
with open("pixels.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data)
