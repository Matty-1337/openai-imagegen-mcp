import openai
import os
import base64
import uuid


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    background: str = "auto",
) -> dict:
    """Generate an image using OpenAI's gpt-image-1 model."""
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    result = await client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size=size,
        quality=quality,
        background=background,
    )

    image_b64 = result.data[0].b64_json

    # Save to temp file
    os.makedirs("/tmp/imagegen", exist_ok=True)
    filename = f"/tmp/imagegen/{uuid.uuid4().hex}.png"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(image_b64))

    return {
        "image_base64": image_b64,
        "file_path": filename,
        "size": size,
        "prompt_used": prompt[:200],
    }
