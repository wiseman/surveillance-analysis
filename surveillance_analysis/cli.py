import logging
import os.path
import pprint
import sys

import click
import ffmpeg
import tqdm
import webrtcvad

logger = logging.getLogger(__name__)

@click.group()
@click.version_option()
def cli():
    "null"


@cli.command(name="analyze")
@click.argument(
    "video",
    nargs=-1
)
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def analyze(video, option):
    "Generate descriptive CSV for videos"
    FORMAT = '%(asctime)s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.ERROR)
    click.echo("filename,creation_date,duration,has_audio,resolution")
    file_sizes = {f: os.path.getsize(f) / (1024 * 1024) for f in video}
    total_file_mb = sum(file_sizes.values())
    with tqdm.tqdm(total=int(total_file_mb), unit="MB") as pbar:
        for f in file_sizes:
            logger.info("Analyzing %s", f)
            probe = ffmpeg.probe(f)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            video_duration = float(video_stream['duration'])
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            has_audio = audio_stream is not None
            filename = os.path.basename(f)
            creation_date = video_stream['tags']['creation_time']
            width = video_stream['width']
            height = video_stream['height']
            resolution = f"{width}x{height}"
            speech_time = 0
            total_time = 0
            if has_audio:
                logger.info("Decoding audio %s s", video_duration)
                audio = decode_audio(f)
                logger.info("Doing VAD")
                speech_time, total_time = vad_analyze(audio)
            click.echo(f"{filename},{creation_date},{video_duration},{has_audio},{resolution},{total_time:.1f},{speech_time:.1f}")
            pbar.update(file_sizes[f])


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def decode_audio(in_filename, **input_kwargs):
    try:
        out, err = (ffmpeg
            .input(in_filename, **input_kwargs)
            .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    return out

# pcm_data must be 16 Khz, 16 bit mono audio data.
def vad_analyze(pcm_data):
    SAMPLE_RATE = 16000
    vad = webrtcvad.Vad(3)
    num_speech_frames = 0
    num_frames = 0
    for frame in frame_generator(30, pcm_data, SAMPLE_RATE):
        num_frames += 1
        if vad.is_speech(frame.bytes, sample_rate=SAMPLE_RATE):
            num_speech_frames += 1
    return float(num_speech_frames) * 0.030, float(num_frames) * 0.030
