# 🚀 YOLOv8 安装 & 测试指南

YOLOv8 是 Ultralytics 开发的新一代目标检测模型，支持分类、检测、分割等任务。本文档指导你如何在本地环境安装 YOLOv8，并进行测试，以确保其正常运行。

## 📌 1. 环境准备

### **1.1 硬件要求**

- **GPU 推荐**：NVIDIA 显卡（建议 3060Ti 及以上）
- **CPU 可运行**，但速度较慢
- **系统兼容性**：Windows / Linux / MacOS

### **1.2 依赖项**

安装 YOLOv8 之前，需要安装 Python 及相关工具：

#### ✅ **检查 Python 版本（建议 Python 3.8+）**

```bash
python --version
```

如果 Python 版本低于 3.8，建议升级。

#### ✅ **创建虚拟环境（推荐，确保环境干净）**

```bash
# Windows（使用 PowerShell）
python -m venv yolov8_env
./yolov8_env/Scripts/activate

# Linux / MacOS
python3 -m venv yolov8_env
source yolov8_env/bin/activate
```

## 📌 2. 安装 YOLOv8

YOLOv8 由 Ultralytics 开发，可通过 pip 直接安装。

```bash
pip install ultralytics
```

### **2.1 验证安装是否成功**

```bash
python -c "from ultralytics import YOLO; print(YOLO('yolov8n.pt'))"
```

如果没有报错，则说明安装成功。

------

## 📌 3. 运行 YOLOv8 目标检测测试

### **3.1 下载预训练模型**

YOLOv8 提供多个预训练模型，适用于不同的计算能力：

| 模型         | 速度（FPS） | 精度（mAP） | 适用场景               |
| ------------ | ----------- | ----------- | ---------------------- |
| `yolov8n.pt` | 🚀 **最快**  | 🔹 较低      | 轻量级任务             |
| `yolov8s.pt` | ⚡ 快        | 🔹 一般      | 适合中小规模任务       |
| `yolov8m.pt` | ⏳ 中等      | 🔹 高        | 适合计算能力较强的显卡 |
| `yolov8l.pt` | 🐢 慢        | 🔹 更高      | 适合高性能 GPU         |
| `yolov8x.pt` | 🏋️ 最慢      | 🔹 **最高**  | 适合超高精度任务       |

### **3.2 运行目标检测（使用示例图片）**

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.pt')  # 使用 nano 版本

# 运行目标检测（官方提供的测试图片）
results = model.predict(source='https://ultralytics.com/images/zidane.jpg', save=True, conf=0.5)
```

运行完成后，会在 `runs/detect/predict` 目录下生成带有检测框的图片。

### **3.3 在本地图片上测试目标检测**

```python
# 在本地图片上测试
model.predict(source='test.jpg', save=True, conf=0.5)
```

### **3.4 在视频上进行目标检测**

```python
# 运行目标检测（本地视频）
model.predict(source='video.mp4', save=True)
```

------

## 📌 4. 训练自定义数据集

如果你想用自己的数据训练 YOLOv8，首先需要准备 YOLO 格式的数据集。

### **4.1 数据格式**

YOLO 数据格式需要以下文件结构：

```plaintext
dataset/
 ├── images/
 │   ├── train/  # 训练图片
 │   ├── val/    # 验证图片
 ├── labels/
 │   ├── train/  # 训练集标签（.txt 文件）
 │   ├── val/    # 验证集标签
 ├── data.yaml  # 数据集配置文件
```

### **4.2 创建 \**``\** 文件**

```yaml
path: ./dataset  # 数据集根目录
train: images/train  # 训练集路径
val: images/val  # 验证集路径
nc: 3  # 类别数
names: ['fire', 'smoke', 'electric_vehicle']  # 类别名称
```

### **4.3 训练 YOLOv8**

```python
# 训练 YOLOv8
model.train(data='data.yaml', epochs=50, imgsz=640, batch=8)
```

------

## 📌 5. 导出 YOLOv8 模型（部署）

YOLOv8 可以导出为多种格式，以便在不同环境中部署：

### **5.1 导出为 ONNX 格式（适用于 TensorRT 部署）**

```python
model.export(format='onnx')
```

### **5.2 导出为 TensorRT**

```python
model.export(format='engine')
```

------

## 🎯 6. 总结

### **✅ 你已经完成：**

1. **安装 YOLOv8**
2. **运行预训练模型进行目标检测**
3. **在本地图片、视频上进行推理**
4. **准备数据集，训练自己的模型**
5. **导出模型用于部署**

**🎯 你现在可以用 YOLOv8 进行目标检测任务，并准备自定义数据集训练！** 🚀