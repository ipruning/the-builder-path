from flow import create_qa_flow


def main():
    shared = {
        "question": "In one sentence, what's the end of universe?",
        "answer": None,
    }

    create_qa_flow.run(shared)
    print("Question:", shared["question"])
    print("Answer:", shared["answer"])


if __name__ == "__main__":
    main()
