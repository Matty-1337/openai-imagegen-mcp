"""OpenAI Image Generation MCP Server for CoreTAP content pipeline."""

import base64
import json
import os
import uuid

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from brand_presets import BRAND_PRESETS, PLATFORM_SIZES
from client import generate_image
from composite import composite_logos

IMAGE_DIR = "/tmp/imagegen"
BASE_URL = os.getenv(
    "PUBLIC_URL", "https://openai-imagegen-mcp-production.up.railway.app"
)

os.makedirs(IMAGE_DIR, exist_ok=True)

mcp = FastMCP(
    "openai_imagegen",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)


def _save_image(image_bytes: bytes, filename: str | None = None) -> str:
    """Save image bytes to disk and return the public URL."""
    if filename is None:
        filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return f"{BASE_URL}/images/{filename}"


def _apply_composite(image_bytes: bytes, composite: bool, logos: str) -> bytes:
    """Apply logo compositing if enabled."""
    if composite and logos != "none":
        return composite_logos(image_bytes, logos=logos)
    return image_bytes


@mcp.custom_route("/images/{filename}", methods=["GET"])
async def serve_image(request: Request) -> Response:
    """Serve generated images as static files."""
    filename = request.path_params["filename"]
    if not filename.endswith(".png") or "/" in filename or "\\" in filename:
        return Response("Not found", status_code=404)
    filepath = os.path.join(IMAGE_DIR, filename)
    if not os.path.isfile(filepath):
        return Response("Not found", status_code=404)
    return FileResponse(filepath, media_type="image/png")


@mcp.custom_route("/generate", methods=["POST"])
async def rest_generate(request: Request) -> Response:
    """REST API for ProjectOps (bulk-approve, generate-image, autopilot).

    JSON body: prompt (required), optional brand, size, quality, background, composite, logos.
    Returns: {"url": "...", "image_url": "...", "size": "..."}
    """
    try:
        body = await request.json()
    except Exception:
        return Response(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            media_type="application/json",
        )

    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return Response(
            json.dumps({"error": "prompt is required"}),
            status_code=400,
            media_type="application/json",
        )

    brand = body.get("brand")
    size = body.get("size", "1024x1024")
    quality = body.get("quality", "high")
    background = body.get("background", "auto")
    composite = body.get("composite", True)
    logos = body.get("logos", "both")

    full_prompt = prompt
    if brand and brand in BRAND_PRESETS:
        preset = BRAND_PRESETS[brand]
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]

    try:
        result = await generate_image(
            prompt=full_prompt, size=size, quality=quality, background=background
        )
        raw_bytes = base64.b64decode(result["image_base64"])
        final_bytes = _apply_composite(raw_bytes, composite, logos)
        image_url = _save_image(final_bytes)
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status_code=500,
            media_type="application/json",
        )

    return Response(
        json.dumps(
            {
                "url": image_url,
                "image_url": image_url,
                "size": result.get("size"),
            }
        ),
        media_type="application/json",
    )


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def img_generate(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    background: str = "auto",
    brand: str | None = None,
    composite: bool = True,
    logos: str = "both",
    return_format: str = "url",
) -> str:
    """Generate an image using OpenAI's GPT-image-1 model.

    Args:
        prompt: Description of the image to generate.
        size: Image size. Options: "1024x1024", "1536x1024", "1024x1536", "auto".
        quality: Image quality. Options: "low", "medium", "high".
        background: Background type. Options: "auto", "transparent", "opaque".
        brand: Brand preset name to auto-prepend visual specs. Options: "coretap", "delta-kinetics", "veritas".
        composite: Whether to composite DK/CoreTAP logos onto the image. Default True.
        logos: Which logos to composite. Options: "both", "dk", "coretap", "none". Default "both".
        return_format: "url" (default) returns a public URL, "base64" returns inline data.
    """
    full_prompt = prompt
    if brand and brand in BRAND_PRESETS:
        preset = BRAND_PRESETS[brand]
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]

    result = await generate_image(
        prompt=full_prompt, size=size, quality=quality, background=background
    )

    # Apply logo compositing
    raw_bytes = base64.b64decode(result["image_base64"])
    final_bytes = _apply_composite(raw_bytes, composite, logos)
    image_url = _save_image(final_bytes)

    if return_format == "base64":
        b64 = base64.b64encode(final_bytes).decode()
        data_url = f"data:image/png;base64,{b64}"
        return (
            f"Image generated successfully.\n"
            f"Size: {result['size']}\n"
            f"URL: {image_url}\n"
            f"Logos: {logos if composite else 'none'}\n"
            f"Prompt used: {result['prompt_used']}\n\n"
            f"![Generated Image]({data_url})"
        )

    return (
        f"Image generated successfully.\n"
        f"Size: {result['size']}\n"
        f"URL: {image_url}\n"
        f"Logos: {logos if composite else 'none'}\n"
        f"Prompt used: {result['prompt_used']}\n\n"
        f"![Generated Image]({image_url})"
    )


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def img_social(
    prompt: str,
    platform: str = "instagram_square",
    brand: str = "coretap",
    style: str = "photorealistic",
    composite: bool = True,
    logos: str = "both",
    return_format: str = "url",
) -> str:
    """Generate a social media image with brand presets built in.

    Args:
        prompt: What the image should show.
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
        style: Visual style. Options: "photorealistic", "editorial", "abstract_data", "minimalist".
        composite: Whether to composite DK/CoreTAP logos onto the image. Default True.
        logos: Which logos to composite. Options: "both", "dk", "coretap", "none". Default "both".
        return_format: "url" (default) returns a public URL, "base64" returns inline data.
    """
    size = PLATFORM_SIZES.get(platform, "1024x1024")
    preset = BRAND_PRESETS.get(brand, BRAND_PRESETS["coretap"])
    style_mod = preset.get("styles", {}).get(style, "")

    full_prompt = (
        preset["prompt_prefix"] + style_mod + prompt + " " + preset["prompt_suffix"]
    )

    result = await generate_image(prompt=full_prompt, size=size)

    # Apply logo compositing
    raw_bytes = base64.b64decode(result["image_base64"])
    final_bytes = _apply_composite(raw_bytes, composite, logos)
    image_url = _save_image(final_bytes)

    if return_format == "base64":
        b64 = base64.b64encode(final_bytes).decode()
        data_url = f"data:image/png;base64,{b64}"
        return (
            f"Social media image generated.\n"
            f"Platform: {platform} ({size})\n"
            f"Brand: {preset['name']}\n"
            f"Style: {style}\n"
            f"Logos: {logos if composite else 'none'}\n"
            f"URL: {image_url}\n\n"
            f"![Generated Image]({data_url})"
        )

    return (
        f"Social media image generated.\n"
        f"Platform: {platform} ({size})\n"
        f"Brand: {preset['name']}\n"
        f"Style: {style}\n"
        f"Logos: {logos if composite else 'none'}\n"
        f"URL: {image_url}\n\n"
        f"![Generated Image]({image_url})"
    )


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def img_batch(
    prompts: list[str],
    platform: str = "instagram_square",
    brand: str = "coretap",
    composite: bool = True,
    logos: str = "both",
    return_format: str = "url",
) -> str:
    """Generate multiple images at once for content calendar batching (max 4).

    Args:
        prompts: List of image descriptions (max 4).
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
        composite: Whether to composite DK/CoreTAP logos onto the images. Default True.
        logos: Which logos to composite. Options: "both", "dk", "coretap", "none". Default "both".
        return_format: "url" (default) returns public URLs, "base64" returns inline data.
    """
    if len(prompts) > 4:
        return "Error: Maximum 4 prompts allowed per batch."

    size = PLATFORM_SIZES.get(platform, "1024x1024")
    preset = BRAND_PRESETS.get(brand, BRAND_PRESETS["coretap"])

    results = []
    for i, prompt in enumerate(prompts):
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]
        result = await generate_image(prompt=full_prompt, size=size)

        # Apply logo compositing
        raw_bytes = base64.b64decode(result["image_base64"])
        final_bytes = _apply_composite(raw_bytes, composite, logos)
        image_url = _save_image(final_bytes)

        if return_format == "base64":
            b64 = base64.b64encode(final_bytes).decode()
            image_ref = f"data:image/png;base64,{b64}"
        else:
            image_ref = image_url

        results.append(
            f"### Image {i + 1}\n"
            f"URL: {image_url}\n\n"
            f"![Image {i + 1}]({image_ref})"
        )

    return (
        f"Batch complete: {len(prompts)} images generated.\n"
        f"Platform: {platform} ({size})\n"
        f"Brand: {preset['name']}\n"
        f"Logos: {logos if composite else 'none'}\n\n"
        + "\n\n".join(results)
    )


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def img_upload(
    image_base64: str,
    composite: bool = True,
    logos: str = "both",
    filename: str | None = None,
) -> str:
    """Upload a pre-made image to the server and get a public URL.

    Optionally composites DK/CoreTAP logos onto it.

    Args:
        image_base64: Base64-encoded PNG/JPG image data.
        composite: Whether to add logos. Default True.
        logos: Which logos: "both", "dk", "coretap", "none". Default "both".
        filename: Optional custom filename (auto-generated if not provided).

    Returns: Public URL to the hosted image.
    """
    raw_bytes = base64.b64decode(image_base64)
    final_bytes = _apply_composite(raw_bytes, composite, logos)
    image_url = _save_image(final_bytes, filename=filename)

    return (
        f"Image uploaded successfully.\n"
        f"Logos: {logos if composite else 'none'}\n"
        f"URL: {image_url}\n\n"
        f"![Uploaded Image]({image_url})"
    )


@mcp.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def img_composite(
    image_url: str,
    logos: str = "both",
) -> str:
    """Take an existing image URL from this server and composite logos onto it.

    Returns a new public URL with the composited version.

    Args:
        image_url: URL of an existing image on this server (e.g. .../images/abc123.png).
        logos: Which logos: "both", "dk", "coretap", "none". Default "both".

    Returns: Public URL to the composited image.
    """
    # Extract filename from URL and read from disk
    url_filename = image_url.rstrip("/").split("/")[-1]
    if not url_filename.endswith(".png") or "/" in url_filename or "\\" in url_filename:
        return "Error: Invalid image URL. Must be a .png URL from this server."

    filepath = os.path.join(IMAGE_DIR, url_filename)
    if not os.path.isfile(filepath):
        return f"Error: Image not found: {url_filename}"

    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    final_bytes = composite_logos(raw_bytes, logos=logos)
    new_url = _save_image(final_bytes)

    return (
        f"Image composited successfully.\n"
        f"Original: {image_url}\n"
        f"Logos: {logos}\n"
        f"URL: {new_url}\n\n"
        f"![Composited Image]({new_url})"
    )


@mcp.tool(annotations={"readOnlyHint": True})
async def img_list_presets() -> str:
    """List available brand presets, styles, and platform size mappings."""
    lines = ["# Available Brand Presets\n"]

    for key, preset in BRAND_PRESETS.items():
        lines.append(f"## {preset['name']} (`{key}`)")
        lines.append(f"**Prefix:** {preset['prompt_prefix'][:100]}...")
        styles = ", ".join(preset.get("styles", {}).keys())
        lines.append(f"**Styles:** {styles}")
        lines.append("")

    lines.append("## Platform Sizes")
    for plat, size in PLATFORM_SIZES.items():
        lines.append(f"- `{plat}`: {size}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")
