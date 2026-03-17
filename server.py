"""OpenAI Image Generation MCP Server for CoreTAP content pipeline."""
import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import FileResponse, Response

from brand_presets import BRAND_PRESETS, PLATFORM_SIZES
from client import generate_image

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
    return_format: str = "url",
) -> str:
    """Generate an image using OpenAI's GPT-image-1 model.

    Args:
        prompt: Description of the image to generate.
        size: Image size. Options: "1024x1024", "1536x1024", "1024x1536", "auto".
        quality: Image quality. Options: "low", "medium", "high".
        background: Background type. Options: "auto", "transparent", "opaque".
        brand: Brand preset name to auto-prepend visual specs. Options: "coretap", "delta-kinetics", "veritas".
        return_format: "url" (default) returns a public URL, "base64" returns inline data.
    """
    full_prompt = prompt
    if brand and brand in BRAND_PRESETS:
        preset = BRAND_PRESETS[brand]
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]

    result = await generate_image(
        prompt=full_prompt, size=size, quality=quality, background=background
    )

    filename = os.path.basename(result["file_path"])
    image_url = f"{BASE_URL}/images/{filename}"

    if return_format == "base64":
        data_url = f"data:image/png;base64,{result['image_base64']}"
        return (
            f"Image generated successfully.\n"
            f"Size: {result['size']}\n"
            f"Saved to: {result['file_path']}\n"
            f"Prompt used: {result['prompt_used']}\n\n"
            f"![Generated Image]({data_url})"
        )

    return (
        f"Image generated successfully.\n"
        f"Size: {result['size']}\n"
        f"URL: {image_url}\n"
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
    return_format: str = "url",
) -> str:
    """Generate a social media image with brand presets built in.

    Args:
        prompt: What the image should show.
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
        style: Visual style. Options: "photorealistic", "editorial", "abstract_data", "minimalist".
        return_format: "url" (default) returns a public URL, "base64" returns inline data.
    """
    size = PLATFORM_SIZES.get(platform, "1024x1024")
    preset = BRAND_PRESETS.get(brand, BRAND_PRESETS["coretap"])
    style_mod = preset.get("styles", {}).get(style, "")

    full_prompt = (
        preset["prompt_prefix"] + style_mod + prompt + " " + preset["prompt_suffix"]
    )

    result = await generate_image(prompt=full_prompt, size=size)

    filename = os.path.basename(result["file_path"])
    image_url = f"{BASE_URL}/images/{filename}"

    if return_format == "base64":
        data_url = f"data:image/png;base64,{result['image_base64']}"
        return (
            f"Social media image generated.\n"
            f"Platform: {platform} ({size})\n"
            f"Brand: {preset['name']}\n"
            f"Style: {style}\n"
            f"Saved to: {result['file_path']}\n\n"
            f"![Generated Image]({data_url})"
        )

    return (
        f"Social media image generated.\n"
        f"Platform: {platform} ({size})\n"
        f"Brand: {preset['name']}\n"
        f"Style: {style}\n"
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
    return_format: str = "url",
) -> str:
    """Generate multiple images at once for content calendar batching (max 4).

    Args:
        prompts: List of image descriptions (max 4).
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
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
        filename = os.path.basename(result["file_path"])
        image_url = f"{BASE_URL}/images/{filename}"

        if return_format == "base64":
            data_url = f"data:image/png;base64,{result['image_base64']}"
            image_ref = data_url
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
        f"Brand: {preset['name']}\n\n"
        + "\n\n".join(results)
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
