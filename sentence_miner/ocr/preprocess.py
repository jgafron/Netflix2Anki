import cv2
import numpy as np

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    scale_factor = 1.5  
    width = int(gray.shape[1] * scale_factor)
    height = int(gray.shape[0] * scale_factor)
    resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)

    blurred = cv2.GaussianBlur(resized, (5, 5), 0)

    _, binary_img = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((1, 1), np.uint8)
    denoised = cv2.dilate(binary_img, kernel, iterations=1)
    denoised = cv2.erode(denoised, kernel, iterations=1)

    processed_image_path = 'processed_image.png'
    cv2.imwrite(processed_image_path, denoised)

    return processed_image_path