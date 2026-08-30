import asyncio

from voice.live_session import create_live_session


async def main():
    print("Starting Gemini Live session...")

    async with await create_live_session() as session:

        print("Live session connected.")

        await session.send_realtime_input(
            text="Hello. Please say that the VoiceClaim voice system is connected."
        )

        async for response in session.receive():

            if response.text:
                print("Gemini:", response.text)

            if (
                response.server_content
                and response.server_content.output_transcription
            ):
                print(
                    "Transcript:",
                    response.server_content.output_transcription.text,
                )

                break


if __name__ == "__main__":
    asyncio.run(main())