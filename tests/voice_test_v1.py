import subprocess
from pathlib import Path


VOICES = {
    "narrator": "models/en_US-lessac-medium.onnx",
    "pei_qian": "models/en_US-kristin-medium.onnx",
    "system": "models/en_US-amy-medium.onnx",
}


TEXTS = {
    "narrator": "He had returned back in time by ten years.",
    "pei_qian": "What's going on?!",
    "system": "Binding of the Wealth Conversion System in progress.",
}


OUTPUT_DIR = Path("voice_tests")
OUTPUT_DIR.mkdir(exist_ok=True)


for role, model in VOICES.items():

    output = OUTPUT_DIR / f"{role}.wav"

    print("=" * 70)
    print(f"Role   : {role}")
    print(f"Model  : {model}")
    print(f"Text   : {TEXTS[role]}")
    print(f"Output : {output}")
    print()

    command = [
        "python",
        "-m",
        "piper",
        "--model",
        model,
        "--output_file",
        str(output),
    ]

    with open(output, "wb") as _:
        pass

    subprocess.run(
        command,
        input=TEXTS[role],
        text=True,
        check=True,
    )

    print("SUCCESS")
    print()


print("=" * 70)
print("VOICE TEST COMPLETE")
print("=" * 70)
print()
print(f"Test files are in: {OUTPUT_DIR}")