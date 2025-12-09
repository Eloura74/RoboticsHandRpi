#!/usr/bin/env python3
"""
Serveur MJPEG pour la webcam locale du Raspberry Pi.
Stream la webcam via HTTP sur le port 8091 pour affichage dans le dashboard.

Usage:
    python apps/camera/rpi_camera_server.py
    
URL du stream:
    http://192.168.1.60:8091/stream.mjpg
"""

import cv2
import time
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# ---------------------------------------
# CONFIGURATION
# ---------------------------------------

STREAM_PORT = 8091              # Port du serveur MJPEG (différent du hand tracker)
CAMERA_DEVICE = 0               # Device de la webcam (/dev/video0)
JPEG_QUALITY = 70               # Qualité JPEG (0-100, 70 = bon compromis)
STREAM_FPS = 30                 # FPS souhaité pour le stream
FRAME_DELAY = 1.0 / STREAM_FPS  # Délai entre frames

# Résolution de la webcam (optionnel, auto-détection par défaut)
CAMERA_WIDTH = 640              # Largeur (640x480 = VGA)
CAMERA_HEIGHT = 480             # Hauteur

# Globals
frame_to_stream = None          # Frame actuelle à streamer
lock = threading.Lock()         # Lock pour accès thread-safe à la frame

# ---------------------------------------
# SERVEUR MJPEG
# ---------------------------------------

class CamHandler(BaseHTTPRequestHandler):
    """
    Handler HTTP pour servir le flux MJPEG.
    Répond aux requêtes GET sur /stream.mjpg.
    """
    
    def log_message(self, format, *args):
        """Supprime les logs HTTP verbeux."""
        pass

    def do_GET(self):
        """
        Gère les requêtes GET.
        - /stream.mjpg : Stream MJPEG multipart
        - Autre : Erreur 404
        """
        if self.path.endswith('.mjpg') or self.path.endswith('/stream.mjpg'):
            # Headers pour stream MJPEG multipart
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            # Boucle de streaming
            while True:
                # Récupération thread-safe de la frame
                with lock:
                    if frame_to_stream is None:
                        time.sleep(0.01)
                        continue
                    img = frame_to_stream.copy()

                # Encodage JPEG avec qualité configurée
                ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                if not ret:
                    continue

                # Envoi de la frame JPEG au client
                try:
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-length', str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b"\r\n")
                except:
                    # Client déconnecté
                    break

                # Délai pour maintenir le FPS cible
                time.sleep(FRAME_DELAY)
        else:
            # Route non trouvée
            self.send_response(404)
            self.end_headers()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Serveur HTTP multithread pour gérer plusieurs clients simultanément."""
    pass


def start_stream_server():
    """
    Démarre le serveur HTTP MJPEG.
    Bloque le thread courant (à lancer dans un thread séparé).
    """
    try:
        server = ThreadedHTTPServer(('0.0.0.0', STREAM_PORT), CamHandler)
        print(f"[CAMERA] 📡 Serveur MJPEG démarré sur port {STREAM_PORT}")
        print(f"[CAMERA] 🌐 URL: http://192.168.1.60:{STREAM_PORT}/stream.mjpg")
        server.serve_forever()
    except OSError as e:
        print(f"[CRITICAL] ❌ Port {STREAM_PORT} déjà occupé : {e}")
        print(f"[SOLUTION] Arrêter le processus existant ou changer le port")
        sys.exit(1)


# ---------------------------------------
# CAPTURE WEBCAM
# ---------------------------------------

def capture_loop():
    """
    Boucle de capture de la webcam.
    Lit les frames et les stocke dans la variable globale pour le streaming.
    """
    global frame_to_stream

    print("[CAMERA] 🎥 Initialisation de la webcam...")
    
    # Ouverture de la webcam
    cap = cv2.VideoCapture(CAMERA_DEVICE)
    if not cap.isOpened():
        print(f"[ERROR] ❌ Impossible d'ouvrir la webcam sur /dev/video{CAMERA_DEVICE}")
        print("[SOLUTION] Vérifier la connexion USB et les permissions")
        sys.exit(1)

    # Configuration de la résolution (optionnel)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, STREAM_FPS)

    # Affichage de la configuration réelle
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"[CAMERA] ✓ Webcam ouverte : {actual_width}x{actual_height} @ {actual_fps} FPS")
    print(f"[CAMERA] ✓ Qualité JPEG : {JPEG_QUALITY}%")
    print("[CAMERA] ✓ Capture démarrée\n")

    try:
        while True:
            # Lecture d'une frame
            ret, frame = cap.read()
            if not ret:
                print("[WARNING] ⚠️ Impossible de lire la frame webcam")
                time.sleep(0.1)
                continue

            # Flip horizontal pour effet miroir naturel (optionnel)
            frame = cv2.flip(frame, 1)

            # Ajout d'un overlay de label (optionnel)
            cv2.putText(
                frame, 
                "RPi WEBCAM - CAM-02",
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6,
                (0, 255, 255),  # Cyan
                2,
                cv2.LINE_AA
            )

            # Timestamp en bas à droite (optionnel)
            timestamp = time.strftime("%H:%M:%S")
            cv2.putText(
                frame,
                timestamp,
                (actual_width - 100, actual_height - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),  # Cyan
                1,
                cv2.LINE_AA
            )

            # Mise à jour thread-safe de la frame globale
            with lock:
                frame_to_stream = frame

            # Petit délai pour ne pas saturer le CPU
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[CAMERA] ⏹️  Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"[ERROR] ❌ Erreur dans la boucle de capture : {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Libération de la webcam
        cap.release()
        print("[CAMERA] ✓ Webcam libérée")


# ---------------------------------------
# MAIN
# ---------------------------------------

def main():
    """
    Point d'entrée principal.
    Lance le serveur HTTP et la boucle de capture en threads séparés.
    """
    print("=" * 60)
    print("  NEURO-HAND V2.0 - Serveur Webcam RPi")
    print("=" * 60)
    print()

    # Lancement du serveur HTTP dans un thread daemon
    server_thread = threading.Thread(target=start_stream_server, daemon=True)
    server_thread.start()
    
    # Petit délai pour s'assurer que le serveur démarre
    time.sleep(1)

    # Lancement de la boucle de capture (bloquant)
    capture_loop()


if __name__ == "__main__":
    main()
