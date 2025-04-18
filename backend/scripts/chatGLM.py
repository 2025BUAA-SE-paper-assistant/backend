import openai

server_ip = "10.2.16.28"
url = f"http://{server_ip}:2338"

if __name__ == "__main__":
    openai.api_base = f"http://{server_ip}:2338/v1"
    openai.api_key = "none"
    history = []
    while True:
        user_input = input("用户：")
        history.append({"role": "user", "content": user_input})
        if user_input.lower() == "exit":
            break
        response = openai.ChatCompletion.create(
            model="chatglm2-6b", messages=history, stream=False
        )
        if response.choices[0].message.role == "assistant":
            print("ChatGLM2-6B：", response.choices[0].message.content)
            history.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
