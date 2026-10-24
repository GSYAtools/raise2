import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def main():
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"

    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")

    if not api_key:
        print("ERROR: OPENAI_API_KEY is not configured.")
        sys.exit(1)

    if not model:
        print("ERROR: OPENAI_MODEL is not configured.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print(f"Requested model: {model}")

    response = client.responses.create(
        model=model,
        instructions=(
            "Follow the user instruction exactly. "
            "Do not add any additional text."
        ),
        input="Return exactly the text: RAISE2_OK",
    )

    print(f"Response ID: {response.id}")
    print(f"Returned model: {response.model}")
    print(f"Output: {response.output_text}")

    if response.output_text.strip() != "RAISE2_OK":
        print("SMOKE TEST: FAIL")
        sys.exit(1)

    print("SMOKE TEST: PASS")


if __name__ == "__main__":
    main()
