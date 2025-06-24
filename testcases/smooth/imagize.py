import csv
import cv2
import numpy as np

# ================= Configuration =================
IMAGE_SIZE = 32  # Set to 32, 64, etc. depending on input CSV
INPUT_FILE = 'filtered.csv'
# =================================================

def save_image(image_2d, index):
    img_array = np.array(image_2d, dtype=np.uint8)
    resized = cv2.resize(img_array, (IMAGE_SIZE, IMAGE_SIZE), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'image{index + 1}.png', resized)

def main():
    with open(INPUT_FILE, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    for idx, row in enumerate(rows):
        if len(row) != IMAGE_SIZE * IMAGE_SIZE:
            print(f"Skipping row {idx+1}: expected {IMAGE_SIZE * IMAGE_SIZE} pixels, got {len(row)}")
            continue

        try:
            pixels = [float(x.strip()) for x in row]
        except ValueError:
            print(f"Skipping row {idx+1}: non-numeric data found")
            continue

        # reshape to IMAGE_SIZE x IMAGE_SIZE
        img = [pixels[i * IMAGE_SIZE:(i + 1) * IMAGE_SIZE] for i in range(IMAGE_SIZE)]

        # save image
        save_image(img, idx)

if __name__ == '__main__':
    main()
