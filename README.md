# 🌍 AI 여행 큐레이션 프로그램

> **Gemini AI + Kakao Local API**를 활용한 스마트 여행 추천 서비스 ✈️  
> 날짜만 입력하면 **AI가 도시를 추천**하고, **맛집 정보**와 함께 **1일 여행 코스**를 제안합니다!

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-API-orange?logo=google)
![Kakao](https://img.shields.io/badge/Kakao-Local_API-yellow?logo=kakao)

---

## 📖 프로그램 개요

### 🎯 이게 뭔가요?

**여행 날짜만 알려주세요!** AI가 알아서 다 해드립니다! 🤖

1. **📅 날짜 입력** → 예: `2024-12-25`
2. **🤖 Gemini AI 분석** → 날씨/축제/계절 고려해 **최적 도시** 추천!
3. **🍽️ Kakao API 호출** → 그 도시의 **인기 맛집 TOP 5** 검색!
4. **📄 최종 리포트** → **Markdown 형식** 여행 계획서 완성!

### ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🎯 **AI 도시 추천** | 날짜/계절/행사 고려한 스마트 추천 |
| 🌤️ **날씨 예측** | 해당 날짜 예상 날씨 정보 제공 |
| 🎉 **행사 정보** | 진행 중인 축제/이벤트 안내 |
| 🍜 **맛집 검색** | Kakao Local API 실시간 검색 |
| 🗺️ **1일 코스** | 오전/점심/오후/저녁 완벽 일정 |
| 📄 **Markdown 리포트** | 바로 활용 가능한 예쁜 형식 |

---

## 🛠️ 설치 방법

### 📋 사전 요구사항

- **Python 3.10 이상** ([다운로드](https://www.python.org/downloads/))
- **Git** ([다운로드](https://git-scm.com/downloads))

### 1️⃣ 프로젝트 클론

```bash
git clone https://github.com/your-username/travel-recommendation.git
cd travel-recommendation
```

### 2️⃣ 가상환경 생성 및 활성화

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Mac / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

> 💡 활성화되면 프롬프트 앞에 `(venv)`가 표시됩니다!

### 3️⃣ 필수 라이브러리 설치

```bash
pip install -r requirements.txt
```

---

## 🔑 .env 설정 방법

### 1️⃣ API 키 발급

#### 🤖 Gemini API 키
1. **[Google AI Studio](https://aistudio.google.com/app/apikey)** 접속
2. Google 계정 로그인 → **"Create API Key"** 클릭
3. 발급된 키 복사

#### 🗺️ Kakao REST API 키
1. **[Kakao Developers](https://developers.kakao.com/)** 접속
2. **"내 애플리케이션" → "애플리케이션 추가하기"**
3. 앱 생성 후 **"앱 키"** 탭에서 **"REST API 키"** 복사

### 2️⃣ .env 파일 생성

프로젝트 **루트 디렉토리**에 `.env` 파일 생성 후 아래 내용 작성! 👇

```env
GEMINI_API_KEY=여기에_Gemini_키_붙여넣기
KAKAO_API_KEY=여기에_Kakao_REST_API_키_붙여넣기
```

> ⚠️ **주의!** 따옴표(`"`, `'`) 없이 작성하세요!

---

## 🚀 실행 예시

### 📌 기본 사용법

```bash
python main.py --date 2024-12-25
```

### 🎨 실행 결과 예시

```
==================================================
🌍 여행 추천 프로그램 시작!
==================================================

📅 입력받은 날짜: 2024-12-25
🗓️  요일: 수요일

🤖 Gemini API 호출 중...
✅ Gemini 응답 파싱 성공!

🏙️  추천 도시: 부산
🌤️  예상 날씨: 맑고 쌀쌀함 (최고 8도/최저 1도)
🎉 행사/축제: 해운대 빛축제, 부산크리스마스트리문화축제

🍽️  Kakao API 호출 중... (부산 맛집 검색)
✅ 맛집 5곳 검색 완료!

📄 최종 여행 리포트 생성 완료!
```

---

## 📁 결과물 위치 안내

### 📂 프로젝트 구조

```
travel-recommendation/
├── 📄 main.py              # 메인 실행 파일
├── 📄 requirements.txt     # 필수 라이브러리 목록
├── 📄 .env                 # 🔒 API 키 (Git 제외!)
├── 📄 .gitignore           # Git 제외 파일 목록
├── 📄 README.md            # 이 파일! 📖
└── 📁 venv/                # 가상환경 (Git 제외)
```

### 📄 결과물 저장 방법

터미널 출력을 파일로 저장하고 싶다면! 💾

```bash
python main.py --date 2024-12-25 > travel_report.md
```

→ `.md` 파일로 저장하면 VS Code/GitHub에서 예쁘게 렌더링됩니다! 🎨

---

## 🔒 API 키 보안 주의사항

### ⚠️ 절대 하지 말아야 할 것!

#### ❌ `.env` 파일을 Git에 커밋 금지!

```bash
# .gitignore에 반드시 포함!
.env
```

**확인 방법** 🔍
```bash
git status
```
→ `.env`가 목록에 나타나면 **위험**! 즉시 `.gitignore`에 추가!

#### ❌ API 키를 코드에 직접 작성 금지!

```python
# 🚫 절대 금지!
api_key = "AIzaSyABC123..."

# ✅ 올바른 방법!
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
```

### ✅ 안전 수칙

| 규칙 | 설명 |
|------|------|
| 🔐 **환경변수 사용** | 항상 `.env` 파일로 관리 |
| 🚫 **Git 제외** | `.gitignore`에 `.env` 필수 포함 |
| 🔄 **주기적 교체** | 3~6개월마다 재발급 권장 |
| 🚨 **노출 시 즉시 재발급** | 실수로 노출됐다면 바로 폐기! |

### 🆘 API 키 노출 시 재발급

- **Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey) → 기존 키 삭제 후 재발급
- **Kakao**: [Kakao Developers](https://developers.kakao.com/) → 앱 설정 → 키 재발급

---

## 📜 라이선스

MIT License

---

**🎉 이제 여행 준비 완료! 즐거운 여행 되세요!** ✈️🌍