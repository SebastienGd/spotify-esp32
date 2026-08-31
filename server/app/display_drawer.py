import numpy as np
from omegaconf import DictConfig
from PIL import Image, ImageDraw, ImageFont

from app.pixel_art import PixelArt
from app.spotify import Spotify


class DisplayDrawer:
    def __init__(self, spotify: Spotify, pixel_art: PixelArt, conf: DictConfig):
        self.spotify = spotify
        self.pixel_art = pixel_art
        self.display_width = conf.display_width
        self.display_height = conf.display_height
        self.face_width = conf.face_width
        self.face_height = conf.face_height
        self.playback_width = conf.playback_width
        self.playback_height = conf.playback_height
        self.scroll_spacer = conf.scroll_spacer
        self._scroll_offset = 0

    def draw_display(self) -> Image.Image:
        display = Image.new("1", (self.display_width, self.display_height), 0)

        display.paste(self.draw_artist(), (0, 0))

        display.paste(
            self.draw_playback_state(
                interpolated_progress_ms=self.spotify.interpolate_progress_ms(),
            ),
            (self.face_width, 0),
        )

        return display

    def draw_artist(self) -> Image.Image:
        image = Image.new("1", (self.face_width, self.face_height), 0)

        bitmap = self.pixel_art.bitmap

        if bitmap is None:
            return image

        face = Image.fromarray(bitmap)

        if face.size != (self.face_width, self.face_height):
            face = face.resize(
                (self.face_width, self.face_height),
                Image.Resampling.NEAREST,
            )

        face = face.convert("1")
        image.paste(face, (0, 0))

        return image

    def draw_playback_state(self, interpolated_progress_ms: int | None = None) -> Image.Image:
        width = self.playback_width
        height = self.playback_height

        image = Image.new("1", (width, height), 0)
        draw = ImageDraw.Draw(image)
        playback = self.spotify.playback_state

        if not playback or not playback.item:
            return image

        track = playback.item
        song_name = track.name or ""
        artist_name = track.artists[0].name if track.artists else "Unknown"
        progress_ms = interpolated_progress_ms if interpolated_progress_ms is not None else (playback.progress_ms or 0)
        duration_ms = track.duration_ms or 0
        current_time = self._format_time(progress_ms)
        total_time = self._format_time(duration_ms)

        if duration_ms > 0:
            progress = progress_ms / duration_ms
        else:
            progress = 0.0

        progress = max(0.0, min(progress, 1.0))

        title_font = self._load_font(size=10, bold=True)
        artist_font = self._load_font(size=7)
        time_font = self._load_font(size=6)

        margin = 2
        usable_width = width - margin * 2

        self._draw_scrolling_text(
            draw,
            song_name,
            title_font,
            y=2,
            margin=margin,
            available_width=usable_width,
        )

        self._draw_scrolling_text(
            draw,
            artist_name,
            artist_font,
            y=18,
            margin=margin,
            available_width=usable_width,
        )

        bar_x = margin
        bar_y = 34
        bar_width = usable_width
        bar_height = 6

        draw.rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width - 1,
                bar_y + bar_height - 1,
            ),
            outline=1,
        )

        inner_width = bar_width - 2
        progress_width = round(inner_width * progress)

        if progress_width > 0:
            draw.rectangle(
                (
                    bar_x + 1,
                    bar_y + 1,
                    bar_x + progress_width,
                    bar_y + bar_height - 2,
                ),
                fill=1,
            )

        time_y = 48

        draw.text(
            (margin, time_y),
            current_time,
            font=time_font,
            fill=1,
        )

        total_width = self._text_width(
            draw,
            total_time,
            time_font,
        )

        draw.text(
            (
                width - margin - total_width,
                time_y,
            ),
            total_time,
            font=time_font,
            fill=1,
        )

        return image

    @staticmethod
    def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
        font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"

        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            return ImageFont.load_default()

    @staticmethod
    def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def _draw_scrolling_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        y: int,
        margin: int,
        available_width: int,
    ) -> None:
        text_width = self._text_width(draw, text, font)

        if text_width <= available_width:
            draw.text(
                ((self.playback_width - text_width) // 2, y),
                text,
                font=font,
                fill=1,
            )
            return

        cycle_width = text_width + self._text_width(draw, self.scroll_spacer, font)
        text_x = margin - (self._scroll_offset % cycle_width)

        draw.text((text_x, y), text, font=font, fill=1)
        draw.text((text_x + cycle_width, y), text, font=font, fill=1)

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        total_seconds = milliseconds // 1000

        minutes = total_seconds // 60
        seconds = total_seconds % 60

        return f"{minutes}:{seconds:02d}"

    @staticmethod
    def to_bytes(image: Image.Image) -> bytes:
        bitmap = (np.asarray(image.convert("1")) > 0).astype(np.uint8)
        packed = np.packbits(bitmap, axis=1, bitorder="little")
        return packed.tobytes()

    def advance_scroll(self) -> None:
        self._scroll_offset += 1

    def reset_scroll_offset(self) -> None:
        self._scroll_offset = 0
