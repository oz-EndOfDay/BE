import asyncio
from typing import Dict, Optional

import openai
from pydantic import BaseModel

from src.config import Settings

settings = Settings()


class DiaryAnalysis(BaseModel):
    mood_analysis: str
    emotional_insights: str
    advice: str
    confidence_score: float = 0.0
    raw_analysis_data: Optional[Dict] = None  # type: ignore


class AIAnalysisService:
    def __init__(self) -> None:
        openai.api_key = settings.OPENAI_API_KEY

    async def analyze_diary_entry(self, content: str) -> DiaryAnalysis:
        try:
            # asyncio.to_thread() 사용하여 동기 함수를 비동기로 변환
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,  # type: ignore
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """너는 공감능력 높은 멘토야. 사용자의 일기를 깊이 있게 분석하고 공감과 위로, 구체적인 조언을 제공해줘.""",
                    },
                    {
                        "role": "user",
                        "content": f"""다음 일기 내용을 분석해주세요:
                        {content}

                        분석 형식:
                        1. 감정 상태: 현재 느끼는 감정을 한 문장으로
                        2. 감정 원인: 왜 이런 감정이 드는지 분석
                        3. 조언: 구체적이고 실천 가능한 위로와 조언""",
                    },
                ],
                max_tokens=300,
                temperature=0.7,
            )

            analysis_text = response.choices[0].message.content.strip()

            # 분석 결과 파싱
            lines = analysis_text.split("\n")
            mood_analysis = (
                lines[0].replace("1. 감정 상태: ", "").strip()
                if lines
                else "감정 분석 실패"
            )
            emotional_insights = (
                lines[1].replace("2. 감정 원인: ", "").strip()
                if len(lines) > 1
                else "감정 원인 분석 실패"
            )
            advice = (
                lines[2].replace("3. 조언: ", "").strip()
                if len(lines) > 2
                else "기본 조언"
            )

            return DiaryAnalysis(
                mood_analysis=mood_analysis,
                emotional_insights=emotional_insights,
                advice=advice,
                confidence_score=1.0,
                raw_analysis_data={"text": analysis_text},
            )
        except Exception as e:
            return DiaryAnalysis(
                mood_analysis="분석 실패",
                emotional_insights="서비스 오류",
                advice="잠시 후 다시 시도해주세요",
                confidence_score=0.0,
                raw_analysis_data={"error": str(e)},
            )
