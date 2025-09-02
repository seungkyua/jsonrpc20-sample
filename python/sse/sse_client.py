import warnings
import urllib3

# urllib3 warning 완전 제거 (requests import 전에 실행)
urllib3.disable_warnings()
warnings.filterwarnings('ignore', message='.*OpenSSL.*')

import requests
import json
import time


class MCPSSEClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.sse_url = f"{base_url}/sse"
        self.message_endpoint = None
        self.session = requests.Session()
        
        # SSE 연결을 위한 세션 설정
        self.session.headers.update({
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
    
    def connect(self):
        """SSE 연결을 시작하고 endpoint 이벤트를 기다림"""
        try:
            print(f"SSE 연결 시작: {self.sse_url}")
            
            # SSE는 지속적인 연결이므로 무제한 타임아웃 사용
            with self.session.get(self.sse_url, stream=True, timeout=None) as response:
                response.raise_for_status()
                
                event_type = None
                for line in response.iter_lines():
                    if line is None:
                        continue
                        
                    try:
                        line = line.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    
                    if line.startswith('event: '):
                        event_type = line[len('event: '):].strip()
                        print(f"이벤트 타입: {event_type}")
                        
                    elif line.startswith('data: '):
                        data = line[len('data: '):].strip()
                        if data:
                            try:
                                json_data = json.loads(data)
                                
                                if event_type == 'endpoint':
                                    self.message_endpoint = json_data.get('uri')
                                    print(f"메시지 전송 엔드포인트: {self.message_endpoint}")
                                    print("MCP 연결 완료. 메시지 요청을 보낼 수 있습니다.")
                                    
                                    # 연결 완료 후 메시지 요청
                                    self.request_messages()
                                    
                                elif event_type == 'message':
                                    if json_data.get('method') == 'server_message':
                                        print(f"📨 서버 메시지 {json_data.get('id')}: {json_data.get('params', {}).get('message')}")
                                    else:
                                        print(f"받은 MCP 메시지: {json_data}")
                                    
                            except json.JSONDecodeError:
                                print(f"JSON 파싱 실패: {data}")
                    
                    elif line == '':  # 빈 줄은 이벤트 구분자
                        continue
                        
        except requests.exceptions.Timeout:
            print("연결 시간 초과")
        except requests.exceptions.ConnectionError as e:
            print(f"연결 에러: {e}")
        except requests.exceptions.RequestException as e:
            print(f"연결 중 에러 발생: {e}")
        except Exception as e:
            print(f"예상치 못한 에러: {e}")
    

    

    
    def request_messages(self):
        """서버에 메시지 요청을 보냄"""
        if not self.message_endpoint:
            print("메시지 엔드포인트가 설정되지 않음")
            return
        
        request_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "request_messages",
            "params": {"count": 5}
        }
        
        try:
            print("📤 서버에 메시지 요청 전송...")
            response = self.session.post(
                f"{self.base_url}{self.message_endpoint}",
                json=request_message,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            # SSE 스트림 응답 처리
            for line in response.iter_lines():
                if line is None:
                    continue
                    
                try:
                    line = line.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                
                if line.startswith('event: '):
                    event_type = line[len('event: '):].strip()
                    
                elif line.startswith('data: '):
                    data = line[len('data: '):].strip()
                    if data:
                        try:
                            json_data = json.loads(data)
                            if json_data.get('method') == 'server_message':
                                print(f"📨 서버 메시지 {json_data.get('id')}: {json_data.get('params', {}).get('message')}")
                        except json.JSONDecodeError:
                            print(f"JSON 파싱 실패: {data}")
                
                elif line == '':
                    continue
                    
        except Exception as e:
            print(f"메시지 요청 실패: {e}")
    
    def close(self):
        """연결 종료"""
        self.session.close()
        print("연결 종료")


if __name__ == "__main__":
    client = MCPSSEClient('http://127.0.0.1:5000')
    try:
        client.connect()
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    finally:
        client.close()