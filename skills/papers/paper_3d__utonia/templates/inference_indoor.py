"""Utonia indoor scene feature extraction template."""

import torch
import numpy as np
import utonia


def load_model(repo_id="Pointcept/Utonia"):
    model = utonia.model.load("utonia", repo_id=repo_id).cuda()
    model.eval()
    return model


def extract_features(model, coord, color=None, normal=None, scale=50):
    """Extract per-point features from an indoor point cloud.

    Args:
        model: Loaded Utonia model
        coord: (N, 3) numpy array of xyz coordinates
        color: (N, 3) numpy array of RGB values, optional
        normal: (N, 3) numpy array of surface normals, optional
        scale: Grid sampling scale (larger = finer)

    Returns:
        feat: (N, C) tensor of per-point features
    """
    point = {"coord": coord}
    if color is not None:
        point["color"] = color
    if normal is not None:
        point["normal"] = normal

    transform = utonia.transform.default(
        scale=scale,
        apply_z_positive=True,
        normalize_coord=False,
    )
    point = transform(point)
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)

    with torch.no_grad():
        point = model(point)

    # Unpool to original resolution
    for _ in range(2):
        parent = point.pop("pooling_parent")
        inverse = point.pop("pooling_inverse")
        parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
        point = parent
    while "pooling_parent" in point.keys():
        parent = point.pop("pooling_parent")
        inverse = point.pop("pooling_inverse")
        parent.feat = point.feat[inverse]
        point = parent

    return point.feat[point.inverse]


if __name__ == "__main__":
    model = load_model()
    point = utonia.data.load("sample1")
    feat = extract_features(model, point["coord"], point.get("color"), point.get("normal"))
    print(f"Feature shape: {feat.shape}")
