"""DCNet 模型包装器"""
import os
import re
from typing import Any, Dict
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from models.base import Segmenter
from utils.visualize import create_overlay


# =========================
# DCNet 模型组件定义
# =========================
class HDC(nn.Module):
    """Hybrid Dilated Convolution 模块"""
    def __init__(self, in_ch, out_ch, rates=(1, 2, 3)):
        super().__init__()
        self.branches = nn.ModuleList()
        for r in rates:
            self.branches.append(
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=r, dilation=r, bias=False)
            )
        self.fuse = nn.Conv2d(out_ch * len(rates), out_ch, kernel_size=1, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        feats = [branch(x) for branch in self.branches]
        x_cat = torch.cat(feats, dim=1)
        out = self.fuse(x_cat)
        out = self.bn(out)
        return self.relu(out)


class DenseASPPBlock(nn.Module):
    """DenseASPP 子块"""
    def __init__(self, in_ch, out_ch, dilation):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=dilation, dilation=dilation, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        y = self.conv(x)
        return torch.cat([x, y], dim=1)


class DenseASPP(nn.Module):
    """多层级空洞卷积堆叠"""
    def __init__(self, in_ch, growth_rate=64, rates=(3, 6, 9)):
        super().__init__()
        blocks = []
        channels = in_ch
        for r in rates:
            blocks.append(DenseASPPBlock(channels, growth_rate, dilation=r))
            channels += growth_rate
        self.blocks = nn.ModuleList(blocks)
        self.out_channels = channels

    def forward(self, x):
        for blk in self.blocks:
            x = blk(x)
        return x


class CBAM_Channel(nn.Module):
    """只保留通道注意力的 CBAM"""
    def __init__(self, in_ch, reduction=16):
        super().__init__()
        mid = max(in_ch // reduction, 1)
        self.mlp = nn.Sequential(
            nn.Conv2d(in_ch, mid, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid, in_ch, kernel_size=1, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg = torch.mean(x, dim=(2, 3), keepdim=True)
        att = self.mlp(avg)
        w = self.sigmoid(att)
        return x * w


class AdvancedGAM(nn.Module):
    """通道 + 空间的轻量注意力模块"""
    def __init__(self, in_ch, reduction=16):
        super().__init__()
        mid = max(in_ch // reduction, 1)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.mlp = nn.Sequential(
            nn.Conv2d(in_ch, mid, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid, in_ch, kernel_size=1, bias=False),
            nn.Sigmoid()
        )
        self.spatial_conv = nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False)
        self.spatial_sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg = self.avg_pool(x)
        w_ch = self.mlp(avg)
        x = x * w_ch

        max_map, _ = torch.max(x, dim=1, keepdim=True)
        avg_map = torch.mean(x, dim=1, keepdim=True)
        s = torch.cat([max_map, avg_map], dim=1)
        s = self.spatial_conv(s)
        w_sp = self.spatial_sigmoid(s)
        x = x * w_sp
        return x


class UpsampleBlock(nn.Module):
    """双线性插值 + 3×3 卷积"""
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x, size=None):
        if size is not None:
            x = F.interpolate(x, size=size, mode='bilinear', align_corners=False)
        else:
            x = F.interpolate(x, scale_factor=2.0, mode='bilinear', align_corners=False)
        x = self.conv(x)
        x = self.bn(x)
        return self.relu(x)


class FPN(nn.Module):
    """简化版 FPN：输入为 [C3, C2, C1] 三个不同尺度特征"""
    def __init__(self, in_channels_list, out_ch):
        super().__init__()
        self.lateral_convs = nn.ModuleList()
        self.fpn_convs = nn.ModuleList()
        for in_ch in in_channels_list:
            self.lateral_convs.append(nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False))
            self.fpn_convs.append(
                nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False)
            )

    def forward(self, feats):
        c3, c2, c1 = feats
        p3 = self.lateral_convs[0](c3)
        p2 = self.lateral_convs[1](c2)
        p1 = self.lateral_convs[2](c1)

        p2 = p2 + F.interpolate(p3, size=p2.shape[2:], mode='nearest')
        p1 = p1 + F.interpolate(p2, size=p1.shape[2:], mode='nearest')

        p3 = self.fpn_convs[0](p3)
        p2 = self.fpn_convs[1](p2)
        p1 = self.fpn_convs[2](p1)

        return p1


class DCNet(nn.Module):
    """DCNet 主干网络"""
    def __init__(self, num_classes=2):
        super().__init__()
        # 编码阶段
        self.enc1 = nn.Sequential(
            HDC(3, 16, rates=(1, 2, 3)),
            AdvancedGAM(16)
        )
        self.pool1 = nn.MaxPool2d(2, 2)

        self.enc2 = nn.Sequential(
            HDC(16, 32, rates=(1, 2, 3)),
            AdvancedGAM(32)
        )
        self.pool2 = nn.MaxPool2d(2, 2)

        self.enc3 = nn.Sequential(
            HDC(32, 64, rates=(1, 2, 3)),
            AdvancedGAM(64)
        )
        self.pool3 = nn.MaxPool2d(2, 2)

        self.hdeam_dense = DenseASPP(in_ch=64, growth_rate=64, rates=(3, 6, 9))
        dense_out_ch = self.hdeam_dense.out_channels
        self.hdeam_cbam = CBAM_Channel(dense_out_ch, reduction=16)

        # 解码阶段
        self.up3 = UpsampleBlock(dense_out_ch, 64)
        self.dec3 = nn.Sequential(
            nn.Conv2d(64 + 64, 64, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True)
        )

        self.up2 = UpsampleBlock(64, 32)
        self.dec2 = nn.Sequential(
            nn.Conv2d(32 + 32, 32, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True)
        )

        self.up1 = UpsampleBlock(32, 16)
        self.dec1 = nn.Sequential(
            nn.Conv2d(16 + 16, 16, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True)
        )

        self.fpn = FPN(in_channels_list=[64, 32, 16], out_ch=16)
        self.cls_head = nn.Conv2d(16, num_classes, kernel_size=1, bias=True)

    def forward(self, x):
        # 编码
        e1 = self.enc1(x)
        x1 = self.pool1(e1)

        e2 = self.enc2(x1)
        x2 = self.pool2(e2)

        e3 = self.enc3(x2)
        x3 = self.pool3(e3)

        dense = self.hdeam_dense(x3)
        hdeam_out = self.hdeam_cbam(dense)

        # 解码
        d3 = self.up3(hdeam_out, size=e3.shape[2:])
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3, size=e2.shape[2:])
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2, size=e1.shape[2:])
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        fpn_out = self.fpn([d3, d2, d1])
        logits = self.cls_head(fpn_out)
        return logits


# =========================
# DCNet 包装器实现
# =========================
def build_model(num_classes=2):
    """构建DCNet模型
    
    Args:
        num_classes: 类别数量，默认2（二分类）
        
    Returns:
        DCNet模型实例
    """
    model = DCNet(num_classes=num_classes)
    return model


def load_state_dict_compatible(model, checkpoint, strict=True):
    """兼容多种checkpoint格式的权重加载
    
    Args:
        model: 模型实例
        checkpoint: checkpoint内容（dict或state_dict）
        strict: 是否严格匹配
        
    Returns:
        missing_keys, unexpected_keys
    """
    # 如果checkpoint是dict且包含'state_dict'键
    if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    elif isinstance(checkpoint, dict):
        state_dict = checkpoint
    else:
        raise ValueError(f"不支持的checkpoint格式: {type(checkpoint)}")
    
    # 处理module.前缀（DataParallel包装的情况）
    model_keys = set(model.state_dict().keys())
    checkpoint_keys = set(state_dict.keys())
    
    # 如果checkpoint有module.前缀但模型没有，需要去掉前缀
    if any(k.startswith('module.') for k in checkpoint_keys) and \
       not any(k.startswith('module.') for k in model_keys):
        new_state_dict = {}
        for k, v in state_dict.items():
            new_key = re.sub(r'^module\.', '', k)
            new_state_dict[new_key] = v
        state_dict = new_state_dict
    # 如果模型有module.前缀但checkpoint没有，需要添加前缀
    elif any(k.startswith('module.') for k in model_keys) and \
         not any(k.startswith('module.') for k in checkpoint_keys):
        new_state_dict = {}
        for k, v in state_dict.items():
            new_key = 'module.' + k
            new_state_dict[new_key] = v
        state_dict = new_state_dict
    
    return model.load_state_dict(state_dict, strict=strict)


class DCNetWrapper(Segmenter):
    """DCNet 模型包装器，实现 Segmenter 接口"""
    
    def __init__(self):
        """初始化 DCNet 包装器"""
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded = False
        self.img_size = (512, 512)  # (W, H)
        self.num_classes = 2
    
    def load(self, weights_path: str) -> None:
        """加载模型权重
        
        Args:
            weights_path: 权重文件路径（相对路径）
            
        Raises:
            FileNotFoundError: 权重文件不存在
            ValueError: 权重文件格式错误或加载失败
        """
        if not os.path.exists(weights_path):
            raise FileNotFoundError(f"权重文件不存在: {weights_path}")
        
        try:
            # 构建模型
            if self.model is None:
                self.model = build_model(num_classes=self.num_classes)
            
            # 加载权重
            checkpoint = torch.load(weights_path, map_location=self.device)
            
            # 兼容多种checkpoint格式
            try:
                missing_keys, unexpected_keys = load_state_dict_compatible(
                    self.model, checkpoint, strict=False
                )
                if missing_keys:
                    print(f"[DCNet] 警告: 以下权重未加载: {missing_keys[:5]}...")
                if unexpected_keys:
                    print(f"[DCNet] 警告: 以下权重未使用: {unexpected_keys[:5]}...")
            except Exception as e:
                raise ValueError(f"权重加载失败: {str(e)}")
            
            # 设置为评估模式
            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            
            print(f"[DCNet] 权重加载成功: {weights_path}")
            
        except Exception as e:
            raise ValueError(f"加载权重时出错: {str(e)}")
    
    def preprocess(self, image: Image.Image) -> Dict[str, Any]:
        """图像预处理
        
        Args:
            image: PIL Image 对象
            
        Returns:
            预处理后的数据字典，包含：
            - 'data': 预处理后的tensor [1, 3, H, W]
            - 'original_shape': 原始图像尺寸 (height, width)
            - 'scale': 缩放比例
            
        Raises:
            ValueError: 图像格式不正确
        """
        if image is None or image.size[0] == 0 or image.size[1] == 0:
            raise ValueError("图像无效或尺寸为0")
        
        # 转换为RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 保存原始尺寸
        original_shape = (image.height, image.width)
        
        # Resize到模型输入尺寸 (512, 512)
        resized = image.resize(self.img_size, Image.BILINEAR)
        
        # 转换为numpy并归一化到[0, 1]
        img_array = np.array(resized, dtype=np.float32) / 255.0
        
        # 转换为tensor: [H, W, C] -> [C, H, W] -> [1, C, H, W]
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        
        preprocessed_data = {
            'data': img_tensor,
            'original_shape': original_shape,
            'scale': (self.img_size[0] / original_shape[1], self.img_size[1] / original_shape[0])
        }
        
        return preprocessed_data
    
    def infer(self, preprocessed_data: Dict[str, Any]) -> Dict[str, Any]:
        """模型推理
        
        Args:
            preprocessed_data: 预处理后的数据字典
            
        Returns:
            推理结果字典，包含：
            - 'raw_output': 模型原始输出logits [1, num_classes, H, W]
            - 'original_shape': 原始图像尺寸
            
        Raises:
            RuntimeError: 推理失败或模型未加载
        """
        if not self._loaded:
            raise RuntimeError("模型未加载，请先调用 load() 方法")
        
        if self.model is None:
            raise RuntimeError("模型未初始化")
        
        try:
            tensor = preprocessed_data['data'].to(self.device)
            original_shape = preprocessed_data['original_shape']
            
            with torch.no_grad():
                output = self.model(tensor)
                
                # 处理输出可能是tuple/list/dict的情况
                if isinstance(output, (tuple, list)):
                    # 取第一个元素作为主输出
                    output = output[0]
                elif isinstance(output, dict):
                    # 尝试常见的输出键
                    if 'logits' in output:
                        output = output['logits']
                    elif 'pred' in output:
                        output = output['pred']
                    elif 'output' in output:
                        output = output['output']
                    else:
                        # 取第一个值
                        output = list(output.values())[0]
            
            return {
                'raw_output': output.cpu(),  # 保持tensor格式，后续postprocess处理
                'original_shape': original_shape
            }
            
        except Exception as e:
            raise RuntimeError(f"推理失败: {str(e)}")
    
    def postprocess(self, raw_output: Dict[str, Any], original_shape: tuple) -> np.ndarray:
        """后处理，生成二值mask
        
        Args:
            raw_output: 推理结果字典，包含'raw_output'（tensor）和'original_shape'
            original_shape: 原始图像尺寸 (height, width)（此参数保留接口一致性）
            
        Returns:
            二值mask数组，shape为 (height, width)，值为0或255
            
        Raises:
            ValueError: 输出格式不正确
        """
        if 'raw_output' not in raw_output:
            raise ValueError("推理输出格式不正确：缺少 'raw_output' 字段")
        
        output = raw_output['raw_output']
        original_shape_from_output = raw_output.get('original_shape', original_shape)
        
        # 如果output是tensor，转换为numpy
        if torch.is_tensor(output):
            output = output.cpu().numpy()
        
        # 确保是numpy数组
        if not isinstance(output, np.ndarray):
            raise ValueError(f"不支持的输出类型: {type(output)}")
        
        # 处理batch维度: [B, C, H, W] -> [C, H, W] or [B, H, W] -> [H, W]
        if output.ndim == 4:
            output = output[0]  # 取第一个batch
        if output.ndim == 3:
            # [C, H, W] 多类别，取argmax
            if output.shape[0] == self.num_classes:
                pred = np.argmax(output, axis=0).astype(np.uint8)
            else:
                # 如果不是类别维度，可能是[H, W, C]，取最后一个维度argmax
                pred = np.argmax(output, axis=-1).astype(np.uint8)
        elif output.ndim == 2:
            pred = output.astype(np.uint8)
        else:
            raise ValueError(f"不支持的输出维度: {output.ndim}, shape: {output.shape}")
        
        # 转换为二值mask (0或255)
        # 假设类别1是前景
        binary_mask = (pred > 0).astype(np.uint8) * 255
        
        # Resize回原始尺寸
        if binary_mask.shape[:2] != original_shape_from_output:
            from PIL import Image as PILImage
            mask_img = PILImage.fromarray(binary_mask, mode='L')
            mask_img = mask_img.resize(
                (original_shape_from_output[1], original_shape_from_output[0]),
                PILImage.NEAREST
            )
            binary_mask = np.array(mask_img)
        
        return binary_mask
    
    def visualize(self, image: Image.Image, mask: np.ndarray) -> Dict[str, Image.Image]:
        """可视化结果
        
        Args:
            image: 原始图像
            mask: 二值mask数组，shape为 (height, width)，值为0或255
            
        Returns:
            Dict包含:
            - 'mask': mask图像
            - 'overlay': 叠加可视化图像（mask区域半透明着色）
            
        Raises:
            ValueError: 输入尺寸不匹配
        """
        if image.size[1] != mask.shape[0] or image.size[0] != mask.shape[1]:
            raise ValueError(
                f"图像和mask尺寸不匹配: 图像{image.size} vs mask{mask.shape[:2]}"
            )
        
        # 生成mask图像
        mask_image = Image.fromarray(mask, mode='L')
        
        # 生成overlay图像（mask区域半透明着色）
        overlay_image = create_overlay(image, mask)
        
        return {
            'mask': mask_image,
            'overlay': overlay_image
        }
