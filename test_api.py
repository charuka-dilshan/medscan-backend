import requests

# The URL where your FastAPI server is running
url = "http://127.0.0.1:8000/predict"

# Path to a test image
image_path = "ml/dataset/val/paracetamol/test_pill.jpg"

with open(image_path, "rb") as f:
    files = {"file": f}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())