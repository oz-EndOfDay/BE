import asyncio
import re
from typing import Optional

from openai import OpenAI, RateLimitError
from pydantic import BaseModel

from src.config import Settings

class DiaryAnalysis(BaseModel):
    mood_analysis: str = "서비스 준비 중"
    emotional_insights: str = "현재 무료 체험판 사용 중입니다"
    advice: str = "정확한 분석을 위해 API 설정을 완료해주세요"
    confidence_score: float = 0.0

class AIAnalysisService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=Settings().OPENAI_API_KEY)
        self.max_retries = 3
        self.base_delay = 1

    async def retry_with_backoff(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError:
                wait_time = self.base_delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
        raise Exception("API 요청 최대 재시도 횟수 초과")

    async def analyze_diary_entry(self, content: str) -> DiaryAnalysis:
        try:
            response = await self.retry_with_backoff(
                self.client.chat.completions.create,
                model="gpt-4o-mini",  # Rate Limit에 맞는 모델 선택
                messages=[
                    {
                        "role": "system",
                        "content": "너는 공감능력 높은 멘토야. 사용자의 일기를 깊이 있게 분석하고 공감과 위로, 구체적인 조언을 제공해줘."
                    },
                    {
                        "role": "user",
                        "content": f"다음 일기를 분석해주세요: {content}"
                    }
                ],
                max_tokens=300,
                temperature=0.2
            )

            analysis_text = response.choices[0].message.content.strip()
            return DiaryAnalysis(
                mood_analysis=self._extract_mood(analysis_text),
                emotional_insights=self._extract_insights(analysis_text),
                advice=self._extract_advice(analysis_text),
                confidence_score=0.7
            )

        except Exception as e:
            return DiaryAnalysis(
                mood_analysis="서비스 오류",
                emotional_insights=f"오류 발생: {str(e)}",
                advice="잠시 후 다시 시도해주세요"
            )

    @staticmethod
    def _extract_mood(text: str) -> str:
        mood_patterns = [
            r'감정\s*상태[:\s]*(\w+)',
            r'기분[:\s]*(\w+)',
            r'mood[:\s]*(\w+)'
        ]
        for pattern in mood_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "중립"

    @staticmethod
    def _extract_insights(text: str) -> str:
        insights_patterns = [
            r'인사이트[:\s]*(.+?)(?:\n|$)',
            r'분석[:\s]*(.+?)(?:\n|$)'
        ]
        for pattern in insights_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "추가 분석 필요"

    @staticmethod
    def _extract_advice(text: str) -> str:
        advice_patterns = [
            r'조언[:\s]*(.+?)(?:\n|$)',
            r'제안[:\s]*(.+?)(?:\n|$)'
        ]
        for pattern in advice_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "개인화된 조언을 준비 중입니다"
