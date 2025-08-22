import json
from requests_sse import EventSource

sse_url = 'http://localhost:5000/stream'

try:
    with EventSource(sse_url) as client:
        print("SSE 연결 성공. 서버로부터 오는 모든 이벤트를 출력합니다...")

        for event in client:
            print(f"받은 이벤트: type={event.type}, data={event.data}")

            if event.type == 'message' and event.data:
                try:
                    data = json.loads(event.data)
                    print(f"✅ 데이터가 성공적으로 파싱되었습니다: {data}")
                except json.JSONDecodeError:
                    print(f"❌ JSON 파싱 실패: {event.data}")

except Exception as e:
    print(f"연결 중 에러 발생: {e}")
finally:
    print("연결 종료")