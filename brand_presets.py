BRAND_PRESETS = {
    "coretap": {
        "name": "CoreTAP",
        "prompt_prefix": (
            "Dark-first premium aesthetic. Background: deep black (#0A0E1A). "
            "Lighting: neon cyan (#40F0F0) as primary accent light, "
            "hot magenta (#E040C0) as secondary accent/backlight. "
            "Color palette: cyan, magenta, electric orange, deep navy. "
            "Mood: Bloomberg terminal meets upscale bar. "
            "Premium, data-driven, moody, cinematic. "
            "The image should look like it's glowing and pulsing with energy. "
        ),
        "prompt_suffix": (
            "High resolution, professional photography quality, "
            "shallow depth of field, dramatic lighting, film grain subtle. "
            "No text overlays. No watermarks. Clean composition."
        ),
        "styles": {
            "photorealistic": "Photorealistic editorial photography style. ",
            "editorial": "High-end magazine editorial photography. Dramatic shadows. ",
            "abstract_data": "Abstract data visualization aesthetic. Flowing neon lines and nodes on dark background. Futuristic. ",
            "minimalist": "Minimalist composition. Lots of dark negative space. Single subject. Clean lines. ",
        },
    },
    "delta-kinetics": {
        "name": "Delta Kinetics",
        "prompt_prefix": (
            "Professional technology aesthetic. Colors: Electric Cyan (#00E5E5), "
            "Deep Teal (#0099AA), Ocean Blue (#3DA0D4), Dark Navy (#0A1628). "
            "Clean, modern, authoritative. "
        ),
        "prompt_suffix": (
            "High resolution, professional quality, clean composition. "
            "No text overlays. No watermarks."
        ),
        "styles": {
            "photorealistic": "Photorealistic professional photography. ",
            "editorial": "Corporate editorial style. ",
            "abstract_data": "Abstract technology visualization. ",
            "minimalist": "Clean minimalist design. ",
        },
    },
    "veritas": {
        "name": "Veritas Officiating Institute",
        "prompt_prefix": (
            "Professional sports and education aesthetic. Colors: Violet (#9463FA), "
            "Dark Navy (#0A1628), Amber Gold (#F1AC4F). "
            "Authoritative, precise, athletic. Baseball umpire context. "
        ),
        "prompt_suffix": (
            "High resolution, sports photography quality. "
            "No text overlays. No watermarks."
        ),
        "styles": {
            "photorealistic": "Sports photography style. ",
            "editorial": "Athletic editorial style. ",
            "minimalist": "Clean sports design. ",
        },
    },
}

PLATFORM_SIZES = {
    "instagram_square": "1024x1024",
    "instagram_portrait": "1024x1536",
    "linkedin_landscape": "1536x1024",
    "story": "1024x1536",
    "auto": "auto",
}
