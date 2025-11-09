"""
FFMPEG Tool
Utilities for video assembly and processing
"""
import subprocess
import os
from pathlib import Path
from typing import List, Optional
from loguru import logger


class FFmpegTool:
    """
    Wrapper for FFmpeg operations
    Used for combining videos, adding audio, creating compilations, etc.
    """

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        logger.info(f"🎞️ FFmpeg tool initialized: {self.ffmpeg_path}")

    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        # Try common paths
        common_paths = ["ffmpeg", "ffmpeg.exe", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]

        for path in common_paths:
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return path
            except FileNotFoundError:
                continue

        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg:\n"
            "  Windows: Download from https://ffmpeg.org/download.html\n"
            "  Mac: brew install ffmpeg\n"
            "  Linux: sudo apt-get install ffmpeg"
        )

    def combine_video_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        overwrite: bool = True
    ) -> str:
        """
        Combine video file with audio file

        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file
            overwrite: Whether to overwrite existing file

        Returns:
            Path to output file
        """
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest"
        ]

        if overwrite:
            cmd.append("-y")

        cmd.append(output_path)

        logger.info(f"🎞️ Combining video + audio → {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg failed: {result.stderr}")

        logger.success(f"✅ Created {output_path}")
        return output_path

    def concatenate_videos(
        self,
        video_paths: List[str],
        output_path: str,
        overwrite: bool = True
    ) -> str:
        """
        Concatenate multiple videos into one

        Args:
            video_paths: List of video file paths
            output_path: Path for output file
            overwrite: Whether to overwrite existing file

        Returns:
            Path to output file
        """
        # Create temp file list
        list_file = Path(output_path).parent / "concat_list.txt"

        with open(list_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{os.path.abspath(video_path)}'\n")

        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy"
        ]

        if overwrite:
            cmd.append("-y")

        cmd.append(output_path)

        logger.info(f"🎞️ Concatenating {len(video_paths)} videos → {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temp file
        list_file.unlink()

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg concatenation failed: {result.stderr}")

        logger.success(f"✅ Created {output_path}")
        return output_path

    def add_subtitles(
        self,
        video_path: str,
        subtitle_text: str,
        output_path: str,
        font_size: int = 24,
        overwrite: bool = True
    ) -> str:
        """
        Add subtitle text overlay to video

        Args:
            video_path: Path to video file
            subtitle_text: Text to display
            output_path: Path for output file
            font_size: Font size for subtitles
            overwrite: Whether to overwrite existing file

        Returns:
            Path to output file
        """
        # Escape special characters
        subtitle_text = subtitle_text.replace("'", "\\'").replace(":", "\\:")

        drawtext_filter = (
            f"drawtext=text='{subtitle_text}':fontsize={font_size}:"
            f"fontcolor=white:x=(w-text_w)/2:y=h-th-10:"
            f"box=1:boxcolor=black@0.5:boxborderw=5"
        )

        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vf", drawtext_filter,
            "-c:a", "copy"
        ]

        if overwrite:
            cmd.append("-y")

        cmd.append(output_path)

        logger.info(f"🎞️ Adding subtitles → {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg subtitle failed: {result.stderr}")

        logger.success(f"✅ Created {output_path}")
        return output_path

    def convert_format(
        self,
        input_path: str,
        output_path: str,
        codec: str = "libx264",
        overwrite: bool = True
    ) -> str:
        """
        Convert video to different format/codec

        Args:
            input_path: Path to input video
            output_path: Path for output file
            codec: Video codec to use
            overwrite: Whether to overwrite existing file

        Returns:
            Path to output file
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-c:v", codec,
            "-c:a", "aac"
        ]

        if overwrite:
            cmd.append("-y")

        cmd.append(output_path)

        logger.info(f"🎞️ Converting video → {output_path}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")

        logger.success(f"✅ Created {output_path}")
        return output_path


# Global instance
ffmpeg_tool = FFmpegTool()
