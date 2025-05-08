from flask import Flask, request, jsonify
import time
import json
import re
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "Welcome to Code Execution API",
        "usage": "Send POST requests to /compile/ endpoint with code, language, and test_cases",
        "supported_languages": ["python", "javascript", "php"]
    })

def run_jdoodle_api(code, language, test_cases, main_function):
    """
    Execute code using JDoodle API for all supported languages
    """
    # JDoodle API credentials
    jdoodle_client_id = "cd8255dd76edc58df38d4ecf3a250a68"
    jdoodle_client_secret = "ec2d07d421f7e6f13fa08edc9c1b5cd1fcaea13128d9be7557248d117e55269"
    jdoodle_url = "https://api.jdoodle.com/v1/execute"
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        try:
            # Prepare code with test case inputs based on language
            if language == "javascript":
                formatted_code = prepare_js_code(code, main_function, test_case)
                language_id = "nodejs"
                version_index = "4"  # Latest Node.js version
            elif language == "php":
                formatted_code = prepare_php_code(code, main_function, test_case)
                language_id = "php"
                version_index = "4"  # Latest PHP version
            elif language == "python":
                formatted_code = prepare_python_code(code, main_function, test_case)
                language_id = "python3"
                version_index = "4"  # Latest Python version
            else:
                # Unsupported language
                results.append("1")
                continue
            
            # Prepare payload for JDoodle API
            jdoodle_payload = {
                "clientId": jdoodle_client_id,
                "clientSecret": jdoodle_client_secret,
                "script": formatted_code,
                "language": language_id,
                "versionIndex": version_index
            }
            
            logger.info(f"Sending test case {i+1} to JDoodle API")
            
            # Call JDoodle API
            response = requests.post(jdoodle_url, json=jdoodle_payload)
            response_data = response.json()
            
            if response.status_code == 200:
                # Parse output to determine if test passed
                output = response_data.get("output", "").strip()
                logger.info(f"JDoodle response for test {i+1}: {output}")
                
                # Check if output contains "PASSED" or matches expected result
                passed = "PASSED" in output and not "FAILED" in output
                results.append("0" if passed else "1")
                
                logger.info(f"Test case {i+1} result: {'PASSED' if passed else 'FAILED'}")
            else:
                logger.error(f"JDoodle API error: {response_data}")
                results.append("1")  # Mark as failed if API call fails
        except Exception as e:
            logger.error(f"Error in test case {i+1}: {str(e)}")
            results.append("1")  # Mark as failed on exception
    
    return results

def prepare_js_code(code, main_function, test_case):
    """
    Prepare JavaScript code for execution with test case
    """
    inputs = json.dumps(test_case["input"])
    expected = json.dumps(test_case["expected"])
    
    wrapper_code = f"""
{code}

// Test code execution
const inputs = {inputs};
const expected = {expected};
const result = {main_function}(...inputs);

// Compare results
function compareResults(result, expected) {{
    if (Array.isArray(result) && Array.isArray(expected)) {{
        if (result.length !== expected.length) return false;
        
        // Sort arrays for comparison if they are arrays of primitives
        const sortedResult = [...result].sort((a, b) => a - b);
        const sortedExpected = [...expected].sort((a, b) => a - b);
        
        for (let i = 0; i < sortedResult.length; i++) {{
            if (sortedResult[i] !== sortedExpected[i]) return false;
        }}
        return true;
    }}
    return result === expected;
}}

const passed = compareResults(result, expected);
console.log(passed ? "PASSED" : "FAILED");
console.log("Result:", JSON.stringify(result));
console.log("Expected:", JSON.stringify(expected));
"""
    return wrapper_code

def prepare_python_code(code, main_function, test_case):
    """
    Prepare Python code for execution with test case
    """
    inputs = json.dumps(test_case["input"])
    expected = json.dumps(test_case["expected"])
    
    wrapper_code = f"""
{code}

# Test code execution
import json

inputs = json.loads('''{inputs}''')
expected = json.loads('''{expected}''')
result = {main_function}(*inputs)

# Compare results
def compare_results(result, expected):
    if isinstance(result, list) and isinstance(expected, list):
        if len(result) != len(expected):
            return False
        
        # Sort arrays for comparison if they are arrays of primitives
        sorted_result = sorted(result)
        sorted_expected = sorted(expected)
        
        return sorted_result == sorted_expected
    return result == expected

passed = compare_results(result, expected)
print("PASSED" if passed else "FAILED")
print(f"Result: {{json.dumps(result)}}")
print(f"Expected: {{json.dumps(expected)}}")
"""
    return wrapper_code

def prepare_php_code(code, main_function, test_case):
    """
    Prepare PHP code for execution with test case
    """
    # Convert input array to PHP array format
    php_inputs = json_to_php_array(test_case["input"])
    php_expected = json_to_php_array(test_case["expected"])
    
    wrapper_code = f"""<?php
{code}

// Test code execution
$inputs = {php_inputs};
$expected = {php_expected};

// Call function with unpacked arguments
$result = {main_function}(...$inputs);

// Compare results
function compareResults($result, $expected) {{
    if (is_array($result) && is_array($expected)) {{
        if (count($result) !== count($expected)) return false;
        
        // Sort arrays for comparison
        sort($result);
        sort($expected);
        
        return $result == $expected; // PHP uses == for array comparison
    }}
    return $result === $expected;
}}

$passed = compareResults($result, $expected);
echo $passed ? "PASSED" : "FAILED";
echo "\\nResult: " . json_encode($result);
echo "\\nExpected: " . json_encode($expected);
?>"""
    return wrapper_code

def json_to_php_array(json_array):
    """Convert JSON array to PHP array syntax"""
    if not isinstance(json_array, list):
        if isinstance(json_array, (int, float)):
            return str(json_array)
        elif isinstance(json_array, str):
            return f'"{json_array}"'
        elif json_array is None:
            return "null"
        else:
            return str(json_array)
    
    php_items = []
    for item in json_array:
        if isinstance(item, list):
            php_items.append(json_to_php_array(item))
        elif isinstance(item, (int, float)):
            php_items.append(str(item))
        elif isinstance(item, str):
            php_items.append(f'"{item}"')
        elif item is None:
            php_items.append("null")
        else:
            php_items.append(str(item))
    
    return "[" + ", ".join(php_items) + "]"

@app.route('/compile/', methods=['POST'])
def compile_and_run():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required_fields = ['code', 'language', 'test_cases']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        code = data.get('code', '')
        language = data.get('language', '').lower()
        test_cases = data.get('test_cases', [])
        main_function = data.get('main_function', 'main')
        
        if language not in ['javascript', 'python', 'php']:
            return jsonify({"error": f"Unsupported language: {language}"}), 400
        
        if not isinstance(test_cases, list) or not test_cases:
            return jsonify({"error": "test_cases must be a non-empty array"}), 400
            
        for i, test_case in enumerate(test_cases):
            if not isinstance(test_case, dict):
                return jsonify({"error": f"Test case {i} must be an object"}), 400
            if "input" not in test_case:
                return jsonify({"error": f"Test case {i} missing 'input' field"}), 400
            if "expected" not in test_case:
                return jsonify({"error": f"Test case {i} missing 'expected' field"}), 400
            if not isinstance(test_case["input"], list):
                return jsonify({"error": f"Test case {i} 'input' must be an array"}), 400
        
        # Function validation (check if the function exists in the code)
        if language == 'python':
            if not re.search(rf"def\s+{re.escape(main_function)}\s*\(", code):
                return jsonify({"error": f"Function '{main_function}' not found in the code"}), 400
        elif language == 'javascript':
            if not re.search(rf"function\s+{re.escape(main_function)}\s*\(", code):
                return jsonify({"error": f"Function '{main_function}' not found in the code"}), 400
        elif language == 'php':
            if not re.search(rf"function\s+{re.escape(main_function)}\s*\(", code):
                return jsonify({"error": f"Function '{main_function}' not found in the code"}), 400
        
        # Use JDoodle API for all languages
        results = run_jdoodle_api(code, language, test_cases, main_function)
        
        response = {
            "response": {
                "array": [
                    {f"[{i}]": results[i]} for i in range(len(results))
                ]
            }
        }
        
        return jsonify(response)
    
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON object: Expecting value"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)