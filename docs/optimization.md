# Optimization Strategies for Low-Resource Systems

- Use EfficientNet-B0 or ResNet18 with 224x224 input
- Quantize linear layers with dynamic quantization
- Cache preprocessed frames for videos
- Early exit: stop video analysis after stable confidence
- Use batch inference for frame-level scoring
- Limit max frames (24 to 32) per video
- Reduce model size with pruning or weight sharing
- Use ONNX Runtime for CPU inference (optional)
