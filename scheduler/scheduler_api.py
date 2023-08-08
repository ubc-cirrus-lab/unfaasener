from flask import Flask, request
import subprocess

app = Flask(__name__)

# Define the leader host and port
host = 'localhost'
port = 1111

@app.route('/run_scheduler', methods=['POST'])
def run_scheduler():
    mode = request.json.get('mode')
    command = ["python3", "rpsCIScheduler.py", mode]
    subprocess.Popen(command)
    return 'Scheduler started', 200

if __name__ == '__main__':
    app.run(host=host, port=port)
