"""推理引擎"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any
from PIL import Image
import numpy as np
import torch
from models.registry import ModelRegistry
from models.base import Segmenter


# 配置日志
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class InferenceEngine:
    """推理引擎，管理模型加载和推理流程"""
    
    # 支持的图像扩展名
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    
    def __init__(self, model_name: str, weights_path: Optional[str] = None, device: Optional[str] = None):
        """初始化推理引擎
        
        Args:
            model_name: 模型名称（如 "DCNet", "SEAFNet"）
            weights_path: 权重文件路径（相对路径），可选
            device: 设备（'cuda' 或 'cpu'），如果为None则自动检测
            
        Raises:
            KeyError: 模型未注册
        """
        # 获取模型类
        try:
            model_class = ModelRegistry.get(model_name)
        except KeyError as e:
            available = ModelRegistry.list_models()
            raise KeyError(
                f"模型 '{model_name}' 未注册。可用模型: {available}。"
                f"请确保模型已正确注册到 ModelRegistry。"
            ) from e
        
        # 实例化模型
        self.model: Segmenter = model_class()
        self.model_name = model_name
        self._loaded = False
        self.weights_path = weights_path
        
        # 设置设备
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"[InferenceEngine] 初始化完成 - 模型: {model_name}, 设备: {self.device}")
        
        # 如果提供了权重路径，自动加载
        if weights_path:
            self.load(weights_path=weights_path, model_name=model_name)
    
    def load(self, weights_path: Optional[str] = None, model_name: Optional[str] = None,
             device: Optional[str] = None) -> None:
        """加载模型权重
        
        Args:
            weights_path: 权重文件路径（相对路径），优先参数。如果为None则尝试从registry获取默认路径
            model_name: 模型名称，如果为None则使用初始化时的模型
            device: 设备（'cuda' 或 'cpu'），如果为None则使用初始化时的设备
            
        Raises:
            FileNotFoundError: 权重文件不存在
            ValueError: 权重文件格式错误
            RuntimeError: 模型未初始化
        """
        # 使用传入的参数或默认值
        if model_name is not None:
            model_class = ModelRegistry.get(model_name)
            self.model = model_class()
            self.model_name = model_name
        
        if device is not None:
            self.device = device
        
        # 确定权重路径
        if weights_path is None:
            # 尝试从registry获取默认路径
            cfg = ModelRegistry.get_config(self.model_name)
            if cfg and "default_weights" in cfg:
                weights_path = cfg["default_weights"]
            else:
                weights_path = self.weights_path
        
        if weights_path is None:
            raise FileNotFoundError(
                f"未指定权重文件路径。请提供 weights_path 参数。\n"
                f"示例: engine.load(weights_path='weights/{self.model_name}/best_model.pth')"
            )
        
        # 检查权重文件是否存在
        if not os.path.exists(weights_path):
            abs_path = os.path.abspath(weights_path)
            raise FileNotFoundError(
                f"权重文件不存在: {weights_path}\n"
                f"绝对路径: {abs_path}\n"
                f"请检查：\n"
                f"  1. 权重文件路径是否正确\n"
                f"  2. 是否已下载训练好的模型权重\n"
                f"  3. 文件是否在正确的目录下（建议放在 weights/{self.model_name}/ 目录）"
            )
        
        # 加载权重
        try:
            start_time = time.time()
            self.model.load(weights_path)
            load_time = (time.time() - start_time) * 1000
            
            self._loaded = True
            self.weights_path = weights_path
            
            logger.info(f"[InferenceEngine] 权重加载成功 - 文件: {weights_path}, 耗时: {load_time:.2f}ms")
        except Exception as e:
            raise RuntimeError(f"加载权重失败: {str(e)}") from e
    
    def _ensure_loaded(self) -> None:
        """确保模型已加载"""
        if not self._loaded:
            raise RuntimeError(
                f"模型 '{self.model_name}' 未加载。请先调用 load() 方法加载权重。\n"
                f"示例: engine.load(weights_path='weights/{self.model_name}/best_model.pth')"
            )
    
    def _load_image(self, input_data: Union[str, np.ndarray]) -> Image.Image:
        """加载图像（从路径或numpy数组）
        
        Args:
            input_data: 图像路径（str）或numpy数组 (H, W, C) 或 (H, W)
            
        Returns:
            PIL Image对象（RGB模式）
        """
        if isinstance(input_data, str):
            # 从文件路径加载
            if not os.path.exists(input_data):
                raise FileNotFoundError(f"图像文件不存在: {input_data}")
            image = Image.open(input_data)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        elif isinstance(input_data, np.ndarray):
            # 从numpy数组加载
            if input_data.ndim == 2:
                # 灰度图
                image = Image.fromarray(input_data, mode='L').convert('RGB')
            elif input_data.ndim == 3:
                # 彩色图 (H, W, C)
                if input_data.shape[2] == 3:
                    # 确保值在0-255范围
                    if input_data.dtype != np.uint8:
                        if input_data.max() <= 1.0:
                            input_data = (input_data * 255).astype(np.uint8)
                        else:
                            input_data = np.clip(input_data, 0, 255).astype(np.uint8)
                    image = Image.fromarray(input_data, mode='RGB')
                elif input_data.shape[2] == 1:
                    # 单通道
                    image = Image.fromarray(input_data.squeeze(), mode='L').convert('RGB')
                else:
                    raise ValueError(f"不支持的图像通道数: {input_data.shape[2]}")
            else:
                raise ValueError(f"不支持的数组维度: {input_data.ndim}, shape: {input_data.shape}")
            return image
        else:
            raise TypeError(f"不支持的输入类型: {type(input_data)}, 支持 str 或 np.ndarray")
    
    def _normalize_mask(self, mask: np.ndarray) -> np.ndarray:
        """将mask归一化为0/1格式
        
        Args:
            mask: mask数组（可能是0/255或0/1）
            
        Returns:
            归一化后的mask（0或1）
        """
        # 如果最大值大于1，说明是0-255格式，转换为0-1
        if mask.max() > 1:
            mask = (mask > 127).astype(np.uint8)
        else:
            mask = mask.astype(np.uint8)
        
        # 确保只有0和1
        mask = np.clip(mask, 0, 1)
        return mask
    
    def predict(self, input_data: Union[str, np.ndarray], 
                save_output: Optional[str] = None) -> Dict[str, Any]:
        """执行推理
        
        Args:
            input_data: 输入图像，可以是文件路径（str）或numpy数组
            save_output: 输出目录路径（可选），如果提供则保存结果
        
        Returns:
            结果字典，包含：
            - 'mask': 二值mask数组（0/1），shape为 (H, W)
            - 'overlay': overlay图像的PIL Image对象
            - 'time_ms': 推理耗时（毫秒）
            - 'output_path': 输出路径（如果save_output不为None）
        
        Raises:
            RuntimeError: 模型未加载或推理失败
            FileNotFoundError: 图像文件不存在
            ValueError: 输入格式不正确
        """
        self._ensure_loaded()
        
        start_time = time.time()
        
        try:
            # 加载图像
            image = self._load_image(input_data)
            original_shape = image.size  # (W, H)
            
            # 预处理
            preprocessed = self.model.preprocess(image)
            preprocessed_shape = preprocessed.get('original_shape', (image.height, image.width))
            
            # 推理
            raw_output = self.model.infer(preprocessed)
            
            # 兼容模型输出为 dict/tuple/list
            if isinstance(raw_output, dict):
                # 已经是字典格式，直接使用
                pass
            elif isinstance(raw_output, (tuple, list)):
                # 转换为字典格式
                if len(raw_output) >= 1:
                    raw_output = {
                        'raw_output': raw_output[0],
                        'original_shape': preprocessed_shape
                    }
            else:
                # 其他格式，包装成字典
                raw_output = {
                    'raw_output': raw_output,
                    'original_shape': preprocessed_shape
                }
            
            # 后处理
            mask = self.model.postprocess(raw_output, preprocessed_shape)
            
            # 确保mask恢复原图尺寸
            mask_array = np.array(mask)
            if mask_array.shape[:2] != (image.height, image.width):
                mask_img = Image.fromarray(mask_array, mode='L')
                mask_img = mask_img.resize((image.width, image.height), Image.NEAREST)
                mask_array = np.array(mask_img)
            
            # 归一化为0/1格式
            mask_normalized = self._normalize_mask(mask_array)
            
            # 可视化
            visualizations = self.model.visualize(image, mask_normalized * 255)  # visualize需要0-255格式
            overlay = visualizations['overlay']
            
            # 计算耗时
            elapsed_ms = (time.time() - start_time) * 1000
            
            # 准备返回结果
            result = {
                'mask': mask_normalized,
                'overlay': overlay,
                'time_ms': elapsed_ms,
                'output_path': None
            }
            
            # 如果指定了保存路径
            if save_output is not None:
                os.makedirs(save_output, exist_ok=True)
                
                # 确定文件名
                if isinstance(input_data, str):
                    base_name = Path(input_data).stem
                else:
                    base_name = f"output_{int(time.time())}"
                
                # 保存mask（转换为0-255格式用于保存）
                mask_path = os.path.join(save_output, f"{base_name}_mask.png")
                mask_img_255 = Image.fromarray(mask_normalized * 255, mode='L')
                mask_img_255.save(mask_path)
                
                # 保存overlay
                overlay_path = os.path.join(save_output, f"{base_name}_overlay.png")
                overlay.save(overlay_path)
                
                result['output_path'] = {
                    'mask': mask_path,
                    'overlay': overlay_path
                }
            
            logger.info(
                f"[InferenceEngine] 推理完成 - "
                f"输入: {input_data if isinstance(input_data, str) else 'numpy_array'}, "
                f"尺寸: {original_shape}, "
                f"耗时: {elapsed_ms:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[InferenceEngine] 推理失败 - "
                f"输入: {input_data if isinstance(input_data, str) else 'numpy_array'}, "
                f"耗时: {elapsed_ms:.2f}ms, "
                f"错误: {str(e)}"
            )
            raise
    
    def predict_batch(self, input_dir: str, output_dir: str = "outputs",
                     extensions: Optional[set] = None) -> Dict[str, Any]:
        """批量推理
        
        Args:
            input_dir: 输入图像目录
            output_dir: 输出目录
            extensions: 图像扩展名集合，如果为None则使用默认的 {'.jpg', '.jpeg', '.png'}
        
        Returns:
            统计信息字典，包含：
            - 'total_count': 处理的图像数量
            - 'success_count': 成功数量
            - 'failed_count': 失败数量
            - 'total_time_ms': 总耗时（毫秒）
            - 'avg_time_ms': 平均耗时（毫秒）
            - 'failed_files': 失败的文件列表
        """
        self._ensure_loaded()
        
        if extensions is None:
            extensions = self.SUPPORTED_EXTENSIONS
        
        # 检查输入目录
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 创建输出目录结构
        mask_dir = os.path.join(output_dir, 'mask')
        overlay_dir = os.path.join(output_dir, 'overlay')
        os.makedirs(mask_dir, exist_ok=True)
        os.makedirs(overlay_dir, exist_ok=True)
        
        # 查找所有图像文件
        image_files = []
        for ext in extensions:
            image_files.extend(Path(input_dir).glob(f"*{ext}"))
            image_files.extend(Path(input_dir).glob(f"*{ext.upper()}"))
        
        image_files = sorted(set(image_files))
        
        if len(image_files) == 0:
            logger.warning(f"[InferenceEngine] 在目录 {input_dir} 中未找到图像文件")
            return {
                'total_count': 0,
                'success_count': 0,
                'failed_count': 0,
                'total_time_ms': 0.0,
                'avg_time_ms': 0.0,
                'failed_files': []
            }
        
        logger.info(f"[InferenceEngine] 开始批量推理 - 输入目录: {input_dir}, 图像数量: {len(image_files)}")
        
        # 统计信息
        total_count = len(image_files)
        success_count = 0
        failed_count = 0
        failed_files = []
        total_time_ms = 0.0
        
        # 批量处理
        for i, image_path in enumerate(image_files, 1):
            try:
                logger.info(f"[InferenceEngine] 处理 [{i}/{total_count}]: {image_path.name}")
                
                # 执行推理
                result = self.predict(str(image_path), save_output=None)
                
                # 保存结果
                base_name = image_path.stem
                mask_path = os.path.join(mask_dir, f"{base_name}_mask.png")
                overlay_path = os.path.join(overlay_dir, f"{base_name}_overlay.png")
                
                # 保存mask（转换为0-255格式）
                mask_255 = (result['mask'] * 255).astype(np.uint8)
                mask_img = Image.fromarray(mask_255, mode='L')
                mask_img.save(mask_path)
                
                # 保存overlay
                result['overlay'].save(overlay_path)
                
                success_count += 1
                total_time_ms += result['time_ms']
                
                logger.info(f"[InferenceEngine] 完成 [{i}/{total_count}]: {image_path.name}, 耗时: {result['time_ms']:.2f}ms")
                
            except Exception as e:
                failed_count += 1
                failed_files.append(str(image_path))
                logger.error(f"[InferenceEngine] 处理失败 [{i}/{total_count}]: {image_path.name}, 错误: {str(e)}")
        
        # 计算平均耗时
        avg_time_ms = total_time_ms / success_count if success_count > 0 else 0.0
        
        # 输出统计信息
        stats = {
            'total_count': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'total_time_ms': total_time_ms,
            'avg_time_ms': avg_time_ms,
            'failed_files': failed_files
        }
        
        logger.info(
            f"[InferenceEngine] 批量推理完成 - "
            f"总数: {total_count}, "
            f"成功: {success_count}, "
            f"失败: {failed_count}, "
            f"总耗时: {total_time_ms:.2f}ms, "
            f"平均耗时: {avg_time_ms:.2f}ms"
        )
        
        return stats
