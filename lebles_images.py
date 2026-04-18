# import os, shutil

# base_dir = "Dataset/dtd/images/"
# labels_dir = "Dataset/dtd/labels/"
# output_dir = "Dataset/DTD_ImageFolder/"

# os.makedirs(output_dir, exist_ok=True)

# for label_file in os.listdir(labels_dir):
#     class_name = label_file.split("_")[0]  # e.g. 'cracked'
#     class_dir = os.path.join(output_dir, class_name)
#     os.makedirs(class_dir, exist_ok=True)

#     with open(os.path.join(labels_dir, label_file)) as f:
#         for line in f:
#             img_name = line.strip() + ".jpg"
#             src = os.path.join(base_dir, img_name)
#             dst = os.path.join(class_dir, img_name)
#             if os.path.exists(src):
#                 shutil.copy(src, dst)

# import os, shutil, pandas as pd

# labels_df = pd.read_csv("Dataset/FMD_Labels.csv")  # adjust if .mat file
# src_dir = "Dataset/image/"
# dst_dir = "Dataset/FMD_ImageFolder/"

# for _, row in labels_df.iterrows():
#     img_name = row["filename"]
#     label = row["category"]

#     class_dir = os.path.join(dst_dir, label)
#     os.makedirs(class_dir, exist_ok=True)

#     src = os.path.join(src_dir, img_name)
#     dst = os.path.join(class_dir, img_name)
#     if os.path.exists(src):
#         shutil.copy(src, dst)

# from torchvision import datasets
# dataset = datasets.ImageFolder("Dataset/Combined_Textures/")
# print("Classes:", dataset.classes)
# print("Number of classes:", len(dataset.classes))

# 
# import os

# dataset_path = "Dataset/Combined_Textures"
# class_names = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
# print("Classes:", class_names)
# print("Number of classes:", len(class_names))

# import os
# from PIL import Image

# dataset_path = "Dataset/Combined_Textures"
# default_ext = ".png"  # or ".jpg" depending on your dataset

# for cls in os.listdir(dataset_path):
#     cls_path = os.path.join(dataset_path, cls)
#     if os.path.isdir(cls_path):
#         for fname in os.listdir(cls_path):
#             fpath = os.path.join(cls_path, fname)
#             if os.path.isfile(fpath) and '.' not in fname:
#                 try:
#                     # Try opening with PIL to confirm it's an image
#                     Image.open(fpath)
#                     new_fpath = fpath + default_ext
#                     os.rename(fpath, new_fpath)
#                     print(f"Renamed: {fname} → {os.path.basename(new_fpath)}")
#                 except:
#                     print(f"Skipped non-image file: {fname}")

# import os

# dataset_path = "Dataset/Combined_Textures"

# for cls in os.listdir(dataset_path):
#     cls_path = os.path.join(dataset_path, cls)
#     if os.path.isdir(cls_path):
#         for fname in os.listdir(cls_path):
#             if os.path.isfile(os.path.join(cls_path, fname)) and '.' not in fname:
#                 print(f"Missing extension: {cls}/{fname}")

#import os

#dataset_path = os.path.join(os.getcwd(), "Dataset", "Combined_Textures")
#valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp")

#for cls in os.listdir(dataset_path):
#    cls_path = os.path.join(dataset_path, cls)
#    if os.path.isdir(cls_path):
#        images = [f for f in os.listdir(cls_path) if f.lower().endswith(valid_exts)]
#        print(f"{cls}: {len(images)} valid images")

import torch
print(torch.cuda.is_available())   # should be True
print(torch.version.cuda)          # should show 12.1
print(torch.cuda.get_device_name(0))  # should print "NVIDIA GeForce RTX 4060"
