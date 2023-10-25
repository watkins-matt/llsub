#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys

import pysubs2
import tqdm
from deep_translator import GoogleTranslator

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
)
logger = logging.getLogger(__name__)


class SRTFile:
    def __init__(self, file_path: str, subs: pysubs2.SSAFile = None):
        """
        Initialize an SRTFile object.

        :param file_path: The path to the SRT file.
        :param subs: Optional SSAFile object containing the subtitles.
        """
        self.file_path = file_path
        self.language = self._extract_language(file_path) if subs is None else None
        self.subs = subs if subs is not None else pysubs2.load(file_path)

    @staticmethod
    def _extract_language(file_path: str) -> str:
        """
        Extract the language identifier from the file path.

        :param file_path: The path to the SRT file.
        :return: A two-letter language identifier.
        """
        match = re.search(r"\.([a-z]{2})\.srt$", file_path)
        if match:
            return match.group(1)
        raise ValueError("Unable to extract language from filename.")

    def generate_translated_subtitles(
        self, target_language: str, write_to_disk: bool = True
    ) -> "SRTFile":
        """
        Generate translated subtitles.
        Optionally write the translated subtitles to disk.

        :param target_language: The target language for translation.
        :param write_to_disk: Whether to write the translated subtitles to disk.
        :return: A new SRTFile object containing the translated subtitles.
        """
        max_characters = 5000  # Maximum characters for translation
        text_blocks = self._create_text_blocks(max_characters)
        translated_blocks = self._translate_text_blocks(text_blocks, target_language)

        # Create a new SRTFile instance for the translated subtitles
        translated_srt_file = SRTFile(
            self.get_file_path_for_language(target_language), subs=pysubs2.SSAFile()
        )

        # Note that the translated blocks contain multiple events each,
        # so translated_text is a string containing then entire file with each
        # event separated by two newlines. We split the string on two newlines
        # to get a list of events independently.
        translated_text = "\n\n".join(translated_blocks)
        translated_events = translated_text.strip().split("\n\n")

        # Create a new event for each translated event and add it to the
        # translated_srt_file
        for i, event in enumerate(self.subs):
            new_event = pysubs2.SSAEvent()
            new_event.start = event.start
            new_event.end = event.end
            new_event.text = translated_events[i]
            translated_srt_file.subs.append(new_event)

        # Save the translated subtitles to disk
        if write_to_disk:
            translated_srt_file.save(target_language)

        return translated_srt_file

    def generate_merged_subtitles(
        self,
        translated_srt_file: "SRTFile",
        language_id: str,
        write_to_disk: bool = True,
    ) -> "SRTFile":
        """
        Generate merged subtitles. Optionally write the merged subtitles to disk.

        :param translated_srt_file: An SRTFile containing the translated subtitles.
        :param language_id: The language identifier for the merged subtitles.
        :param write_to_disk: Whether to write the merged subtitles to disk.
        :return: A new SRTFile object containing the merged subtitles.
        """
        if len(self.subs) != len(translated_srt_file.subs):
            raise ValueError(
                "Subtitle files have different number of events; cannot merge."
            )

        merged_ssa_file = self._create_merged_ssa_file(translated_srt_file)

        # Create a new SRTFile instance for the merged subtitles
        merged_srt_file = SRTFile(
            self.get_file_path_for_language(language_id), subs=merged_ssa_file
        )

        # Save the merged subtitles to disk
        if write_to_disk:
            merged_srt_file.save(language_id)

        return merged_srt_file

    def _create_text_blocks(self, max_characters: int) -> list:
        """
        Create text blocks for translation. Blocks are created by concatenating
        events until the maximum number of characters is reached.

        :param max_characters: The maximum number of characters in each block.
        :return: A list of text blocks.
        """
        text_blocks = []
        current_text_block = ""

        for event in self.subs:
            if len(current_text_block) + len(event.text) < max_characters:
                current_text_block += event.text + "\n\n"
            else:
                text_blocks.append(current_text_block)
                current_text_block = event.text + "\n\n"
        text_blocks.append(current_text_block)  # Add the last block

        return text_blocks

    def _translate_text_blocks(self, text_blocks: list, target_language: str) -> list:
        """
        Translate a list of text blocks. The text blocks are concatenated
        using _create_text_blocks(). Each block should be the maximum number
        of characters that the translation API allows.

        Google Translator is currently limited to 5000 characters per request.

        :param text_blocks: A list of text blocks.
        :param target_language: The target language for translation.
        :return: A list of translated text blocks.
        """
        translator = GoogleTranslator(source=self.language, target=target_language)
        translated_blocks = []

        for text_block in tqdm.tqdm(text_blocks, desc="Translating subtitles"):
            # Temporarily replace \N with a unique marker
            text_block_temp = text_block.replace("\\N", "--")
            translated_text_temp = translator.translate(text=text_block_temp)
            # Replace the unique marker back with \N
            translated_text = translated_text_temp.replace("--", "\\N")
            translated_blocks.append(translated_text)

        return translated_blocks

    def get_file_path_for_language(self, target_language: str) -> str:
        """
        Generates a string that represent the current file using
        another language code.

        :param target_language: Target language identifier.
        :return: Path for the new SRT file in the given language.
        """
        return self.file_path.replace(
            f".{self.language}.srt", f".{target_language}.srt"
        )

    def _create_merged_ssa_file(
        self, translated_srt_file: "SRTFile"
    ) -> pysubs2.SSAFile:
        """
        Create a merged SSA file, by combining the events in the current SRTFile
        and the translated SRTFile.

        :param translated_srt_file: An SRTFile containing the translated subtitles.
        :return: A new SSAFile containing the merged subtitles.
        """
        merged_ssa_file = pysubs2.SSAFile()

        # Merge every event in the original and translated SRT files
        for original_event, translated_event in zip(
            self.subs, translated_srt_file.subs, strict=True
        ):
            original_lines = original_event.text.split("\\N")

            # Remove empty lines from translated_lines
            translated_lines = [
                line for line in translated_event.text.split("\\N") if line.strip()
            ]

            # Initialize an empty string to hold the final interleaved text
            final_interleaved_text = ""

            # Check if the number of lines is the same in both texts
            if len(original_lines) == len(translated_lines):
                # If the line count is matched, interleave the lines
                for original_line, translated_line in zip(
                    original_lines, translated_lines, strict=True
                ):
                    # Note that pysubs2 won't generate the extra line break with a \n
                    # only, which is why we use \r\n here
                    final_interleaved_text += (
                        f"{original_line}\n({translated_line})\r\n\r\n"
                    )
            else:
                # If the line count is mismatched, list original lines first,
                # then translated lines. \r\n is required for the extra line break.
                final_interleaved_text += "\n".join(original_lines) + "\r\n\r\n"
                final_interleaved_text += "\n".join(
                    [f"({line})" for line in translated_lines]
                )

            # Create the new subtitle event and add it to the merged file
            merged_event = pysubs2.SSAEvent()
            merged_event.start = original_event.start
            merged_event.end = original_event.end
            merged_event.plaintext = final_interleaved_text
            merged_ssa_file.append(merged_event)

        return merged_ssa_file

    def save(self, language_id: str) -> None:
        """
        Saves the subtitles to disk.

        :param language_id: The language identifier to use in the filename.
        """
        output_file = self.get_file_path_for_language(language_id)
        self.subs.save(output_file, format_="srt")


def parse_arguments():
    """
    Parses the command-line arguments.

    :return: Parsed arguments from argparse.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Creates bilingual (language learner) subtitles from an original "
            "translated SRT file."
        )
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Input SRT file",
    )
    parser.add_argument(
        "target_language",
        type=str,
        nargs="?",
        default="en",
        help="Target language for translation (default: en)",
    )
    parser.add_argument(
        "--translate-only",
        action="store_true",
        help="Only translate the subtitles without merging.",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing dual language subtitles if they exist.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    srt_file = SRTFile(args.input_file)
    target_language = args.target_language

    if srt_file.language == target_language:
        logger.error(
            f"Error: Target language '{target_language}' is the same as the "
            f"source language '{srt_file.language}'. No work to perform."
        )
        sys.exit(1)

    # Check if translated subtitles already exist
    translated_file_path = srt_file.get_file_path_for_language(target_language)
    if os.path.exists(translated_file_path):
        logger.info("Translated subtitles already exist. Loading...")
        translated_srt_file = SRTFile(translated_file_path)
    # We need to generate the translated subtitle file
    else:
        logger.info("Generating translated subtitles...")
        translated_srt_file = srt_file.generate_translated_subtitles(target_language)

    # We are generating the dual language subtitles, not just translating
    if not args.translate_only:
        # Check to see if the dual language subtitles exist
        language_id = f"{srt_file.language}-{target_language}"
        dual_lang_file_path = srt_file.get_file_path_for_language(language_id)

        if os.path.exists(dual_lang_file_path) and not args.force:
            logger.error("Dual language subtitles already exist. No work to perform.")
            sys.exit(1)
        elif os.path.exists(dual_lang_file_path) and args.force:
            logger.info("Forcing overwrite of existing dual language subtitles.")

        logger.info("Generating dual language subtitles...")

        try:
            # Merge the original srt_file and the translated_srt_file
            merged_srt_file = srt_file.generate_merged_subtitles(
                translated_srt_file, language_id
            )
            logger.info(
                f"Generated dual language subtitles: {merged_srt_file.file_path}."
            )

        # There was a mismatch in the number of events in the original and translated
        except ValueError as e:
            logger.error(e)
            sys.exit(1)


if __name__ == "__main__":
    main()
