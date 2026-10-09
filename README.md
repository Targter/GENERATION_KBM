# KBM Tile Studio

A local batch generator for Krishna Building Material tile catalogues.

## What it does

1. Upload one original tile image.
2. Set the real tile size (default: 2×4).
3. Choose a generation pack.
4. The app sends the same original tile to the image model for every concept.
5. Generated images are saved in `outputs/<run-id>/`.

The default pack includes:
- 01 Product Showcase
- 02 Detail / Texture
- 03 Repeated Floor
- 04 Living Room
- 05 Bedroom
- 06 Kitchen
- 07 Bathroom
- 08 Wall Application
- 09 Combination Board (uses only the supplied tile unless another tile is uploaded)
- 10 Border Concept
- 11 Bathroom Concept
- 12 Kitchen Concept
- 13 Bedroom Concept
- 14 Living Room Concept
- 15 2D Elevation

## Important

This tool uses the OpenAI API. You need your own API key and API billing/credits. API usage is billed separately from a ChatGPT subscription.

The app uses GPT Image 2.5 by default. `sunburst` is used for higher-fidelity editing; `flare` can be selected for faster generation.

## Run

### Windows / macOS / Linux

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and put your API key in it:

```env
OPENAI_API_KEY=your_api_key_here
```

5. Start:

```bash
streamlit run app.py
```

6. Open the local URL shown by Streamlit.

## Recommended workflow

Start with only the first 3 outputs. Check that the model preserves the tile.

Then run room concepts.

For combinations/borders, upload the other actual tile references too. The app supports multiple reference tiles.

## Notes

AI image generation can still occasionally alter patterns or geometry. For commercially important catalogue assets, inspect the generated tile against the original before publishing.
