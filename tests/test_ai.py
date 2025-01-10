import pytest

from src.diary.service.AIAnalysis import analyze_diary_entry


@pytest.mark.asyncio
async def test_diary_analysis():
    # 테스트용 일기 내용
    test_diary_content = """
    오늘 정말 힘든 하루였어요. 
    업무 스트레스가 너무 많아서 지쳤고, 
    마음이 무겁고 우울했습니다.
    """

    # 일기 분석 수행
    result = analyze_diary_entry(test_diary_content)

    # 결과 검증
    assert result is not None, "분석 결과가 None입니다"
    assert isinstance(result, str), "분석 결과는 문자열이어야 합니다"
    assert len(result) > 0, "분석 결과가 비어있습니다"


@pytest.mark.asyncio
async def test_diary_analysis_error_handling():
    # 빈 내용으로 테스트
    result = analyze_diary_entry("")

    # 오류 처리 검증
    assert result is not None, "빈 내용에 대한 분석 결과가 None입니다"
    assert isinstance(result, str), "분석 결과는 문자열이어야 합니다"
    assert len(result) > 0, "빈 내용에 대한 분석 결과가 비어있습니다"
