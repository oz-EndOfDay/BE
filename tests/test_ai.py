import pytest

from src.diary.service.AIAnalysis import AIAnalysisService


@pytest.mark.asyncio
async def test_diary_analysis():
    # AIAnalysisService 인스턴스 생성
    ai_service = AIAnalysisService()

    # 테스트용 일기 내용
    test_diary_content = """
    오늘 정말 힘든 하루였어요. 
    업무 스트레스가 너무 많아서 지쳤고, 
    마음이 무겁고 우울했습니다.
    """

    # 일기 분석 수행
    result = await ai_service.analyze_diary_entry(test_diary_content)

    # 결과 검증
    assert result is not None, "분석 결과가 None입니다"

    # DiaryAnalysis 모델 검증
    assert hasattr(result, "mood_analysis"), "mood_analysis 필드 누락"
    assert hasattr(result, "emotional_insights"), "emotional_insights 필드 누락"
    assert hasattr(result, "advice"), "advice 필드 누락"

    # 필드 값 검증
    assert len(result.mood_analysis) > 0, "mood_analysis가 비어있습니다"
    assert len(result.emotional_insights) > 0, "emotional_insights가 비어있습니다"
    assert len(result.advice) > 0, "advice가 비어있습니다"

    # 신뢰도 점수 검증
    assert 0 <= result.confidence_score <= 1, "confidence_score 범위 오류"


@pytest.mark.asyncio
async def test_diary_analysis_error_handling():
    # AIAnalysisService 인스턴스 생성
    ai_service = AIAnalysisService()

    # 빈 내용으로 테스트
    result = await ai_service.analyze_diary_entry("")

    # 오류 처리 검증
    assert result.mood_analysis in [
        "서비스 오류",
        "분석 실패",
        "분석 제한",
    ], "Unexpected mood analysis result"

    # 오류 메시지 존재 여부 확인 방식 변경
    assert (
        result.emotional_insights is not None
    ), "Emotional insights should not be None"
    assert len(result.emotional_insights) > 0, "Emotional insights should not be empty"

    assert len(result.advice) > 0
