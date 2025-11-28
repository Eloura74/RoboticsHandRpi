import cv2
import mediapipe as mp
import socket
import json
import time
import math
import threading
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# ---------------------------------------
# CONFIGURATION
# ---------------------------------------

UDP_IP = "192.168.1.60"    # IP du Raspberry Pi
UDP_PORT = 5005
STREAM_PORT = 8090

# Seuils GÉNÉRAUX (index, majeur, annulaire, auriculaire)
THRESHOLD_OPEN = 1.8
THRESHOLD_CLOSED = 0.9

# Seuils SPÉCIAUX pour le pouce (distance plus faible)
THUMB_THRESHOLD_OPEN = 1.30
THUMB_THRESHOLD_CLOSED = 0.70

# Stabilisation sécurité au démarrage
STARTUP_STABLE_FRAMES = 30     # nombre d'images consécutives main ouverte
STARTUP_DELAY_MS = 2000        # délai minimum avant de démarrer la stabilisation
OPEN_THRESHOLD_CHECK = 0.30    # toutes les valeurs doigts doivent être < à ça

# Globals
frame_to_stream = None
lock = threading.Lock()
is_stabilized = False
stable_frame_count = 0
startup_time = time.time()

last_sent_values = {
    "pouce_articulation": 0.0,
    "index": 0.0,
    "majeur": 0.0,
    "annulaire_auriculaire": 0.0
}
last_visible_state = False  # pour éviter d'envoyer 1000 fois le même flag

# ---------------------------------------
# SERVER MJPG STREAM
# ---------------------------------------

class CamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # On supprime les logs HTTP verbeux
        pass

    def do_GET(self):
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()

            while True:
                with lock:
                    if frame_to_stream is None:
                        time.sleep(0.01)
                        continue
                    img = frame_to_stream.copy()

                ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                if not ret:
                    continue

                try:
                    self.wfile.write(b"--jpgboundary\r\n")
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-length', str(len(jpeg)))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b"\r\n")
                except:
                    break

                time.sleep(0.03)
        else:
            self.send_response(404)
            self.end_headers()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


def start_stream_server():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', STREAM_PORT), CamHandler)
        print(f"[VIDEO] Serveur MJPG sur {STREAM_PORT}")
        server.serve_forever()
    except OSError as e:
        print(f"[CRITICAL] Port {STREAM_PORT} occupé : {e}")
        print("SOLUTION suggérée : taskkill /F /IM python.exe (sous Windows)")
        sys.exit(1)

# ---------------------------------------
# MEDIAPIPE
# ---------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

# ---------------------------------------
# ENVOI UDP
# ---------------------------------------

def send_packet(payload: dict):
    """Envoi UDP vers le Raspberry en JSON."""
    try:
        sock.sendto(json.dumps(payload).encode("utf-8"), (UDP_IP, UDP_PORT))
    except Exception as e:
        print(f"[UDP-ERR] {e}")


def send_visible_flag(visible: bool):
    """Envoie uniquement un flag visible/tracking, sans valeurs de doigts."""
    global last_visible_state

    # Évite de spammer si l'état ne change pas
    if visible == last_visible_state:
        return

    packet = {
        "visible": bool(visible),
        "tracking": bool(visible)
    }
    print(f"[UDP] visible={packet['visible']} tracking={packet['tracking']}")
    send_packet(packet)
    last_visible_state = visible


# ---------------------------------------
# MAIN LOOP
# ---------------------------------------

def main():
    global frame_to_stream, is_stabilized, stable_frame_count, startup_time, last_sent_values

    print("[INIT] Démarrage du hand_tracker avec stabilisation sécurisée...")

    # Thread vidéo MJPEG
    t = threading.Thread(target=start_stream_server, daemon=True)
    t.start()
    time.sleep(1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Caméra introuvable")
        return

    print(f"[UDP] Envoi vers {UDP_IP}:{UDP_PORT}")

    tips_ids = {
        "pouce": mp_hands.HandLandmark.THUMB_TIP,
        "index": mp_hands.HandLandmark.INDEX_FINGER_TIP,
        "majeur": mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        "annulaire": mp_hands.HandLandmark.RING_FINGER_TIP,
        "auriculaire": mp_hands.HandLandmark.PINKY_TIP,
    }

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            h, w, _ = frame.shape

            # Valeurs par défaut : main ouverte (0.0 = ouvert côté robot)
            final_states = {
                "pouce_articulation": 0.0,
                "index": 0.0,
                "majeur": 0.0,
                "annulaire_auriculaire": 0.0
            }

            hand_detected = False

            if results.multi_hand_landmarks:
                hand_detected = True

                for lm in results.multi_hand_landmarks:

                    mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

                    allp = lm.landmark
                    wrist = allp[mp_hands.HandLandmark.WRIST]
                    ref = allp[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                    palm = get_distance(wrist, ref)

                    # ---- CALCUL PAR DOIGT ----
                    for dname, tid in tips_ids.items():
                        tip = allp[tid]
                        ratio = get_distance(wrist, tip) / palm

                        # Seuils dédiés pour le pouce
                        if dname == "pouce":
                            t_open = THUMB_THRESHOLD_OPEN
                            t_closed = THUMB_THRESHOLD_CLOSED
                        else:
                            t_open = THRESHOLD_OPEN
                            t_closed = THRESHOLD_CLOSED

                        # Conversion ratio → 0..1 (1 = doigt très ouvert côté humain)
                        if ratio >= t_open:
                            val = 1.0
                        elif ratio <= t_closed:
                            val = 0.0
                        else:
                            val = (ratio - t_closed) / (t_open - t_closed)

                        # Inversion (0 = ouvert côté robot, 1 = fermé)
                        mapped = 1.0 - val

                        # Mapping dans final_states
                        if dname == "pouce":
                            final_states["pouce_articulation"] = mapped
                        elif dname == "index":
                            final_states["index"] = mapped
                        elif dname == "majeur":
                            final_states["majeur"] = mapped
                        elif dname in ("annulaire", "auriculaire"):
                            # On prend le max des deux pour annulaire+auriculaire groupés
                            final_states["annulaire_auriculaire"] = max(
                                final_states["annulaire_auriculaire"], mapped
                            )

                # ---- STABILISATION AU DÉMARRAGE ----
                elapsed = (time.time() - startup_time) * 1000

                if not is_stabilized:
                    if elapsed > STARTUP_DELAY_MS:
                        # On considère la main "ouverte" si tous les doigts < OPEN_THRESHOLD_CHECK
                        if all(v < OPEN_THRESHOLD_CHECK for v in final_states.values()):
                            stable_frame_count += 1
                            if stable_frame_count >= STARTUP_STABLE_FRAMES:
                                is_stabilized = True
                                print("[READY] Main ouverte stabilisée ! Tracking actif.")
                                # Informer le RPi que le tracking démarre
                                send_visible_flag(True)
                        else:
                            stable_frame_count = 0

                    remaining = max(0, STARTUP_STABLE_FRAMES - stable_frame_count)
                    cv2.putText(frame, f"MAIN OUVERTE REQUISE: {remaining}",
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 165, 255), 2)

                else:
                    # Tracking actif + main détectée
                    cv2.putText(frame, "TRACKING ACTIF",
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2)

                    # Paquet complet vers le RPi
                    packet = {
                        "pouce_articulation": final_states["pouce_articulation"],
                        "index": final_states["index"],
                        "majeur": final_states["majeur"],
                        "annulaire_auriculaire": final_states["annulaire_auriculaire"],
                        "visible": True,
                        "tracking": True
                    }
                    send_packet(packet)
                    last_sent_values = final_states.copy()
                    last_visible_state = True

            else:
                # Aucune main détectée
                stable_frame_count = 0
                cv2.putText(frame, "EN ATTENTE DE MAIN...",
                            (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 165, 255), 2)

                if is_stabilized:
                    # Si on a déjà été en mode tracking et que la main disparait,
                    # on informe explicitement le RPi -> ouverture de sécurité.
                    send_visible_flag(False)

            # Mise à jour de l'image pour le stream MJPG
            with lock:
                frame_to_stream = frame

            cv2.imshow("DEBUG LOCAL", frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    except Exception as e:
        print(f"[CRASH] {e}")

    finally:
        # À la fin, on informe explicitement le RPi que le tracking est arrêté
        try:
            send_visible_flag(False)
        except Exception as e:
            print(f"[WARN] Impossible d'envoyer le flag de fin : {e}")

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()




# import cv2
# import mediapipe as mp
# import socket
# import json
# import time
# import math
# import threading
# import sys
# from http.server import BaseHTTPRequestHandler, HTTPServer
# from socketserver import ThreadingMixIn

# # ---------------------------------------
# # CONFIGURATION
# # ---------------------------------------

# UDP_IP = "192.168.1.60"    # IP du Raspberry Pi
# UDP_PORT = 5005
# STREAM_PORT = 8090

# # Seuils GÉNÉRAUX (index, majeur, annulaire, auriculaire)
# THRESHOLD_OPEN = 1.8
# THRESHOLD_CLOSED = 0.9

# # Seuils SPÉCIAUX pour le pouce (distance plus faible)
# THUMB_THRESHOLD_OPEN = 1.30
# THUMB_THRESHOLD_CLOSED = 0.70

# # Stabilisation sécurité au démarrage
# STARTUP_STABLE_FRAMES = 30
# STARTUP_DELAY_MS = 2000
# OPEN_THRESHOLD_CHECK = 0.30

# # Globals
# frame_to_stream = None
# lock = threading.Lock()
# is_stabilized = False
# stable_frame_count = 0
# startup_time = time.time()
# last_sent_values = {
#     "pouce_articulation":0.0,
#     "index":0.0,
#     "majeur":0.0,
#     "annulaire_auriculaire":0.0
# }

# # ---------------------------------------
# # SERVER MJPG STREAM
# # ---------------------------------------

# class CamHandler(BaseHTTPRequestHandler):
#     def log_message(self, format, *args):
#         pass

#     def do_GET(self):
#         if self.path.endswith('.mjpg'):
#             self.send_response(200)
#             self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
#             self.end_headers()

#             while True:
#                 with lock:
#                     if frame_to_stream is None:
#                         time.sleep(0.01)
#                         continue
#                     img = frame_to_stream.copy()

#                 ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
#                 if not ret:
#                     continue

#                 try:
#                     self.wfile.write(b"--jpgboundary\r\n")
#                     self.send_header('Content-Type', 'image/jpeg')
#                     self.send_header('Content-length', str(len(jpeg)))
#                     self.end_headers()
#                     self.wfile.write(jpeg.tobytes())
#                     self.wfile.write(b"\r\n")
#                 except:
#                     break

#                 time.sleep(0.03)
#         else:
#             self.send_response(404)
#             self.end_headers()

# class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
#     pass

# def start_stream_server():
#     try:
#         server = ThreadedHTTPServer(('0.0.0.0', STREAM_PORT), CamHandler)
#         print(f"[VIDEO] Serveur MJPG sur {STREAM_PORT}")
#         server.serve_forever()
#     except OSError as e:
#         print(f"[CRITICAL] Port {STREAM_PORT} occupé : {e}")
#         print("SOLUTION : taskkill /F /IM python.exe")
#         sys.exit(1)

# # ---------------------------------------
# # MEDIAPIPE
# # ---------------------------------------

# mp_hands = mp.solutions.hands
# mp_draw = mp.solutions.drawing_utils
# hands = mp_hands.Hands(
#     max_num_hands=1,
#     min_detection_confidence=0.7,
#     min_tracking_confidence=0.5
# )

# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# def get_distance(p1, p2):
#     return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

# # ---------------------------------------
# # MAIN LOOP
# # ---------------------------------------

# def main():
#     global frame_to_stream, is_stabilized, stable_frame_count, startup_time

#     print("[INIT] Démarrage avec stabilisation sécurisée...")

#     # Thread vidéo
#     t = threading.Thread(target=start_stream_server, daemon=True)
#     t.start()
#     time.sleep(1)

#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("[ERROR] Caméra introuvable")
#         return

#     print(f"[UDP] Envoi vers {UDP_IP}:{UDP_PORT}")

#     tips_ids = {
#         "pouce": mp_hands.HandLandmark.THUMB_TIP,
#         "index": mp_hands.HandLandmark.INDEX_FINGER_TIP,
#         "majeur": mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
#         "annulaire": mp_hands.HandLandmark.RING_FINGER_TIP,
#         "auriculaire": mp_hands.HandLandmark.PINKY_TIP,
#     }

#     try:
#         while True:
#             ok, frame = cap.read()
#             if not ok:
#                 continue

#             frame = cv2.flip(frame, 1)
#             rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = hands.process(rgb)

#             h, w, _ = frame.shape
#             final_states = {
#                 "pouce_articulation": 0.0,
#                 "index": 0.0,
#                 "majeur": 0.0,
#                 "annulaire_auriculaire": 0.0
#             }

#             if results.multi_hand_landmarks:
#                 for lm in results.multi_hand_landmarks:

#                     mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

#                     allp = lm.landmark
#                     wrist = allp[mp_hands.HandLandmark.WRIST]
#                     ref = allp[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
#                     palm = get_distance(wrist, ref)

#                     # ---- CALCUL PAR DOIGT ----
#                     for dname, tid in tips_ids.items():
#                         tip = allp[tid]
#                         ratio = get_distance(wrist, tip) / palm

#                         # Seuils dédiés pour le pouce
#                         if dname == "pouce":
#                             t_open = THUMB_THRESHOLD_OPEN
#                             t_closed = THUMB_THRESHOLD_CLOSED
#                         else:
#                             t_open = THRESHOLD_OPEN
#                             t_closed = THRESHOLD_CLOSED

#                         # Conversion ratio → 0..1
#                         if ratio >= t_open:
#                             val = 1.0
#                         elif ratio <= t_closed:
#                             val = 0.0
#                         else:
#                             val = (ratio - t_closed) / (t_open - t_closed)

#                         # Inversion (0 = ouvert)
#                         mapped = 1.0 - val

#                         # Mapping dans final_states
#                         if dname == "pouce":
#                             final_states["pouce_articulation"] = mapped
#                         elif dname == "index":
#                             final_states["index"] = mapped
#                         elif dname == "majeur":
#                             final_states["majeur"] = mapped
#                         elif dname in ("annulaire", "auriculaire"):
#                             final_states["annulaire_auriculaire"] = max(
#                                 final_states["annulaire_auriculaire"], mapped
#                             )

#                     # ---- STABILISATION ----
#                     elapsed = (time.time() - startup_time) * 1000

#                     if not is_stabilized:
#                         if elapsed > STARTUP_DELAY_MS:
#                             if all(v < OPEN_THRESHOLD_CHECK for v in final_states.values()):
#                                 stable_frame_count += 1
#                                 if stable_frame_count >= STARTUP_STABLE_FRAMES:
#                                     is_stabilized = True
#                                     print("[READY] Main ouverte stabilisée ! Tracking actif.")
#                             else:
#                                 stable_frame_count = 0

#                         remaining = max(0, STARTUP_STABLE_FRAMES - stable_frame_count)
#                         cv2.putText(frame, f"MAIN OUVERTE REQUISE: {remaining}",
#                                     (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
#                                     (0, 165, 255), 2)
#                     else:
#                         cv2.putText(frame, "TRACKING ACTIF",
#                                     (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
#                                     (0, 255, 0), 2)

#                         sock.sendto(json.dumps(final_states).encode(),
#                                     (UDP_IP, UDP_PORT))
#             else:
#                 stable_frame_count = 0
#                 cv2.putText(frame, "EN ATTENTE DE MAIN...",
#                             (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
#                             (0, 165, 255), 2)

#             with lock:
#                 frame_to_stream = frame

#             cv2.imshow("DEBUG LOCAL", frame)
#             if cv2.waitKey(1) & 0xFF == 27:
#                 break

#     except Exception as e:
#         print(f"[CRASH] {e}")

#     finally:
#         cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()
