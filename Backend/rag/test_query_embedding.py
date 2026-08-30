from rag.embeddings import embed_query


def main():

    question = (
        "I had a collision and my car was damaged. "
        "Is the damage covered?"
    )

    vector = embed_query(question)

    print()
    print("Query embedding generated successfully.")
    print("Dimensions:", len(vector))
    print("First 5 values:", vector[:5])


if __name__ == "__main__":
    main()