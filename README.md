# 文物纹样分割推理系统

一个可部署的文物纹样分割推理系统，支持多种分割模型。

## 项目结构

```
relic_seg_system/
├── app.py                 # 主应用入口
├── core/
│   └── engine.py         # 推理引擎
├── models/
│   ├── base.py           # Segmenter 统一接口
│   ├── registry.py       # 模型注册表
│   └── dcnet_wrapper.py  # DCNet 模型包装器
├── utils/
│   └── visualize.py      # 可视化工具
├── tools/
│   └── smoke_test.py     # 冒烟测试
├── demo/                 # 示例图像目录
├── weights/              # 模型权重目录
├── outputs/              # 输出结果目录
├── requirements.txt      # 依赖列表
└── README.md            # 本文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 冒烟测试

运行冒烟测试验证系统基本功能：

```bash
python tools/smoke_test.py
```

测试会：
- 读取 `demo/sample_001.jpg`
- 使用 DCNet 模型进行推理（占位实现）
- 在 `outputs/` 目录下保存 `mask.png` 和 `overlay.png`

### 2. 命令行使用

```bash
# 基本用法
python app.py --input demo/sample_001.jpg

# 指定模型和权重
python app.py --model DCNet --weights weights/dcnet.pth --input demo/sample_001.jpg

# 自定义输出目录
python app.py --input demo/sample_001.jpg --output my_outputs

# 只保存mask
python app.py --input demo/sample_001.jpg --save-mask --no-save-overlay
```

## 接口说明

### Segmenter 接口

所有模型必须实现 `Segmenter` 接口，包含以下方法：

- `load(weights_path)`: 加载模型权重
- `preprocess(image)`: 图像预处理
- `infer(preprocessed_data)`: 模型推理
- `postprocess(raw_output, original_shape)`: 后处理生成mask
- `visualize(image, mask)`: 可视化结果

### 添加新模型

1. 在 `models/` 目录下创建 `<model_name>_wrapper.py`
2. 实现 `Segmenter` 接口
3. 在 `models/registry.py` 中注册模型：

```python
from models.registry import ModelRegistry
from models.your_model_wrapper import YourModelWrapper

ModelRegistry.register("YourModel", YourModelWrapper)
```

## 可视化

系统支持两种可视化方式：

1. **mask图像**: 纯黑白二值mask
2. **overlay图像**: mask区域半透明着色叠加在原图上，背景保持不变

## 注意事项

- 所有路径使用相对路径，不要硬编码绝对路径
- DCNet 的 `build_model()` 目前为 TODO 占位，需根据实际模型实现
- 系统仅用于推理，不包含训练逻辑
- 确保异常提示清晰，便于调试

## 开发规范

- 严格遵循目录结构
- 新增模型只允许修改 `models/<name>_wrapper.py` 和 `models/registry.py`
- 所有模型必须实现 `Segmenter` 接口
- 后端先通过 smoke test，再进行 UI 开发
