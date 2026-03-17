from mcp.server.fastmcp import FastMCP

from brand_presets import BRAND_PRESETS, PLATFORM_SIZES
from client import generate_image

mcp = FastMCP("openai_imagegen")


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
) -> str:
    """Generate an image using OpenAI's GPT-image-1 model.

    Args:
        prompt: Description of the image to generate.
        size: Image size. Options: "1024x1024", "1536x1024", "1024x1536", "auto".
        quality: Image quality. Options: "low", "medium", "high".
        background: Background type. Options: "auto", "transparent", "opaque".
        brand: Brand preset name to auto-prepend visual specs. Options: "coretap", "delta-kinetics", "veritas".
    """
    full_prompt = prompt
    if brand and brand in BRAND_PRESETS:
        preset = BRAND_PRESETS[brand]
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]

    result = await generate_image(
        prompt=full_prompt, size=size, quality=quality, background=background
    )

    data_url = f"data:image/png;base64,{result['image_base64']}"
    return (
        f"Image generated successfully.\n"
        f"Size: {result['size']}\n"
        f"Saved to: {result['file_path']}\n"
        f"Prompt used: {result['prompt_used']}\n\n"
        f"![Generated Image]({data_url})"
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
) -> str:
    """Generate a social media image with brand presets built in.

    Args:
        prompt: What the image should show.
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
        style: Visual style. Options: "photorealistic", "editorial", "abstract_data", "minimalist".
    """
    size = PLATFORM_SIZES.get(platform, "1024x1024")
    preset = BRAND_PRESETS.get(brand, BRAND_PRESETS["coretap"])
    style_mod = preset.get("styles", {}).get(style, "")

    full_prompt = (
        preset["prompt_prefix"] + style_mod + prompt + " " + preset["prompt_suffix"]
    )

    result = await generate_image(prompt=full_prompt, size=size)

    data_url = f"data:image/png;base64,{result['image_base64']}"
    return (
        f"Social media image generated.\n"
        f"Platform: {platform} ({size})\n"
        f"Brand: {preset['name']}\n"
        f"Style: {style}\n"
        f"Saved to: {result['file_path']}\n\n"
        f"![Generated Image]({data_url})"
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
) -> str:
    """Generate multiple images at once for content calendar batching (max 4).

    Args:
        prompts: List of image descriptions (max 4).
        platform: Target platform. Options: "instagram_square", "instagram_portrait", "linkedin_landscape", "story".
        brand: Brand preset. Options: "coretap", "delta-kinetics", "veritas".
    """
    if len(prompts) > 4:
        return "Error: Maximum 4 prompts allowed per batch."

    size = PLATFORM_SIZES.get(platform, "1024x1024")
    preset = BRAND_PRESETS.get(brand, BRAND_PRESETS["coretap"])

    results = []
    for i, prompt in enumerate(prompts):
        full_prompt = preset["prompt_prefix"] + prompt + " " + preset["prompt_suffix"]
        result = await generate_image(prompt=full_prompt, size=size)
        data_url = f"data:image/png;base64,{result['image_base64']}"
        results.append(
            f"### Image {i + 1}\n"
            f"Saved to: {result['file_path']}\n\n"
            f"![Image {i + 1}]({data_url})"
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
    import os

    # FastMCP reads port/host from FASTMCP_PORT / FASTMCP_HOST env vars
    os.environ.setdefault("FASTMCP_PORT", os.getenv("PORT", "8000"))
    os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
    mcp.run(transport="sse")
