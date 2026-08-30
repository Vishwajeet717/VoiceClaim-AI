
from rag.answer import answer_policy_question


def main():
    question = (
        "Does my policy cover damage caused by a meteor?"
    )

    result = answer_policy_question(
        question=question,
        policy_id=1,
    )

    print()
    print("QUESTION")
    print("=" * 70)
    print(question)

    print()
    print("ANSWER")
    print("=" * 70)
    print(result["answer"])

    print()
    print("SOURCES")
    print("=" * 70)

    for source in result["sources"]:
        print(
            f"Document {source['id']} | "
            f"Similarity: {source['similarity']:.6f}"
        )


if __name__ == "__main__":
    main()

