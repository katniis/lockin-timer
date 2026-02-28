import json
import os
from models.profile import Profile
from config import DATA_DIR


class StorageService:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        safe = name.lower().replace(" ", "_")
        return os.path.join(self.data_dir, f"{safe}.json")

    def list_profiles(self) -> list[str]:
        names = []
        for f in os.listdir(self.data_dir):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(self.data_dir, f)) as fp:
                        data = json.load(fp)
                        names.append(data["name"])
                except Exception:
                    pass
        return sorted(names)

    def load_profile(self, name: str) -> Profile:
        path = self._path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Profile '{name}' not found.")
        with open(path) as f:
            return Profile.from_dict(json.load(f))

    def save_profile(self, profile: Profile):
        path = self._path(profile.name)
        with open(path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)

    def delete_profile(self, name: str):
        path = self._path(name)
        if os.path.exists(path):
            os.remove(path)

    def profile_exists(self, name: str) -> bool:
        return os.path.exists(self._path(name))

    def append_session(self, profile: Profile, session_dict: dict):
        profile.sessions.append(session_dict)
        self.save_profile(profile)
