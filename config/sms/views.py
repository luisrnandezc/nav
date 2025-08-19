from django.shortcuts import render
import os
from openai import OpenAI

def test_openai_key(custom_prompt=None):
    """
    A function to test the OpenAI API key and optionally analyze custom content.
    
    Args:
        custom_prompt (str, optional): Custom prompt for incident analysis
    """
    # Retrieve the API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not found in environment variables."

    try:
        # Initialize the OpenAI client with the retrieved key
        client = OpenAI(api_key=api_key)

        # Use custom prompt if provided, otherwise use default
        if custom_prompt:
            messages = [
                {"role": "system", "content": "Eres un experto en SMS (Safety Management System). IMPORTANTE: SIEMPRE responde ÚNICAMENTE con JSON válido. NUNCA incluyas texto explicativo antes o después del JSON."},
                {"role": "user", "content": custom_prompt}
            ]
        else:
            messages = [
                {"role": "system", "content": "Eres un comediante."},
                {"role": "user", "content": "Cuéntame un chiste corto"}
            ]

        # Make a request to the chat completions endpoint
        response = client.chat.completions.create(
            model="gpt-5",
            messages=messages,
            max_completion_tokens=5000  # Increased for comprehensive SMS analysis
        )

        # Extract the content from the response
        content = response.choices[0].message.content
        return content
        
    except Exception as e:
        return "API key validation failed. Error: {}".format(e)

# To run the test, you can call the function:
# print(test_openai_key())
