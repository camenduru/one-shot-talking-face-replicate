import os
from cog import BasePredictor, Input, Path

import sys
sys.path.append('/content/one-shot-talking-face')

import os, subprocess, torchaudio, torch
from PIL import Image

def inference(image_file, wav_file):
    waveform, sample_rate = torchaudio.load(wav_file)
    waveform = torch.mean(waveform, dim=0, keepdim=True)
    torchaudio.save("/content/train/audio.wav", waveform, sample_rate, encoding="PCM_S", bits_per_sample=16)
    image = Image.open(image_file)
    image = pad_image(image)
    image.save("/content/train/image.png")

    pocketsphinx_run = subprocess.run(['pocketsphinx', '-phone_align', 'yes', 'single', '/content/train/audio.wav'], check=True, capture_output=True)
    jq_run = subprocess.run(['jq', '[.w[]|{word: (.t | ascii_upcase | sub("<S>"; "sil") | sub("<SIL>"; "sil") | sub("\\\(2\\\)"; "") | sub("\\\(3\\\)"; "") | sub("\\\(4\\\)"; "") | sub("\\\[SPEECH\\\]"; "SIL") | sub("\\\[NOISE\\\]"; "SIL")), phones: [.w[]|{ph: .t | sub("\\\+SPN\\\+"; "SIL") | sub("\\\+NSN\\\+"; "SIL"), bg: (.b*100)|floor, ed: (.b*100+.d*100)|floor}]}]'], input=pocketsphinx_run.stdout, capture_output=True)
    with open("/content/train/test.json", "w") as f:
        f.write(jq_run.stdout.decode('utf-8').strip())

    os.system(f"cd /content/train/one-shot-talking-face && python3 -B test_script.py --img_path /content/train/image.png --audio_path /content/train/audio.wav --phoneme_path /content/train/test.json --save_dir /content/train/train")
    return "/content/train/image_audio.mp4"

class Predictor(BasePredictor):
    def setup(self) -> None:
    def predict(
        self,
        image_file: Path = Input(description="Input Image"),
        wav_file: Path = Input(default="Input WAV"),
    ) -> Path:
        video_path = inference(image_file, wav_file)
        return Path(video_path)