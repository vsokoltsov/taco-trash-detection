# Trash Annotations in Context

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

The main tested models were:

- [Mask R-CNN / Matterport reference implementation](https://github.com/matterport/mask_rcnn);
- [Torchvision Mask R-CNN ResNet50-FPN v2](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn_v2.html);
- [Torchvision Faster R-CNN ResNet50-FPN v2](https://docs.pytorch.org/vision/main/models/faster_rcnn.html).

YOLO-based models were considered as possible alternatives:

- [YOLOv8](https://docs.ultralytics.com/models/yolov8);
- [YOLO11](https://docs.ultralytics.com/models/yolo11).
