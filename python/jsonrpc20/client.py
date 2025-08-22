import json
import requests


def send_rpc_request(url, method, params, request_id):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": {"code": -1, "message": str(e)}}


if __name__ == "__main__":
    server_url = "http://localhost:8000"

    # 성공적인 요청 예제
    result = send_rpc_request(server_url, "add", [5, 3], 1)
    if "result" in result:
        print(f"결과: 5 + 3 = {result['result']}")
    else:
        print(f"에러 발생: {result['error']['message']}")

    # 존재하지 않는 메서드 요청 예제
    result_invalid = send_rpc_request(server_url, "subtract", [10, 2], 2)
    if "error" in result_invalid:
        print(f"에러 발생: {result_invalid['error']['message']}")