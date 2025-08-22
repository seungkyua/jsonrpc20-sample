from flask import Flask, Response, render_template
import time
import json

app = Flask(__name__)


@app.route('/web')
def index():
    # templates 폴더에 있는 index.html 파일을 렌더링하여 반환
    return render_template('sse_client.html')


@app.route('/stream')
def stream():
    def event_stream():
        while True:
            # SSE 형식에 맞춰 데이터를 생성합니다.
            # 'data: ' 접두사가 필수입니다.
            # 여러 줄의 데이터는 \n\n으로 구분합니다.
            data = {'time': time.strftime('%H:%M:%S')}
            yield f'data: {json.dumps(data)}\n\n'
            time.sleep(3)  # 3초마다 데이터를 보냅니다.

    # Response 객체를 생성하고 MIME 타입을 'text/event-stream'으로 설정합니다.
    return Response(event_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(port=5000, debug=True)