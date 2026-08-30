from rag.embeddings import embed_text


def main():

    text = (
        "Comprehensive motor insurance covers accidental "
        "damage to the insured vehicle resulting from collision."
    )

    vector = embed_text(text)

    print()
    print("Embedding generated successfully.")
    print("Dimensions:", len(vector))
    print("First 5 values:", vector[:5])


if __name__ == "__main__":
    main()