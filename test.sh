#!/bin/bash

# 스크립트 실행 시 오류 발생하면 즉시 중단
set -e

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting Code Quality Checks..."

# Black 코드 포맷팅 확인
echo -e "\n${GREEN}[1/5] Running Black Formatter Check${NC}"
poetry run black . --check

# isort 임포트 정렬 확인
echo -e "\n${GREEN}[2/5] Running Isort Import Sorting${NC}"
poetry run isort . --check --diff

# Mypy 타입 체크
echo -e "\n${GREEN}[3/5] Running Mypy Type Checking${NC}"
poetry run mypy .

# Pytest 테스트 실행
echo -e "\n${GREEN}[4/5] Running Pytest${NC}"
poetry run pytest tests/

# FastAPI 서버 시작 테스트
echo -e "\n${GREEN}[5/5] Testing FastAPI Server Startup${NC}"
poetry run uvicorn src.main:app --reload &
SERVER_PID=$!
sleep 5

# 서버 상태 확인
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ FastAPI Server Started Successfully${NC}"
else
    echo -e "${RED}❌ FastAPI Server Startup Failed${NC}"
    kill $SERVER_PID
    exit 1
fi

# 서버 종료
kill $SERVER_PID

echo -e "\n${GREEN}🎉 All Checks Passed Successfully!${NC}"
exit 0
