"""
Laptop Camera Live Stream
=========================
Hosts a live video stream from this laptop's camera.
Any device (phone / other laptop) connected to this laptop's
hotspot can watch the stream in a browser.

Run:  python app.py
Then open the URL printed in the terminal on any connected device.
"""

import socket
import subprocess
import sys
import cv2
from flask import Flask, Response, render_template

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PORT = 5000
CAMERA_INDEX = 0          # try 1 or 2 if you have multiple cameras
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 70         # 1-100, lower = faster / less bandwidth

app = Flask(__name__)


# ----------------------------------------------------------------------
# Camera handling
# ----------------------------------------------------------------------
def open_camera():
    """Open the camera, trying a couple of backends for reliability."""
    # CAP_DSHOW works best on Windows; fall back to default otherwise.
    for backend in (cv2.CAP_DSHOW, cv2.CAP_ANY):
        cam = cv2.VideoCapture(CAMERA_INDEX, backend)
        if cam.isOpened():
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            return cam
        cam.release()
    return None


camera = open_camera()
if camera is None:
    print("\n[ERROR] Could not open the camera.")
    print("  - Make sure no other app (Zoom, Teams, Camera) is using it.")
    print("  - Try changing CAMERA_INDEX in app.py to 1 or 2.\n")
    sys.exit(1)


def generate_frames():
    """Continuously read frames and yield them as an MJPEG stream."""
    while True:
        success, frame = camera.read()
        if not success:
            continue
        ok, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
        )
        if not ok:
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ----------------------------------------------------------------------
# Hotspot + networking helpers
# ----------------------------------------------------------------------
def turn_on_hotspot():
    """Attempt to turn on the Windows Mobile Hotspot via PowerShell."""
    if not sys.platform.startswith("win"):
        print("[INFO] Auto hotspot is Windows-only. Turn it on manually.")
        return

    ps_script = r'''
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    Function Await($WinRtTask, $ResultType) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
        $netTask.Result
    }
    try {
        $profile = [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
        $tm = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($profile)
        if ($tm.TetheringOperationalState -eq 1) {
            Write-Output "Hotspot already ON"
        } else {
            Await ($tm.StartTetheringAsync()) ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]) | Out-Null
            Write-Output "Hotspot turned ON"
        }
    } catch {
        Write-Output "Could not start hotspot automatically: $($_.Exception.Message)"
    }
    '''
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=30,
        )
        msg = (result.stdout or result.stderr).strip()
        print(f"[HOTSPOT] {msg}")
    except Exception as e:
        print(f"[HOTSPOT] Failed: {e}. Turn the hotspot on manually.")


def get_local_ip():
    """Return the LAN/hotspot IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def get_hotspot_ip():
    """
    Find the Windows hotspot adapter IP (usually 192.168.137.1).
    Returns None if not found.
    """
    if not sys.platform.startswith("win"):
        return None
    try:
        out = subprocess.run(
            ["ipconfig"], capture_output=True, text=True, timeout=10
        ).stdout
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("IPv4") and "192.168.137." in line:
                return line.split(":")[-1].strip()
    except Exception:
        pass
    return None


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("        LAPTOP CAMERA LIVE STREAM")
    print("=" * 55)

    turn_on_hotspot()

    lan_ip = get_local_ip()
    hotspot_ip = get_hotspot_ip()

    print("\n  Stream is starting...")
    print("  Connect your phone / other laptop to this laptop's hotspot,")
    print("  then open ONE of these URLs in a browser:\n")
    print(f"     ->  http://{lan_ip}:{PORT}")
    if hotspot_ip and hotspot_ip != lan_ip:
        print(f"     ->  http://{hotspot_ip}:{PORT}   (hotspot devices)")
    print(f"\n  On this laptop you can also use: http://localhost:{PORT}")
    print("\n  Press CTRL+C to stop.")
    print("=" * 55 + "\n")

    try:
        app.run(host="0.0.0.0", port=PORT, threaded=True)
    finally:
        camera.release()
