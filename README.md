# Trash Annotations in Context

This project is implementation of service for detection of trash and litter based on its image

## 🔗Useful links

* [Official website](http://tacodataset.org/)
* [Paper](https://arxiv.org/pdf/2003.06975)
* [Dataset + implementation](https://github.com/pedropro/TACO)

## ❓Problem statement

Litter and polution is a world-wide problem. Every year more and more square meters are becoming inhabitat and poison water and soil. At the same time, in the city environment it might be complicated to quickly determine the litter. Could machine learning and computer vision models help solving this environmental hazard?

## 🎯Objective

This project aims to:
* Provide solution for detection of trash based on its image
* Pack the solution into API service for further usage
* [Optional] provide solution better than initial model

## 🗂️Dataset

For this issue, the dataset of [trash annotations in context](http://tacodataset.org/) was chosen

* It consists of 1500 images with multiple litter elements.
* Each image has multiple `masks` and `bbox` definitions for objects that were marked as trash

## 📊Initial metrics

* Related [paper](https://arxiv.org/pdf/2003.06975) provided these metrics:

| Dataset  | Class score  | Litter score | Ration score  |
|:--------:|:------------:|:------------:|:-------------:|
|  TACO_1  | $15.9 \pm 1.0$  | $26.2 \pm 1.0$ | $26.1 \pm$ |
|  TACO_10 | $17.6 \pm 1.6$  | $18.4 pm 1.5$  | $19.4 \pm 1.5$ |

Where `score` are defined as:

$$
\Large Scores = 
\begin{cases}
max_i p_i, \hspace{25pt} \text{class score} \\
1 - p_{N+1}, \hspace{15pt} \text{litter score} \\
\frac{max_i p_i}{p_{N+1} + \epsilon}, \hspace{35pt} \text{ratio score}
\end{cases}
$$

* According to paper, the metrics are related to masks task, not detection


## 📶Evaluation metrics

* For the evaluation metric, [mean average precision](https://lightning.ai/docs/torchmetrics/stable/detection/mean_average_precision.html) was chosen

* According to the initial requirement, validation of `mAP` for such problem scores by groups:
  * `mAP@0.5` < 0.6 – **1 point**
  * `mAP@0.5` >= 0.6 – **4 point**


## ⚙️Environment

* This project was implemented and executed in:
  * [Google Colab](https://colab.research.google.com/)
  * [Thunder compute](https://www.thundercompute.com/)
* Therefore, related notebooks will be adjusted for running it in both environments

## 🤖Model selection

* For this project, it is planned to use models:
  * [Mask RCNN v1](https://github.com/matterport/mask_rcnn)
  * [Mask RCNN v2](https://docs.pytorch.org/vision/main/models/generated/torchvision.models.detection.maskrcnn_resnet50_fpn_v2.html)
  * [Faster RCNN](https://docs.pytorch.org/vision/main/models/faster_rcnn.html)
  * [YOLO v8](https://docs.ultralytics.com/models/yolov8#overview)
  * [YOLO v11](https://docs.ultralytics.com/models/yolo11#overview)