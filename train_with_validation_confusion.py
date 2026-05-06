import os
import csv
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt
from collections import Counter
import time
from torch.amp import autocast, GradScaler


# -----------------------------
# Improved Grad-CAM Save Function
# -----------------------------
def save_gradcam(img_tensor, cam, save_path, alpha=0.4):
    """
    Save Grad-CAM overlay and heatmap images.

    img_tensor: original image tensor (C,H,W)
    cam: Grad-CAM mask (H,W) normalized between 0-1
    save_path: base path for saving (will generate overlay + heatmap)
    alpha: transparency for overlay
    """
    # Convert tensor to numpy image
    img_np = img_tensor.permute(1, 2, 0).cpu().numpy()
    img_np = (img_np * 255).astype(np.uint8)
    
    # Check for invalid image dimensions (prevent OpenCV resize error)
    if img_np.shape[0] == 0 or img_np.shape[1] == 0:
        print(f"⚠️ Skipping Grad-CAM save for {save_path} (invalid image dimensions: {img_np.shape})")
        return

    # Resize CAM to match image size
    if cam is None or cam.size == 0:
        print(f"⚠️ Skipping Grad-CAM save for {save_path} (empty CAM)")
        return

    cam_resized = cv2.resize(cam, (img_np.shape[1], img_np.shape[0]))
    cam_resized = (cam_resized * 255).astype(np.uint8)

    # Apply colormap
    heatmap = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)

    # Overlay with transparency
    overlay = cv2.addWeighted(img_np, 1 - alpha, heatmap, alpha, 0)

    # Save both versions
    cv2.imwrite(save_path.replace(".jpg", "_overlay.jpg"), overlay)
    cv2.imwrite(save_path.replace(".jpg", "_heatmap.jpg"), heatmap)

# -----------------------------
# 1. Transformations
# -----------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# -----------------------------
# 2. Load Dataset
# -----------------------------
if __name__ == "__main__":
    dataset_path = os.path.join(os.getcwd(), "Dataset", "Combined_Textures")
    dataset = datasets.ImageFolder(dataset_path, transform=transform)
    classes = dataset.classes
    num_classes = len(classes)

    print("✅ Detected Classes:", classes)
    print("Number of classes:", num_classes)

    # Explicit hazard mapping for navigation assistance goals
    surface_hazard = {
        "aluminium_foil": {"severity": "unsafe", "description": "slippery surface"},
        "brown_bread": {"severity": "safe", "description": "normal surface"},
        "corduroy": {"severity": "caution", "description": "uneven surface"},
        "cotton": {"severity": "safe", "description": "normal surface"},
        "cracker": {"severity": "caution", "description": "fragile surface"},
        "linen": {"severity": "safe", "description": "normal surface"},
        "orange_peel": {"severity": "caution", "description": "textured surface"},
        "sandpaper": {"severity": "unsafe", "description": "abrasive surface"},
        "sponge": {"severity": "caution", "description": "soft or wet-looking surface"},
        "styrofoam": {"severity": "unsafe", "description": "unstable surface"},
    }

    def get_hazard_meta(cls_name):
        return surface_hazard.get(cls_name, {"severity": "unknown", "description": "unknown surface"})

    print("✅ Hazard mapping loaded for navigation risk categories.")

    # -----------------------------
    # 3. Train/Validation Split
    # -----------------------------
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    # -----------------------------
    # 4. Define CNN (ResNet-50 with pretrained weights)
    # -----------------------------
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, num_classes)

    labels_all = [label for _, label in dataset.samples]
    weights = compute_class_weight('balanced', classes=np.arange(num_classes), y=labels_all)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    weights = torch.tensor(weights, dtype=torch.float).to(device)   # FIXED: move weights to GPU

    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = optim.Adam(model.parameters(), lr=0.0005)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    # Mixed precision scaler
    scaler = GradScaler()

    # -----------------------------
    # 5. Training + Validation Loop with Early Stopping + Logging
    # -----------------------------
    epochs = 50
    patience = 5
    best_acc = 0
    counter = 0

    train_losses, val_accuracies = [], []
    all_preds, all_labels = [], []

    model.to(device)

    start_time = time.time()

    for epoch in range(epochs):
        epoch_start = time.time()

        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            running_loss += loss.item()
        avg_loss = running_loss / len(train_loader)
        train_losses.append(avg_loss)

        # Validation
        model.eval()
        correct, total = 0, 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                    outputs = model(images)

                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                all_preds.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        val_acc = 100 * correct / total
        val_accuracies.append(val_acc)

        epoch_end = time.time()
        epoch_duration = epoch_end - epoch_start

        # GPU memory usage logging
        if torch.cuda.is_available():
            mem_alloc = torch.cuda.memory_allocated(device) / (1024 ** 2)
            mem_reserved = torch.cuda.memory_reserved(device) / (1024 ** 2)
            mem_max = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}, Val Acc: {val_acc:.2f}% "
              f"| ⏱ {epoch_duration:.2f}s "
              f"| GPU: {mem_alloc:.1f}MB allocated, {mem_reserved:.1f}MB reserved, {mem_max:.1f}MB peak (AMP enabled)")
        else:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}, Val Acc: {val_acc:.2f}% | ⏱ {epoch_duration:.2f}s (CPU mode)")

        scheduler.step()

        # Early stopping check
        if val_acc > best_acc:
            best_acc = val_acc
            counter = 0
            torch.save(model.state_dict(), "best_model.pth")
        else:
            counter += 1
            if counter >= patience:
                print(f"⏹ Early stopping at epoch {epoch+1}")
                break

    total_time = time.time() - start_time
    print(f"🏁 Total training time: {total_time/60:.2f} minutes")
    # -----------------------------
    # 5b. Training Dashboard Export
    # -----------------------------
    plt.figure(figsize=(10,5))
    plt.plot(range(1, len(train_losses)+1), train_losses, label="Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training Loss Curve")
    plt.legend()
    plt.savefig("training_loss_curve.png")
    plt.close()

    plt.figure(figsize=(10,5))
    plt.plot(range(1, len(val_accuracies)+1), val_accuracies, label="Validation Accuracy", color="orange")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.title("Validation Accuracy Curve")
    plt.legend()
    plt.savefig("validation_accuracy_curve.png")
    plt.close()

    print("✅ Training dashboard exported: training_loss_curve.png & validation_accuracy_curve.png")

    # -----------------------------
    # 6. Confusion Matrix + Per-Class Accuracy
    # -----------------------------
    cm = confusion_matrix(all_labels, all_preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
    disp.plot(cmap=plt.cm.Blues, xticks_rotation=45)
    plt.title("Confusion Matrix - Validation Set")
    plt.savefig("training_confusion_matrix.png")
    plt.close()

    cm_diag = np.diag(cm)
    cm_sum = cm.sum(axis=1)
    per_class_acc = cm_diag / cm_sum

    print("\n📊 Per-Class Accuracy:")
    for cls, acc in zip(classes, per_class_acc):
        print(f"{cls}: {acc*100:.2f}%")

    hazard_accuracy = {"safe": [], "caution": [], "unsafe": [], "unknown": []}
    for cls, acc in zip(classes, per_class_acc):
        severity = get_hazard_meta(cls)["severity"]
        hazard_accuracy.setdefault(severity, []).append(acc)

    print("\n📌 Hazard-Grouped Accuracy:")
    for severity in ["safe", "caution", "unsafe", "unknown"]:
        values = hazard_accuracy.get(severity, [])
        if values:
            print(f"{severity.title()} surface avg accuracy: {np.mean(values)*100:.2f}%")
        else:
            print(f"{severity.title()} surface avg accuracy: N/A")

    # -----------------------------
    # 7. Confusion Summary Generator
    # -----------------------------
    confusion_pairs = [(classes[t], classes[p]) for t, p in zip(all_labels, all_preds) if t != p]
    pair_counts = Counter(confusion_pairs)
    top_confusions = pair_counts.most_common(10)

    print("\n🔝 Top 10 Confusion Pairs (Actual → Predicted):")
    for (actual, predicted), count in top_confusions:
        print(f"{actual} → {predicted}: {count} times")

    # -----------------------------
    # 8. Save Diagnostics to CSV
    # -----------------------------
    with open("diagnostics.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Class", "Accuracy (%)", "Hazard Severity", "Description"])
        for cls, acc in zip(classes, per_class_acc):
            hazard_meta = get_hazard_meta(cls)
            writer.writerow([cls, f"{acc*100:.2f}", hazard_meta["severity"], hazard_meta["description"]])
        writer.writerow([])
        writer.writerow(["Actual", "Predicted", "Count"])
        for (actual, predicted), count in top_confusions:
            writer.writerow([actual, predicted, count])
    print("✅ Diagnostics saved to diagnostics.csv")

    # -----------------------------
    # 10. Final AMP Efficiency Summary
    # -----------------------------
    if torch.cuda.is_available():
        avg_epoch_time = total_time / len(val_accuracies)
        peak_mem = torch.cuda.max_memory_allocated(device) / (1024 ** 2)

        print("\n⚡ AMP Efficiency Summary:")
        print(f"Average epoch time: {avg_epoch_time:.2f} seconds")
        print(f"Peak GPU memory usage: {peak_mem:.1f} MB")
        print("Mixed Precision (AMP) was enabled throughout training.")


    # -----------------------------
    # 9. Batch Grad-CAM Explorer
    # -----------------------------
    def grad_cam(model, image_tensor, target_class, pred_class):
        model.eval()
        gradients, activations = [], []

        def backward_hook(module, grad_input, grad_output):
            gradients.append(grad_output[0])
        def forward_hook(module, input, output):
            activations.append(output)

        target_layer = model.layer4[-1].conv3
        target_layer.register_forward_hook(forward_hook)
        target_layer.register_full_backward_hook(backward_hook)

        # Forward pass with autocast for efficiency
        with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
            output = model(image_tensor.unsqueeze(0).to(device))


        # Proper target tensor
        target = torch.tensor([target_class], dtype=torch.long, device=device)
        loss = F.cross_entropy(output, target)  

        # Backward pass
        model.zero_grad()
        loss.backward()

        grads = gradients[0].mean(dim=(2, 3), keepdim=True)
        act = activations[0]
        cam = (act * grads).sum(dim=1).squeeze().detach().cpu().numpy()
        cam = np.maximum(cam, 0)
        cam = cam / (cam.max() + 1e-8)

        return cam

    # -----------------------------
    # Grad-CAM Export Section
    # -----------------------------
    os.makedirs("GradCAM_Reports", exist_ok=True)

    for idx, (img, label) in enumerate(val_dataset):
        img = img.to(device)

        # Forward pass without gradients (just to get prediction)
        with torch.no_grad():
            with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                output = model(img.unsqueeze(0))
            pred_class = output.argmax(dim=1).item()

        if pred_class != label:  # only save misclassified samples
            # Now call grad_cam WITH gradients enabled
            cam = grad_cam(model, img, label, pred_class)

            actual = classes[label]
            predicted = classes[pred_class] 
            save_path = f"GradCAM_Reports/{actual}_to_{predicted}_{idx}.jpg"

            save_gradcam(img.cpu(), cam, save_path, alpha=0.3)

            # Free memory
            del cam, img, output
            torch.cuda.empty_cache()



