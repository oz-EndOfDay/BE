import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


def analyze_diary_entry(content: str) -> str:
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"다음 일기의 감정을 분석해주세요: {content}"}
        ],
        stream=True,
    )

    analysis_result = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            # print(chunk.choices[0].delta.content, end="")
            analysis_result += chunk.choices[0].delta.content

    return analysis_result
