import torch
import torch.nn as nn
import torchvision.models as models


class CNNDetector(nn.Module):
    def __init__(self, backbone="resnet18", num_classes=2):
        super().__init__()
        self.backbone_name = backbone
        if backbone == "resnet18":
            model = models.resnet18(weights=None)
            in_features = model.fc.in_features
            model.fc = nn.Identity()
            self.feature_extractor = model
            self.classifier = nn.Linear(in_features, num_classes)
        elif backbone == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Identity()
            self.feature_extractor = model
            self.classifier = nn.Linear(in_features, num_classes)
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")

    def forward(self, x):
        feats = self.feature_extractor(x)
        logits = self.classifier(feats)
        return logits, feats


class ConvAutoencoder(nn.Module):
    def __init__(self, in_channels=3, latent_dim=128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, 2, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, 2, 1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, 3, 2, 1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.fc_enc = nn.Linear(128, latent_dim)
        self.fc_dec = nn.Linear(latent_dim, 128)
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, 4, 2, 1),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, in_channels, 4, 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        enc = self.encoder(x).view(x.size(0), -1)
        z = self.fc_enc(enc)
        dec = self.fc_dec(z).view(x.size(0), 128, 1, 1)
        out = self.decoder(dec)
        return out, z


class EnsembleDetector(nn.Module):
    def __init__(self, cnn: CNNDetector, ae: ConvAutoencoder, weights=(0.7, 0.3)):
        super().__init__()
        self.cnn = cnn
        self.ae = ae
        self.weights = weights

    def forward(self, x):
        logits, feats = self.cnn(x)
        recon, _ = self.ae(x)
        return logits, recon, feats

    def score(self, x):
        logits, recon, _ = self.forward(x)
        probs = torch.softmax(logits, dim=1)[:, 1]
        recon_err = torch.mean((x - recon) ** 2, dim=[1, 2, 3])
        recon_score = torch.sigmoid(recon_err * 10.0)
        final_score = self.weights[0] * probs + self.weights[1] * recon_score
        return final_score, probs, recon_score
