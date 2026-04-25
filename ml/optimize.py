import torch


def quantize_cnn(model):
    # Dynamic quantization for linear layers only (safe for CPU)
    qmodel = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},
        dtype=torch.qint8,
    )
    return qmodel
