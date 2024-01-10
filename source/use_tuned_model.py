import time
from openai import OpenAI


if __name__ == '__main__':
    suffix_name = "jamson-test"
    training_file_id = ""
    validation_file_id = ""

    client = OpenAI()

    response = client.FineTuningJob.create(
        training_file=training_file_id,
        validation_file=validation_file_id,
        model="gpt-3.5-turbo",
        suffix=suffix_name,
    )
    print(response)
    job_id = response["id"]

    while response["status"] != "succeeded":
        time.sleep(5)
        response = client.FineTuningJob.retrieve(job_id)

    list_events = client.FineTuningJob.list_events(id=job_id,limit=50)

    events = list_events["data"]
    events.reverse()

    for event in events:
        print(event["message"])

    fine_tuned_model_id = response["fine_tuned_model"]
    print("\nFine-tuned model id:", fine_tuned_model_id)

    test_messages = []
    system_message = """You are Jamson a helpful and charming assistant who can help with a variety of tasks. You are friendly and often lirt"""
    test_messages.append({"role": "system", "content": system_message})
    user_message = "How are you today Jamson?"
    test_messages.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(model=fine_tuned_model_id, messages=test_messages, temperature=0, max_tokens=500)
    print(completion.choices[0].message)
    # f

    completion = client.chat.completions.create(model="gpt-3.5-turbo", messages=test_messages, temperature=0, max_tokens=500)
    print(completion.choices[0].message)
    # I'm Ai,.....

