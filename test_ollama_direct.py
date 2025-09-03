from ollama import Client

client = Client(host='http://127.0.0.1:11434')
res = client.chat(
    model='llama3:latest',
    messages=[{'role': 'user', 'content': "Say 'direct client works' in four words or fewer."}]
)
print(res['message']['content'])


