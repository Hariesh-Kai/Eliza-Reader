import json
import os
import re
from typing import Dict, List, Optional


# ============================================================
# ELIZA READER
# Character Memory V1
#
# Purpose:
#   Maintain persistent information about characters.
#
# This layer does NOT:
#   - detect speakers
#   - generate voices
#   - generate dialogue
#   - modify story text
#
# It only maintains character identity and voice state.
# ============================================================


MEMORY_FILE = "data/analysis/characters.json"


# ============================================================
# Character Memory
# ============================================================

class CharacterMemory:

    def __init__(self, memory_file: str = MEMORY_FILE):

        self.memory_file = memory_file

        self.data = {
            "characters": {}
        }

        self.load()


    # --------------------------------------------------------
    # Load memory
    # --------------------------------------------------------

    def load(self) -> None:

        if not os.path.exists(self.memory_file):

            return

        try:

            with open(
                self.memory_file,
                "r",
                encoding="utf-8"
            ) as file:

                loaded = json.load(file)

            if isinstance(loaded, dict):
                self.data = loaded

            if "characters" not in self.data:
                self.data["characters"] = {}

        except (
            json.JSONDecodeError,
            OSError
        ):

            print(
                "Warning: Could not load character memory."
            )

            self.data = {
                "characters": {}
            }


    # --------------------------------------------------------
    # Save memory
    # --------------------------------------------------------

    def save(self) -> None:

        with open(
            self.memory_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.data,
                file,
                indent=4,
                ensure_ascii=False
            )


    # --------------------------------------------------------
    # Normalize character ID
    # --------------------------------------------------------

    @staticmethod
    def make_character_id(name: str) -> str:

        character_id = name.lower().strip()

        character_id = re.sub(
            r"[^a-z0-9]+",
            "_",
            character_id
        )

        character_id = character_id.strip("_")

        return character_id


    # --------------------------------------------------------
    # Add character
    # --------------------------------------------------------

    def add_character(
        self,
        name: str,
        aliases: Optional[List[str]] = None
    ) -> str:

        character_id = self.make_character_id(
            name
        )

        if character_id in self.data["characters"]:

            # Add new aliases without deleting
            # existing information.

            if aliases:

                existing_aliases = self.data[
                    "characters"
                ][character_id].get(
                    "aliases",
                    []
                )

                for alias in aliases:

                    if alias not in existing_aliases:

                        existing_aliases.append(alias)

                self.data[
                    "characters"
                ][character_id][
                    "aliases"
                ] = existing_aliases

            self.save()

            return character_id


        self.data["characters"][character_id] = {

            "name": name,

            "aliases": aliases or [],

            "voice": {
                "voice_id": None,
                "voice_gender": None,
                "voice_style": None,
                "speed": 1.0,
                "pitch": 0,
                "emotion": None
            },

            "statistics": {
                "dialogue_count": 0,
                "high_confidence_count": 0,
                "medium_confidence_count": 0,
                "low_confidence_count": 0
            }
        }

        self.save()

        return character_id


    # --------------------------------------------------------
    # Get character
    # --------------------------------------------------------

    def get_character(
        self,
        character_id: str
    ) -> Optional[Dict]:

        return self.data[
            "characters"
        ].get(character_id)


    # --------------------------------------------------------
    # Find character by name
    # --------------------------------------------------------

    def find_character(
        self,
        name: str
    ) -> Optional[Dict]:

        character_id = self.make_character_id(
            name
        )

        character = self.get_character(
            character_id
        )

        if character:
            return character

        # Search aliases

        lowered_name = name.lower().strip()

        for character_id, character in self.data[
            "characters"
        ].items():

            for alias in character.get(
                "aliases",
                []
            ):

                if alias.lower().strip() == lowered_name:

                    return character

        return None


    # --------------------------------------------------------
    # Set voice
    # --------------------------------------------------------

    def set_voice(
        self,
        character_id: str,
        voice_id: str,
        voice_gender: Optional[str] = None,
        voice_style: Optional[str] = None
    ) -> bool:

        character = self.get_character(
            character_id
        )

        if not character:
            return False

        character["voice"].update({

            "voice_id": voice_id,

            "voice_gender": voice_gender,

            "voice_style": voice_style
        })

        self.save()

        return True


    # --------------------------------------------------------
    # Update voice settings
    # --------------------------------------------------------

    def update_voice_settings(
        self,
        character_id: str,
        speed: Optional[float] = None,
        pitch: Optional[float] = None,
        emotion: Optional[str] = None
    ) -> bool:

        character = self.get_character(
            character_id
        )

        if not character:
            return False

        voice = character["voice"]

        if speed is not None:
            voice["speed"] = speed

        if pitch is not None:
            voice["pitch"] = pitch

        if emotion is not None:
            voice["emotion"] = emotion

        self.save()

        return True


    # --------------------------------------------------------
    # Record dialogue
    # --------------------------------------------------------

    def record_dialogue(
        self,
        character_id: str,
        confidence: Optional[str] = None
    ) -> bool:

        character = self.get_character(
            character_id
        )

        if not character:
            return False

        statistics = character[
            "statistics"
        ]

        statistics[
            "dialogue_count"
        ] += 1

        if confidence == "HIGH":

            statistics[
                "high_confidence_count"
            ] += 1

        elif confidence == "MEDIUM":

            statistics[
                "medium_confidence_count"
            ] += 1

        elif confidence == "LOW":

            statistics[
                "low_confidence_count"
            ] += 1

        self.save()

        return True


    # --------------------------------------------------------
    # List characters
    # --------------------------------------------------------

    def list_characters(self) -> List[Dict]:

        characters = []

        for character_id, character in self.data[
            "characters"
        ].items():

            item = dict(character)

            item["character_id"] = character_id

            characters.append(item)

        return characters


    # --------------------------------------------------------
    # Print memory
    # --------------------------------------------------------

    def print_memory(self) -> None:

        print("\n" + "=" * 70)
        print("ELIZA READER - CHARACTER MEMORY")
        print("=" * 70)

        characters = self.list_characters()

        if not characters:

            print("\nNo characters registered.")

            return

        for character in characters:

            print(
                f"\nCharacter ID : "
                f"{character['character_id']}"
            )

            print(
                f"Name         : "
                f"{character['name']}"
            )

            print(
                f"Aliases      : "
                f"{character['aliases']}"
            )

            voice = character.get(
                "voice",
                {}
            )

            print(
                f"Voice ID     : "
                f"{voice.get('voice_id')}"
            )

            print(
                f"Voice Gender : "
                f"{voice.get('voice_gender')}"
            )

            print(
                f"Voice Style  : "
                f"{voice.get('voice_style')}"
            )

            print(
                f"Speed        : "
                f"{voice.get('speed')}"
            )

            print(
                f"Pitch        : "
                f"{voice.get('pitch')}"
            )

            print(
                f"Emotion      : "
                f"{voice.get('emotion')}"
            )

            statistics = character.get(
                "statistics",
                {}
            )

            print(
                f"Dialogue     : "
                f"{statistics.get('dialogue_count', 0)}"
            )


# ============================================================
# Initialize known characters
# ============================================================

def initialize_characters(
    memory: CharacterMemory
) -> None:

    # Known character from the current chapter.
    memory.add_character(
        "Pei Qian"
    )


# ============================================================
# Test
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Character Memory V1")
    print("=" * 70)

    memory = CharacterMemory()

    initialize_characters(
        memory
    )

    memory.print_memory()

    print("\n" + "-" * 70)
    print("Testing character lookup")
    print("-" * 70)

    character = memory.find_character(
        "Pei Qian"
    )

    if character:

        print(
            "\nFound character:"
        )

        print(
            f"Name: {character['name']}"
        )

    print("\n" + "-" * 70)
    print("Testing voice assignment")
    print("-" * 70)

    character_id = memory.make_character_id(
        "Pei Qian"
    )

    memory.set_voice(
        character_id=character_id,
        voice_id="voice_001",
        voice_gender="female",
        voice_style="calm"
    )

    memory.update_voice_settings(
        character_id=character_id,
        speed=1.0,
        pitch=0,
        emotion="neutral"
    )

    memory.print_memory()

    print("\n" + "=" * 70)
    print(
        f"Character memory saved to: "
        f"{MEMORY_FILE}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()