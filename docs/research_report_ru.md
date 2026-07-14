# Research Report: TACO Trash Detection And Segmentation

## 1. Постановка задачи

Цель проекта - обучить модель компьютерного зрения для поиска объектов мусора на изображениях из датасета TACO. В проекте рассматривались две близкие задачи:

- **Object detection**: найти bounding boxes объектов мусора и определить класс каждого объекта.
- **Instance segmentation**: дополнительно предсказать маску каждого найденного объекта.

Практическая цель исследования - получить модель, которую можно использовать в веб-приложении для разметки изображений мусора. Исследовательская цель - сравнить несколько архитектур, понять ограничения датасета и проверить гипотезы о том, почему качество моделей остается низким при большом количестве классов.

Основные ноутбуки исследования:

- [`notebooks/01_data_loading.ipynb`](../notebooks/01_data_loading.ipynb) - загрузка TACO и построение object-level dataframe.
- [`notebooks/02_eda.ipynb`](../notebooks/02_eda.ipynb) - EDA: классы, supercategories, размеры объектов, количество объектов на изображение.
- [`notebooks/03_train.ipynb`](../notebooks/03_train.ipynb) - базовое обучение Mask R-CNN.
- [`notebooks/04_experiments.ipynb`](../notebooks/04_experiments.ipynb) - проверка гипотез о классах, sampler, bbox и размере объектов.
- [`notebooks/05_mask_rcnn_v1.ipynb`](../notebooks/05_mask_rcnn_v1.ipynb) - основной pipeline Mask R-CNN v1.
- [`notebooks/05_mask_rcnn_v2.ipynb`](../notebooks/05_mask_rcnn_v2.ipynb) - эксперименты с Mask R-CNN v2.
- [`notebooks/05_fast_rcnn.ipynb`](../notebooks/05_fast_rcnn.ipynb) - Faster R-CNN baseline.
- [`notebooks/05_yolo_v8.ipynb`](../notebooks/05_yolo_v8.ipynb) - YOLOv8 baseline.
- [`notebooks/05_yolo_v11.ipynb`](../notebooks/05_yolo_v11.ipynb) - YOLO11 experiments and final model.

## 2. Датасет и EDA

Использовался датасет [TACO: Trash Annotations in Context](https://arxiv.org/pdf/2003.06975). Аннотации содержат изображения, bounding boxes, polygon segmentations, object classes, supercategories и scene-level метаданные.

Важные наблюдения из EDA:

- Датасет сильно несбалансирован по классам: часть классов встречается часто, часть - единично.
- На одном изображении может быть много объектов, иногда десятки объектов.
- Значительная часть объектов маленькая относительно размера изображения.
- Категории визуально близки: разные типы пластика, крышек, упаковок и бутылок часто похожи между собой.
- Catch-all категории вроде `Other` или `Unlabeled litter` ухудшают классификацию, потому что объединяют визуально разные объекты.

Вывод из EDA: задача сложна не только из-за архитектуры модели, но и из-за свойств данных - мелкие объекты, class imbalance, class ambiguity и noisy labels.

## 3. Метрика

Основная метрика проекта - **bounding-box mAP@0.5**.

Для одного класса Average Precision считается как площадь под precision-recall кривой:

```math
AP_c = \\int_0^1 p_c(r)\\,dr
```

Mean Average Precision усредняет AP по классам:

```math
mAP = \\frac{1}{C}\\sum_{c=1}^{C} AP_c
```

В `mAP@0.5` предсказание считается правильным, если IoU между предсказанным и ground-truth bounding box не меньше `0.5`:

```math
IoU(B_p, B_{gt}) = \\frac{|B_p \\cap B_{gt}|}{|B_p \\cup B_{gt}|}
```

Дополнительно использовались:

- `bbox mAP@0.5:0.95` - COCO-style mAP, усредненный по IoU thresholds от `0.5` до `0.95`.
- `bbox mAP@0.75` - более строгая локализационная метрика.
- `bbox mAR@100` - recall при ограничении до 100 детекций.
- `match_rate` - доля GT объектов, для которых нашлось предсказание с IoU >= 0.5.
- `class_accuracy_on_matches` - точность классификации среди matched объектов.
- Для Mask R-CNN дополнительно считались segmentation mAP, Dice, generalized Dice и mask mIoU.

В статье TACO приводятся AP-style instance segmentation scores: `Class score`, `Litter score`, `Ratio score`. Эти значения связаны с COCO-style AP по маскам и не являются прямым аналогом `bbox mAP@0.5`, поэтому использовались только как контекст.

## 4. Проверенные архитектуры

### Mask R-CNN v1

Mask R-CNN v1 использовалась как основная двухстадийная segmentation architecture. Модель предсказывает bounding boxes, классы и instance masks. Эксперименты включали:

- heads-only training;
- full fine-tuning;
- merged taxonomy;
- оригинальные bbox vs mask-derived bbox;
- small-object anchors;
- copy-paste augmentation для маленьких объектов;
- threshold tuning.

Лучший Mask R-CNN v1 результат:

- `bbox mAP@0.5 = 0.187`;
- `bbox mAP@0.5:0.95 = 0.126`.

### Mask R-CNN v2

Mask R-CNN v2 была проверена как более современный TorchVision вариант. Были сделаны heads stage и несколько циклов full fine-tuning, но модель стабильно уступала v1.

Лучший результат:

- `bbox mAP@0.5 ≈ 0.079`;
- `bbox mAP@0.5:0.95 ≈ 0.035`.

Вывод: в текущем pipeline v2 не дала улучшения и не использовалась как production model.

### Faster R-CNN

Faster R-CNN проверялась как detection-only baseline без mask branch. Логика была аналогична Mask R-CNN: сначала raw top-10 classes, затем merged taxonomy и full fine-tuning.

Лучший результат:

- `bbox mAP@0.5 = 0.143`;
- `bbox mAP@0.5:0.95 = 0.096`.

Merged taxonomy улучшила Faster R-CNN, но модель осталась существенно слабее YOLO.

### YOLOv8m

YOLOv8m использовалась как one-stage detector baseline. Уже короткий smoke-test показал, что YOLO быстрее обучается и дает более сильный bbox результат, чем Mask/Faster R-CNN.

Финальный YOLOv8m результат:

- `bbox mAP@0.5 = 0.327`;
- `bbox mAP@0.5:0.95 = 0.263`.

### YOLO11

YOLO11 проверялась в нескольких вариантах:

- YOLO11m;
- YOLO11l;
- YOLO11x;
- exact top-10 classes;
- merged top-10 classes;
- filtered top-5 classes.

Лучший результат достигнут моделью **YOLO11l top-5**:

- `bbox mAP@0.5 = 0.502`;
- `bbox mAP@0.5:0.95 = 0.350`;
- `precision = 0.592`;
- `recall = 0.497`.

Эта модель была выбрана для inference, потому что единственная достигла целевого порога `mAP@0.5 >= 0.5`. Важно: она решает более узкую задачу, так как поддерживает только 5 классов.

## 5. Результаты

### 5.1 Сравнение лучших моделей

![Best validation metrics by architecture](plots/model_comparison.svg)

| Model | Task | bbox mAP@0.5 | bbox mAP@0.5:0.95 |
|:--|:--|--:|--:|
| Mask R-CNN v1 | Detection + segmentation | 0.187 | 0.126 |
| Mask R-CNN v2 | Detection + segmentation | 0.079 | 0.035 |
| Faster R-CNN | Detection | 0.143 | 0.096 |
| YOLOv8m | Detection | 0.327 | 0.263 |
| YOLO11l top-5 | Detection | **0.502** | **0.350** |

Главный вывод: YOLO models оказались заметно эффективнее для bounding-box detection на этом датасете. Двухстадийные модели давали полезные диагностические результаты, но не достигали сравнимого качества.

### 5.2 Mask R-CNN v1 progression

![Mask R-CNN v1 improvements](plots/mask_rcnn_v1_progression.svg)

Mask R-CNN v1 улучшалась постепенно:

- merged taxonomy уменьшила class confusion;
- full fine-tuning улучшил backbone features;
- small-object anchors помогли маленьким объектам;
- copy-paste augmentation дала небольшой общий прирост, но могла ухудшать `map_small`.

Несмотря на улучшения, итоговый результат остался ниже YOLOv8/YOLO11.

### 5.3 Faster R-CNN ablation

![Faster R-CNN ablation](plots/faster_rcnn_ablation.svg)

Faster R-CNN подтвердил важность label taxonomy. Переход от exact top-10 к merged classes поднял `mAP@0.5` примерно с `0.083` до `0.143`. Однако дальнейшее обучение быстро насыщалось: match rate оставался около `0.35-0.39`, то есть большая часть объектов все еще не находилась с IoU >= 0.5.

### 5.4 Влияние количества классов

![Class granularity](plots/class_granularity.svg)

Гипотеза "слишком много классов ухудшает detection quality" подтвердилась:

- classless setup дал самый высокий mAP среди быстрых проверок;
- top-5 был лучше top-10;
- class accuracy падала при увеличении количества классов.

Это означает, что основная проблема не только в локализации, но и в неоднозначной классификации TACO-категорий.

### 5.5 YOLO и taxonomy trade-off

![YOLO taxonomy comparison](plots/yolo_taxonomy_comparison.svg)

YOLO11l top-5 достиг целевого `mAP@0.5 >= 0.5`, но top-10 и merged top-10 не смогли повторить этот результат. Следовательно, уменьшение числа классов улучшает метрику, но снижает практическое покрытие приложения.

## 6. Проверенные гипотезы

### Гипотеза 1: слишком большое количество классов ухудшает качество детекции

Подтвердилась. Classless и top-5 setups были лучше top-10. Увеличение числа классов снижало `class_accuracy_on_matches` и mAP.

### Гипотеза 2: некоторые классы являются шумными и ухудшают обучение

Частично подтвердилась. Ошибки часто концентрировались вокруг визуально близких и catch-all классов. Это объясняет, почему merging и фильтрация классов улучшали результаты.

### Гипотеза 3: weighted sampler усиливает путаницу между классами

Не дала сильного подтверждения. Sampler не решил ключевую проблему class ambiguity и не стал основным инструментом улучшения.

### Гипотеза 4: модели нужно меньше категорий, а не больше эпох

Подтвердилась. Дополнительные эпохи часто приводили к plateau, тогда как уменьшение/слияние классов давало более заметное изменение качества.

### Гипотеза 5: выбор между оригинальными bbox и bbox из масок влияет на качество

Подтвердилась частично. Для detection models логичнее использовать оригинальные bbox из аннотаций, а mask-derived bbox полезны только при сильных geometric transforms.

### Гипотеза 6: размер объектов является одной из главных причин низкого качества

Подтвердилась. Маленькие объекты были слабым местом Mask R-CNN. Small anchors улучшили `map_small`, но не решили задачу полностью.

### Гипотеза 7: класс "Other" слишком широкий

Подтвердилась. `Other` объединяет визуально разные объекты, что ухудшает классификацию. Удаление или замена catch-all класса на более осмысленную taxonomy улучшает стабильность.

### Гипотеза 8: комбинация улучшений должна давать лучший результат

Комбинация merged taxonomy, full fine-tuning, tuned thresholds, small-object anchors и augmentation дала лучший Mask R-CNN v1 результат, но все равно уступила YOLO.

## 7. Анализ ошибок

Основные причины ограниченного качества:

1. **Мелкие объекты.** Много объектов занимает очень малую часть изображения, что усложняет локализацию.
2. **Классовая неоднозначность.** Похожие категории отличаются тонкими визуальными признаками.
3. **Несбалансированность классов.** Редкие классы дают нестабильную оценку и низкий AP.
4. **Catch-all labels.** `Other` и `Unlabeled litter` не являются визуально однородными классами.
5. **Много объектов в сцене.** Некоторые изображения содержат большое число объектов, что увеличивает количество false positives и missed detections.
6. **Разные цели моделей.** Mask R-CNN оптимизирует также mask branch, тогда как итоговая метрика проекта - bbox mAP@0.5.

## 8. Что можно улучшить дальше

Потенциальные улучшения:

- Собрать более чистую taxonomy без broad `Other` classes.
- Доразметить или удалить редкие/noisy classes.
- Использовать cross-validation для более надежной оценки.
- Настроить small-object augmentation и tiling, но осторожно: SAHI в текущих проверках увеличивал число false positives.
- Проверить YOLO segmentation models, если нужны masks.
- Использовать semi-supervised relabeling или manual review для спорных классов.
- Подбирать confidence/NMS thresholds отдельно для production inference и для validation reporting.

## 9. Итоговый вывод

Исследование показало, что качество модели сильнее всего зависит не только от архитектуры, но и от постановки class taxonomy. Двухстадийные модели Mask R-CNN и Faster R-CNN полезны для анализа и segmentation, но на TACO они достигли сравнительно низкого bbox mAP. YOLOv8 и YOLO11 оказались значительно сильнее для bounding-box detection.

Лучшей моделью стала **YOLO11l top-5**, достигшая:

- `bbox mAP@0.5 = 0.502`;
- `bbox mAP@0.5:0.95 = 0.350`.

Именно эта модель выбрана для inference в приложении. Ограничение результата состоит в том, что модель поддерживает только 5 классов, поэтому фактическое покрытие мусорных категорий уже, чем у broader taxonomy models. Тем не менее это единственный проверенный вариант, который достиг целевого качества по основной метрике.
