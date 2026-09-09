"""
WATERSCOPE ML Engine - Siamese Bi-Temporal Change Detection Networks
Includes:
- SiameseChangeNet: Siamese ResNet-18 twin with multi-scale feature difference fusion
- DifferenceAttentionBlock: Cross-attention gating mechanism for bi-temporal feature differences
- AttentionSiameseChangeNet: Advanced Siamese architecture with difference attention blocks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class FeatureFusionBlock(nn.Module):
    """
    Standard feature difference and concatenation block.
    """
    def __init__(self, channels: int):
        super().__init__()
        self.fusion_conv = nn.Sequential(
            nn.Conv2d(channels * 3, channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, feat0: torch.Tensor, feat1: torch.Tensor) -> torch.Tensor:
        diff = torch.abs(feat1 - feat0)
        cat = torch.cat([feat0, feat1, diff], dim=1)
        fused = self.fusion_conv(cat)
        return fused + diff

class DifferenceAttentionBlock(nn.Module):
    """
    Spatial & Channel Cross-Attention between bi-temporal features T0 and T1.
    Suppresses transient seasonal variations (sun angle, crop phenology)
    and amplifies structural water/soil/vegetation interventions.
    """
    def __init__(self, channels: int):
        super().__init__()
        # Channel Attention on absolute difference
        self.mlp = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels, max(channels // 8, 8), kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(max(channels // 8, 8), channels, kernel_size=1),
            nn.Sigmoid()
        )
        # Spatial Attention on difference
        self.spatial_conv = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),
            nn.Sigmoid()
        )
        # Projection for concatenated [F0, F1, F_diff]
        self.proj = nn.Sequential(
            nn.Conv2d(channels * 3, channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, feat0: torch.Tensor, feat1: torch.Tensor) -> torch.Tensor:
        diff = torch.abs(feat1 - feat0)
        # Channel gating
        ch_gate = self.mlp(diff)
        diff_ch = diff * ch_gate
        # Spatial gating
        avg_pool = torch.mean(diff_ch, dim=1, keepdim=True)
        max_pool, _ = torch.max(diff_ch, dim=1, keepdim=True)
        sp_gate = self.spatial_conv(torch.cat([avg_pool, max_pool], dim=1))
        diff_att = diff_ch * sp_gate

        cat = torch.cat([feat0, feat1, diff_att], dim=1)
        fused = self.proj(cat)
        return fused + diff_att

class DecoderStage(nn.Module):
    def __init__(self, in_c: int, skip_c: int, out_c: int):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_c, out_c, kernel_size=2, stride=2)
        self.conv = nn.Sequential(
            nn.Conv2d(out_c + skip_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor, skip: torch.Tensor = None) -> torch.Tensor:
        x = self.up(x)
        if skip is not None:
            if x.shape[2:] != skip.shape[2:]:
                x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
            x = torch.cat([x, skip], dim=1)
        return self.conv(x)

class SiameseChangeNet(nn.Module):
    """
    Siamese Bi-Temporal Network for Farm Pond Change Detection.
    - Shared weights encoder for T0 and T1
    - Multi-scale feature difference / fusion
    - Optional Difference Attention cross-gating
    - Decoder for high-resolution pixel change mask
    - Classification head for dominant change determination
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = True, use_attention: bool = False):
        super().__init__()
        self.num_classes = num_classes
        self.use_attention = use_attention

        # Shared Siamese Encoder (ResNet-18)
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        base = models.resnet18(weights=weights)

        self.init_conv = nn.Sequential(base.conv1, base.bn1, base.relu)
        self.maxpool = base.maxpool
        self.layer1 = base.layer1 # 64 ch
        self.layer2 = base.layer2 # 128 ch
        self.layer3 = base.layer3 # 256 ch
        self.layer4 = base.layer4 # 512 ch

        FusionCls = DifferenceAttentionBlock if use_attention else FeatureFusionBlock

        # Multi-scale Fusion Blocks
        self.fuse0 = FusionCls(64)
        self.fuse1 = FusionCls(64)
        self.fuse2 = FusionCls(128)
        self.fuse3 = FusionCls(256)
        self.fuse4 = FusionCls(512)

        # Decoder stages
        self.dec4 = DecoderStage(512, 256, 256)
        self.dec3 = DecoderStage(256, 128, 128)
        self.dec2 = DecoderStage(128, 64, 64)
        self.dec1 = DecoderStage(64, 64, 32)

        # Segmentation output head
        self.seg_head = nn.Sequential(
            nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, num_classes, kernel_size=1)
        )

        # Dominant change classification head
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier_head = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def extract_features(self, x: torch.Tensor):
        x0 = self.init_conv(x)  # [B, 64, H/2, W/2]
        x_p = self.maxpool(x0)  # [B, 64, H/4, W/4]
        l1 = self.layer1(x_p)   # [B, 64, H/4, W/4]
        l2 = self.layer2(l1)    # [B, 128, H/8, W/8]
        l3 = self.layer3(l2)    # [B, 256, H/16, W/16]
        l4 = self.layer4(l3)    # [B, 512, H/32, W/32]
        return x0, l1, l2, l3, l4

    def forward(self, img0: torch.Tensor, img1: torch.Tensor):
        # 1. Siamese Feature Extraction (Shared weights)
        f0_x0, f0_l1, f0_l2, f0_l3, f0_l4 = self.extract_features(img0)
        f1_x0, f1_l1, f1_l2, f1_l3, f1_l4 = self.extract_features(img1)

        # 2. Multi-scale Feature Difference & Fusion
        fused_x0 = self.fuse0(f0_x0, f1_x0)
        fused_l1 = self.fuse1(f0_l1, f1_l1)
        fused_l2 = self.fuse2(f0_l2, f1_l2)
        fused_l3 = self.fuse3(f0_l3, f1_l3)
        fused_l4 = self.fuse4(f0_l4, f1_l4)

        # 3. Dominant Change Classification Head
        bottleneck_pooled = self.global_pool(fused_l4).flatten(1)
        cls_logits = self.classifier_head(bottleneck_pooled)

        # 4. Decoder with Fused Skip Connections
        d4 = self.dec4(fused_l4, fused_l3)
        d3 = self.dec3(d4, fused_l2)
        d2 = self.dec2(d3, fused_l1)
        d1 = self.dec1(d2, fused_x0)

        # 5. Pixel-level Segmentation Logits
        seg_logits = self.seg_head(d1)
        if seg_logits.shape[2:] != img0.shape[2:]:
            seg_logits = F.interpolate(seg_logits, size=img0.shape[2:], mode="bilinear", align_corners=False)

        return {
            "seg_logits": seg_logits,
            "cls_logits": cls_logits,
            "fused_features": fused_l4
        }

class AttentionSiameseChangeNet(SiameseChangeNet):
    """
    Convenience class initializing SiameseChangeNet with difference attention enabled.
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = True):
        super().__init__(num_classes=num_classes, pretrained=pretrained, use_attention=True)
