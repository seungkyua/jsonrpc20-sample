import requests
import json


def listen_for_sse(url):
    try:
        # stream=True 옵션을 사용하여 스트리밍 연결 시작
        with requests.get(url, stream=True) as response:
            # 상태 코드가 200이 아니면 에러
            response.raise_for_status()

            # SSE 스트림 파싱
            for line in response.iter_lines():
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    # 'data: ' 접두사 제거
                    data = line[len('data: '):].strip()
                    if data:
                        try:
                            json_data = json.loads(data)
                            print(f"받은 데이터: {json_data}")
                        except json.JSONDecodeError:
                            print(f"JSON 파싱 실패: {data}")

    except requests.exceptions.RequestException as e:
        print(f"연결 중 에러 발생: {e}")


if __name__ == "__main__":
    sse_url = 'http://localhost:5000/stream'
    print("SSE 연결 시작...")
    listen_for_sse(sse_url)
    print("연결 종료")