"""文物纹样分割推理系统主应用"""
import os
import argparse
from core.engine import InferenceEngine
from models.registry import ModelRegistry


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="文物纹样分割推理系统")
    parser.add_argument(
        "--model",
        type=str,
        default="DCNet",
        help=f"模型名称 (可用: {', '.join(ModelRegistry.list_models())})"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="权重文件路径（相对路径）"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入图像路径（相对路径）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="输出目录（相对路径）"
    )
    parser.add_argument(
        "--save-mask",
        action="store_true",
        help="保存mask图像"
    )
    parser.add_argument(
        "--save-overlay",
        action="store_true",
        default=True,
        help="保存overlay图像（默认开启）"
    )
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        return 1
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # 创建推理引擎
        print(f"初始化模型: {args.model}")
        engine = InferenceEngine(model_name=args.model, weights_path=args.weights)
        
        # 执行推理
        print(f"执行推理: {args.input}")
        results = engine.predict(args.input)
        
        # 保存结果
        base_name = os.path.splitext(os.path.basename(args.input))[0]
        
        if args.save_mask or args.save_overlay:
            if args.save_mask:
                mask_path = os.path.join(args.output, f"{base_name}_mask.png")
                results['visualizations']['mask'].save(mask_path)
                print(f"✓ mask已保存: {mask_path}")
            
            if args.save_overlay:
                overlay_path = os.path.join(args.output, f"{base_name}_overlay.png")
                results['visualizations']['overlay'].save(overlay_path)
                print(f"✓ overlay已保存: {overlay_path}")
        
        print("✓ 推理完成")
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
