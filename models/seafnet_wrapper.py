"""SEAFNet 模型包装器"""
import os
import re
from typing import Any, Dict
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from models.base import Segmenter
from models.registry import ModelRegistry
from utils.visualize import create_overlay


# =========================
# SEAFNet 模型组件定义
# =========================
class ConvBNReLU(nn.Module):
    """基础卷积-BN-ReLU模块"""
    def __init__(self, in_ch, out_ch, k=3, s=1, p=1, groups=1):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=k, stride=s, padding=p, groups=groups, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.act = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))


class SobelEdge(nn.Module):
    """Sobel 边缘算子：输出边缘强度（0~1 归一化）"""
    def __init__(self):
        super().__init__()
        kx = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=torch.float32).view(1, 1, 3, 3)
        ky = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=torch.float32).view(1, 1, 3, 3)
        self.register_buffer("kx", kx)
        self.register_buffer("ky", ky)

    def forward(self, x):
        # x: [B,C,H,W] -> 灰度边缘更稳定：先做通道均值
        g = x.mean(dim=1, keepdim=True)
        gx = F.conv2d(g, self.kx, padding=1)
        gy = F.conv2d(g, self.ky, padding=1)
        mag = torch.sqrt(gx * gx + gy * gy + 1e-6)
        # 归一化到 0~1（每张图独立归一化）
        b = mag.shape[0]
        mag_flat = mag.view(b, -1)
        mn = mag_flat.min(dim=1)[0].view(b, 1, 1, 1)
        mx = mag_flat.max(dim=1)[0].view(b, 1, 1, 1)
        mag = (mag - mn) / (mx - mn + 1e-6)
        return mag


class EASA(nn.Module):
    """EASA（Edge-Aware SimAM Attention）：
    将 Sobel 边缘先验注入到无参数注意框架中，对边界邻域的响应进行自适应放大。
    """
    def __init__(self, lam=1.0):
        super().__init__()
        self.edge = SobelEdge()
        self.lam = lam

    def forward(self, x):
        # SimAM-like：利用通道内统计量形成无参数权重
        mu = x.mean(dim=(2, 3), keepdim=True)
        var = (x - mu).pow(2).mean(dim=(2, 3), keepdim=True)
        energy = (x - mu).pow(2) / (4 * (var + 1e-6)) + 0.5
        sim_w = torch.sigmoid(1.0 / (energy + 1e-6))

        # 边缘先验：对边界邻域加权放大（广播到所有通道）
        e = self.edge(x)  # [B,1,H,W]
        edge_w = 1.0 + self.lam * e

        w = sim_w * edge_w
        return x * w


class ADDA(nn.Module):
    """ADDA（Adaptive Dense Dilated Aggregation）：
    多尺度空洞卷积分支 + 全局上下文路径
    通过可学习的尺度权重对各分支进行自适应融合
    """
    def __init__(self, in_ch, out_ch, rates=(3, 6, 9)):
        super().__init__()
        self.rates = rates
        self.branches = nn.ModuleList(
            [
                nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=r, dilation=r, bias=False),
                    nn.BatchNorm2d(out_ch),
                    nn.ReLU(inplace=True),
                )
                for r in rates
            ]
        )
        self.global_path = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

        # 生成 (D+1) 个权重：来自 GAP(X) 的通道描述
        self.alpha_gen = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(in_ch, len(rates) + 1, kernel_size=1, bias=True),
        )
        self.sigmoid = nn.Sigmoid()

        # 融合后通道压缩
        self.fuse = nn.Sequential(
            nn.Conv2d(out_ch, out_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        feats = [b(x) for b in self.branches]  # D 个
        g = self.global_path(x)
        g = F.interpolate(g, size=x.shape[2:], mode="bilinear", align_corners=False)

        alpha = self.sigmoid(self.alpha_gen(x))  # [B, D+1, 1, 1]
        # 为了数值稳定：做一次归一化
        alpha = alpha / (alpha.sum(dim=1, keepdim=True) + 1e-6)

        y = 0.0
        for i, f in enumerate(feats):
            y = y + alpha[:, i : i + 1] * f
        y = y + alpha[:, len(feats) : len(feats) + 1] * g
        y = self.fuse(y)
        return y


class EGCFP(nn.Module):
    """EGCFP（Edge-Guided Context Fusion Path）：
    在编码-解码衔接处，将浅层边缘纹理与深层语义特征做空间对齐与门控融合。
    """
    def __init__(self, shallow_ch, deep_ch, out_ch):
        super().__init__()
        self.shallow_proj = nn.Conv2d(shallow_ch, out_ch, kernel_size=1, bias=False)
        self.deep_proj = nn.Conv2d(deep_ch, out_ch, kernel_size=1, bias=False)

        self.gate = nn.Sequential(
            nn.Conv2d(out_ch * 2, out_ch, kernel_size=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=1, bias=True),
            nn.Sigmoid(),
        )
        self.refine = ConvBNReLU(out_ch, out_ch, k=3, p=1)

    def forward(self, shallow, deep):
        # shallow: 高分辨率；deep: 低分辨率
        s = self.shallow_proj(shallow)
        d = self.deep_proj(deep)
        d = F.interpolate(d, size=s.shape[2:], mode="bilinear", align_corners=False)

        g = self.gate(torch.cat([s, d], dim=1))
        out = s + g * d
        return self.refine(out)


class DADBlock(nn.Module):
    """DAD 的基本解码单元：上采样 + 跳跃融合 + 细化"""
    def __init__(self, in_ch, skip_ch, out_ch):
        super().__init__()
        self.up = ConvBNReLU(in_ch, out_ch, k=3, p=1)
        self.fuse = ConvBNReLU(out_ch + skip_ch, out_ch, k=3, p=1)

    def forward(self, x, skip):
        x = F.interpolate(x, size=skip.shape[2:], mode="bilinear", align_corners=False)
        x = self.up(x)
        x = torch.cat([x, skip], dim=1)
        return self.fuse(x)


class SEAFNet(nn.Module):
    """SEAFNet（Semantic Edge-Aware Fusion Network）"""
    def __init__(self, num_classes=2, base_ch=16):
        super().__init__()

        # 浅层特征提取（fstem）
        self.stem = nn.Sequential(
            ConvBNReLU(3, base_ch, k=3, p=1),
            ConvBNReLU(base_ch, base_ch, k=3, p=1),
        )

        # 编码器（3 个尺度）
        self.easa1 = EASA(lam=1.0)
        self.enc1 = nn.Sequential(
            ConvBNReLU(base_ch, base_ch, k=3, p=1),
            ConvBNReLU(base_ch, base_ch, k=3, p=1)
        )
        self.pool1 = nn.MaxPool2d(2, 2)  # 512->256

        self.easa2 = EASA(lam=1.0)
        self.enc2 = nn.Sequential(
            ConvBNReLU(base_ch, base_ch * 2, k=3, p=1),
            ConvBNReLU(base_ch * 2, base_ch * 2, k=3, p=1),
        )
        self.pool2 = nn.MaxPool2d(2, 2)  # 256->128

        self.easa3 = EASA(lam=1.0)
        self.enc3 = nn.Sequential(
            ConvBNReLU(base_ch * 2, base_ch * 4, k=3, p=1),
            ConvBNReLU(base_ch * 4, base_ch * 4, k=3, p=1),
        )
        self.pool3 = nn.MaxPool2d(2, 2)  # 128->64

        # 高层自适应稠密空洞金字塔（ADDA）
        self.adda = ADDA(in_ch=base_ch * 4, out_ch=base_ch * 8, rates=(3, 6, 9))

        # 语义边缘引导融合路径（EGCFP）
        self.egcfp = EGCFP(shallow_ch=base_ch, deep_ch=base_ch * 8, out_ch=base_ch)

        # 细节聚合解码器（DAD）
        self.dad3 = DADBlock(in_ch=base_ch * 8, skip_ch=base_ch * 4, out_ch=base_ch * 4)  # 64->128
        self.dad2 = DADBlock(in_ch=base_ch * 4, skip_ch=base_ch * 2, out_ch=base_ch * 2)  # 128->256
        self.dad1 = DADBlock(in_ch=base_ch * 2, skip_ch=base_ch, out_ch=base_ch)  # 256->512

        self.cls_head = nn.Conv2d(base_ch, num_classes, kernel_size=1, bias=True)

    def forward(self, x):
        # stem
        f0 = self.stem(x)  # [B, base, 512,512]

        # enc1
        e1 = self.enc1(self.easa1(f0))  # [B, base, 512,512]
        x1 = self.pool1(e1)  # 256

        # enc2
        e2 = self.enc2(self.easa2(x1))  # [B, 2base, 256,256]
        x2 = self.pool2(e2)  # 128

        # enc3
        e3 = self.enc3(self.easa3(x2))  # [B, 4base, 128,128]
        x3 = self.pool3(e3)  # 64

        # ctx
        fctx = self.adda(x3)  # [B, 8base, 64,64]

        # egcfp：在高分辨率端对齐语义与边缘
        edge_guided = self.egcfp(e1, fctx)  # [B, base, 512,512]

        # dad decode
        d3 = self.dad3(fctx, e3)  # -> [B, 4base, 128,128]
        d2 = self.dad2(d3, e2)  # -> [B, 2base, 256,256]
        d1 = self.dad1(d2, edge_guided)  # -> [B, base, 512,512]

        logits = self.cls_head(d1)  # [B,2,512,512]
        return logits


# =========================
# SEAFNet 包装器实现
# =========================
def build_model(num_classes=2, base_ch=16):
    """构建SEAFNet模型
    
    Args:
        num_classes: 类别数量，默认2（二分类）
        base_ch: 基础通道数，默认16
        
    Returns:
        SEAFNet模型实例
    
    TODO: 实现模型构造逻辑
    """
    # TODO: 实现模型构造
    model = SEAFNet(num_classes=num_classes, base_ch=base_ch)
    return model
    # raise NotImplementedError("build_model() 待实现，请参考训练代码中的模型构造")


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


class SEAFNetWrapper(Segmenter):
    """SEAFNet 模型包装器，实现 Segmenter 接口"""
    
    def __init__(self):
        """初始化 SEAFNet 包装器"""
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._loaded = False
        
        # 从registry获取配置
        self.cfg = ModelRegistry.get_config("SEAFNet")
        if self.cfg is None:
            # 如果配置不存在，使用默认值
            self.cfg = {
                "input_size": (512, 512),
                "mean": [0.485, 0.456, 0.406],
                "std": [0.229, 0.224, 0.225],
                "threshold": 0.5,
                "num_classes": 2
            }
        
        self.input_size = self.cfg["input_size"]  # (W, H)
        self.num_classes = self.cfg["num_classes"]
        self.threshold = self.cfg["threshold"]
        
        # 转换为tensor用于归一化
        self.mean = torch.tensor(self.cfg["mean"]).view(1, 3, 1, 1)
        self.std = torch.tensor(self.cfg["std"]).view(1, 3, 1, 1)
    
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
                    print(f"[SEAFNet] 警告: 以下权重未加载: {missing_keys[:5]}...")
                if unexpected_keys:
                    print(f"[SEAFNet] 警告: 以下权重未使用: {unexpected_keys[:5]}...")
            except Exception as e:
                raise ValueError(f"权重加载失败: {str(e)}")
            
            # 设置为评估模式
            self.model.to(self.device)
            self.model.eval()
            self._loaded = True
            
            print(f"[SEAFNet] 权重加载成功: {weights_path}")
            
        except Exception as e:
            raise ValueError(f"加载权重时出错: {str(e)}")
    
    def preprocess(self, image: Image.Image) -> Dict[str, Any]:
        """图像预处理（通用方案）
        
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
        
        # Resize到模型输入尺寸
        resized = image.resize(self.input_size, Image.BILINEAR)
        
        # 转换为numpy并归一化到[0, 1]
        img_array = np.array(resized, dtype=np.float32) / 255.0
        
        # 转换为tensor: [H, W, C] -> [C, H, W] -> [1, C, H, W]
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        
        # 标准化（使用mean和std）
        mean = self.mean.to(img_tensor.device)
        std = self.std.to(img_tensor.device)
        img_tensor = (img_tensor - mean) / std
        
        preprocessed_data = {
            'data': img_tensor,
            'original_shape': original_shape,
            'scale': (self.input_size[0] / original_shape[1], self.input_size[1] / original_shape[0])
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
        """后处理，生成二值mask（通用方案）
        
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
        
        # 处理batch维度: [B, C, H, W] -> [C, H, W]
        if output.ndim == 4:
            output = output[0]  # 取第一个batch
        
        # 根据类别数选择处理方式
        if output.ndim == 3:
            if output.shape[0] == self.num_classes:
                # 多分类：二分类用sigmoid+threshold，多分类用argmax>0
                if self.num_classes == 2:
                    # 二分类：对前景类（通常是第1类）应用sigmoid
                    prob = 1.0 / (1.0 + np.exp(-output[1]))  # sigmoid
                    pred = (prob > self.threshold).astype(np.uint8)
                else:
                    # 多分类：argmax，然后>0视为前景
                    pred = np.argmax(output, axis=0).astype(np.uint8)
                    pred = (pred > 0).astype(np.uint8)
            else:
                # 如果不是类别维度，可能是[H, W, C]
                pred = np.argmax(output, axis=-1).astype(np.uint8)
                pred = (pred > 0).astype(np.uint8)
        elif output.ndim == 2:
            # 已经是2D，直接使用
            pred = output.astype(np.uint8)
            if pred.max() > 1:
                pred = (pred > 127).astype(np.uint8)
        else:
            raise ValueError(f"不支持的输出维度: {output.ndim}, shape: {output.shape}")
        
        # 转换为二值mask (0或255)
        binary_mask = pred.astype(np.uint8) * 255
        
        # Resize回原始尺寸（插值）
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
