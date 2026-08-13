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
# ⭐ NEW: Gemini API 호출 함수
# ==========================================
def get_travel_recommendation(date_str, weekday):
    """
    Gemini API를 호출하여 여행 추천을 받아옴
    
    Args:
        date_str: "2025-11-15" 형식의 날짜 문자열
        weekday: "토요일" 등의 요일 문자열
    
    Returns:
        dict: {recommended_city, weather, events, reason}
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
            print(f"\n🤖 Gemini API 호출 중... (시도 {attempt + 1}/2)")
            
            # API 호출
            response = client.chat.completions.create(
                model="gemini-3.6-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # 창의성 (0=일관성, 1=창의성)
            )
            
            # 응답 텍스트 추출
            content = response.choices[0].message.content.strip()
            
            # 🧹 마크다운 코드블록 제거 (```json ... ``` 방지)
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            # 📦 JSON 파싱
            data = json.loads(content)
            
            # ✅ 필수 키 검증
            required_keys = ["recommended_city", "weather", "events", "reason"]
            missing_keys = [k for k in required_keys if k not in data]
            
            if missing_keys:
                raise ValueError(f"필수 키 누락: {missing_keys}")
            
            print("✅ Gemini 응답 파싱 성공!")
            return data
            
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 파싱 실패: {e}")
            if attempt == 0:
                print("🔄 재시도합니다...")
            else:
                print("❌ 재시도도 실패했습니다.")
                raise
        except ValueError as e:
            print(f"⚠️  검증 실패: {e}")
            if attempt == 0:
                print("🔄 재시도합니다...")
            else:
                print("❌ 재시도도 실패했습니다.")
                raise
        except Exception as e:
            print(f"❌ API 호출 에러: {e}")
            raise

# ==========================================
# ⭐ NEW: Kakao 맛집 검색 함수
# ==========================================
def search_restaurants(city_name):
    """
    Kakao Local API로 특정 도시의 맛집 5곳을 검색
    
    Args:
        city_name: "경주" 같은 도시 이름
    
    Returns:
        dict: {
            "restaurants": [맛집 리스트],
            "errors": [에러 메시지 리스트]
        }
    """
    
    # 📍 Kakao 로컬 검색 API 주소 (키워드로 장소 검색)
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # 🔐 인증 헤더 (KakaoAK + 공백 + REST API 키)
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
    }
    
    # 🔍 검색 조건 설정
    params = {
        "query": f"{city_name} 맛집",  # 검색어 (예: "경주 맛집")
        "size": 5,                      # 결과 5개만 (최대 15개까지 가능)
        "sort": "accuracy"              # 정확도순 정렬 (or "distance" 거리순)
    }
    
    # 📦 결과를 담을 딕셔너리 (성공한 맛집 + 에러 로그)
    result = {
        "restaurants": [],  # 맛집 정보 리스트
        "errors": []        # 에러 발생 시 기록
    }
    
    try:
        print(f"\n🍽️  Kakao API 호출 중... ({city_name} 맛집 검색)")
        
        # 🌐 HTTP GET 요청 보내기 (timeout: 10초 안에 응답 없으면 에러)
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        # 🚨 인증 에러 특별 처리 (401=인증 실패, 403=권한 없음)
        if response.status_code == 401:
            error_msg = "❌ Kakao API 인증 실패 (401): REST API 키를 확인하세요!"
            print(error_msg)
            result["errors"].append(error_msg)
            return result  # 빈 리스트 + 에러 메시지 반환
        
        if response.status_code == 403:
            error_msg = "❌ Kakao API 권한 없음 (403): 앱 설정에서 로컬 API 활성화 확인!"
            print(error_msg)
            result["errors"].append(error_msg)
            return result
        
        # 🔍 그 외 HTTP 에러 확인 (4xx, 5xx 응답 → 예외 발생)
        response.raise_for_status()
        
        # 📦 JSON 응답 파싱 (문자열 → 딕셔너리)
        data = response.json()
        
        # 📋 검색 결과 꺼내기 (documents 키 안에 장소 리스트)
        documents = data.get("documents", [])
        
        # 🈳 검색 결과 0건 처리
        if not documents:
            error_msg = f"⚠️  '{city_name} 맛집' 검색 결과가 0건입니다."
            print(error_msg)
            result["errors"].append(error_msg)
            return result  # 빈 리스트 반환 (프로그램 중단 X)
        
        # 🔄 각 맛집 정보를 우리 형식으로 변환
        for doc in documents:
            restaurant = {
                "name": doc.get("place_name", "이름 없음"),        # 상호명
                "address": doc.get("address_name", "주소 없음"),   # 지번 주소
                "category": doc.get("category_name", "분류 없음"), # 카테고리 (음식점 > 한식 > ...)
                "url": doc.get("place_url", ""),                   # 카카오맵 상세 URL
                "x": doc.get("x", ""),                             # 경도 (longitude)
                "y": doc.get("y", "")                              # 위도 (latitude)
            }
            result["restaurants"].append(restaurant)  # 리스트에 추가
        
        print(f"✅ Kakao 응답 파싱 성공! (맛집 {len(result['restaurants'])}곳)")
        return result
        
    except requests.exceptions.Timeout:
        # ⏱️ 타임아웃 에러 (10초 초과)
        error_msg = "❌ Kakao API 응답 시간 초과 (10초)"
        print(error_msg)
        result["errors"].append(error_msg)
        return result
        
    except requests.exceptions.RequestException as e:
        # 🌐 네트워크 에러 (연결 실패, DNS 에러 등)
        error_msg = f"❌ Kakao API 요청 실패: {e}"
        print(error_msg)
        result["errors"].append(error_msg)
        return result
        
    except json.JSONDecodeError as e:
        # 📦 JSON 파싱 에러 (응답이 이상할 때)
        error_msg = f"❌ Kakao API 응답 JSON 파싱 실패: {e}"
        print(error_msg)
        result["errors"].append(error_msg)
        return result


# ==========================================
# 메인 함수
# ==========================================
def main():
    # API 키 확인
    print("🔐 API 키 확인 중...")
    if not GEMINI_API_KEY or not KAKAO_REST_API_KEY:
        print("❌ API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
        return
    print("✅ API 키 로드 완료!\n")
    
    # argparse 설정
    parser = argparse.ArgumentParser(
        description="🌍 AI 여행 추천 프로그램",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--date",
        type=validate_date,
        required=True,
        help="여행 날짜 (형식: YYYY-MM-DD, 예: 2025-11-15)"
    )
    
    args = parser.parse_args()
    date_obj = args.date
    date_str = date_obj.strftime("%Y-%m-%d")
    
    # 요일 계산
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    weekday = weekdays[date_obj.weekday()]
    
    # 헤더 출력
    print("=" * 50)
    print("🌍 여행 추천 프로그램 시작!")
    print("=" * 50)
    print(f"\n📅 입력받은 날짜: {date_str}")
    print(f"📌 파싱된 날짜: {date_obj.strftime('%Y년 %m월 %d일')}")
    print(f"🗓️  요일: {weekday}")
    
    # ⭐ NEW: Gemini API 호출!
    try:
        recommendation = get_travel_recommendation(date_str, weekday)
        
        # 🎨 결과 출력
        print("\n" + "=" * 50)
        print("🎯 AI 여행 추천 결과")
        print("=" * 50)
        print(f"\n🏙️  추천 도시: {recommendation['recommended_city']}")
        print(f"🌤️  예상 날씨: {recommendation['weather']}")
        print(f"🎉 행사/축제:")
        for event in recommendation['events']:
            print(f"    - {event}")
        #반복문 끝
        print(f"\n💡 추천 이유: {recommendation['reason']}") #반복문 밖
        
        # ⭐ NEW: 추천 도시의 맛집 검색!
        city = recommendation['recommended_city']  # 추천받은 도시 이름 추출
        restaurant_data = search_restaurants(city)  # Kakao API 호출!
        
        # 🍽️ 맛집 결과 출력
        print("\n" + "=" * 50)
        print(f"🍽️  {city} 추천 맛집 TOP 5")
        print("=" * 50)
        
        # 맛집이 하나라도 있으면 출력
        if restaurant_data["restaurants"]:
            for idx, restaurant in enumerate(restaurant_data["restaurants"], 1):
                # enumerate(리스트, 1): 인덱스 1부터 시작 (1번, 2번, 3번...)
                print(f"\n[{idx}] {restaurant['name']}")           # 상호명
                print(f"    📍 주소: {restaurant['address']}")     # 주소
                print(f"    🏷️  분류: {restaurant['category']}")   # 카테고리
                print(f"    🔗 링크: {restaurant['url']}")         # 카카오맵 URL
        else:
            print("\n⚠️  검색된 맛집이 없습니다.")
        
        # 🚨 에러가 있었다면 안내
        if restaurant_data["errors"]:
            print("\n⚠️  발생한 에러:")
            for err in restaurant_data["errors"]:
                print(f"   - {err}")
        
    except Exception as e:
        print(f"\n❌ 여행 추천 실패: {e}")


# ==========================================
# 실행 시작점
# ==========================================
if __name__ == "__main__":
    main()