import requests
import json

# 测试生成题目API
print("测试生成题目API...")
try:
    url = "http://localhost:9000/api/generate-questions"
    headers = {"Content-Type": "application/json"}
    data = {"count": 3}
    response = requests.post(url, headers=headers, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"测试生成题目API失败: {e}")