#!/usr/bin/env python3
"""
MCP JSON-RPC 2.0 Web Client

MCP Specification 2025-06-18에 맞는 Streamable HTTP 웹 클라이언트
"""

from flask import Flask, render_template, request, jsonify, Response
import requests
import json

app = Flask(__name__)

MCP_SERVER_URL = "http://localhost:8000"
MCP_PROTOCOL_VERSION = "2025-06-18"

def get_mcp_headers():
    """MCP Specification에 맞는 헤더 생성"""
    return {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
    }

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('mcp_jsonrpc_client.html')

@app.route('/api/mcp', methods=['POST'])
def handle_mcp():
    """MCP JSON-RPC 2.0 요청 처리"""
    try:
        data = request.get_json()
        headers = get_mcp_headers()
        
        response = requests.post(f"{MCP_SERVER_URL}/mcp", json=data, headers=headers)
        
        # 202 Accepted 처리
        if response.status_code == 202:
            return jsonify({"status": "accepted", "message": "Request accepted"})
        
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mcp/stream', methods=['POST'])
def handle_mcp_stream():
    """MCP JSON-RPC 2.0 스트리밍 요청 처리"""
    try:
        request_data = request.get_json()
        headers = get_mcp_headers()
        
        def generate():
            try:
                response = requests.post(
                    f"{MCP_SERVER_URL}/mcp",
                    json=request_data,
                    headers=headers,
                    stream=True
                )
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            # SSE 형식 파싱
                            data_str = line[6:]  # "data: " 제거
                            try:
                                parsed_data = json.loads(data_str)
                                yield f"data: {json.dumps(parsed_data, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/mcp/listen', methods=['GET'])
def handle_mcp_listen():
    """MCP 서버 이벤트 수신 (GET /mcp)"""
    try:
        headers = {
            "Accept": "text/event-stream",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
        }
        
        def generate():
            try:
                response = requests.get(
                    f"{MCP_SERVER_URL}/mcp",
                    headers=headers,
                    stream=True
                )
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                parsed_data = json.loads(data_str)
                                yield f"data: {json.dumps(parsed_data, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🌐 MCP JSON-RPC 2.0 Web Client (Specification 2025-06-18)")
    print("📱 웹 브라우저에서 http://localhost:5000 접속")
    print("💡 MCP 서버가 실행 중인지 확인하세요: python mcp_jsonrpc_server.py")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
