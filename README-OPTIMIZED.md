# POE2 Trade Pusher 优化版打包指南

## 优化说明

为了减小打包后的程序体积，我们对打包配置进行了以下优化：

1. **排除大型深度学习依赖**：
   - 移除了 PaddleOCR、PaddlePaddle、PyTorch、TorchVision 等大型深度学习框架
   - 移除了 Ultralytics、Matplotlib、SciPy、Pandas 等数据科学库

2. **优化资源文件**：
   - 只包含必要的资源文件，如图标、物品图片和识别模板
   - 排除了大型模型文件，如 OCR 模型

3. **使用 ONNX 运行时**：
   - 使用轻量级的 ONNX 运行时替代完整的深度学习框架
   - 添加了 ONNX 运行时到 hiddenimports 列表

## 使用方法

### 准备工作

在打包前，请确保：

1. 已安装 PyInstaller：
   ```bash
   pip install pyinstaller
   ```

2. 已安装 ONNX 运行时：
   ```bash
   pip install onnxruntime
   ```

3. 将 YOLO 模型转换为 ONNX 格式并放置在正确位置：
   - 模型文件应位于 `models/poe_item_yolov12.onnx`

### 打包步骤

```bash
# 使用优化后的 spec 文件打包
pyinstaller build.spec
```

打包后的文件在 dist 目录下。

### 注意事项

1. 优化后的版本不包含 PaddleOCR 功能，如需使用该功能，请手动安装相关依赖。
2. 如果需要使用完整功能，请参考原始的 requirements.txt 安装所有依赖。
3. 优化后的版本主要针对减小打包体积，可能会影响某些高级功能的使用。