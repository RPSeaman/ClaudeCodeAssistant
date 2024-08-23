from flask import Flask, render_template, request, jsonify, session
import boto3
import json
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# Configure Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'  # replace with your preferred region
)

def extract_code_block(text):
    # Extract the first code block from the text
    match = re.search(r'```[\w]*\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

@app.route('/')
def index():
    session['conversation'] = []
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json['prompt']
    mod_type = request.json['mod_type']
    language = request.json['language']
    
    language_specific_instructions = {
        'r': "Remember to use R-specific conventions and libraries.",
        'nextflow': "Ensure you follow Nextflow DSL2 syntax and best practices for pipeline development."
    }
    
    lang_instruction = language_specific_instructions.get(language, "")
    
    if mod_type == 'lint-improve':
        instructions = (f"You are a code refactoring assistant for {language}. Your task is to lint and improve the given code. "
                        "Provide the refactored code as a single code block, followed by explanations of your changes. "
                        f"Always include the entire refactored script in one code block. {lang_instruction}")
    elif mod_type == 'abstract':
        instructions = (
            f"You are a code refactoring assistant for {language}. Your task is to lint, improve, and abstract the given code "
            "into two parts: an agnostic main file and a config file. Follow these guidelines:\n"
            "1. The main file should contain the core logic and functions, designed to be as agnostic as possible.\n"
            "2. The config file should ONLY contain variable declarations for values that are specific to this particular run or instance. "
            "Do not include any functions or complex logic in the config file.\n"
            "3. In the main file, import the config and use the variables from it.\n"
            "4. Provide each file (main and config) as a separate code block.\n"
            "5. After the code blocks, provide explanations of your changes and the abstraction process.\n"
            "6. Ensure that between the main file and the config file, all functionality of the original script is preserved.\n"
            f"{lang_instruction}"
        )
    else:  # pseudo-to-code
        instructions = (f"You are a code generation assistant for {language}. Your task is to convert the given pseudocode into real, executable {language} code. "
                        "Provide the generated code as a single code block, followed by explanations of your implementation choices. "
                        f"Always include the entire generated script in one code block. {lang_instruction}")

    full_prompt = f"{instructions}\n\nPlease process this {'code' if mod_type != 'pseudo-to-code' else 'pseudocode'}:\n\n```{language}\n{prompt}\n```"
    
    messages = [
        {"role": "user", "content": full_prompt}
    ]
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',  # Claude 3.5 Sonnet
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 1,
            })
        )
        
        response_body = json.loads(response['body'].read())
        assistant_response = response_body['content'][0]['text']
        
        if mod_type == 'lint-improve' or mod_type == 'pseudo-to-code':
            result_code = extract_code_block(assistant_response)
            explanation = re.sub(r'```[\w]*\n.*?```', '', assistant_response, flags=re.DOTALL).strip()
            result = {
                'result_code': result_code,
                'explanation': explanation
            }
        else:  # abstract
            result = {
                'full_response': assistant_response
            }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)