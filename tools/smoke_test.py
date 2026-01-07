"""冒烟测试：验证系统基本功能"""
import os
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.engine import InferenceEngine
from models.registry import ModelRegistry


def main():
    """运行冒烟测试"""
    parser = argparse.ArgumentParser(description="文物纹样分割系统冒烟测试")
    parser.add_argument(
        "--model",
        type=str,
        default="DCNet",
        help=f"模型名称 (默认: DCNet, 可用: {', '.join(ModelRegistry.list_models())})"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="demo/sample_001.jpg",
        help="输入图像路径 (默认: demo/sample_001.jpg)"
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        default="outputs",
        help="输出目录 (默认: outputs)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("开始冒烟测试...")
    print("=" * 50)
    print(f"模型: {args.model}")
    print(f"输入图像: {args.image}")
    print(f"输出目录: {args.out_dir}")
    print("=" * 50)
    
    # 检查输入文件
    if not os.path.exists(args.image):
        print(f"❌ 错误: 找不到测试图像 {args.image}")
        print(f"   请确保文件存在")
        return False
    
    # 检查模型是否注册
    try:
        ModelRegistry.get(args.model)
    except KeyError as e:
        available = ModelRegistry.list_models()
        print(f"❌ 错误: {str(e)}")
        print(f"   可用模型: {', '.join(available)}")
        return False
    
    # 创建输出目录
    os.makedirs(args.out_dir, exist_ok=True)
    
    try:
        # 初始化推理引擎
        print(f"\n[1/2] 初始化推理引擎...")
        engine = InferenceEngine(model_name=args.model)
        print(f"      ✓ 模型 '{args.model}' 已初始化")
        
        # 尝试加载权重
        print(f"\n[2/2] 加载模型权重...")
        try:
            # 尝试从配置获取默认权重路径
            cfg = ModelRegistry.get_config(args.model)
            if cfg and "default_weights" in cfg:
                default_weights = cfg["default_weights"]
                if os.path.exists(default_weights):
                    engine.load(default_weights)
                    print(f"      ✓ 权重已加载: {default_weights}")
                else:
                    print(f"      ⚠ 默认权重文件不存在: {default_weights}")
                    print(f"      ⚠ 使用未训练模型进行测试（结果可能不准确）")
            else:
                print(f"      ⚠ 未配置默认权重路径，使用未训练模型进行测试（结果可能不准确）")
        except Exception as e:
            print(f"      ⚠ 加载权重失败: {str(e)}")
            print(f"      ⚠ 使用未训练模型进行测试（结果可能不准确）")
        
        # 执行推理
        print(f"\n执行推理...")
        print(f"  输入: {args.image}")
        result = engine.predict(args.image)
        print(f"  ✓ 推理完成，耗时: {result['time_ms']:.2f}ms")
        
        # 保存结果
        print(f"\n保存结果...")
        
        # 生成文件名（带模型名前缀）
        model_prefix = args.model.lower()
        mask_filename = f"{model_prefix}_mask.png"
        overlay_filename = f"{model_prefix}_overlay.png"
        
        mask_path = os.path.join(args.out_dir, mask_filename)
        overlay_path = os.path.join(args.out_dir, overlay_filename)
        
        # 保存mask（转换为0-255格式）
        import numpy as np
        from PIL import Image
        mask_255 = (result['mask'] * 255).astype(np.uint8)
        mask_img = Image.fromarray(mask_255, mode='L')
        mask_img.save(mask_path)
        print(f"  ✓ mask已保存: {mask_path}")
        
        # 保存overlay
        result['overlay'].save(overlay_path)
        print(f"  ✓ overlay已保存: {overlay_path}")
        
        print("\n" + "=" * 50)
        print("✓ 冒烟测试通过！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
