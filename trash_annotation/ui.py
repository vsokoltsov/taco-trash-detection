import io

from PIL import Image
import requests
import streamlit as st

st.set_page_config(
    page_title="TACO Trash Detector",
    page_icon="🗑️",
    layout="wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    api_url = st.text_input("API URL", value="http://api:8000")
    model_name = st.selectbox(
        "Model",
        options=["mask_rcnn_v1", "yolo_v8", "yolo_v11_top5"],
        format_func=lambda value: {
            "mask_rcnn_v1": "Mask R-CNN v1",
            "yolo_v8": "YOLOv8",
            "yolo_v11_top5": "YOLOv11l top-5",
        }[value],
    )
    score_thresh = st.slider("Score threshold", 0.05, 0.95, 0.20, 0.05)
    show_masks = st.checkbox(
        "Show segmentation masks",
        value=False,
        disabled=model_name != "mask_rcnn_v1",
        help="Masks are available only for Mask R-CNN v1.",
    )

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🗑️ TACO Trash Detector")
st.caption("Upload a photo and compare Mask R-CNN v1, YOLOv8, and YOLOv11l top-5.")

uploaded = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png", "webp"])

if uploaded:
    col_orig, col_result = st.columns(2)

    with col_orig:
        st.subheader("Original")
        st.image(uploaded, use_container_width=True)

    with st.spinner("Running detection…"):
        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}

        try:
            # ── annotated image ───────────────────────────────────────────
            img_resp = requests.post(
                f"{api_url}/detect",
                files=files,
                params={
                    "model": model_name,
                    "score_thresh": score_thresh,
                    "show_masks": str(show_masks).lower(),
                },
                timeout=60,
            )
            img_resp.raise_for_status()

            # ── json detections ───────────────────────────────────────────
            uploaded.seek(0)
            json_resp = requests.post(
                f"{api_url}/detect/json",
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                params={"model": model_name, "score_thresh": score_thresh},
                timeout=60,
            )
            json_resp.raise_for_status()
            detections = json_resp.json()["detections"]

        except requests.exceptions.ConnectionError:
            st.error(f"Cannot reach API at {api_url}. Is the container running?")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"API error: {e}")
            st.stop()

    with col_result:
        st.subheader(f"Detections ({len(detections)} found)")
        annotated = Image.open(io.BytesIO(img_resp.content))
        st.image(annotated, use_container_width=True)

    # ── Detection table ───────────────────────────────────────────────────────
    if detections:
        st.subheader("Results")

        rows = [
            {
                "Class": d["label"],
                "Score": f"{d['score']:.2%}",
                "x1": int(d["box"][0]),
                "y1": int(d["box"][1]),
                "x2": int(d["box"][2]),
                "y2": int(d["box"][3]),
            }
            for d in sorted(detections, key=lambda x: x["score"], reverse=True)
        ]

        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=1, format="%.2f"
                ),
            },
        )

        # class frequency bar chart
        from collections import Counter

        counts = Counter(d["label"] for d in detections)
        st.subheader("Class breakdown")
        st.bar_chart(counts)
    else:
        st.info("No detections above the score threshold.")
