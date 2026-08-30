from rag.retriever import retrieve_policy_documents


def main():

    question = (
        "I had a collision and my car was damaged. "
        "Is the damage covered?"
    )

    print()
    print("QUESTION")
    print("=" * 70)
    print(question)

    results = retrieve_policy_documents(
        question=question,
        policy_id=1,
        match_count=6,
    )

    print()
    print("RANKING")
    print("=" * 70)

    if not results:
        print("No results returned.")
        return

    for rank, result in enumerate(results, start=1):

        content = result["content"].replace("\n", " ")

        print(
            f"Rank #{rank} | "
            f"Document ID: {result['id']} | "
            f"Similarity: {result['similarity']:.6f}"
        )

        print(f"Content: {content}")

        print("-" * 70)


if __name__ == "__main__":
    main()
    