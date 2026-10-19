"""Google Drive storage for raw footage, edits, previews, captions, licences and reports.

Credentials (environment, never logged):
  GOOGLE_SERVICE_ACCOUNT_JSON   full JSON of a service account that the World Ignored folder is shared with
or
  GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET / GOOGLE_OAUTH_REFRESH_TOKEN  (admin account, scope drive.file)

Folder IDs live in state/drive.json (created once by `wi drive-init`, or filled in by hand to reuse
existing folders). Without credentials `available()` is False and callers must treat files as
not persisted: scheduled runs use temporary containers, so local files disappear.
"""
from __future__ import annotations

import json
import mimetypes
import time
from pathlib import Path

import requests

from . import config

FOLDERS = ["Raw Videos", "Sources and Permissions", "Verified Footage", "Edited Videos — 9x16",
           "Edited Videos — 4x5", "Video Previews", "Captions", "Approved for Publishing", "Published Videos",
           "Daily Performance Reports"]
PRESET_FOLDER = {"v9x16": "Edited Videos — 9x16", "f4x5": "Edited Videos — 4x5", "x720": "Edited Videos — 9x16"}
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"


class StorageUnavailable(RuntimeError):
    pass


class Drive:
    def __init__(self):
        self._token, self._exp = None, 0.0
        self.map_path = config.STATE_DIR / "drive.json"

    # --- auth ------------------------------------------------------------------------------
    def available(self) -> tuple[bool, str]:
        if config.env("GOOGLE_SERVICE_ACCOUNT_JSON"):
            return True, "service account"
        if all(config.env(k) for k in ("GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET", "GOOGLE_OAUTH_REFRESH_TOKEN")):
            return True, "oauth refresh token"
        return False, "no Google credentials (set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_OAUTH_* secrets)"

    def _auth(self) -> dict:
        if self._token and time.time() < self._exp - 60:
            return {"Authorization": f"Bearer {self._token}"}
        sa = config.env("GOOGLE_SERVICE_ACCOUNT_JSON")
        if sa:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
            creds = service_account.Credentials.from_service_account_info(
                json.loads(sa), scopes=["https://www.googleapis.com/auth/drive",
                                        "https://www.googleapis.com/auth/spreadsheets"])
            creds.refresh(Request())
            self._token, self._exp = creds.token, creds.expiry.timestamp() if creds.expiry else time.time() + 3000
        elif config.env("GOOGLE_OAUTH_REFRESH_TOKEN"):
            r = requests.post("https://oauth2.googleapis.com/token", data={
                "client_id": config.env("GOOGLE_OAUTH_CLIENT_ID"), "client_secret": config.env("GOOGLE_OAUTH_CLIENT_SECRET"),
                "refresh_token": config.env("GOOGLE_OAUTH_REFRESH_TOKEN"), "grant_type": "refresh_token"}, timeout=30)
            r.raise_for_status()
            d = r.json()
            self._token, self._exp = d["access_token"], time.time() + d.get("expires_in", 3600)
        else:
            raise StorageUnavailable(self.available()[1])
        return {"Authorization": f"Bearer {self._token}"}

    # --- folders ---------------------------------------------------------------------------
    def folders(self) -> dict:
        if self.map_path.exists():
            return json.loads(self.map_path.read_text())
        return {}

    def init_folders(self, root_id: str | None = None) -> dict:
        """Reuse existing World Ignored folders by name; create only what is missing."""
        m = self.folders()
        root = root_id or m.get("root") or self._find_folder("World Ignored", None) or self._mkdir("World Ignored", None)
        m["root"] = root
        for name in FOLDERS:
            m[name] = m.get(name) or self._find_folder(name, root) or self._mkdir(name, root)
        self.map_path.write_text(json.dumps(m, indent=1, ensure_ascii=False))
        return m

    def _find_folder(self, name: str, parent: str | None) -> str | None:
        q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent:
            q += f" and '{parent}' in parents"
        r = requests.get(f"{API}/files", headers=self._auth(), timeout=30,
                         params={"q": q, "fields": "files(id,name)", "supportsAllDrives": True,
                                 "includeItemsFromAllDrives": True})
        r.raise_for_status()
        files = r.json().get("files", [])
        return files[0]["id"] if files else None

    def _mkdir(self, name: str, parent: str | None) -> str:
        body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent:
            body["parents"] = [parent]
        r = requests.post(f"{API}/files", headers=self._auth(), json=body, params={"supportsAllDrives": True}, timeout=30)
        r.raise_for_status()
        return r.json()["id"]

    # --- files -----------------------------------------------------------------------------
    def find(self, name: str, folder: str) -> dict | None:
        fid = self.folders()[folder]
        r = requests.get(f"{API}/files", headers=self._auth(), timeout=30, params={
            "q": f"name = '{name}' and '{fid}' in parents and trashed = false",
            "fields": "files(id,name,webViewLink,md5Checksum,size)", "supportsAllDrives": True,
            "includeItemsFromAllDrives": True})
        r.raise_for_status()
        f = r.json().get("files", [])
        return f[0] if f else None

    def upload(self, path: str | Path, folder: str, name: str | None = None) -> dict:
        """Resumable upload; idempotent by name within the folder (an existing file is updated, not duplicated)."""
        path = Path(path)
        name = name or path.name
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        existing = self.find(name, folder)
        meta = {"name": name} if existing else {"name": name, "parents": [self.folders()[folder]]}
        url = f"{UPLOAD}/{existing['id']}" if existing else UPLOAD
        method = requests.patch if existing else requests.post
        init = method(url, headers={**self._auth(), "X-Upload-Content-Type": mime}, json=meta, timeout=60,
                      params={"uploadType": "resumable", "supportsAllDrives": True, "fields": "id,webViewLink,size"})
        init.raise_for_status()
        session = init.headers["Location"]
        size = path.stat().st_size
        chunk = 8 * 1024 * 1024
        with open(path, "rb") as fh:
            offset = 0
            while True:
                data = fh.read(chunk)
                end = offset + len(data) - 1
                for attempt in range(5):
                    try:
                        r = requests.put(session, data=data, timeout=300, headers={
                            "Content-Range": f"bytes {offset}-{end}/{size}" if data else f"bytes */{size}"})
                        break
                    except requests.RequestException:
                        time.sleep(2 ** attempt)
                else:
                    raise RuntimeError("Drive upload failed after retries")
                if r.status_code in (200, 201):
                    return r.json()
                if r.status_code != 308:
                    r.raise_for_status()
                offset = end + 1

    def upload_text(self, text: str, folder: str, name: str) -> dict:
        tmp = config.WORK_DIR / "tmp" / name
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(text, encoding="utf-8")
        return self.upload(tmp, folder, name)

    def download(self, file_id: str, dest: str | Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(f"{API}/files/{file_id}", headers=self._auth(), params={"alt": "media", "supportsAllDrives": True},
                          stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for part in r.iter_content(1 << 20):
                    fh.write(part)
        return dest

    def share_link(self, file_id: str) -> str:
        """Temporary 'anyone with the link' read access, needed for platforms that pull media from a URL
        (Instagram, Threads). Call `unshare` after publishing."""
        r = requests.post(f"{API}/files/{file_id}/permissions", headers=self._auth(), timeout=30,
                          params={"supportsAllDrives": True}, json={"role": "reader", "type": "anyone"})
        r.raise_for_status()
        return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

    def unshare(self, file_id: str) -> None:
        r = requests.get(f"{API}/files/{file_id}/permissions", headers=self._auth(), timeout=30,
                         params={"supportsAllDrives": True, "fields": "permissions(id,type)"})
        r.raise_for_status()
        for p in r.json().get("permissions", []):
            if p["type"] == "anyone":
                requests.delete(f"{API}/files/{file_id}/permissions/{p['id']}", headers=self._auth(), timeout=30,
                                params={"supportsAllDrives": True})


# --- Google Sheets tracker mirror ------------------------------------------------------------------
SHEETS = "https://sheets.googleapis.com/v4/spreadsheets"


def sync_tracker(drive: Drive, csv_text: str, analytics_rows: list[list] | None = None) -> dict:
    """Overwrite the tracker tab with the current tracker and append analytics snapshot rows.

    The service account / OAuth user needs edit access to the sheet (settings.google.tracker_sheet_id).
    """
    import csv
    import io
    sid = config.settings()["google"]["tracker_sheet_id"]
    h = drive._auth()
    meta = requests.get(f"{SHEETS}/{sid}", headers=h, params={"fields": "sheets.properties"}, timeout=30)
    meta.raise_for_status()
    tabs = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.json()["sheets"]}
    first = next(iter(tabs))
    rows = list(csv.reader(io.StringIO(csv_text)))
    requests.post(f"{SHEETS}/{sid}/values/'{first}'!A:Z:clear", headers=h, timeout=30).raise_for_status()
    requests.put(f"{SHEETS}/{sid}/values/'{first}'!A1", headers=h, params={"valueInputOption": "RAW"},
                 json={"values": rows}, timeout=60).raise_for_status()
    out = {"tracker_rows": len(rows) - 1}
    if analytics_rows:
        if "Analytics" not in tabs:
            requests.post(f"{SHEETS}/{sid}:batchUpdate", headers=h, timeout=30, json={"requests": [
                {"addSheet": {"properties": {"title": "Analytics"}}}]}).raise_for_status()
            analytics_rows = [["Date", "Platform", "Video ID", "Views", "Reach", "Likes", "Comments", "Shares", "Saves",
                               "Avg watch (s)", "Followers"]] + analytics_rows
        requests.post(f"{SHEETS}/{sid}/values/'Analytics'!A1:append", headers=h, timeout=60,
                      params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
                      json={"values": analytics_rows}).raise_for_status()
        out["analytics_rows"] = len(analytics_rows)
    return out
