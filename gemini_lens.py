from google import genai


# Replace with your Gemini API Key
API_KEY = "api"

client = genai.Client(api_key=API_KEY)


def analyze_image(image_path,prompt):

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            genai.types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg"
            )
        ]
    )

    return response.text
