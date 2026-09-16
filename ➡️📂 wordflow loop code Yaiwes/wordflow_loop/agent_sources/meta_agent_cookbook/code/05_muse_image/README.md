# Muse Image

Recipes for building with [Muse Image](https://dev.meta.ai/docs/getting-started/cookbook#muse-image), the reasoning model that generates and edits images through the conversational Responses API. Each recipe drives a task end to end through one chained conversation, from a first render to a finished result you can reproduce.

## Recipes

| # | Recipe | What it does |
|---|--------|--------------|
| [01](01_image_api_fundamentals/) | Generate, edit, and compose images | Drive Muse Image through the Responses API: generate an image from a prompt, refine it over chained turns, and attach reference images to steer or compose several into one scene. |
| [02](02_backyard_restyle/) | Ground image generation in web search | Let the model search the live web mid-generation, so it renders from furniture actually sold today, then place a coordinated outdoor set into a photo of a real backyard. |
| [03](03_anchored_generation/) | Consistency across an image series | Anchor a whole series on a small reference set and carry it through the conversation, so the character, style, and setting stay on-model from one image to the next. |
| [04](04_image_editing_with_reasoning/) | Editing with image understanding and reasoning | Edit a specific part of an image by describing it, letting the model reason over the frame and refine the same image across turns, changing what you ask for while preserving the rest. |
