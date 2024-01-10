import tiktoken
import numpy as np
import json
from openai import OpenAI
from collections import defaultdict

data_path = "document/data/howto_conversations.jsonl"
json_dataset = []
# Token conuting functions
encoding = tiktoken.get_encoding("cl100k_base")

MAX_TOKEN_PER_EXAMPLE = 4096
TARGET_EPOCHS = 3
MIN_TARGET_EXAMPLES = 100
MAX_TARGET_EXAMPLES = 25000
MIN_DEFAULT_EPOCHS = 1
MAX_DEFAULT_EPOCHS = 25


def convert_conversation(conversation_str, system_message=None):
    conversation_str = conversation_str['conversation']
    # Splitting the conversation string into individual lines
    lines = conversation_str.split('\n\n')

    # Initializing the messages list
    messages = []

    # Including the system message if provided
    if system_message:
        messages.append({
            "role": "system",
            "content": system_message
        })

    # Iterating through the lines and formatting the messages
    for line in lines:
        # splitting each line by the colon character to separate the speaker and content
        parts = line.split(": ", 1)
        if len(parts) < 2:
            continue

        # Identifying the role based on the speaker's name
        role = "user" if parts[0].strip() == "Theodore" else "assistant"

        # Formatting the message
        message = {
            "role": role,
            "content": parts[1].strip()
        }
        messages.append(message)

    # Creating the final output dictionary
    output_dict = {
        "messages": messages
    }

    return output_dict


def checkformat(dataset):
    format_errors = defaultdict(int)
    for ex in dataset:
        if not isinstance(ex, dict):
            format_errors["data_type"] += 1
            continue

        messages = ex.get("messages", None)
        if not messages:
            format_errors["missing_messages_list"] += 1
            continue

        for message in messages:
            if "role" not in message or "content" not in message:
                format_errors["message_missing_key"] += 1
            if any(k not in ("role", "content", "name") for k in message):
                format_errors["message_unrecognized_key"] += 1
            if message.get("role", None) not in ("system", "user", "assistant"):
                format_errors["unrecognized_role"] += 1
            
            content = message.get("content", None)
            if not content or not isinstance(content, str):
                format_errors["missing_content"] += 1
        
        if not any(message.get("role", None) == "assistant" for message in messages):
            format_errors["example_missing_assistant_message"] += 1
    
    if format_errors:
        print("Found errors:")
        for k, v in format_errors.items():
            print(f"{k}: {v}")
    else:
        print("No errors found")


def num_tokens_from_messages(messages, tokens_per_message=3, tokens_per_name=1):
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def num_assistant_tokens_from_messages(messages):
    num_tokens = 0
    for message in messages:
        if message["role"] == "assistant":
            num_tokens += len(encoding.encode(message["content"]))
    return num_tokens


def print_distribution(values, name):
    print(f"\n#### Distribution of {name}:")
    print(f"min / max: {min(values)}, {max(values)}")
    print(f"mean / median: {np.mean(values)}, {np.median(values)}")
    print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")


def count_token(dataset):
    n_missing_system = 0
    n_missing_user = 0
    n_messages = []
    convo_lens = []
    assistant_message_lens = []

    for ex in dataset:
        messages = ex["messages"]
        if not any(message["role"] == "system" for message in messages):
            n_missing_system += 1
        if not any(message["role"] == "user" for message in messages):
            n_missing_user += 1
        n_messages.append(len(messages))
        convo_lens.append(num_tokens_from_messages(messages))
        assistant_message_lens.append(num_assistant_tokens_from_messages(messages))

    print("Num examples missing system message", n_missing_system)
    print("Num examples missing user message", n_missing_user)
    print_distribution(n_messages, "num_messages_per_example")
    print_distribution(convo_lens, "num_total_tokens_per_example")
    print_distribution(assistant_message_lens, "num_assistant_tokens_per_example")
    n_too_long = sum(l > 4096 for l in convo_lens)
    print(f"\n{n_too_long} examples may be over the 4096 token limit.")
    calculate_price(dataset, convo_lens)


def calculate_price(dataset, convo_lens):
    n_epochs = TARGET_EPOCHS
    n_train_examples = len(dataset)
    if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
        n_epochs = min(MAX_DEFAULT_EPOCHS, MIN_TARGET_EXAMPLES // n_train_examples)
    elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
        n_epochs = max(MIN_DEFAULT_EPOCHS, MAX_TARGET_EXAMPLES // n_train_examples)

    # Model	Input	Output
    # gpt-3.5-turbo-1106	    $0.0010 / 1K tokens	    $0.0020 / 1K tokens
    # gpt-3.5-turbo-instruct	$0.0015 / 1K tokens	    $0.0020 / 1K tokens
    n_billing_tokens_in_dataset = sum(min(MAX_TOKEN_PER_EXAMPLE, length) for length in convo_lens)
    print(f"Dataset has ~{n_billing_tokens_in_dataset} tokens that will be charged for during training")
    print(f"By default, you'll train for {n_epochs} on this dataset")
    print(f"By default, you'll be charged for ~{n_epochs * n_billing_tokens_in_dataset} tokens")
    print(f"Total costs will be ${0.002 * (n_epochs * n_billing_tokens_in_dataset / 1000)}")


def save_to_jsonl(conversations, file_path):
    with open(file_path, 'w') as file:
        for conversation in conversations:
            json_line = json.dumps(conversation)
            file.write(json_line + '\n')


if __name__ == '__main__':
    with open(data_path, 'r', encoding="utf-8") as f:
        for jsonstr in f.readlines():
            json_dataset.append(json.loads(jsonstr))

    dataset = []
    system_message = """You are Jamson a helpful and charming assistant who can help with a variety of tasks. You are friendly and often lirt"""

    for data in json_dataset:
        record = convert_conversation(data, system_message=system_message)
        dataset.append(record)

    checkformat(dataset)

    count_token(dataset)

    # Initial dataset stats
    print("Num examples:", len(dataset))

    save_to_jsonl(dataset, '/Users/romani/Codes/smartGPT/samantha_tasks_train.jsonl')
    save_to_jsonl(dataset[10:15], "/Users/romani/Codes/smartGPT/samantha_tasks_validation.jsonl")

    client = OpenAI()

    training_response = client.File.create(file=open('/Users/romani/Codes/smartGPT/samantha_tasks_train.jsonl', 'rb'), purpose="fine-tune")
    training_file_id = training_response["id"]

    validation_response = client.File.create(file=open('/Users/romani/Codes/smartGPT/samantha_tasks_validation.jsonl', 'rb'), purpose="fine-tune")
    validation_file_id = validation_response["id"]

    print("Training file id:", training_file_id)
    print("Validation file id:", validation_file_id)
    