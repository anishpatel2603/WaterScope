"""
WATERSCOPE ML Engine - Advanced Multi-Class Change Detection Loss Functions
Includes:
- MultiClassFocalLoss for downweighting easy negative background pixels
- TverskyLoss / MaskAwareDiceLoss for penalizing false negatives on rare change classes
- Hybrid ChangeDetectionLoss combining Focal, Weighted Cross-Entropy, and Tversky/Dice losses
"""

from typing import Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiClassFocalLoss(nn.Module):
    """
    Multi-class Focal Loss:
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)
    Down-weights easy well-classified background pixels to focus on rare change boundaries.
    """
    def __init__(
        self,
        alpha: Optional[torch.Tensor] = None,
        gamma: float = 2.0,
        reduction: str = "mean",
        ignore_index: int = -100
    ):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
        self.ignore_index = ignore_index

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # logits: [B, C, H, W], targets: [B, H, W]
        ce_loss = F.cross_entropy(
            logits,
            targets,
            weight=self.alpha,
            reduction="none",
            ignore_index=self.ignore_index
        )
        pt = torch.exp(-ce_loss)
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss

class MultiClassTverskyLoss(nn.Module):
    """
    Multi-class Tversky Loss:
    TL = 1 - (TP + smooth) / (TP + alpha*FP + beta*FN + smooth)
    Setting beta > alpha (e.g., beta=0.7, alpha=0.3) penalizes false negatives heavily,
    vital for extremely rare change classes like Demolished, Dried, and Wetted ponds.
    """
    def __init__(
        self,
        alpha: float = 0.3,
        beta: float = 0.7,
        smooth: float = 1.0,
        class_weights: Optional[torch.Tensor] = None
    ):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.smooth = smooth
        self.class_weights = class_weights

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        num_classes = logits.shape[1]
        probs = F.softmax(logits, dim=1) # [B, C, H, W]
        targets_one_hot = F.one_hot(targets.clamp(0, num_classes - 1), num_classes=num_classes).permute(0, 3, 1, 2).float()

        dims = (0, 2, 3)
        tp = torch.sum(probs * targets_one_hot, dims)
        fp = torch.sum(probs * (1.0 - targets_one_hot), dims)
        fn = torch.sum((1.0 - probs) * targets_one_hot, dims)

        tversky_index = (tp + self.smooth) / (tp + self.alpha * fp + self.beta * fn + self.smooth)
        class_loss = 1.0 - tversky_index

        if self.class_weights is not None:
            weights = self.class_weights.to(logits.device)
            return (class_loss * weights).sum() / weights.sum()

        return class_loss.mean()

class ChangeDetectionLoss(nn.Module):
    """
    Production Hybrid Loss for Bi-Temporal Watershed Monitoring:
    Combines Focal Loss (or Weighted Cross-Entropy) with Tversky/Dice Loss
    and an auxiliary change classification head loss.
    """
    def __init__(
        self,
        class_weights: Optional[torch.Tensor] = None,
        loss_type: str = "focal_tversky", # "focal_tversky", "ce_dice", "focal_dice"
        ce_weight: float = 0.4,
        seg_weight: float = 0.6,
        aux_cls_weight: float = 0.2,
        gamma: float = 2.0,
        tversky_alpha: float = 0.3,
        tversky_beta: float = 0.7
    ):
        super().__init__()
        self.loss_type = loss_type
        self.ce_weight = ce_weight
        self.seg_weight = seg_weight
        self.aux_cls_weight = aux_cls_weight

        # Primary pixel-level loss components
        self.focal = MultiClassFocalLoss(alpha=class_weights, gamma=gamma)
        self.ce = nn.CrossEntropyLoss(weight=class_weights)
        self.tversky = MultiClassTverskyLoss(
            alpha=tversky_alpha,
            beta=tversky_beta,
            class_weights=class_weights
        )

        # Auxiliary image-level classification loss
        self.aux_ce = nn.CrossEntropyLoss(weight=class_weights)

    def forward(
        self,
        seg_logits: torch.Tensor,
        seg_targets: torch.Tensor,
        cls_logits: Optional[torch.Tensor] = None,
        cls_targets: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        if self.loss_type == "focal_tversky":
            pixel_loss = self.ce_weight * self.focal(seg_logits, seg_targets) + self.seg_weight * self.tversky(seg_logits, seg_targets)
        elif self.loss_type == "ce_dice":
            pixel_loss = self.ce_weight * self.ce(seg_logits, seg_targets) + self.seg_weight * self.tversky(seg_logits, seg_targets)
        else: # default focal + tversky
            pixel_loss = self.ce_weight * self.focal(seg_logits, seg_targets) + self.seg_weight * self.tversky(seg_logits, seg_targets)

        total_loss = pixel_loss

        if cls_logits is not None and cls_targets is not None:
            aux_loss = self.aux_ce(cls_logits, cls_targets)
            total_loss = total_loss + self.aux_cls_weight * aux_loss

        return total_loss
