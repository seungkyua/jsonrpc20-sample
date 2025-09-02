# MCP JSON-RPC 2.0 Server

[MCP Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports#backwards-compatibility)에 완전히 준수하는 Streamable HTTP 서버입니다.

## 🚀 특징

- **MCP Specification 완전 준수**: 2025-06-18 버전 완벽 구현
- **Streamable HTTP**: 표준 MCP 전송 프로토콜 사용
- **보안 강화**: Origin 헤더 검증, localhost 바인딩
- **통합 엔드포인트**: `/mcp` 하나로 모든 요청 처리
- **SSE 스트리밍**: Server-Sent Events 표준 준수

## 📡 엔드포인트

- `GET /` - 서버 정보 및 프로토콜 버전
- `GET /mcp` - SSE 스트림 시작 (서버→클라이언트)
- `POST /mcp` - JSON-RPC 2.0 요청 처리 (단일/배치/스트리밍)

## 🔧 도구

1. **`get_weather`** - 도시별 날씨 정보
2. **`calculate`** - 수학 계산 (덧셈, 뺄셈, 곱셈, 나눗셈)
3. **`stream_data`** - 데이터 스트리밍

## 🔒 보안

- **Origin 헤더 검증**: DNS 리바인딩 공격 방지
- **localhost 바인딩**: `127.0.0.1`만 허용
- **프로토콜 버전 검증**: 지원되지 않는 버전 거부

## 💻 사용 예제

### 필수 헤더
```bash
Accept: application/json, text/event-stream
Content-Type: application/json
MCP-Protocol-Version: 2025-06-18
```

### 단일 요청
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_weather",
    "params": {"location": "서울"},
    "id": "uuid-123"
  }'
```

### 배치 요청
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '[
    {
      "jsonrpc": "2.0",
      "method": "get_weather",
      "params": {"location": "부산"},
      "id": "uuid-456"
    },
    {
      "jsonrpc": "2.0",
      "method": "calculate",
      "params": {"operation": "add", "a": 10, "b": 20},
      "id": "uuid-789"
    }
  ]'
```

### 스트리밍 요청
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{
    "jsonrpc": "2.0",
    "method": "stream_data",
    "params": {"count": 3},
    "id": "uuid-stream"
  }'
```

### 서버 이벤트 수신 (GET)
```bash
curl -X GET http://localhost:8000/mcp \
  -H "Accept: text/event-stream" \
  -H "MCP-Protocol-Version: 2025-06-18"
```

### 알림 (Notification)
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -H "MCP-Protocol-Version: 2025-06-18" \
  -d '{
    "jsonrpc": "2.0",
    "method": "server_notification",
    "params": {"message": "Hello from client"}
  }'
```

## 🚀 실행

```bash
cd streamablemcp
pip install -r requirements.txt

# 서버 실행
python mcp_jsonrpc_server.py

# 클라이언트 테스트
python mcp_jsonrpc_client.py

# 웹 클라이언트
python mcp_jsonrpc_web_client.py

# 테스트
python test_mcp_jsonrpc.py
```

## 🌐 접속

- **서버**: http://localhost:8000
- **웹 클라이언트**: http://localhost:5000
- **API 문서**: http://localhost:8000/docs

## 📚 HTTP 상태 코드

### 성공 응답
- `200 OK` - 정상 요청 처리
- `202 Accepted` - 알림/응답 처리됨

### 오류 응답
- `400 Bad Request` - 잘못된 요청
- `403 Forbidden` - Origin 검증 실패
- `404 Not Found` - 메서드 없음
- `405 Method Not Allowed` - 지원하지 않는 메서드
- `500 Internal Server Error` - 서버 오류

## 🔄 SSE 스트리밍

스트리밍 응답은 SSE 형식으로 전송됩니다:

```
data: {"jsonrpc": "2.0", "result": {"status": "start"}, "id": "request-id"}

data: {"jsonrpc": "2.0", "result": {"status": "data", "value": "..."}, "id": "request-id"}

data: {"jsonrpc": "2.0", "result": {"status": "complete"}, "id": "request-id"}
```

## ⚠️ 오류 코드

- `-32700`: Parse error
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## 📋 MCP Specification 준수사항

✅ **프로토콜 헤더**: `MCP-Protocol-Version` 지원  
✅ **Accept 헤더**: `application/json, text/event-stream` 검증  
✅ **HTTP 상태 코드**: 202 Accepted, 400, 404, 405 등  
✅ **SSE 형식**: `text/event-stream` 미디어 타입  
✅ **GET/POST 지원**: `/mcp` 엔드포인트  
✅ **보안**: Origin 헤더 검증, localhost 바인딩  
✅ **알림 처리**: JSON-RPC notification 지원  
✅ **배치 요청**: JSON-RPC 2.0 배치 처리  
✅ **스트리밍**: SSE 기반 실시간 스트리밍
