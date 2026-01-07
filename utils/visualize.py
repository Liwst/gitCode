"""可视化工具"""
import numpy as np
from PIL import Image


def create_overlay(image: Image.Image, mask: np.ndarray, color: tuple = (255, 0, 0), alpha: float = 0.5) -> Image.Image:
    """创建mask叠加可视化图像
    
    mask区域半透明着色，背景不变
    
    Args:
        image: 原始图像（PIL Image）
        mask: 二值mask数组，shape为 (height, width)，值为0或255
        color: 着色RGB颜色，默认红色 (255, 0, 0)
        alpha: 透明度，范围0-1，默认0.5
        
    Returns:
        叠加后的图像（PIL Image）
        
    Raises:
        ValueError: 输入尺寸不匹配或参数无效
    """
    if image.size[1] != mask.shape[0] or image.size[0] != mask.shape[1]:
        raise ValueError(
            f"图像和mask尺寸不匹配: 图像{image.size} vs mask{mask.shape[:2]}"
        )
    
    if not (0 <= alpha <= 1):
        raise ValueError(f"透明度alpha必须在0-1之间，当前值: {alpha}")
    
    if len(color) != 3 or not all(0 <= c <= 255 for c in color):
        raise ValueError(f"颜色必须是RGB三元组，范围0-255，当前值: {color}")
    
    # 转换为numpy数组
    img_array = np.array(image)
    
    # 确保图像是RGB模式
    if len(img_array.shape) == 2:  # 灰度图
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[2] == 4:  # RGBA
        img_array = img_array[:, :, :3]
    
    # 归一化mask到0-1范围
    mask_normalized = (mask > 127).astype(np.float32)
    
    # 创建颜色遮罩
    color_overlay = np.zeros_like(img_array, dtype=np.float32)
    color_overlay[:, :, 0] = color[0]  # R
    color_overlay[:, :, 1] = color[1]  # G
    color_overlay[:, :, 2] = color[2]  # B
    
    # 应用透明度：mask区域使用alpha混合，背景不变
    mask_3d = mask_normalized[:, :, np.newaxis]  # (H, W, 1)
    
    # 混合：mask区域 = alpha * color + (1-alpha) * image，背景 = image
    result = img_array.astype(np.float32) * (1 - mask_3d * alpha) + color_overlay * (mask_3d * alpha)
    
    # 转换为uint8
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return Image.fromarray(result, mode='RGB')
