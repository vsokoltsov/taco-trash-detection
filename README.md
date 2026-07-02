# Trash Annotations in Context

[![CI](https://github.com/vsokoltsov/taco-trash-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/vsokoltsov/taco-trash-detection/actions/workflows/ci.yml)

This project explores trash and litter detection using the [TACO dataset](https://github.com/pedropro/TACO) and instance detection/segmentation models.

The work is implemented primarily in Jupyter notebooks and focuses on evaluating how well different model and label configurations detect litter in real-world images.

This repository was prepared as the final project for the [Deep Learning School](https://dls.samcs.ru/) [Computer Vision course](https://dls.samcs.ru/part1). The course covers computer-vision topics including convolutional neural networks, image segmentation, and object detection.

## 🔗 Useful Links

- [TACO dataset website](http://tacodataset.org/)
- [TACO paper](https://arxiv.org/pdf/2003.06975)
- [Dataset and original implementation](https://github.com/pedropro/TACO)
- [Deep Learning School](https://dls.samcs.ru/)
- [Deep Learning School Computer Vision course](https://dls.samcs.ru/part1)
- [TorchMetrics mAP documentation](https://lightning.ai/docs/torchmetrics/stable/detection/mean_average_precision.html)
- [Torchvision Mask R-CNN v2](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn_v2.html)
- [Torchvision Faster R-CNN](https://docs.pytorch.org/vision/main/models/faster_rcnn.html)

## ❓ Problem Statement

Litter and pollution are worldwide environmental problems. Trash objects in real scenes are often small, occluded, deformed, transparent, dirty, or visually similar to the background. This makes detection in uncontrolled environments harder than detecting clean, isolated recyclable objects.

The goal of this project is to investigate whether computer vision models can detect litter instances in context and to understand which factors limit model quality.

## 🎯 Objective

This project aims to:

- train and evaluate object detection / instance segmentation models on TACO;
- compare label setups such as classless detection, top-N supercategories, and merged categories;
- diagnose why multiclass classification quality is low;
- prepare the model and notebooks for later API/service integration.

## ▶️ Demo

![](./docs/demo.gif)

## 🗂️ Dataset

The project uses [Trash Annotations in Context](https://github.com/pedropro/TACO).

Key dataset properties:

- 1,500 real-world images;
- 4,784 annotated litter instances according to the paper;
- polygon masks and bounding boxes for each litter object;
- 60 fine-grained categories grouped into 28 supercategories;
- strong class imbalance and many visually ambiguous labels.

The paper explicitly notes that all objects may be treated as one class, `litter`, and that some categories can be visually hard to distinguish. This became an important part of the experiments in this project.

## 📄 Paper Baseline

The TACO paper reports Mask R-CNN results on instance segmentation, not only bounding-box detection. The reported scores are AP-style mask metrics averaged over IoU thresholds, following the COCO-style evaluation protocol. Because of that, these numbers should not be compared directly with this project's main `bbox_map_50` metric.

The paper evaluates two taxonomy settings:

- `TACO_1`: classless litter detection/segmentation, where every annotated object is treated as `litter`;
- `TACO_10`: multiclass litter detection/segmentation using 9 frequent supercategories plus an `Other` class.

The table below reports the paper's AP-style mask results:

| Dataset | Class score | Litter score | Ratio score |
|:--|--:|--:|--:|
| TACO_1 | $15.9 \pm 1.0$ | $26.2 \pm 1.0$ | $26.1 \pm 1.0$ |
| TACO_10 | $17.6 \pm 1.6$ | $18.4 \pm 1.5$ | $19.4 \pm 1.5$ |

The three columns use different prediction ranking strategies:

- **Class score** uses the maximum class probability among foreground classes. It is most relevant for multiclass classification.
- **Litter score** uses the probability of being any litter object rather than background. It is especially relevant for classless litter detection.
- **Ratio score** compares the strongest foreground class probability against the background probability.

The paper defines the scores as:

$$
Scores =
\begin{cases}
\max_i p_i, & \text{class score} \\
1 - p_{N+1}, & \text{litter score} \\
\frac{\max_i p_i}{p_{N+1} + \epsilon}, & \text{ratio score}
\end{cases}
$$

where $p_{N+1}$ is the background probability.

In this project, the course target metric is bbox `mAP@0.5`, so the paper's mask AP values are used as context rather than as a strict baseline. The important qualitative comparison is consistent: classless litter detection is easier than fine-grained multiclass litter classification.

## 📶 Evaluation Metrics

The main project metric is bbox mean average precision:

- `bbox_map_50`: bounding-box mAP at IoU threshold 0.5;
- `bbox_map`: COCO-style bbox mAP averaged over multiple IoU thresholds;
- `bbox_mar_100`: mean average recall with up to 100 detections;
- `class_accuracy_on_matches`: class accuracy only for predictions matched to a ground-truth box at IoU >= 0.5;
- `match_rate`: fraction of ground-truth objects that received a matched prediction.

The course requirement scores `mAP@0.5` as:

- `mAP@0.5 < 0.6` - 1 point;
- `mAP@0.5 >= 0.6` - 4 points.

## ⚙️ Environment

The notebooks were run in:

- [Google Colab](https://colab.research.google.com/);
- [Thunder Compute](https://www.thundercompute.com/) with NVIDIA A100 GPU.

The notebooks are adjusted for remote GPU training, checkpoint saving, TensorBoard logging, and CSV-based experiment tracking.

## 🤖 Models

Current implementation status:

- [Mask R-CNN / Matterport reference implementation](https://github.com/matterport/mask_rcnn) is the only model implemented in the current version of the project.

Other architectures are planned for future iterations:

- [Torchvision Mask R-CNN ResNet50-FPN v2](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn_v2.html);
- [Torchvision Faster R-CNN ResNet50-FPN v2](https://docs.pytorch.org/vision/main/models/faster_rcnn.html);
- [YOLOv8](https://docs.ultralytics.com/models/yolov8);
- [YOLO11](https://docs.ultralytics.com/models/yolo11).

The experimental notes below include conclusions from exploratory model comparisons made during research. The productionized project code currently focuses on Mask R-CNN v1.

### Inference format

The web service runs inference using the model exported to **ONNX format**, not the original PyTorch checkpoint. This removes the PyTorch and torchvision dependencies from the production container, reducing the image size and improving startup time.

The export process is documented and implemented in [`notebooks/06_inference.ipynb`](notebooks/06_inference.ipynb), which covers:

- wrapping the Mask R-CNN model for single-image ONNX-compatible I/O;
- exporting with `opset_version=12` using tracing-based export;
- validating the exported model against the PyTorch original using IoU-based detection matching;
- running inference with ONNX Runtime (`onnxruntime-gpu` on Linux, `onnxruntime` on macOS).

> **Note:** `dynamo=True` export is not supported for Mask R-CNN because the RPN uses data-dependent NMS whose output size cannot be resolved statically at export time. Tracing-based export (`dynamo=False`) is the only viable option for this architecture.

## 🏆 Best Model Results

The best model is **Mask R-CNN v1** (`v1_small_objects_cosine_stage_3_25`, epoch 15) trained with the following configuration:

- **Taxonomy**: official `map_17` class map (17 classes from the TACO authors)
- **Anchors**: custom small-object anchor scales `(8, 16, 32)` at P2 FPN level
- **Input**: multi-scale training `(800, 1024, 1280)` px, fixed `1024` px at inference
- **Augmentation**: horizontal flip, brightness/contrast, random scale, rotation, Gaussian blur, CLAHE
- **Training**: full backbone fine-tuning with differential learning rates; cosine annealing schedule

### Metrics (single-split validation, score threshold 0.05)

| Metric | Value |
|:--|--:|
| bbox mAP@0.5 | **0.187** |
| bbox mAP (all IoU) | 0.126 |
| segm mAP@0.5 | ~0.172 |
| segm mAP (all IoU) | ~0.125 |
| match rate | 0.482 |
| class accuracy on matches | 0.557 |
| map\_small | 0.013 |
| Dice (mask) | 0.883 |

### TACO-10 comparison

Evaluated on the official TACO-10 taxonomy (same 10 classes as the paper), the model achieves **segm mAP ≈ 12.5%** vs the paper's reported **19.4% ± 1.5%**.

The gap is explained by three structural differences:
1. **Cigarette class is permanently zero** — the `map_17` taxonomy groups Cigarettes into `Other`, so the model never learned to predict them as a separate class. This alone accounts for roughly 2 percentage points.
2. **Single train/val split** vs the paper's 4-fold cross-validation.
3. **Fewer training epochs** (~30 effective epochs on the new taxonomy vs the paper's 100).

### Key observations

- **Class taxonomy is the dominant factor.** Switching from the ad-hoc top-10 setup to the official `map_17` taxonomy improved bbox mAP@0.5 from 0.118 → 0.176 (+49%) in a single training run.
- **Backbone unfreezing is the second largest lever** (+0.021 mAP over heads-only training).
- **Small objects remain the main limitation.** `map_small = 0.013` — tiny objects (cigarette butts, pop tabs, bottle caps) are detected only occasionally. Adding smaller FPN anchors (8 px at P2) improved `map_small` from 0.002 to 0.013 (6.5×), but further improvement requires copy-paste augmentation or higher-resolution training.
- **Segmentation quality is high for detected objects.** Dice score of 0.883 means the mask shape is accurate when an object is found — the bottleneck is detection recall, not mask precision.
- **ratio\_score did not improve mAP** for this model, unlike what the paper reports for their implementation.

### Progress across experiments

| Stage | bbox mAP@0.5 |
|:--|--:|
| Baseline heads-only, top-10 classes | 0.118 |
| Backbone unfrozen | 0.139 |
| Small anchors + map\_17 taxonomy | 0.176 |
| Correct LR warm restart (stage 3) | **0.187** |

---

## 🌐 API

The detection service exposes two endpoints served by FastAPI + ONNX Runtime.

### `POST /detect`

Returns an annotated JPEG image with bounding boxes and optional segmentation masks drawn directly on the source image.

**Request** — `multipart/form-data`

| Field | Type | Description |
|:--|:--|:--|
| `file` | file | Source image (JPEG, PNG, WebP) |
| `score_thresh` | float | Confidence threshold (default `0.20`) |
| `show_masks` | bool | Overlay segmentation masks (default `false`) |

**Response** — `image/jpeg`

The image is resized to `1280 × 1024` px with coloured bounding boxes and label badges. Each class has a consistent colour across calls.

---

### `POST /detect/json`

Returns structured detection results as JSON.

**Request** — `multipart/form-data`

| Field | Type | Description |
|:--|:--|:--|
| `file` | file | Source image |
| `score_thresh` | float | Confidence threshold (default `0.20`) |

**Response** — `application/json`

```json
{
  "detections": [
    {
      "label": "Can",
      "score": 0.82,
      "box": [120.4, 88.1, 310.7, 295.3]
    }
  ]
}
```

`box` is in `[x1, y1, x2, y2]` format (xyxy), pixel coordinates relative to the `1280 × 1024` output resolution.

---

### `GET /health`

Returns `{"status": "ok"}` when the model is loaded and ready. Returns `503` while the model is still downloading or loading at startup.

---

## 🚀 Running the Project

### Requirements

| Tool | Purpose | Install |
|:--|:--|:--|
| **Docker** | Container runtime for the API and UI services | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | Multi-service orchestration | bundled with Docker Desktop |
| **Make** | Convenience wrapper for common commands | pre-installed on macOS/Linux |
| **uv** | Python package manager (dev/test only) | `curl -Lsf https://astral.sh/uv/install.sh \| sh` |

> **Note:** The project was developed and tested on **macOS with Docker Desktop (Apple Silicon)**. The API container is built for `linux/amd64` via emulation (`platform: linux/amd64` in `docker-compose.yml`). Build times on Apple Silicon are slower than on a native Linux host due to QEMU emulation.

### Quick start

```bash
# 1. Clone the repository
git clone https://github.com/vsokoltsov/taco-trash-detection.git
cd taco-trash-detection

# 2. Create a .env file with your model path
cp .env.example .env
# edit .env and set MASK_RCNN_V1_PATH, STORAGE, USE_GPU

# 3. Start the services
docker compose up --build
```

- **API** → http://localhost:8000
- **API docs** → http://localhost:8000/docs
- **UI** → http://localhost:8501

### Environment variables (`.env`)

| Variable | Description | Example |
|:--|:--|:--|
| `MASK_RCNN_V1_PATH` | Google Drive URL or GCS path to the ONNX model | `https://drive.google.com/uc?id=...` |
| `STORAGE` | Storage backend (`gdrive` or `gcp`) | `gdrive` |
| `USE_GPU` | Enable CUDA inference (`true` / `false`) | `false` |

### Local development (without Docker)

```bash
# Install dev dependencies
uv sync --extra dev

# Run checks
make check      # lint + typecheck + tests

make lint       # ruff check only
make typecheck  # ty check only
make test       # pytest only
make fix        # auto-fix lint + format
```

### Docker services

| Service | Image | Port |
|:--|:--|:--|
| `api` | CUDA 12.4 + Ubuntu 22.04 + Python 3.12 | `8000` |
| `ui` | python:3.12-slim | `8501` |

On a Linux GPU server (with the NVIDIA Container Toolkit installed), GPU inference is enabled automatically via the `deploy.resources` section in `docker-compose.yml`. On macOS, set `USE_GPU=false` to use CPU inference.
