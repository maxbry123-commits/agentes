from openai import OpenAI
import base64
import os
import yaml


def call_llm(prompt, image=None):
    """Call the LLM. Pass `image` (PNG bytes) to use a vision model on a screenshot."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
    if image is None:
        content = prompt
    else:
        b64 = base64.b64encode(image).decode()
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]
    r = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        temperature=0,
    )
    return r.choices[0].message.content


def parse_yaml(reply):
    """Pull the ```yaml block out of an LLM reply and parse it into a dict."""
    if "```" in reply:
        reply = reply.split("```")[1]
        if reply.startswith("yaml"):
            reply = reply[len("yaml"):]
    return yaml.safe_load(reply)


if __name__ == "__main__":
    print("## Testing call_llm")
    prompt = "In a few words, what is the meaning of life?"
    print(f"## Prompt: {prompt}")
    response = call_llm(prompt)
    print(f"## Response: {response}")
