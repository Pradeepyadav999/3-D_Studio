import cv2
import numpy as np

img = cv2.imread("storage/uploads/products/fk_f738a9d0/img_0.jpg")
h, w = img.shape[:2]
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)

# Skin detection in YCrCb: Cr in [133, 173], Cb in [77, 127]
skin_mask = (ycrcb[:, :, 1] >= 133) & (ycrcb[:, :, 1] <= 175) & (ycrcb[:, :, 2] >= 77) & (ycrcb[:, :, 2] <= 128)
skin_pct = np.sum(skin_mask) / (h * w)
print(f"Total skin pixels in full image: {skin_pct*100:.1f}%")

# Check candidate chest region (y from 0.22 to 0.65, x from 0.20 to 0.80)
roi_skin = skin_mask[int(h*0.22):int(h*0.65), int(w*0.20):int(w*0.80)]
roi_skin_pct = np.sum(roi_skin) / roi_skin.size
print(f"Skin pixels in candidate chest ROI: {roi_skin_pct*100:.1f}%")

# In the upper neck ROI (y from 0.22 to 0.38)
upper_roi_skin = skin_mask[int(h*0.22):int(h*0.38), int(w*0.30):int(w*0.70)]
print(f"Skin in neck ROI (y: 0.22-0.38): {np.sum(upper_roi_skin)/upper_roi_skin.size*100:.1f}%")

