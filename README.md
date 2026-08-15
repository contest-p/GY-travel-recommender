Markdown
# 🌏 AI 국내 여행지 추천 프로그램

사용자가 입력한 날짜에 맞춰 **LLM(Gemini) API**와 **지도(Kakao) API**를 결합하여 최적의 여행지와 맛집 리스트, 마크다운 형태의 종합 여행 리포트를 자동 생성해 주는 CLI 기반 프로그램입니다.

---

## 📌 주요 기능

* **1차 여행지 추천:** LLM이 날짜에 맞는 추천 도시, 날씨 요약, 축제/행사 정보 생성
* **2차 맛집 검색:** 추천된 도시를 기반으로 지도 API를 통해 주변 맛집 리스트 자동 검색
* **최종 리포트 생성:** 검색된 데이터를 종합하여 1일 일정표가 포함된 Markdown 리포트 자동 작성
* **자동 결과 저장:** `results/` 폴더 내 원본 JSON 및 최종 Markdown 리포트 파일 저장

---

## 🛠️ 설치 및 설정 방법

### 1. 라이브러리 설치
터미널에서 아래 명령어를 입력하여 필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
2. 환경 변수(.env) 설정
프로젝트 최상단 폴더에 .env 파일을 생성한 뒤, 발급받은 API 키를 작성합니다.

코드 스니펫
GEMINI_API_KEY="본인의_제미나이_API_키"
KAKAO_REST_API_KEY="본인의_카카오_REST_API_키"
🚀 실행 방법
터미널에 -date 옵션과 함께 YYYY-MM-DD 형식으로 날짜를 입력하여 실행합니다.

Bash
python main.py -date "2026-10-15"
📁 결과물 저장 위치 안내
프로그램 실행이 완료되면 프로젝트 폴더 내 results/ 폴더가 자동 생성되며 아래 두 가지 파일이 저장됩니다.

YYYY-MM-DD_data.json: 1차 추천 결과 + 맛집 검색 결과가 담긴 원본 데이터

YYYY-MM-DD_travel_plan.md: 최종 정돈된 여행 추천 리포트 문서

⚠️ API 키 보안 주의사항
🚨 경고: API 키가 포함된 .env 파일은 절대 깃허브(GitHub) 등 외부에 공개된 저장소에 업로드해서는 안 됩니다.

키가 유출될 경우 오남용이나 과금 문제가 발생할 수 있으므로, 반드시 .gitignore 파일에 .env가 등록되어 있는지 확인해 주세요.


---

### 💡 붙여넣은 후 깃허브 업로드(3단계)

`README.md` 파일 저장 후 VSCode 터미널에 순서대로 입력하시면 깃허브에 아주 이쁘게 올라갑니다!

```bash
git add README.md
git commit -m "docs: README.md 마크다운 가독성 및 디자인 개선"
git push origin main