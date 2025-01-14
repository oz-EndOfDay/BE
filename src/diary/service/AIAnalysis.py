import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

'''
analysis_result 이거는 조언으로 충분한 수면: 규칙적인 수면 습관으로 몸과 마음을 회복하세요.
짧은 낮잠: 피로할 땐 15~30분 낮잠으로 에너지를 충전하세요.
스트레스 관리: 유머와 장난스러운 순간으로 스트레스를 해소하세요.
리프레시 활동: 산책이나 스트레칭으로 기분 전환과 에너지를 높이세요. 3-4가지정도만 130자 내외로 하면될거같아요 예시 데이터 주면되지않을까요 ㅠ 또 하나는 감정분석도 100자내외정도 ?

감정분석 100자 내외 조언 130자내외 (3-4가지정도만)

데이터는 괜찬은듯 ?
(실용적 조언마다 간단한 핵심 키워드 : 실용적인 조언 의 형태로 반환해 주세요.)
'''
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
