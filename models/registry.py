"""模型注册表"""
from typing import Dict, Type, Optional
from models.base import Segmenter


class ModelRegistry:
    """模型注册表，管理所有可用的分割模型"""
    
    _registry: Dict[str, Type[Segmenter]] = {}
    _configs: Dict[str, Dict] = {}
    
    @classmethod
    def register(cls, name: str, model_class: Type[Segmenter]) -> None:
        """注册模型类
        
        Args:
            name: 模型名称（如 "DCNet"）
            model_class: 实现 Segmenter 接口的模型类
            
        Raises:
            ValueError: 模型名称已存在或类未实现 Segmenter 接口
        """
        if name in cls._registry:
            raise ValueError(f"模型 '{name}' 已注册")
        
        if not issubclass(model_class, Segmenter):
            raise ValueError(f"模型类必须实现 Segmenter 接口")
        
        cls._registry[name] = model_class
    
    @classmethod
    def get(cls, name: str) -> Type[Segmenter]:
        """获取模型类
        
        Args:
            name: 模型名称
            
        Returns:
            模型类
            
        Raises:
            KeyError: 模型未注册
        """
        if name not in cls._registry:
            available = ", ".join(cls._registry.keys()) if cls._registry else "无"
            raise KeyError(f"模型 '{name}' 未注册。可用模型: {available}")
        
        return cls._registry[name]
    
    @classmethod
    def list_models(cls) -> list:
        """列出所有已注册的模型名称
        
        Returns:
            模型名称列表
        """
        return list(cls._registry.keys())
    
    @classmethod
    def clear(cls) -> None:
        """清空注册表（主要用于测试）"""
        cls._registry.clear()
    
    @classmethod
    def set_config(cls, name: str, config: Dict) -> None:
        """设置模型配置
        
        Args:
            name: 模型名称
            config: 配置字典，包含 weights_dir, default_weights, input_size, mean, std, threshold 等
        """
        cls._configs[name] = config
    
    @classmethod
    def get_config(cls, name: str) -> Optional[Dict]:
        """获取模型配置
        
        Args:
            name: 模型名称
            
        Returns:
            配置字典，如果不存在则返回None
        """
        return cls._configs.get(name)


# 自动注册 DCNet
from models.dcnet_wrapper import DCNetWrapper
ModelRegistry.register("DCNet", DCNetWrapper)
ModelRegistry.set_config("DCNet", {
    "weights_dir": "weights/DCNet",
    "default_weights": "weights/DCNet/best_model_dcnet.pth",
    "input_size": (512, 512),  # (W, H)
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225],
    "threshold": 0.5,
    "num_classes": 2
})

# 自动注册 SEAFNet
from models.seafnet_wrapper import SEAFNetWrapper
ModelRegistry.register("SEAFNet", SEAFNetWrapper)
ModelRegistry.set_config("SEAFNet", {
    "weights_dir": "weights/SEAFNet",
    "default_weights": "weights/SEAFNet/best_model_seafnet.pth",
    "input_size": (512, 512),  # (W, H)
    "mean": [0.485, 0.456, 0.406],
    "std": [0.229, 0.224, 0.225],
    "threshold": 0.5,
    "num_classes": 2
})