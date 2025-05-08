import requests
import json

url = "http://127.0.0.1:5000/compile/"

# JavaScript version of the Two Sum problem
payload = {
    "code": """
function main(nums, target) {
    const numMap = {};
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (complement in numMap) {
            return [numMap[complement], i];
        }
        numMap[nums[i]] = i;
    }
    return [];
}
    """,
    "language": "javascript",
    "main_function": "main",
    "test_cases": [
        {
            "input": [[2, 7, 11, 15], 9],
            "expected": [0, 1],
            "desc": "first test case - should pass"
        },
        {
            "input": [[3, 2, 4], 6],
            "expected": [1, 2],
            "desc": "second test case - should pass"
        },
        {
            "input": [[1, 5, 8, 3, 9, 2], 11],
            "expected": [2, 3],
            "desc": "third test case - should pass"
        },
        {
            "input": [[3, 3], 6],
            "expected": [0, 1],
            "desc": "fourth test case - should pass"
        },
        {
            "input": [[-1, -2, -3, -4], -7],
            "expected": [2, 3],
            "desc": "fifth test case - should pass"
        }
    ]
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, json=payload)
    print("Status code:", response.status_code)
    print("Response body:", json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error occurred: {e}")
    print("Make sure the API server is running at http://127.0.0.1:5000")