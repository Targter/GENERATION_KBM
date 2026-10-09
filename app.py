import base64
import io
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

load_dotenv()

APP_TITLE = "KBM Tile Studio"
OUT_ROOT = Path("outputs")
OUT_ROOT.mkdir(exist_ok=True)

PACKS = {
    "Core Showcase Pack": [
        ("01_product_showcase", "Pure Product Showcase"),
        ("02_detail_texture", "Detail / Texture Showcase"),
        ("03_repeated_floor", "Repeated Floor Test"),
        ("04_living_room", "Living Room Floor"),
        ("05_bedroom", "Bedroom Floor"),
        ("06_kitchen", "Kitchen Floor"),
        ("07_bathroom", "Bathroom Floor"),
        ("08_wall_application", "Wall Application"),
        ("09_combination_board", "Combination Board"),
        ("10_border_concept", "Border Concept"),
        ("11_bathroom_concept", "Complete Bathroom Concept"),
        ("12_kitchen_concept", "Complete Kitchen Concept"),
        ("13_bedroom_concept", "Complete Bedroom Concept"),
        ("14_living_room_concept", "Complete Living Room Concept"),
        ("15_2d_elevation", "2D Elevation"),
    ]
}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def image_to_bytes(upload):
    return upload.getvalue()

def build_prompt(kind, tile_size, finish, tile_name, extra):
    master_rules = f"""
MASTER TILE RULES — NON-NEGOTIABLE:
- The supplied reference image is the exact master tile.
- Preserve its exact visible pattern, veining, colours, texture and finish.
- Do NOT redesign, reinterpret, simplify, beautify, recolour, mirror, invent or replace the tile pattern.
- Do NOT stretch or squash the tile.
- The real tile size is {tile_size}; preserve its 1:{2 if tile_size.strip() == '2×4' or tile_size.strip() == '2x4' else 'actual'} physical proportion.
- Finish: {finish}.
- If the tile is repeated, each tile must retain the same design characteristics as the supplied master.
- Do not introduce a different tile unless the prompt explicitly requests an uploaded secondary reference.
- No fake product name, brand, price or specification.
- Make the result photorealistic and suitable for a professional tile catalogue.
"""
    contexts = {
        "01_product_showcase": """
Create a premium catalogue product photograph of the exact supplied tile.
Show one full 2×4 portrait tile/slab as the hero product, with its complete edges visible.
Use a restrained luxury showroom background. The tile is the subject.
No room scene, no furniture, no extra tile designs, no decorative text.
""",
        "02_detail_texture": """
Create a premium material-detail board using the exact supplied tile.
Show a clean full-tile view plus close-up views of the same pattern, surface texture and high-gloss reflection.
Do not invent any new pattern.
""",
        "03_repeated_floor": """
Create a clean architectural floor test using only the exact supplied tile repeated across a large floor.
Show realistic grout joints and correct perspective. Preserve the tile's design and orientation.
Use a neutral, unfurnished architectural space so the tile remains the focus.
""",
        "04_living_room": """
Create a premium modern living room. Apply the exact supplied tile ONLY to the floor.
Keep walls, furniture and decor neutral so the tile is clearly visible.
Photorealistic interior photography, realistic reflections and daylight.
""",
        "05_bedroom": """
Create a premium contemporary bedroom. Apply the exact supplied tile ONLY to the floor.
Keep all other surfaces visually restrained and neutral. Preserve the tile exactly.
Photorealistic, realistic scale and perspective.
""",
        "06_kitchen": """
Create a premium modern modular kitchen. Apply the exact supplied tile ONLY to the floor.
Use neutral cabinetry and restrained materials so the tile remains the hero.
Photorealistic daylight interior.
""",
        "07_bathroom": """
Create a premium bathroom. Apply the exact supplied tile ONLY to the floor.
Use plain complementary walls and minimal fixtures. Preserve the tile exactly.
Photorealistic architectural interior.
""",
        "08_wall_application": """
Create a premium interior feature wall using the exact supplied tile.
The tile must remain the exact master pattern and proportions.
Keep the floor and surrounding surfaces neutral and simple.
""",
        "09_combination_board": """
Create a clean professional tile combination board.
Use the exact supplied master tile as the primary swatch. If secondary tile reference images are supplied,
show them only as secondary swatches and do not alter any tile design.
Do not generate fictional tile patterns.
""",
        "10_border_concept": """
Create a clean premium bathroom wall concept using the exact supplied master tile as the main field tile.
Add a simple dark neutral border only if it is visually appropriate, but do not invent a decorative tile pattern.
Make the border a plain material/tile, not a fake version of the master.
Show a realistic 6-inch horizontal border as the default.
""",
        "11_bathroom_concept": """
Create a complete premium bathroom design using the exact supplied master tile as the primary wall or floor material.
Use neutral complementary surfaces. If secondary uploaded tile references exist, use them for the feature/border/floor.
The result must look like a real buildable tile combination, not an abstract render.
""",
        "12_kitchen_concept": """
Create a complete premium kitchen concept using the exact supplied master tile as the primary floor or backsplash material.
If secondary uploaded tile references exist, use them as complementary materials only.
Keep the design realistic and buildable.
""",
        "13_bedroom_concept": """
Create a complete premium bedroom concept using the exact supplied master tile as the floor.
Use restrained wall and furniture materials. Do not change the tile.
""",
        "14_living_room_concept": """
Create a complete premium living-room/hall concept using the exact supplied master tile as the floor.
Use an elegant contemporary Indian-home aesthetic with realistic furniture, lighting and proportions.
Do not change the tile.
""",
        "15_2d_elevation": """
Create a clean 2D architectural elevation of a premium bathroom wall using the exact supplied tile.
Show the tile layout, grout joints and a simple 6-inch border concept.
Use orthographic front elevation, no perspective distortion.
Do not invent a different tile pattern.
"""
    }
    return master_rules + contexts[kind] + f"""
Product name: {tile_name or 'Not specified'}.
Additional instruction: {extra or 'None'}.
Do not add specifications that were not supplied.
"""

def call_image(client, model, master_bytes, secondary_bytes, prompt, size, quality):
    images = [io.BytesIO(master_bytes)]
    for b in secondary_bytes:
        images.append(io.BytesIO(b))
    # The Python SDK accepts file-like image inputs for image edits.
    result = client.images.edit(
        model=model,
        image=images if len(images) > 1 else images[0],
        prompt=prompt,
        size=size,
        quality=quality,
    )
    data = base64.b64decode(result.data[0].b64_json)
    return data

st.set_page_config(page_title=APP_TITLE, page_icon="KBM", layout="wide")
st.title(APP_TITLE)
st.caption("Batch-create a consistent tile catalogue from your real product images.")

with st.sidebar:
    st.header("Master Product")
    tile = st.file_uploader("Upload master tile image", type=["png", "jpg", "jpeg", "webp"])
    tile_name = st.text_input("Tile name / code", placeholder="e.g. KBM-001")
    tile_size = st.text_input("Actual tile size", value="2×4")
    finish = st.text_input("Finish", value="High Gloss")

    st.header("Secondary Tiles")
    secondary = st.file_uploader(
        "Optional: upload matching tiles for combinations/borders",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    st.header("Generation")
    model = st.selectbox(
        "Image model",
        ["gpt-image-2.5-sunburst", "gpt-image-2.5-flare"],
        index=0,
        help="Sunburst prioritizes precision; Flare is faster."
    )
    quality = st.selectbox("Quality", ["high", "xhigh", "max"], index=0)
    size = st.selectbox("Output format", ["1024x1536", "1536x1024", "1024x1024"], index=0)
    extra = st.text_area("Global instruction", placeholder="Optional instruction for every concept.")

if tile:
    st.image(tile, caption="Master reference", width=360)
    st.info(f"Locked: {tile_size} | {finish} | Every generation receives this master image.")
else:
    st.warning("Upload your original tile first.")

st.subheader("Choose outputs")
pack = st.selectbox("Pack", list(PACKS.keys()))
selected = st.multiselect(
    "Concepts",
    PACKS[pack],
    default=[x for x in PACKS[pack][:3]],
    format_func=lambda x: x[1],
)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.warning("Set OPENAI_API_KEY in .env before generating.")

if st.button("Generate selected concepts", type="primary", disabled=(not tile or not api_key or not selected)):
    client = OpenAI(api_key=api_key)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUT_ROOT / f"{slug(tile_name or 'tile')}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    master_bytes = image_to_bytes(tile)
    secondary_bytes = [image_to_bytes(x) for x in secondary]

    progress = st.progress(0)
    status = st.empty()
    results = []

    for i, (kind, label) in enumerate(selected):
        status.write(f"Generating {i+1}/{len(selected)} — {label}")
        try:
            prompt = build_prompt(kind, tile_size, finish, tile_name, extra)
            output = call_image(client, model, master_bytes, secondary_bytes, prompt, size, quality)
            path = run_dir / f"{kind}.png"
            path.write_bytes(output)
            results.append((label, path))
        except Exception as e:
            st.error(f"{label}: {e}")
        progress.progress((i + 1) / len(selected))

    status.success(f"Finished. Files saved to {run_dir}")
    st.session_state["last_run"] = str(run_dir)

if st.session_state.get("last_run"):
    run_dir = Path(st.session_state["last_run"])
    if run_dir.exists():
        st.subheader("Latest run")
        cols = st.columns(3)
        for idx, path in enumerate(sorted(run_dir.glob("*.png"))):
            with cols[idx % 3]:
                st.image(str(path), caption=path.stem, use_container_width=True)
                st.download_button(
                    "Download",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="image/png",
                    key=f"dl_{path.name}",
                )

        zip_path = run_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in run_dir.glob("*"):
                z.write(p, arcname=p.name)
        st.download_button(
            "Download entire generated pack",
            data=zip_path.read_bytes(),
            file_name=zip_path.name,
            mime="application/zip",
        )
