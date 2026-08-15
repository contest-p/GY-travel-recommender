import argparse
import os
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
def get_travel_recommendation(date_str, weekday):
    """
    Gemini API를 호출하여 여행 추천을 받아옴
    """
    
    # 🎨 프롬프트 설계 (JSON 강제!)
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

    # 🔄 최대 2번 시도 (실패 시 재시도 1회)
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
            print(f"⚠️  검증/파싱 실패: {e}")
            if attempt == 0:
                print("🔄 재시도합니다...")
            else:
                print("❌ 재시도도 실패했습니다.")
                raise
        except Exception as e:
            print(f"❌ API 호출 에러: {e}")
            raise


# ==========================================
# Kakao 맛집 검색 함수
# ==========================================
def search_restaurants(city_name):
    """
    Kakao Local API로 특정 도시의 맛집 5곳을 검색
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": f"{city_name} 맛집", 
        "size": 5,                      
        "sort": "accuracy"              
    }
    
    result = {"restaurants": [], "errors": []}
    
    try:
        print(f"\n🍽️  [2/3] 맛집 검색 중(지도/장소 API)...")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 401:
            error_msg = "인증 실패(401). 키 설정을 확인하세요."
            print(f"  - 오류: {error_msg}")
            result["errors"].append({"step": "place_search", "type": "AUTH_ERROR", "message": error_msg})
            return result
        
        if response.status_code == 403:
            error_msg = "권한 없음(403). 앱 설정에서 로컬 API 활성화 확인!"
            print(f"  - 오류: {error_msg}")
            result["errors"].append({"step": "place_search", "type": "AUTH_ERROR", "message": error_msg})
            return result
        
        response.raise_for_status()
        data = response.json()
        documents = data.get("documents", [])
        
        if not documents:
            error_msg = f"'{city_name} 맛집' 검색 결과 0건"
            print(f"  - {error_msg}")
            result["errors"].append({"step": "place_search", "type": "EMPTY_RESULT", "message": error_msg})
            return result 
        
        for doc in documents:
            restaurant = {
                "name": doc.get("place_name", "이름 없음"),
                "address": doc.get("address_name", "주소 없음"),
                "category": doc.get("category_name", "분류 없음"),
                "url": doc.get("place_url", ""),
                "x": doc.get("x", ""),
                "y": doc.get("y", "")
            }
            result["restaurants"].append(restaurant)
        
        print(f"  - 맛집 {len(result['restaurants'])}곳 검색 완료")
        return result
        
    except Exception as e:
        error_msg = f"요청 실패: {str(e)}"
        print(f"  - 오류: {error_msg}")
        result["errors"].append({"step": "place_search", "type": "REQUEST_ERROR", "message": error_msg})
        return result


# ==========================================
# ⭐ NEW: 2차 LLM API 호출 (최종 리포트 생성)
# ==========================================
def generate_final_report(date_str, recommendation, restaurant_data):
    """
    1차 추천 데이터와 2차 맛집 데이터를 종합해 마크다운 리포트를 작성합니다.
    """
    print("\n📝 [3/3] 최종 리포트 생성 중(LLM)...")
    
    city = recommendation.get("recommended_city", "알 수 없음")
    weather = recommendation.get("weather", "정보 없음")
    events = ", ".join(recommendation.get("events", []))
    reason = recommendation.get("reason", "정보 없음")
    
    # 맛집 리스트를 프롬프트에 넣기 좋게 텍스트로 변환
    restaurants = restaurant_data.get("restaurants", [])
    if restaurants:
        restaurant_text = "\n".join([f"- {r['name']} ({r['category']}) : {r['address']}" for r in restaurants])
    else:
        restaurant_text = "데이터 없음 (검색된 맛집이 없습니다.)"

    prompt = f"""당신은 훌륭한 여행 가이드입니다.
다음 수집된 정보들을 바탕으로 '{date_str} 국내 여행 추천 리포트'를 마크다운(Markdown) 형식으로 예쁘게 작성해주세요.

[기본 정보]
- 추천 도시: {city}
- 날씨 요약: {weather}
- 행사/축제: {events}
- 추천 이유: {reason}

[맛집 정보]
{restaurant_text}

아래의 제목(Heading)들을 반드시 포함하여 리포트를 작성해 주세요.
## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
## 1일 일정 제안 (오전/오후/저녁으로 나누어 자연스럽게 작성)
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
        return f"# 리포트 생성 실패\n\n- 발생한 에러: {e}"


# ==========================================
# ⭐ NEW: 결과 파일 저장
# ==========================================
def save_results(date_str, recommendation, restaurant_data, report_md):
    """
    results 폴더를 만들고 JSON 파일과 마크다운 파일을 저장합니다.
    """
    os.makedirs("results", exist_ok=True)
    
    # 원본 데이터를 하나로 묶어 JSON으로 저장
    final_json_data = {
        "recommendation": recommendation,
        "restaurants": restaurant_data.get("restaurants", []),
        "errors": restaurant_data.get("errors", [])
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
    if not GEMINI_API_KEY or not KAKAO_REST_API_KEY:
        print("❌ API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    
    # 명령어로 실행할 때 옵션 설정 (-date, --date 모두 가능하도록 수정)
    parser = argparse.ArgumentParser(description="🌍 AI 여행 추천 프로그램")
    parser.add_argument(
        "-date", "--date",
        type=validate_date,
        required=True,
        help="여행 날짜 (형식: YYYY-MM-DD, 예: 2025-11-15)"
    )
    
    args = parser.parse_args()
    date_obj = args.date
    date_str = date_obj.strftime("%Y-%m-%d")
    
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday = weekdays[date_obj.weekday()]
    
    try:
        # 1. 여행지 추천 받기 (LLM)
        recommendation = get_travel_recommendation(date_str, weekday)
        
        # 2. 맛집 검색하기 (Kakao API)
        city = recommendation['recommended_city']
        restaurant_data = search_restaurants(city)
        
        # 3. 종합 리포트 생성 (LLM)
        report_md = generate_final_report(date_str, recommendation, restaurant_data)
        
        # 4. 파일로 저장하기
        save_results(date_str, recommendation, restaurant_data, report_md)
        
    except Exception as e:
        print(f"\n❌ 프로그램 실행 중 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    main()