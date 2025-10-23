import requests


class VoiceVoxClient:
    def __init__(self, base_url="http://127.0.0.1:50021"):
        self.base_url = base_url

    def synthesize(self, text, speaker=1, output_path="voice.wav"):
        res = requests.post(
            f"{self.base_url}/audio_query", params={"text": text, "speaker": speaker}
        )
        res.raise_for_status()
        query = res.json()
        res = requests.post(f"{self.base_url}/synthesis", params={"speaker": speaker}, json=query)
        res.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(res.content)
