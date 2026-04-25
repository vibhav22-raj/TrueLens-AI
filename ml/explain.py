import cv2
import numpy as np
import torch


def _normalize_cam(cam):
    cam = np.maximum(cam, 0)
    cam = cam - cam.min()
    cam = cam / (cam.max() + 1e-8)
    return cam


class GradCAM:
    def __init__(self, model, target_layer_name):
        self.model = model
        self.target_layer_name = target_layer_name
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _get_target_layer(self):
        for name, module in self.model.named_modules():
            if name == self.target_layer_name:
                return module
        raise ValueError(f"Layer not found: {self.target_layer_name}")

    def _register_hooks(self):
        layer = self._get_target_layer()

        def fwd_hook(_, __, output):
            self.activations = output.detach()

        def bwd_hook(_, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        layer.register_forward_hook(fwd_hook)
        layer.register_full_backward_hook(bwd_hook)

    def generate(self, input_tensor, class_idx=None):
        self.model.zero_grad()
        logits, _ = self.model(input_tensor)
        if class_idx is None:
            class_idx = torch.argmax(logits, dim=1).item()
        loss = logits[:, class_idx].sum()
        loss.backward()

        grads = self.gradients
        acts = self.activations
        weights = torch.mean(grads, dim=[2, 3], keepdim=True)
        cam = torch.sum(weights * acts, dim=1).squeeze(0).cpu().numpy()
        cam = _normalize_cam(cam)
        return cam


def overlay_cam(image_bgr, cam, alpha=0.5):
    h, w = image_bgr.shape[:2]
    cam_resized = cv2.resize(cam, (w, h))
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(image_bgr, 1 - alpha, heatmap, alpha, 0)
    return overlay


def reconstruction_error_map(x, recon):
    err = (x - recon) ** 2
    err = err.mean(dim=1).squeeze(0).cpu().numpy()
    err = _normalize_cam(err)
    return err
