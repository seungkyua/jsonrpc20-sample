from flask import Flask, Response, render_template, request, jsonify
import time
import json
import uuid
from functools import wraps

app = Flask(__name__)

# 클라이언트 연결을 저장하는 딕셔너리
clients = {}

def validate_origin(f):
    """Origin 헤더를 검증하는 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        origin = request.headers.get('Origin')
        if origin and not origin.startswith(('http://localhost:', 'http://127.0.0.1:')):
            return jsonify({'error': 'Invalid origin'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/web')
def index():
    return render_template('sse_client.html')

@app.route('/sse')
@validate_origin
def sse_endpoint():
    """MCP SSE 엔드포인트 - 클라이언트 연결을 위한 SSE 스트림"""
    def event_stream():
        client_id = str(uuid.uuid4())
        clients[client_id] = {
            'id': client_id,
            'message_endpoint': f'/message/{client_id}'
        }
        
        try:
            # MCP 스펙에 따라 endpoint 이벤트를 먼저 전송
            yield f'event: endpoint\ndata: {json.dumps({"uri": clients[client_id]["message_endpoint"]})}\n\n'
            
            # MCP 스펙에 따라 연결 유지 (클라이언트 메시지 대기)
            while client_id in clients:
                try:
                    time.sleep(0.1)  # CPU 사용량 줄이기
                except (GeneratorExit, BrokenPipeError, ConnectionResetError):
                    break
                except Exception as e:
                    print(f"SSE 스트림 에러: {e}")
                    break
                
        except (GeneratorExit, BrokenPipeError, ConnectionResetError):
            # 클라이언트 연결이 끊어짐
            pass
        except Exception as e:
            # 기타 예외 처리
            print(f"SSE 스트림 초기화 에러: {e}")
        finally:
            # 클라이언트 정리
            if client_id in clients:
                del clients[client_id]
                print(f"클라이언트 {client_id} 연결 해제")
    
    response = Response(event_stream(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/message/<client_id>', methods=['POST'])
@validate_origin
def message_endpoint(client_id):
    """클라이언트로부터 MCP 메시지를 받는 엔드포인트"""
    if client_id not in clients:
        return jsonify({'error': 'Invalid client ID'}), 400
    
    try:
        message = request.get_json()
        if not message:
            return jsonify({'error': 'Invalid JSON'}), 400
        
        method = message.get("method")
        
        if method == "request_messages":
            # 클라이언트가 메시지 요청을 보냄 - SSE 스트림으로 응답
            def stream_response():
                for i in range(5):
                    server_message = {
                        "jsonrpc": "2.0",
                        "id": i + 1,
                        "method": "server_message",
                        "params": {
                            "message": f"서버에서 보내는 메시지 {i + 1}/5",
                            "timestamp": time.time()
                        }
                    }
                    yield f'event: message\ndata: {json.dumps(server_message)}\n\n'
                    
                    if i < 4:
                        time.sleep(1)
            
            response = Response(stream_response(), mimetype='text/event-stream')
            response.headers['Cache-Control'] = 'no-cache'
            response.headers['Connection'] = 'keep-alive'
            return response
            
        else:
            # 기타 메서드는 일반 HTTP 응답
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "echo": message,
                    "timestamp": time.time()
                }
            }
            return jsonify(response)
        
    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": request.get_json().get("id") if request.get_json() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }
        return jsonify(error_response), 500

if __name__ == '__main__':
    # 보안을 위해 localhost에만 바인딩
    app.run(host='127.0.0.1', port=5000, debug=True)