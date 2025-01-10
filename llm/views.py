from openai import OpenAI
from django.conf import settings
from django.http import JsonResponse

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_image(request):
    prompt = request.GET.get("prompt", "")
    if not prompt:
        return JsonResponse({"error": "Prompt is required"}, status=400)

    # GPT-4로 DALL-E 프롬프트 생성
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a detailed DALL-E prompt for: {prompt}"}
        ]
    )
    #gpt_response = response.choices[0].message.content
    gpt_response = response["choices"][0]["message"]["content"]

    # DALL-E로 이미지 생성
    image_response = client.images.generate(
        prompt=gpt_response,
        n=1,
        size="1024x1024"
    )
    #image_url = image_response.data[0].url
    image_url = image_response["data"][0]["url"]

    return JsonResponse({"response": gpt_response, "image_url": image_url})
