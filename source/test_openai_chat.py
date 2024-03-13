from openai import OpenAI

client = OpenAI()


if __name__ == '__main__':
    # gpt-3.5-turbo
    # ft:gpt-3.5-turbo-1106:personal:zhangjiangmeishi:92CF8aeE
    completion = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
        {"role": "user", "content": "在上海有哪些好吃的东北菜推荐？"}
    ])

    print(completion.choices[0].message)

