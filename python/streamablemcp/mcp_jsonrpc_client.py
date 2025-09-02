#!/usr/bin/env python3
"""
MCP JSON-RPC 2.0 Client

MCP Specification 2025-06-18에 맞는 Streamable HTTP 클라이언트
"""

import asyncio
import aiohttp
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime

class MCPClient:
    """MCP Specification 2025-06-18에 맞는 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None
        self.protocol_version = "2025-06-18"
        self.session_id = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def create_request(self, method: str, params: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
        """JSON-RPC 2.0 요청 생성"""
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }
    
    def get_headers(self) -> Dict[str, str]:
        """MCP Specification에 맞는 헤더 생성"""
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": self.protocol_version
        }
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        return headers
    
    async def call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출"""
        if not self.session:
            raise RuntimeError("세션이 초기화되지 않았습니다. 'async with' 문을 사용하세요.")
        
        request = self.create_request(method, params)
        headers = self.get_headers()
        
        async with self.session.post(f"{self.base_url}/mcp", json=request, headers=headers) as response:
            if response.status == 202:
                # Notification/Response 처리됨
                return {"status": "accepted", "message": "Request accepted"}
            
            response.raise_for_status()
            return await response.json()
    
    async def call_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배치 요청"""
        if not self.session:
            raise RuntimeError("세션이 초기화되지 않았습니다. 'async with' 문을 사용하세요.")
        
        headers = self.get_headers()
        
        async with self.session.post(f"{self.base_url}/mcp", json=requests, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def stream(self, method: str, params: Dict[str, Any]):
        """도구 스트리밍"""
        if not self.session:
            raise RuntimeError("세션이 초기화되지 않았습니다. 'async with' 문을 사용하세요.")
        
        request = self.create_request(method, params)
        headers = self.get_headers()
        
        async with self.session.post(f"{self.base_url}/mcp", json=request, headers=headers) as response:
            response.raise_for_status()
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    # SSE 형식 파싱
                    data_str = line[6:]  # "data: " 제거
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        continue
    
    async def listen_server_events(self):
        """서버 이벤트 수신 (GET /mcp)"""
        if not self.session:
            raise RuntimeError("세션이 초기화되지 않았습니다. 'async with' 문을 사용하세요.")
        
        headers = {
            "Accept": "text/event-stream",
            "MCP-Protocol-Version": self.protocol_version
        }
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        async with self.session.get(f"{self.base_url}/mcp", headers=headers) as response:
            response.raise_for_status()
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        continue

async def demo():
    """데모 실행"""
    print("🚀 MCP JSON-RPC 2.0 Client 데모 (Specification 2025-06-18)")
    print("=" * 60)
    
    async with MCPClient() as client:
        # 단일 요청 테스트
        print("📡 단일 요청 테스트:")
        
        # 날씨 정보
        result = await client.call("get_weather", {"location": "서울"})
        if "result" in result:
            print(f"   🌤️  날씨: {result['result']['location']} - {result['result']['temperature']}")
        
        # 계산
        result = await client.call("calculate", {"operation": "multiply", "a": 15, "b": 3})
        if "result" in result:
            print(f"   🧮 계산: {result['result']['a']} × {result['result']['b']} = {result['result']['result']}")
        
        # 배치 요청 테스트
        print("\n📦 배치 요청 테스트:")
        batch_requests = [
            client.create_request("get_weather", {"location": "부산"}),
            client.create_request("calculate", {"operation": "add", "a": 10, "b": 20}),
            client.create_request("stream_data", {"count": 2})
        ]
        
        results = await client.call_batch(batch_requests)
        print(f"   ✅ {len(results)}개 요청 처리 완료")
        
        # 스트리밍 테스트
        print("\n🌊 스트리밍 테스트:")
        print("   📊 데이터 스트리밍:")
        async for data in client.stream("stream_data", {"count": 3}):
            if "result" in data:
                status = data["result"].get("status")
                if status == "start":
                    print(f"      🚀 스트리밍 시작")
                elif status == "data":
                    print(f"      📊 {data['result']['index']}: {data['result']['value']}")
                elif status == "complete":
                    print(f"      ✅ 스트리밍 완료")
        
        # 날씨 스트리밍 테스트
        print("\n   🌤️  날씨 스트리밍:")
        async for data in client.stream("get_weather", {"location": "제주", "stream": True}):
            if "result" in data:
                status = data["result"].get("status")
                if status == "start":
                    print(f"      🚀 스트리밍 시작")
                elif status == "data":
                    print(f"      📊 {data['result']['field']}: {data['result']['value']}")
                elif status == "complete":
                    print(f"      ✅ 스트리밍 완료")
        
        # 서버 이벤트 수신 테스트
        print("\n📡 서버 이벤트 수신 테스트:")
        print("   🎧 서버 알림 수신 중... (Enter 키를 누르면 종료)")
        
        # 사용자 입력을 비동기적으로 처리하기 위한 이벤트 루프
        loop = asyncio.get_event_loop()
        
        async def wait_for_enter():
            """Enter 키 입력 대기"""
            await loop.run_in_executor(None, input)
            return True
        
        async def listen_events():
            """서버 이벤트 수신"""
            try:
                async for event in client.listen_server_events():
                    if "method" in event and event["method"] == "server_notification":
                        message = event["params"]["message"]
                        print(f"      📢 서버: {message}")
            except Exception as e:
                print(f"      ❌ 이벤트 수신 오류: {e}")
        
        # Enter 키 입력과 이벤트 수신을 동시에 처리
        try:
            # Python 3.8+ 호환성을 위해 ensure_future 사용
            enter_task = asyncio.ensure_future(wait_for_enter())
            events_task = asyncio.ensure_future(listen_events())
            
            # 두 태스크 중 하나가 완료될 때까지 대기
            done, pending = await asyncio.wait(
                [enter_task, events_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 완료되지 않은 태스크 취소
            for task in pending:
                task.cancel()
            
            print("      ✅ 사용자가 Enter를 눌러 종료했습니다.")
        except Exception as e:
            print(f"      ❌ 오류: {e}")
        
        print("\n🎉 모든 테스트 완료!")

if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\n👋 프로그램이 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류: {e}")
