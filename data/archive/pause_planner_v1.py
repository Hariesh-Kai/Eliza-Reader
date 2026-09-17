import json
from pathlib import Path


INPUT_FILE = "chapter_interpretation.json"
OUTPUT_FILE = "pause_plan_v1.json"


# ============================================================
# DEFAULT PAUSE SETTINGS
# ============================================================

PAUSES = {
    "NARRATION_TO_NARRATION": 0.20,
    "NARRATION_TO_DIALOGUE": 0.35,
    "NARRATION_TO_SYSTEM": 0.45,

    "DIALOGUE_TO_NARRATION": 0.30,
    "DIALOGUE_TO_DIALOGUE": 0.25,
    "DIALOGUE_TO_SYSTEM": 0.40,

    "SYSTEM_TO_NARRATION": 0.50,
    "SYSTEM_TO_DIALOGUE": 0.50,
    "SYSTEM_TO_SYSTEM": 0.20,
}


# ============================================================
# LOAD INTERPRETATION
# ============================================================

def load_story():

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return data


# ============================================================
# GET PAUSE
# ============================================================

def get_pause(previous_type, current_type):

    key = (
        f"{previous_type}_TO_{current_type}"
    )

    return PAUSES.get(
        key,
        0.30
    )


# ============================================================
# BUILD PLAN
# ============================================================

def build_pause_plan():

    print("=" * 70)
    print("ELIZA READER")
    print("Pause Planner V1")
    print("=" * 70)

    print()

    data = load_story()

    segments = data.get(
        "segments",
        []
    )

    print(
        f"Loaded {len(segments)} interpreted segments."
    )

    print()

    plan = []

    previous_type = None

    for index, segment in enumerate(
        segments
    ):

        current_type = segment[
            "type"
        ]

        if previous_type is None:

            pause_before = 0.0

        else:

            pause_before = get_pause(
                previous_type,
                current_type
            )

        item = {

            "segment":
                segment["segment"],

            "type":
                current_type,

            "pause_before":
                pause_before,

            "text":
                segment["text"]
        }

        plan.append(
            item
        )

        previous_type = current_type

    # ========================================================
    # SAVE
    # ========================================================

    output = {

        "version":
            "Pause Planner V1",

        "source":
            INPUT_FILE,

        "default_pauses":
            PAUSES,

        "segments":
            plan
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # REPORT
    # ========================================================

    print("=" * 70)
    print("PAUSE PLAN")
    print("=" * 70)

    print()

    for item in plan[:15]:

        print(
            f"[{item['segment']:03d}] "
            f"{item['type']:<10} "
            f"Pause: "
            f"{item['pause_before']:.2f}s"
        )

    print()

    print(
        f"Total segments : {len(plan)}"
    )

    print(
        f"Output         : {OUTPUT_FILE}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_pause_plan()
