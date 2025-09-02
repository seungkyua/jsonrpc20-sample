#!/usr/bin/env python3
"""
MCP JSON-RPC 2.0 Server

MCP Specification 2025-06-18에 맞는 Streamable HTTP 서버
"""

import asyncio
import json
import uuid
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="MCP JSON-RPC 2.0 Server", version="1.0.0")

# MCP 프로토콜 버전
MCP_PROTOCOL_VERSION = "2025-06-18"

# 보안: localhost만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 도구들
TOOLS = {
    "get_weather": {
        "description": "도시의 날씨 정보를 가져옵니다",
        "params": {"location": "string"}
    },
    "calculate": {
        "description": "수학 계산을 수행합니다",
        "params": {"operation": "string", "a": "number", "b": "number"}
    },
    "stream_data": {
        "description": "데이터를 스트리밍합니다",
        "params": {"count": "number"}
    }
}

# 오류 코드
ERROR_CODES = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603
}

def create_response(result=None, error=None, request_id=None):
    """JSON-RPC 2.0 응답 생성"""
    response = {"jsonrpc": "2.0"}
    if error:
        response["error"] = error
    if result is not None:
        response["result"] = result
    if request_id is not None:
        response["id"] = request_id
    return response

def validate_mcp_headers(request: Request):
    """MCP 헤더 검증"""
    # Origin 헤더 검증 (보안)
    origin = request.headers.get("origin")
    if origin and not (origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")):
        raise HTTPException(status_code=403, detail="Invalid origin")
    
    # Accept 헤더 검증
    accept = request.headers.get("accept", "")
    if "application/json" not in accept and "text/event-stream" not in accept:
        raise HTTPException(status_code=400, detail="Accept header must include application/json and/or text/event-stream")
    
    # MCP 프로토콜 버전 헤더 검증
    protocol_version = request.headers.get("mcp-protocol-version")
    if protocol_version and protocol_version != MCP_PROTOCOL_VERSION:
        raise HTTPException(status_code=400, detail=f"Unsupported MCP protocol version: {protocol_version}")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "MCP JSON-RPC 2.0 Server",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "endpoint": "/mcp",
        "tools": list(TOOLS.keys())
    }

@app.get("/mcp")
async def handle_mcp_get(request: Request):
    """MCP GET 엔드포인트 - SSE 스트림 시작"""
    validate_mcp_headers(request)
    
    # Accept 헤더에서 text/event-stream 확인
    accept = request.headers.get("accept", "")
    if "text/event-stream" not in accept:
        raise HTTPException(status_code=405, detail="Method Not Allowed - SSE not supported")
    
    # SSE 스트림 시작
    async def sse_stream():
        # 서버에서 클라이언트로의 메시지 스트림
        yield "data: {\"jsonrpc\": \"2.0\", \"method\": \"server_notification\", \"params\": {\"message\": \"SSE stream started\"}}\n\n"
        
        # 주기적으로 서버 상태 전송
        for i in range(5):
            await asyncio.sleep(2)
            yield f"data: {{\"jsonrpc\": \"2.0\", \"method\": \"server_notification\", \"params\": {{\"message\": \"Server heartbeat {i+1}\"}}}}\n\n"
    
    return StreamingResponse(
        sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.post("/mcp")
async def handle_mcp_post(
    request: Request,
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version"),
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """MCP POST 엔드포인트 - JSON-RPC 요청 처리"""
    validate_mcp_headers(request)
    
    try:
        body = await request.json()
        
        # JSON-RPC notification 또는 response 처리
        if is_notification_or_response(body):
            # notification/response는 202 Accepted 반환
            return Response(status_code=202)
        
        # 스트리밍 요청 확인
        if is_streaming_request(body):
            return StreamingResponse(
                handle_streaming_request(body),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        # 배치 요청 처리
        if isinstance(body, list):
            result = await process_batch(body)
            return result
        
        # 단일 요청 처리
        result = await process_single(body)
        return result
        
    except json.JSONDecodeError:
        error_response = create_response(
            error={"code": ERROR_CODES["PARSE_ERROR"], "message": "Parse error"},
            request_id=None
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=400
        )
    except Exception as e:
        error_response = create_response(
            error={"code": ERROR_CODES["INTERNAL_ERROR"], "message": str(e)},
            request_id=None
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=500
        )

def is_notification_or_response(body):
    """JSON-RPC notification 또는 response인지 확인"""
    if isinstance(body, dict):
        # notification: method가 있지만 id가 없음
        if "method" in body and "id" not in body:
            return True
        # response: result 또는 error가 있지만 method가 없음
        if ("result" in body or "error" in body) and "method" not in body:
            return True
    return False

def is_streaming_request(body):
    """스트리밍 요청인지 확인"""
    if isinstance(body, dict):
        method = body.get("method")
        params = body.get("params", {})
        return ((method == "stream_data" and params.get("stream") == True) or 
                (method == "get_weather" and params.get("stream") == True) or
                (method == "calculate" and params.get("stream") == True))
    return False

async def process_single(request_data: Dict[str, Any]):
    """단일 JSON-RPC 2.0 요청 처리"""
    # 기본 검증
    if not isinstance(request_data, dict):
        error_response = create_response(
            error={"code": ERROR_CODES["INVALID_REQUEST"], "message": "Invalid Request"},
            request_id=None
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=400
        )
    
    if request_data.get("jsonrpc") != "2.0":
        error_response = create_response(
            error={"code": ERROR_CODES["INVALID_REQUEST"], "message": "jsonrpc must be '2.0'"},
            request_id=request_data.get("id")
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=400
        )
    
    method = request_data.get("method")
    if not method:
        error_response = create_response(
            error={"code": ERROR_CODES["INVALID_REQUEST"], "message": "method is required"},
            request_id=request_data.get("id")
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=400
        )
    
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    # 알림 처리 (id가 없는 경우)
    if request_id is None:
        return Response(status_code=202)
    
    # 도구 실행
    if method in TOOLS:
        try:
            result = await execute_tool(method, params)
            response = create_response(result=result, request_id=request_id)
            return Response(
                content=json.dumps(response),
                media_type="application/json"
            )
        except ValueError as e:
            error_response = create_response(
                error={"code": ERROR_CODES["INVALID_PARAMS"], "message": str(e)},
                request_id=request_id
            )
            return Response(
                content=json.dumps(error_response),
                media_type="application/json",
                status_code=400
            )
        except Exception as e:
            error_response = create_response(
                error={"code": ERROR_CODES["INTERNAL_ERROR"], "message": str(e)},
                request_id=request_id
            )
            return Response(
                content=json.dumps(error_response),
                media_type="application/json",
                status_code=500
            )
    else:
        error_response = create_response(
            error={"code": ERROR_CODES["METHOD_NOT_FOUND"], "message": f"Method '{method}' not found"},
            request_id=request_id
        )
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=404
        )

async def process_batch(requests: List[Dict[str, Any]]):
    """배치 JSON-RPC 2.0 요청 처리"""
    if not requests:
        error_response = [create_response(
            error={"code": ERROR_CODES["INVALID_REQUEST"], "message": "Empty batch"},
            request_id=None
        )]
        return Response(
            content=json.dumps(error_response),
            media_type="application/json",
            status_code=400
        )
    
    results = []
    for request_data in requests:
        result = await process_single(request_data)
        if hasattr(result, 'body'):
            # Response 객체인 경우 JSON 파싱
            result_data = json.loads(result.body.decode())
            results.append(result_data)
        else:
            # 직접 응답인 경우
            results.append(result)
    
    return Response(
        content=json.dumps(results),
        media_type="application/json"
    )

async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """도구 실행"""
    if tool_name == "get_weather":
        location = params.get("location", "서울")
        return {
            "location": location,
            "temperature": "22°C",
            "condition": "맑음",
            "humidity": "65%",
            "timestamp": datetime.now().isoformat()
        }
    
    elif tool_name == "calculate":
        operation = params.get("operation")
        a = params.get("a")
        b = params.get("b")
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    elif tool_name == "stream_data":
        count = params.get("count", 5)
        return {
            "message": f"{count}개의 데이터를 생성했습니다",
            "count": count,
            "timestamp": datetime.now().isoformat()
        }
    
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

async def handle_streaming_request(request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """스트리밍 요청 처리 - SSE 형식"""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id", str(uuid.uuid4()))
        
        if method == "get_weather":
            location = params.get("location", "서울")
            
            # SSE 형식으로 응답
            yield f"data: {json.dumps(create_response(result={'status': 'start', 'tool': method}, request_id=request_id))}\n\n"
            
            weather_data = [
                {"field": "location", "value": location},
                {"field": "temperature", "value": "22°C"},
                {"field": "condition", "value": "맑음"},
                {"field": "humidity", "value": "65%"}
            ]
            
            for data in weather_data:
                yield f"data: {json.dumps(create_response(result={'status': 'data', **data}, request_id=request_id))}\n\n"
                await asyncio.sleep(0.5)
            
            yield f"data: {json.dumps(create_response(result={'status': 'complete', 'tool': method}, request_id=request_id))}\n\n"
        
        elif method == "calculate":
            operation = params.get("operation")
            a = params.get("a")
            b = params.get("b")
            
            yield f"data: {json.dumps(create_response(result={'status': 'start', 'tool': method, 'operation': operation}, request_id=request_id))}\n\n"
            
            if operation == "divide" and b == 0:
                yield f"data: {json.dumps(create_response(error={'code': ERROR_CODES['INVALID_PARAMS'], 'message': 'Division by zero'}, request_id=request_id))}\n\n"
                return
            
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                result = a / b
            
            yield f"data: {json.dumps(create_response(result={'status': 'complete', 'result': result}, request_id=request_id))}\n\n"
        
        elif method == "stream_data":
            count = params.get("count", 5)
            
            yield f"data: {json.dumps(create_response(result={'status': 'start', 'tool': method, 'count': count}, request_id=request_id))}\n\n"
            
            for i in range(count):
                yield f"data: {json.dumps(create_response(result={'status': 'data', 'index': i + 1, 'value': f'데이터 {i + 1}'}, request_id=request_id))}\n\n"
                await asyncio.sleep(0.3)
            
            yield f"data: {json.dumps(create_response(result={'status': 'complete', 'total': count}, request_id=request_id))}\n\n"
    
    except Exception as e:
        yield f"data: {json.dumps(create_response(error={'code': ERROR_CODES['INTERNAL_ERROR'], 'message': str(e)}, request_id=request_id))}\n\n"

if __name__ == "__main__":
    print("🚀 MCP JSON-RPC 2.0 Server (Specification 2025-06-18)")
    print("📡 엔드포인트: http://localhost:8000/mcp")
    print("🔧 도구:", ", ".join(TOOLS.keys()))
    print("⚠️  보안: localhost만 허용")
    
    # 보안: localhost만 바인딩
    uvicorn.run(app, host="127.0.0.1", port=8000)
