#!/usr/bin/env python3
"""
MCP JSON-RPC 2.0 테스트 스크립트

MCP Specification 2025-06-18에 맞는 Streamable HTTP 테스트
"""

import requests
import json
import uuid

MCP_PROTOCOL_VERSION = "2025-06-18"

def get_mcp_headers():
    """MCP Specification에 맞는 헤더 생성"""
    return {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
    }

def test_server():
    """서버 연결 테스트"""
    print("🔍 서버 연결 테스트...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            info = response.json()
            print(f"✅ 서버 연결: {info['message']}")
            print(f"   프로토콜 버전: {info['protocol_version']}")
            print(f"   엔드포인트: {info['endpoint']}")
            print(f"   도구: {', '.join(info['tools'])}")
            return True
        else:
            print(f"❌ 서버 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

def test_single_request():
    """단일 요청 테스트"""
    print("\n📡 단일 요청 테스트:")
    
    headers = get_mcp_headers()
    
    # 날씨 요청
    request_data = {
        "jsonrpc": "2.0",
        "method": "get_weather",
        "params": {"location": "부산"},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            data = result["result"]
            print(f"   🌤️  날씨: {data['location']} - {data['temperature']}")
        elif "error" in result:
            print(f"   ❌ 오류: {result['error']['message']}")
    
    # 계산 요청
    request_data = {
        "jsonrpc": "2.0",
        "method": "calculate",
        "params": {"operation": "multiply", "a": 15, "b": 3},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if "result" in result:
            data = result["result"]
            print(f"   🧮 계산: {data['a']} × {data['b']} = {data['result']}")

def test_batch_request():
    """배치 요청 테스트"""
    print("\n📦 배치 요청 테스트:")
    
    headers = get_mcp_headers()
    
    batch_requests = [
        {
            "jsonrpc": "2.0",
            "method": "get_weather",
            "params": {"location": "서울"},
            "id": str(uuid.uuid4())
        },
        {
            "jsonrpc": "2.0",
            "method": "calculate",
            "params": {"operation": "add", "a": 10, "b": 20},
            "id": str(uuid.uuid4())
        },
        {
            "jsonrpc": "2.0",
            "method": "stream_data",
            "params": {"count": 2},
            "id": str(uuid.uuid4())
        }
    ]
    
    response = requests.post("http://localhost:8000/mcp", json=batch_requests, headers=headers)
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ {len(results)}개 요청 처리 완료")
        for i, result in enumerate(results):
            if "result" in result:
                print(f"      요청 {i+1}: 성공")
            elif "error" in result:
                print(f"      요청 {i+1}: 오류 - {result['error']['message']}")

def test_streaming():
    """스트리밍 테스트"""
    print("\n🌊 스트리밍 테스트:")
    
    headers = get_mcp_headers()
    
    # 데이터 스트리밍
    print("   📊 데이터 스트리밍:")
    request_data = {
        "jsonrpc": "2.0",
        "method": "stream_data",
        "params": {"count": 3},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers, stream=True)
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]  # "data: " 제거
                    try:
                        data = json.loads(data_str)
                        if "result" in data:
                            status = data["result"].get("status")
                            if status == "start":
                                print(f"      🚀 스트리밍 시작")
                            elif status == "data":
                                print(f"      📊 {data['result']['index']}: {data['result']['value']}")
                            elif status == "complete":
                                print(f"      ✅ 스트리밍 완료")
                                break
                    except json.JSONDecodeError:
                        continue
    
    # 날씨 스트리밍
    print("   🌤️  날씨 스트리밍:")
    request_data = {
        "jsonrpc": "2.0",
        "method": "get_weather",
        "params": {"location": "제주", "stream": True},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers, stream=True)
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        if "result" in data:
                            status = data["result"].get("status")
                            if status == "start":
                                print(f"      🚀 스트리밍 시작")
                            elif status == "data":
                                print(f"      📊 {data['result']['field']}: {data['result']['value']}")
                            elif status == "complete":
                                print(f"      ✅ 스트리밍 완료")
                                break
                    except json.JSONDecodeError:
                        continue

def test_server_events():
    """서버 이벤트 테스트"""
    print("\n📡 서버 이벤트 테스트:")
    
    headers = {
        "Accept": "text/event-stream",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
    }
    
    print("   🎧 서버 알림 수신 중... (5초)")
    
    try:
        response = requests.get("http://localhost:8000/mcp", headers=headers, stream=True, timeout=5)
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if "method" in data and data["method"] == "server_notification":
                                message = data["params"]["message"]
                                print(f"      📢 서버: {message}")
                        except json.JSONDecodeError:
                            continue
    except requests.exceptions.Timeout:
        print("      ⏰ 시간 초과")
    except Exception as e:
        print(f"      ❌ 오류: {e}")

def test_error_handling():
    """오류 처리 테스트"""
    print("\n⚠️  오류 처리 테스트:")
    
    headers = get_mcp_headers()
    
    # 존재하지 않는 도구
    request_data = {
        "jsonrpc": "2.0",
        "method": "nonexistent_tool",
        "params": {},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers)
    if response.status_code == 404:
        result = response.json()
        if "error" in result:
            print(f"   ✅ 오류 처리: {result['error']['code']} - {result['error']['message']}")
    
    # 잘못된 파라미터
    request_data = {
        "jsonrpc": "2.0",
        "method": "calculate",
        "params": {"operation": "divide", "a": 10, "b": 0},
        "id": str(uuid.uuid4())
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers)
    if response.status_code == 400:
        result = response.json()
        if "error" in result:
            print(f"   ✅ 파라미터 오류: {result['error']['message']}")

def test_notification():
    """알림 테스트"""
    print("\n📢 알림 테스트:")
    
    headers = get_mcp_headers()
    
    # JSON-RPC notification (id가 없음)
    request_data = {
        "jsonrpc": "2.0",
        "method": "server_notification",
        "params": {"message": "This is a notification"}
    }
    
    response = requests.post("http://localhost:8000/mcp", json=request_data, headers=headers)
    if response.status_code == 202:
        print("   ✅ 알림 처리: 202 Accepted")

def main():
    """메인 테스트"""
    print("🧪 MCP JSON-RPC 2.0 테스트 (Specification 2025-06-18)")
    print("=" * 50)
    
    if not test_server():
        return
    
    test_single_request()
    test_batch_request()
    test_streaming()
    test_server_events()
    test_error_handling()
    test_notification()
    
    print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류: {e}")
