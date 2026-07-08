"""Convert the COCO-style TACO dataset to YOLO detection format."""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import random
import shutil
from typing import Any

MAP_17 = {
    "Aerosol": "Can",
    "Aluminium foil": "Aluminium foil",
    "Battery": "Other",
    "Aluminium blister pack": "Other",
    "Carded blister pack": "Other",
    "Clear plastic bottle": "Plastic bottle",
    "Glass bottle": "Glass bottle",
    "Other plastic bottle": "Plastic bottle",
    "Plastic bottle cap": "Plastic bottle cap",
    "Metal bottle cap": "Metal bottle cap",
    "Broken glass": "Other",
    "Drink can": "Can",
    "Food Can": "Can",
    "Corrugated carton": "Carton",
    "Drink carton": "Carton",
    "Egg carton": "Carton",
    "Meal carton": "Carton",
    "Other carton": "Carton",
    "Paper cup": "Cup",
    "Disposable plastic cup": "Cup",
    "Foam cup": "Cup",
    "Glass cup": "Cup",
    "Other plastic cup": "Cup",
    "Food waste": "Other",
    "Plastic lid": "Plastic lid",
    "Metal lid": "Other",
    "Magazine paper": "Paper",
    "Tissues": "Paper",
    "Wrapping paper": "Paper",
    "Normal paper": "Paper",
    "Paper bag": "Paper",
    "Plastified paper bag": "Paper",
    "Pizza box": "Carton",
    "Garbage bag": "Plastic film",
    "Single-use carrier bag": "Plastic film",
    "Polypropylene bag": "Plastic film",
    "Produce bag": "Plastic film",
    "Cereal bag": "Plastic film",
    "Bread bag": "Plastic film",
    "Plastic film": "Plastic film",
    "Crisp packet": "Wrapper",
    "Other plastic wrapper": "Wrapper",
    "Retort pouch": "Wrapper",
    "Spread tub": "Plastic container",
    "Tupperware": "Plastic container",
    "Disposable food container": "Plastic container",
    "Foam food container": "Plastic container",
    "Other plastic container": "Plastic container",
    "Plastic glooves": "Other",
    "Plastic utensils": "Other",
    "Pop tab": "Pop tab",
    "Rope & strings": "Other",
    "Scrap metal": "Other",
    "Shoe": "Other",
    "Six pack rings": "Plastic film",
    "Squeezable tube": "Other",
    "Plastic straw": "Straw",
    "Paper straw": "Straw",
    "Styrofoam piece": "Styrofoam piece",
    "Toilet tube": "Carton",
    "Unlabeled litter": "Other",
    "Glass jar": "Other",
    "Other plastic": "Other",
    "Cigarette": "Other",
}


def build_class_mapping(
    categories: list[dict[str, Any]],
    taxonomy: str,
    drop_other: bool,
) -> tuple[dict[int, int | None], list[str]]:
    """Build zero-based YOLO classes from TACO category IDs."""
    categories_by_id = {int(category["id"]): category for category in categories}

    if taxonomy == "original":
        class_names = [
            str(categories_by_id[category_id]["name"]) for category_id in sorted(categories_by_id)
        ]
        source_to_yolo: dict[int, int | None] = {
            category_id: yolo_id for yolo_id, category_id in enumerate(sorted(categories_by_id))
        }
        return source_to_yolo, class_names

    mapped_names = {MAP_17.get(str(category["name"]), "Other") for category in categories}
    if drop_other:
        mapped_names.discard("Other")
    class_names = sorted(mapped_names)
    name_to_yolo = {name: class_id for class_id, name in enumerate(class_names)}

    source_to_yolo = {}
    for category_id, category in categories_by_id.items():
        mapped_name = MAP_17.get(str(category["name"]), "Other")
        source_to_yolo[category_id] = name_to_yolo.get(mapped_name)

    return source_to_yolo, class_names


def split_image_ids(
    image_ids: list[int],
    train_fraction: float,
    seed: int,
) -> tuple[set[int], set[int]]:
    """Create a deterministic image split."""
    permutation = list(range(len(image_ids)))
    random.Random(seed).shuffle(permutation)
    train_size = int(train_fraction * len(image_ids))
    train_ids = {image_ids[index] for index in permutation[:train_size]}
    val_ids = {image_ids[index] for index in permutation[train_size:]}
    return train_ids, val_ids


def convert_bbox_to_yolo(
    bbox: list[float],
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float] | None:
    """Convert and clamp a COCO ``xywh`` box to normalized YOLO coordinates."""
    x, y, width, height = (float(value) for value in bbox)
    x1 = min(max(x, 0.0), float(image_width))
    y1 = min(max(y, 0.0), float(image_height))
    x2 = min(max(x + width, 0.0), float(image_width))
    y2 = min(max(y + height, 0.0), float(image_height))

    width = x2 - x1
    height = y2 - y1
    if width <= 0.0 or height <= 0.0:
        return None

    return (
        ((x1 + x2) / 2.0) / image_width,
        ((y1 + y2) / 2.0) / image_height,
        width / image_width,
        height / image_height,
    )


def materialize_image(source: Path, destination: Path, mode: str) -> None:
    """Copy or link one source image into the YOLO directory tree."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink()

    if mode == "copy":
        shutil.copy2(source, destination)
    elif mode == "hardlink":
        os.link(source, destination)
    else:
        destination.symlink_to(source.resolve())


def write_dataset_yaml(output_dir: Path, class_names: list[str]) -> Path:
    """Write an Ultralytics dataset configuration without requiring PyYAML."""
    yaml_path = output_dir / "taco.yaml"
    lines = [
        f"path: {json.dumps(str(output_dir.resolve()))}",
        "train: images/train",
        "val: images/val",
        "names:",
    ]
    lines.extend(
        f"  {class_id}: {json.dumps(class_name)}" for class_id, class_name in enumerate(class_names)
    )
    yaml_path.write_text("\n".join(lines) + "\n")
    return yaml_path


def convert_taco_to_yolo(
    taco_dir: Path,
    output_dir: Path,
    taxonomy: str = "map17",
    drop_other: bool = False,
    train_fraction: float = 0.8,
    seed: int = 42,
    image_mode: str = "symlink",
) -> Path:
    """Convert TACO annotations and images to a YOLO detection dataset."""
    annotations_path = taco_dir / "annotations.json"
    with annotations_path.open() as file:
        coco = json.load(file)

    images = {int(image["id"]): image for image in coco["images"]}
    annotations_by_image: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for annotation in coco["annotations"]:
        annotations_by_image[int(annotation["image_id"])].append(annotation)

    source_to_yolo, class_names = build_class_mapping(
        coco["categories"], taxonomy=taxonomy, drop_other=drop_other
    )
    image_ids = sorted(images)
    train_ids, val_ids = split_image_ids(image_ids, train_fraction, seed)

    skipped_boxes = 0
    written_annotations = 0
    for image_id in image_ids:
        image = images[image_id]
        split = "train" if image_id in train_ids else "val"
        relative_image_path = Path(image["file_name"])
        source_image = taco_dir / relative_image_path
        if not source_image.is_file():
            raise FileNotFoundError(f"TACO image does not exist: {source_image}")

        image_destination = output_dir / "images" / split / relative_image_path
        materialize_image(source_image, image_destination, image_mode)

        label_path = output_dir / "labels" / split / relative_image_path.with_suffix(".txt")
        label_path.parent.mkdir(parents=True, exist_ok=True)
        label_lines = []
        for annotation in annotations_by_image.get(image_id, []):
            class_id = source_to_yolo[int(annotation["category_id"])]
            if class_id is None:
                continue

            yolo_bbox = convert_bbox_to_yolo(
                annotation["bbox"], int(image["width"]), int(image["height"])
            )
            if yolo_bbox is None:
                skipped_boxes += 1
                continue

            coordinates = " ".join(f"{value:.8f}" for value in yolo_bbox)
            label_lines.append(f"{class_id} {coordinates}")
            written_annotations += 1

        label_path.write_text("\n".join(label_lines) + ("\n" if label_lines else ""))

    output_dir.mkdir(parents=True, exist_ok=True)
    split_manifest = {
        "seed": seed,
        "train_fraction": train_fraction,
        "taxonomy": taxonomy,
        "drop_other": drop_other,
        "classes": class_names,
        "train_image_ids": sorted(train_ids),
        "val_image_ids": sorted(val_ids),
        "written_annotations": written_annotations,
        "skipped_invalid_boxes": skipped_boxes,
    }
    (output_dir / "split.json").write_text(json.dumps(split_manifest, indent=2) + "\n")
    return write_dataset_yaml(output_dir, class_names)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taco-dir", type=Path, default=Path("data/raw/taco"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/taco_yolo"))
    parser.add_argument("--taxonomy", choices=("original", "map17"), default="map17")
    parser.add_argument("--drop-other", action="store_true")
    parser.add_argument("--train-fraction", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--image-mode", choices=("symlink", "hardlink", "copy"), default="symlink")
    return parser.parse_args()


def main() -> None:
    """Run the TACO-to-YOLO conversion command."""
    args = parse_args()
    if not 0.0 < args.train_fraction < 1.0:
        raise ValueError("--train-fraction must be between 0 and 1")

    yaml_path = convert_taco_to_yolo(
        taco_dir=args.taco_dir,
        output_dir=args.output_dir,
        taxonomy=args.taxonomy,
        drop_other=args.drop_other,
        train_fraction=args.train_fraction,
        seed=args.seed,
        image_mode=args.image_mode,
    )
    print(f"YOLO dataset written to: {yaml_path.parent.resolve()}")
    print(f"Dataset configuration: {yaml_path.resolve()}")


if __name__ == "__main__":
    main()
