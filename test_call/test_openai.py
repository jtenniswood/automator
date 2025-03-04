import openai
import sys

# Replace with your actual API key
api_key = "YOUR_OPENAI_API_KEY"

if api_key == "YOUR_OPENAI_API_KEY":
    print("Please edit this file to add your actual OpenAI API key")
    print("Usage: python3 test_openai.py YOUR_API_KEY")
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"Using API key from command line arguments: {api_key[:5]}...{api_key[-4:] if len(api_key) > 10 else '...'}")
    else:
        sys.exit(1)

openai.api_key = api_key

print(f"Testing OpenAI API with key: {api_key[:5]}...{api_key[-4:] if len(api_key) > 10 else '...'}")
print("Using model: gpt-3.5-turbo")

try:
    # Simple synchronous call
    print("Making API call...")
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
    print("\nYour API key is VALID. If you're still having issues with the integration,")
    print("check the Home Assistant logs for more details.")
    
except Exception as e:
    print(f"Error calling OpenAI API: {e}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. API key doesn't have permission to access the model")
    print("3. Network connectivity issues")
    print("4. OpenAI service is down")
    print("\nCheck the error message above for more details.") 