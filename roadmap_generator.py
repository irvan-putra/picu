import os
import re
import json
import dashscope
from dashscope import Generation
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

API_KEY = os.getenv('DASHSCOPE_API_KEY') # https://www.alibabacloud.com/help/en/model-studio/developer-reference/get-api-key

def get_user_input():
    trigger = input("What triggered your learning journey? ")
    return trigger.strip()

def sanitize_filename(title):
    return re.sub(r'[^\w\-_\. ]', '_', title).lower().replace(' ', '-')

def generate_roadmap(trigger):
    prompt = f"""
    Create a learning roadmap based on the trigger: "{trigger}".
    Structure the response as JSON (not in a Markdown block) with a 'roadmap' array.
    Each node should contain:
    - title: string
    - content: markdown-formatted string
    - next: array of node titles (must exist in the roadmap)
    Ensure all referenced nodes in 'next' are present in the roadmap.
    """

    # https://www.alibabacloud.com/help/en/model-studio/user-guide/text-generation/
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': prompt}
    ]

    response = Generation.call(
        api_key=API_KEY,
        model="qwen-plus",
        messages=messages,
        result_format="json"
    )
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code}\n{response.text}")
    return response.output.text

def create_markdown_files(roadmap_data):
    if not os.path.exists('example'):
        os.makedirs('example')

    # Create filename mapping
    filename_map = {}
    for node in roadmap_data:
        filename = f"{sanitize_filename(node['title'])}.md"
        filename_map[node['title']] = filename

    # Generate files
    for node in roadmap_data:
        filename = filename_map[node['title']]
        content = f"# {node['title']}\n\n{node['content']}\n\n"
        
        if node.get('next'):
            content += "## Next Steps\n"
            for next_title in node['next']:
                if next_title in filename_map:
                    content += f"- [{next_title}]({filename_map[next_title]})\n"
        
        with open(f"example/{filename}", 'w') as f:
            f.write(content)

def main():
    if not API_KEY:
        raise ValueError("Please set DASHSCOPE_API_KEY environment variable")

    trigger = get_user_input()
    print("Generating roadmap...")
    
    try:
        roadmap_text = generate_roadmap(trigger)
        print(roadmap_text)
        roadmap_json = json.loads(roadmap_text)
        roadmap_data = roadmap_json['roadmap']
        create_markdown_files(roadmap_data)
        print(f"Roadmap created successfully in 'example' folder with {len(roadmap_data)} nodes")
    except Exception as e:
        print("Error: ", e)

if __name__ == "__main__":
    main()