from dotenv import load_dotenv
from src.llm_client import get_lm

load_dotenv()
lm = get_lm(model_name="gpt-4.1-mini", temperature=0.0, max_tokens=10)
print(lm("say 'Hello!' as is")[0])