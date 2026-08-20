import langchain_openai
print("langchain_openai version:", langchain_openai.__version__)
import openai
print("openai version:", openai.__version__)

# Check ChatOpenAI signature
import inspect
sig = inspect.signature(langchain_openai.ChatOpenAI.__init__)
print("ChatOpenAI params:", list(sig.parameters.keys()))