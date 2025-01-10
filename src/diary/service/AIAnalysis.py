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
            {
                "role": "user",
                "content": f"당신은 심리학자입니다. 사용자가 작성한 일기를 분석하여 주요 감정을 식별하고, 이를 바탕으로 공감적이고 실용적인 조언을 제공해주세요.\n 일기 내용 : {content}",
            }
        ],
        stream=True,
    )

    analysis_result = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            # print(chunk.choices[0].delta.content, end="")
            analysis_result += chunk.choices[0].delta.content

    return analysis_result
