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
    assert hasattr(result, 'mood_analysis'), "mood_analysis 필드 누락"
    assert hasattr(result, 'emotional_insights'), "emotional_insights 필드 누락"
    assert hasattr(result, 'advice'), "advice 필드 누락"

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
    assert result.mood_analysis == "서비스 오류" or result.mood_analysis == "분석 실패"
    assert "오류" in result.emotional_insights or "실패" in result.emotional_insights
    assert len(result.advice) > 0


@pytest.mark.asyncio
async def test_multiple_diary_analyses():
    ai_service = AIAnalysisService()

    # 다양한 일기 내용으로 테스트
    test_diaries = [
        "오늘 정말 행복한 하루였어요.",
        "업무 스트레스로 많이 지쳤습니다.",
        "새로운 취미를 시작하게 되었어요."
    ]

    results = []
    for diary in test_diaries:
        result = await ai_service.analyze_diary_entry(diary)
        results.append(result)

    # 모든 분석 결과 검증
    for result in results:
        assert result is not None
        assert len(result.mood_analysis) > 0
        assert len(result.emotional_insights) > 0
        assert len(result.advice) > 0
