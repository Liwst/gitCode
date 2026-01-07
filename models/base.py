"""统一的分割器接口定义"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image


class Segmenter(ABC):
    """分割器统一接口
    
    所有模型必须实现以下方法：
    - load: 加载模型权重
    - preprocess: 图像预处理
    - infer: 模型推理
    - postprocess: 后处理生成mask
    - visualize: 可视化结果
    """
    
    @abstractmethod
    def load(self, weights_path: str) -> None:
        """加载模型权重
        
        Args:
            weights_path: 权重文件路径（相对路径）
            
        Raises:
            FileNotFoundError: 权重文件不存在
            ValueError: 权重文件格式错误
        """
        pass
    
    @abstractmethod
    def preprocess(self, image: Image.Image) -> Any:
        """图像预处理
        
        Args:
            image: PIL Image 对象
            
        Returns:
            预处理后的数据（通常是 tensor 或 numpy array）
            
        Raises:
            ValueError: 图像格式不正确
        """
        pass
    
    @abstractmethod
    def infer(self, preprocessed_data: Any) -> Any:
        """模型推理
        
        Args:
            preprocessed_data: 预处理后的数据
            
        Returns:
            模型原始输出
            
        Raises:
            RuntimeError: 推理失败
        """
        pass
    
    @abstractmethod
    def postprocess(self, raw_output: Any, original_shape: tuple) -> np.ndarray:
        """后处理，生成二值mask
        
        Args:
            raw_output: 模型原始输出
            original_shape: 原始图像尺寸 (height, width)
            
        Returns:
            二值mask数组，shape为 (height, width)，值为0或255
            
        Raises:
            ValueError: 输出格式不正确
        """
        pass
    
    @abstractmethod
    def visualize(self, image: Image.Image, mask: np.ndarray) -> Dict[str, Image.Image]:
        """可视化结果
        
        Args:
            image: 原始图像
            mask: 二值mask数组
            
        Returns:
            Dict包含:
            - 'mask': mask图像
            - 'overlay': 叠加可视化图像（mask区域半透明着色）
            
        Raises:
            ValueError: 输入尺寸不匹配
        """
        pass
