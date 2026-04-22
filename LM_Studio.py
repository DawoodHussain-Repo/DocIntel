from langchain_openai import ChatOpenAI

def get_local_llm(temperature: float = 0.7):
    """
    Initializes a connection to the local LM Studio server.
    Ensure LM Studio has a model loaded and the local server is running (usually port 1234).
    """
    llm = ChatOpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",  # The SDK requires an API key, but LM Studio accepts any string
        temperature=temperature,
        model="local-model",  # LM Studio will automatically use whichever model you have loaded
        max_tokens=1000
    )
    return llm

# --- Quick System Check ---
if __name__ == "__main__":
    print("Initiating local server ping...")
    try:
        test_llm = get_local_llm()
        response = test_llm.invoke("System check. Respond with 'Server Online'.")
        print(f"Status: {response.content}")
    except Exception as e:
        print(f"Connection failed. Is the LM Studio server running? Error: {e}")