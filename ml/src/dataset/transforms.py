"""
WATERSCOPE ML Engine - Bi-temporal Data Augmentations
Applies geometrically identical spatial transformations to T0, T1, and mask simultaneously
while allowing non-destructive photometric variations.
"""

import albumentations as A
from albumentations.pytorch import ToTensorV2

def get_training_transforms(image_size=(256, 256)):
    """
    Returns an Albumentations Compose pipeline with identical spatial transforms
    for T0 (image), T1 (image1), and mask.
    """
    h, w = image_size
    return A.Compose([
        A.Resize(height=h, width=w),
        # Geometric transformations (strictly identical across T0, T1, mask)
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.RandomRotate90(p=0.5),
        A.Affine(scale=(0.9, 1.1), rotate=(-15, 15), translate_percent=(-0.06, 0.06), p=0.4),
        
        # Photometric transformations (subtle brightness & contrast)
        A.RandomBrightnessContrast(brightness_limit=0.15, contrast_limit=0.15, p=0.5),
        
        # Normalization with ImageNet statistics
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ], additional_targets={'image1': 'image'}, is_check_shapes=False)

def get_validation_transforms(image_size=(256, 256)):
    """Validation and test pipeline: deterministic resize and normalization."""
    h, w = image_size
    return A.Compose([
        A.Resize(height=h, width=w),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ], additional_targets={'image1': 'image'}, is_check_shapes=False)
