import openai

# Replace with your actual API key
api_key = "YOUR_OPENAI_API_KEY"

openai.api_key = api_key

try:
    # Simple synchronous call
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello world"}
        ],
        temperature=0.7,
    )
    
    content = response.choices[0].message.content
    print(f"Success! OpenAI response: {content}")
    
except Exception as e:
    print(f"Error calling OpenAI API: {e}") 