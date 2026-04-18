import os
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from PIL import Image

# -----------------------------
# 1. Transformations
# -----------------------------
transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# -----------------------------
# 2. Load Dataset
# -----------------------------
dataset_path = os.path.join(os.getcwd(), "Dataset", "Combined_Textures")
dataset = datasets.ImageFolder(dataset_path, transform=transform)
classes = dataset.classes
num_classes = len(classes)

train_loader = DataLoader(dataset, batch_size=32, shuffle=True)

# -----------------------------
# 3. Define CNN (ResNet18)
# -----------------------------
cnn_model = models.resnet18(weights=None)
cnn_model.fc = nn.Linear(cnn_model.fc.in_features, num_classes)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(cnn_model.parameters(), lr=0.001)

# -----------------------------
# 4. Training Loop
# -----------------------------
epochs = 10
for epoch in range(epochs):
    running_loss = 0.0
    for images, labels in train_loader:
        optimizer.zero_grad()
        outputs = cnn_model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
    avg_loss = running_loss / len(train_loader)
    print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")

# -----------------------------
# 5. Save Model
# -----------------------------
torch.save(cnn_model.state_dict(), "texture_model_combined.pth")
print("✅ Model saved as texture_model_combined.pth")

# -----------------------------
# 6. Quick Test
# -----------------------------
# Pick one sample image from your dataset
test_img_path = os.path.join(dataset_path, "fabric", os.listdir(os.path.join(dataset_path, "fabric"))[0])

img = Image.open(test_img_path)
cnn_model.eval()
with torch.no_grad():
    output = cnn_model(transform(img).unsqueeze(0))
    _, predicted = torch.max(output, 1)
    print("Predicted class:", classes[predicted.item()])
    print("Ground truth folder:", "fabric")
