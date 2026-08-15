import argparse
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import requests  # 🌐 HTTP 요청을 보내기 위한 라이브러리 (Kakao API 호출용)

# ==========================================
# 환경변수 로드
# ==========================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

# Gemini 클라이언트 (OpenAI 호환 방식)
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


# ==========================================
# 날짜 검증 함수
# ==========================================
def validate_date(date_str):
    """YYYY-MM-DD 형식의 날짜 문자열을 검증하고 파싱"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"❌ 날짜 형식이 잘못됨: '{date_str}' (올바른 형식: YYYY-MM-DD)"
        )


# ==========================================
# Gemini API 호출 함수 (여행지 추천)
# ==========================================
def get_travel_recommendation(date_str, weekday, errors):
    """
    Gemini API를 호출하여 여행 추천을 받아옴.
    최종 실패 시 None을 반환하고 errors 리스트에 기록한다(프로그램은 중단하지 않음).
    """

    prompt = f"""당신은 한국 여행 전문가입니다.
{date_str} ({weekday})에 여행하기 좋은 한국의 도시 1곳을 추천해주세요.

추천 기준:
- 문화/역사적 명소가 있는 도시
- 유명한 맛집이나 향토 음식이 있는 도시
- 그 시기에 열리는 축제나 행사가 있으면 우선

반드시 아래 JSON 형식으로만 응답하세요. 다른 설명, 인사말, 마크다운 코드블록은 절대 넣지 마세요.

{{
  "recommended_city": "도시 이름 (예: 경주)",
  "weather": "예상 날씨 (예: 맑음, 최고 18도/최저 8도)",
  "events": ["행사1", "행사2", "행사3"],
  "reason": "추천 이유 (문화/역사/맛집/축제 관점에서 2-3문장)"
}}"""

    last_error_msg = None

    for attempt in range(2):
        try:
            print(f"\n🤖 [1/3] 1차 추천 생성 중(LLM)... (시도 {attempt + 1}/2)")

            response = client.chat.completions.create(
                model="gemini-3.6-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # 🧹 마크다운 코드블록 제거
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            data = json.loads(content)

            # ✅ 필수 키 검증
            required_keys = ["recommended_city", "weather", "events", "reason"]
            missing_keys = [k for k in required_keys if k not in data]

            if missing_keys:
                raise ValueError(f"필수 키 누락: {missing_keys}")

            print(f"  - recommended_city: \"{data['recommended_city']}\"")
            return data

        except (json.JSONDecodeError, ValueError) as e:
            last_error_msg = str(e)
            print(f"⚠️  검증/파싱 실패: {e}")
            if attempt == 0:
                print("🔄 재시도합니다...")
            else:
                print("❌ 재시도도 실패했습니다. 오류를 기록하고 다음 단계로 진행합니다.")
                errors.append({
                    "step": "recommendation",
                    "type": "PARSE_ERROR",
                    "message": last_error_msg
                })
                return None
        except Exception as e:
            print(f"❌ API 호출 에러: {e}")
            errors.append({
                "step": "recommendation",
                "type": "API_ERROR",
                "message": str(e)
            })
            return None

    return None


# ==========================================
# Kakao 맛집 검색 함수
# ==========================================
def search_restaurants(city_name, errors):
    """
    Kakao Local API로 특정 도시의 맛집 5곳을 검색.
    실패해도 프로그램을 중단시키지 않고 빈 리스트를 반환하며 errors에 기록한다.
    """
    if not city_name:
        errors.append({
            "step": "place_search",
            "type": "SKIPPED",
            "message": "추천 도시 정보가 없어 맛집 검색을 건너뜀"
        })
        return []

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": f"{city_name} 맛집",
        "size": 5,
        "sort": "accuracy"
    }

    try:
        print(f"\n🍽️  [2/3] 맛집 검색 중(지도/장소 API)...")

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            error_msg = "인증 실패(401). 키 설정을 확인하세요."
            print(f"  - 오류: {error_msg}")
            errors.append({"step": "place_search", "type": "AUTH_ERROR", "message": error_msg})
            return []

        if response.status_code == 403:
            error_msg = "권한 없음(403). 앱 설정에서 로컬 API 활성화 확인!"
            print(f"  - 오류: {error_msg}")
            errors.append({"step": "place_search", "type": "AUTH_ERROR", "message": error_msg})
            return []

        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])

        if not documents:
            error_msg = f"'{city_name} 맛집' 검색 결과 0건"
            print(f"  - {error_msg}")
            errors.append({"step": "place_search", "type": "EMPTY_RESULT", "message": error_msg})
            return []

        restaurants = []
        for doc in documents:
            restaurants.append({
                "name": doc.get("place_name", "이름 없음"),
                "address": doc.get("address_name", "주소 없음"),
                "category": doc.get("category_name", "분류 없음"),
                "url": doc.get("place_url", ""),
                "x": doc.get("x", ""),
                "y": doc.get("y", "")
            })

        print(f"  - 맛집 {len(restaurants)}곳 검색 완료")
        return restaurants

    except Exception as e:
        error_msg = f"요청 실패: {str(e)}"
        print(f"  - 오류: {error_msg}")
        errors.append({"step": "place_search", "type": "REQUEST_ERROR", "message": error_msg})
        return []


# ==========================================
# 최종 LLM 리포트 생성
# ==========================================
def generate_final_report(date_str, recommendation, restaurants, errors):
    """
    1차 추천 데이터 + 맛집 데이터 + 오류 목록을 종합해 마크다운 리포트를 작성한다.
    """
    print("\n📝 [3/3] 최종 리포트 생성 중(LLM)...")

    city = recommendation.get("recommended_city", "추천 실패")
    weather = recommendation.get("weather", "정보 없음")
    events = ", ".join(recommendation.get("events", [])) or "정보 없음"
    reason = recommendation.get("reason", "정보 없음")

    if restaurants:
        restaurant_text = "\n".join(
    [f"- {r['name']} ({r['category']}) : {r['address']} | 링크: {r['url']}" for r in restaurants]
)
    else:
        restaurant_text = "데이터 없음 (검색된 맛집이 없습니다.)"

    if errors:
        error_text = "\n".join(
            [f"- [{e['step']}/{e['type']}] {e['message']}" for e in errors]
        )
    else:
        error_text = "없음"

    prompt = f"""당신은 훌륭한 여행 가이드입니다.
다음 수집된 정보들을 바탕으로 '{date_str} 국내 여행 추천 리포트'를 마크다운(Markdown) 형식으로 예쁘게 작성해주세요.

[기본 정보]
- 추천 도시: {city}
- 날씨 요약: {weather}
- 행사/축제: {events}
- 추천 이유: {reason}

[맛집 정보]
{restaurant_text}

[오류 정보]
{error_text}

아래의 제목(Heading)들을 반드시 포함하여 리포트를 작성해 주세요. 오류 정보가 "없음"이면 오류 요약 섹션에 "특이사항 없음"이라고만 적어주세요.
## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안 (오전/오후/저녁으로 나누어 자연스럽게 작성)
## 오류 요약(errors)
"""

    try:
        response = client.chat.completions.create(
            model="gemini-3.6-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        print("  - 리포트 생성 완료")
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ 리포트 생성 중 에러 발생: {e}")
        errors.append({"step": "report_generation", "type": "API_ERROR", "message": str(e)})
        # LLM 호출 자체가 실패해도 최소한의 리포트는 남긴다
        return (
            f"# {date_str} 국내 여행 추천 리포트\n\n"
            f"## 추천 지역\n{city}\n\n"
            f"## 추천 이유\n{reason}\n\n"
            f"## 날씨 요약\n{weather}\n\n"
            f"## 행사/축제\n{events}\n\n"
            f"## 맛집 추천\n{restaurant_text}\n\n"
            f"## 1일 일정 제안\n리포트 생성 중 오류로 자동 생성하지 못했습니다.\n\n"
            f"## 오류 요약(errors)\n{error_text}\n"
        )


# ==========================================
# 결과 파일 저장
# ==========================================
def save_results(date_str, recommendation, restaurants, errors, report_md):
    """
    results 폴더를 만들고 JSON 파일과 마크다운 파일을 저장한다.
    """
    os.makedirs("results", exist_ok=True)

    final_json_data = {
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }

    json_filename = f"results/{date_str}_data.json"
    md_filename = f"results/{date_str}_travel_plan.md"

    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(final_json_data, f, ensure_ascii=False, indent=2)

    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n완료! {md_filename} 를 확인하세요.")


# ==========================================
# 메인 함수
# ==========================================
def main():
    # 📌 인자 없이 그냥 실행했을 때 친절한 사용법 안내
    if len(sys.argv) == 1:
        print('📌 사용법: python main.py -date "YYYY-MM-DD"')
        print('   예시  : python main.py -date "2025-11-15"')
        print('\n여행 날짜를 -date 옵션과 함께 입력해주세요!')
        return

    parser = argparse.ArgumentParser(
        description="🌍 AI 여행 추천 프로그램",
        epilog='예시: python main.py -date "2025-11-15"'
    )
    parser.add_argument(
        "-date", "--date",
        type=validate_date,
        required=True,
        help='여행 날짜 (형식: YYYY-MM-DD). 예: -date "2025-11-15"'
    )
    args = parser.parse_args()

    if not GEMINI_API_KEY or not KAKAO_REST_API_KEY:
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에 GEMINI_API_KEY, KAKAO_REST_API_KEY 를 설정해주세요.")
        return

    date_obj = args.date
    date_str = date_obj.strftime("%Y-%m-%d")

    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday = weekdays[date_obj.weekday()]

    json_filename = f"results/{date_str}_data.json"
    errors = []

    try:
        # ⭐ 캐싱: 동일 날짜 데이터가 이미 있으면 API 호출을 건너뛴다
        if os.path.exists(json_filename):
            print(f"\n📦 이미 저장된 데이터가 있습니다! ({json_filename})")
            print("API 호출을 건너뛰고 기존 데이터로 리포트만 다시 재생성합니다.")

            with open(json_filename, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            recommendation = cached_data.get("recommendation", {})
            restaurants = cached_data.get("restaurants", [])
            errors = cached_data.get("errors", [])

        else:
            # 1. 여행지 추천 받기 (LLM) — 실패해도 None 반환, errors에 기록됨
            recommendation = get_travel_recommendation(date_str, weekday, errors)
            if recommendation is None:
                recommendation = {}

            # 2. 맛집 검색하기 (Kakao API) — 추천 도시가 없으면 자동으로 건너뜀
            city = recommendation.get("recommended_city")
            restaurants = search_restaurants(city, errors)

        # 3. 종합 리포트 생성 (LLM) — 어떤 상황에서도 리포트는 생성된다
        report_md = generate_final_report(date_str, recommendation, restaurants, errors)

        # 4. 파일로 저장하기
        save_results(date_str, recommendation, restaurants, errors, report_md)

        if errors:
            print(f"\n⚠️  실행 중 {len(errors)}건의 오류가 있었습니다. (리포트 내 '오류 요약' 섹션 참고)")

    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 예상치 못한 문제가 발생했습니다: {e}")


if __name__ == "__main__":
    main()