"""
WATERSCOPE ML Engine - Baseline Change Detection Model
Image difference / concatenation baseline feeding into a CNN segmentation & classification network.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class ConvBlock(nn.Module):
    def __init__(self, in_c: int, out_c: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_c),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class DecoderBlock(nn.Module):
    def __init__(self, in_c: int, skip_c: int, out_c: int):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_c, out_c, kernel_size=2, stride=2)
        self.conv = ConvBlock(out_c + skip_c, out_c)

    def forward(self, x, skip=None):
        x = self.up(x)
        if skip is not None:
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
            x = torch.cat([x, skip], dim=1)
        return self.conv(x)

class BaselineChangeNet(nn.Module):
    """
    Baseline bi-temporal change model:
    Concatenates T0, T1 and pixel difference |T1 - T0| into 9 input channels.
    Uses ResNet-18 backbone with UNet decoder for change mask and global pooling head.
    """
    def __init__(self, num_classes: int = 5, pretrained: bool = False):
        super().__init__()
        self.num_classes = num_classes
        
        # Base encoder
        base = models.resnet18(weights=models.ResNet18_Weights.DEFAULT if pretrained else None)
        
        # Modify first layer to accept 9 channels (T0: 3, T1: 3, Diff: 3)
        self.initial_conv = nn.Sequential(
            nn.Conv2d(9, 64, kernel_size=7, stride=2, padding=3, bias=False),
            base.bn1,
            base.relu
        )
        self.maxpool = base.maxpool
        
        self.layer1 = base.layer1 # 64
        self.layer2 = base.layer2 # 128
        self.layer3 = base.layer3 # 256
        self.layer4 = base.layer4 # 512
        
        # Decoders
        self.dec4 = DecoderBlock(512, 256, 256)
        self.dec3 = DecoderBlock(256, 128, 128)
        self.dec2 = DecoderBlock(128, 64, 64)
        self.dec1 = DecoderBlock(64, 64, 32)
        
        # Final upsampling to original resolution
        self.final_up = nn.Sequential(
            nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, num_classes, kernel_size=1)
        )
        
        # Global classification head
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )

    def forward(self, img0: torch.Tensor, img1: torch.Tensor):
        # Calculate pixel difference
        diff = torch.abs(img1 - img0)
        x = torch.cat([img0, img1, diff], dim=1) # [B, 9, H, W]
        
        # Encoder
        x0 = self.initial_conv(x) # 64, H/2, W/2
        x_pool = self.maxpool(x0) # 64, H/4, W/4
        
        l1 = self.layer1(x_pool) # 64, H/4, W/4
        l2 = self.layer2(l1)     # 128, H/8, W/8
        l3 = self.layer3(l2)     # 256, H/16, W/16
        l4 = self.layer4(l3)     # 512, H/32, W/32
        
        # Global classification head
        feat_pool = self.global_pool(l4).flatten(1)
        cls_logits = self.classifier(feat_pool)
        
        # Decoder
        d4 = self.dec4(l4, l3)
        d3 = self.dec3(d4, l2)
        d2 = self.dec2(d3, l1)
        d1 = self.dec1(d2, x0)
        
        seg_logits = self.final_up(d1)
        if seg_logits.shape[2:] != img0.shape[2:]:
            seg_logits = F.interpolate(seg_logits, size=img0.shape[2:], mode="bilinear", align_corners=False)
            
        return {
            "seg_logits": seg_logits,
            "cls_logits": cls_logits
        }
