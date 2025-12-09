import cv2
import mediapipe as mp
import socket
import json
import time
import math
import threading
import sys
import numpy as np
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
STARTUP_STABLE_FRAMES = 30
STARTUP_DELAY_MS = 2000
OPEN_THRESHOLD_CHECK = 0.30

# ⭐ PARAMÈTRES VISUELS FUTURISTES
ENABLE_HAND_MASK = True           # True = masque activé
MASK_MARGIN = 40                  # Marge autour de la main (pixels)

# Palette de couleurs cyber/tech (BGR format pour OpenCV)
COLOR_CYAN = (255, 255, 0)        # Cyan néon principal
COLOR_CYAN_DARK = (180, 120, 0)   # Cyan foncé
COLOR_BG_DARK = (20, 10, 5)       # Fond noir-bleuté
COLOR_GLOW = (255, 200, 0)        # Couleur du glow (cyan clair)

# Paramètres effets visuels
GLOW_INTENSITY = 0.6              # Intensité du glow autour de la main (0.0 à 1.0)
GLOW_RADIUS = 25                  # Rayon du blur pour l'effet glow
EDGE_THICKNESS = 2                # Épaisseur du contour néon
GRADIENT_ENABLED = True           # Activer le dégradé radial de fond
SCANLINE_ENABLED = True           # Activer les lignes de scan animées

# Globals
frame_to_stream = None
lock = threading.Lock()
is_stabilized = False
stable_frame_count = 0
startup_time = time.time()
scanline_offset = 0               # Offset pour animation scanlines

last_sent_values = {
    "pouce_articulation": 0.0,
    "index": 0.0,
    "majeur": 0.0,
    "annulaire_auriculaire": 0.0
}
last_visible_state = False

# ---------------------------------------
# SERVER MJPG STREAM
# ---------------------------------------

class CamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Supprime les logs HTTP verbeux
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

                # Qualité JPEG augmentée pour meilleur rendu (70 = bon compromis)
                ret, jpeg = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
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
    """Démarre le serveur MJPG pour streamer la vidéo sur le réseau."""
    try:
        server = ThreadedHTTPServer(('0.0.0.0', STREAM_PORT), CamHandler)
        print(f"[VIDEO] Serveur MJPG sur port {STREAM_PORT}")
        server.serve_forever()
    except OSError as e:
        print(f"[CRITICAL] Port {STREAM_PORT} occupé : {e}")
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
    """Calcule la distance euclidienne entre deux landmarks MediaPipe."""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

# ---------------------------------------
# FONCTIONS VISUELLES PREMIUM
# ---------------------------------------

def create_radial_gradient(h, w, center, color_inner, color_outer):
    """
    Crée un dégradé radial du centre vers l'extérieur.
    Utilisé pour créer un fond futuriste avec point lumineux central.
    
    Args:
        h, w: dimensions de l'image
        center: tuple (x, y) du centre du dégradé
        color_inner: couleur BGR au centre
        color_outer: couleur BGR aux bords
    
    Returns:
        Image BGR avec dégradé radial
    """
    gradient = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Calculer les distances depuis le centre
    y_indices, x_indices = np.ogrid[:h, :w]
    distances = np.sqrt((x_indices - center[0])**2 + (y_indices - center[1])**2)
    max_distance = np.sqrt(center[0]**2 + center[1]**2)
    
    # Normaliser les distances (0 à 1)
    normalized = np.clip(distances / max_distance, 0, 1)
    
    # Interpoler les couleurs
    for i in range(3):
        gradient[:, :, i] = (
            color_inner[i] * (1 - normalized) + 
            color_outer[i] * normalized
        ).astype(np.uint8)
    
    return gradient


def create_hand_mask_advanced(frame, hand_landmarks):
    """
    Crée un masque premium avec contour précis de la main.
    Utilise convex hull avec marge et flou pour des bords doux.
    
    Args:
        frame: image source
        hand_landmarks: landmarks MediaPipe de la main
    
    Returns:
        Masque binaire (0-255) avec la zone de la main
    """
    h, w, _ = frame.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Récupérer tous les points landmarks de la main (21 points)
    points = []
    for lm in hand_landmarks.landmark:
        x = int(lm.x * w)
        y = int(lm.y * h)
        points.append([x, y])
    
    # Créer l'enveloppe convexe (contour englobant la main)
    points_np = np.array(points, dtype=np.int32)
    hull = cv2.convexHull(points_np)
    
    # Dilater le hull pour ajouter une marge élégante autour de la main
    hull_expanded = hull.copy()
    center = hull.mean(axis=0).astype(int)
    
    for i in range(len(hull_expanded)):
        direction = hull_expanded[i][0] - center
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm
            hull_expanded[i][0] = hull_expanded[i][0] + (direction * MASK_MARGIN).astype(int)
    
    # Dessiner le polygone rempli sur le masque
    cv2.fillConvexPoly(mask, hull_expanded, 255)
    
    # Flou gaussien pour adoucir les bords (effet plus naturel)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)
    
    return mask, hull_expanded


def add_neon_glow(image, mask, glow_color, intensity, radius):
    """
    Ajoute un effet de glow/lueur néon autour des zones masquées.
    Simule une lumière cyan rayonnante autour de la main.
    
    Args:
        image: image BGR de base
        mask: masque binaire de la zone à illuminer
        glow_color: couleur BGR du glow
        intensity: intensité de l'effet (0.0 à 1.0)
        radius: rayon du blur pour l'effet glow
    
    Returns:
        Image avec effet glow appliqué
    """
    # Créer une couche de glow
    glow_layer = np.zeros_like(image)
    glow_layer[:] = glow_color
    
    # Appliquer le masque au glow
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    glow_layer = cv2.bitwise_and(glow_layer, mask_3ch)
    
    # Blur intense pour créer l'effet de rayonnement
    glow_blurred = cv2.GaussianBlur(glow_layer, (radius*2+1, radius*2+1), 0)
    
    # Mélanger avec l'image originale
    result = cv2.addWeighted(image, 1.0, glow_blurred, intensity, 0)
    
    return result


def add_edge_highlight(image, hull, color, thickness):
    """
    Dessine un contour néon lumineux sur les bords de la main.
    Crée l'effet de "bordure holographique".
    
    Args:
        image: image BGR de destination
        hull: points du convex hull (contour de la main)
        color: couleur BGR du contour
        thickness: épaisseur de la ligne
    """
    cv2.drawContours(image, [hull], 0, color, thickness, cv2.LINE_AA)


def add_scanlines(image, offset, spacing=4, alpha=0.15):
    """
    Ajoute des lignes de scan horizontales animées (effet CRT/terminal).
    Simule un affichage holographique ou un écran de monitoring.
    
    Args:
        image: image BGR
        offset: décalage vertical pour l'animation
        spacing: espacement entre les lignes
        alpha: transparence des lignes (0.0 à 1.0)
    """
    h, w = image.shape[:2]
    overlay = image.copy()
    
    # Dessiner des lignes horizontales fines
    for y in range(int(offset) % spacing, h, spacing):
        cv2.line(overlay, (0, y), (w, y), COLOR_CYAN_DARK, 1, cv2.LINE_AA)
    
    # Mélanger avec alpha blending
    cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)


def apply_futuristic_hand_rendering(frame, hand_landmarks):
    """
    Pipeline complet de rendu futuriste de la main.
    Applique tous les effets visuels : masque, glow, contours, scanlines, etc.
    
    Args:
        frame: image source de la caméra
        hand_landmarks: landmarks MediaPipe
    
    Returns:
        Image stylisée avec effets futuristes
    """
    h, w, _ = frame.shape
    
    # 1. Créer le masque de la main avec contour précis
    mask, hull = create_hand_mask_advanced(frame, hand_landmarks)
    
    # 2. Créer le fond avec dégradé radial (effet spot lumineux)
    if GRADIENT_ENABLED:
        # Centre du dégradé = centre de la main
        center_x = int(np.mean([lm.x for lm in hand_landmarks.landmark]) * w)
        center_y = int(np.mean([lm.y for lm in hand_landmarks.landmark]) * h)
        background = create_radial_gradient(h, w, (center_x, center_y), 
                                           (40, 30, 15), COLOR_BG_DARK)
    else:
        background = np.full_like(frame, COLOR_BG_DARK, dtype=np.uint8)
    
    # 3. Extraire la main de la frame originale
    mask_norm = mask.astype(float) / 255.0
    mask_3ch = np.stack([mask_norm] * 3, axis=-1)
    
    # Appliquer légère correction colorimétrique cyan sur la main
    hand_colored = frame.copy().astype(float)
    hand_colored[:, :, 0] += 15  # Boost canal bleu
    hand_colored[:, :, 1] += 10  # Boost canal vert
    hand_colored = np.clip(hand_colored, 0, 255).astype(np.uint8)
    
    # Composite : main + fond
    result = (hand_colored * mask_3ch + background * (1 - mask_3ch)).astype(np.uint8)
    
    # 4. Ajouter effet glow cyan autour de la main
    if GLOW_INTENSITY > 0:
        result = add_neon_glow(result, mask, COLOR_GLOW, GLOW_INTENSITY, GLOW_RADIUS)
    
    # 5. Dessiner contour néon sur les bords de la main
    if EDGE_THICKNESS > 0:
        add_edge_highlight(result, hull, COLOR_CYAN, EDGE_THICKNESS)
    
    # 6. Ajouter scanlines animées pour effet tech
    global scanline_offset
    if SCANLINE_ENABLED:
        add_scanlines(result, scanline_offset)
        scanline_offset += 0.5  # Vitesse d'animation
    
    return result


def draw_custom_landmarks(image, hand_landmarks):
    """
    Dessine les landmarks de la main avec un style futuriste personnalisé.
    Remplace le dessin par défaut de MediaPipe par un rendu cyan néon.
    
    Args:
        image: image de destination
        hand_landmarks: landmarks MediaPipe
    """
    h, w, _ = image.shape
    
    # Dessiner les connexions (os de la main) en cyan
    connections = mp_hands.HAND_CONNECTIONS
    for connection in connections:
        start_idx = connection[0]
        end_idx = connection[1]
        
        start = hand_landmarks.landmark[start_idx]
        end = hand_landmarks.landmark[end_idx]
        
        start_point = (int(start.x * w), int(start.y * h))
        end_point = (int(end.x * w), int(end.y * h))
        
        # Ligne cyan avec anti-aliasing
        cv2.line(image, start_point, end_point, COLOR_CYAN, 2, cv2.LINE_AA)
    
    # Dessiner les landmarks (points articulaires) avec effet de glow
    for idx, landmark in enumerate(hand_landmarks.landmark):
        x = int(landmark.x * w)
        y = int(landmark.y * h)
        
        # Point principal cyan
        cv2.circle(image, (x, y), 5, COLOR_CYAN, -1, cv2.LINE_AA)
        
        # Petit halo autour (effet lumineux)
        cv2.circle(image, (x, y), 8, COLOR_CYAN, 1, cv2.LINE_AA)

# ---------------------------------------
# ENVOI UDP
# ---------------------------------------

def send_packet(payload: dict):
    """Envoie un paquet JSON via UDP vers le Raspberry Pi."""
    try:
        sock.sendto(json.dumps(payload).encode("utf-8"), (UDP_IP, UDP_PORT))
    except Exception as e:
        print(f"[UDP-ERR] {e}")


def send_visible_flag(visible: bool):
    """
    Envoie uniquement un flag visible/tracking au RPi.
    Évite de spammer si l'état ne change pas.
    """
    global last_visible_state

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

    print("[INIT] 🚀 Hand Tracker NEURO-HAND V2.0")
    print(f"[VISUAL] Rendu futuriste: {'✓ ACTIVÉ' if ENABLE_HAND_MASK else '✗ DÉSACTIVÉ'}")
    print(f"[VISUAL] Effets: Glow={GLOW_INTENSITY:.1f} | Edge={EDGE_THICKNESS}px | Scanlines={'ON' if SCANLINE_ENABLED else 'OFF'}")

    # Démarrage du serveur de streaming vidéo
    t = threading.Thread(target=start_stream_server, daemon=True)
    t.start()
    time.sleep(1)

    # Initialisation de la caméra
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Caméra introuvable")
        return

    print(f"[UDP] Envoi vers {UDP_IP}:{UDP_PORT}")

    # IDs des tips (bouts) des doigts pour le tracking
    tips_ids = {
        "pouce": mp_hands.HandLandmark.THUMB_TIP,
        "index": mp_hands.HandLandmark.INDEX_FINGER_TIP,
        "majeur": mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        "annulaire": mp_hands.HandLandmark.RING_FINGER_TIP,
        "auriculaire": mp_hands.HandLandmark.PINKY_TIP,
    }

    try:
        while True:
            # Capture de la frame
            ok, frame = cap.read()
            if not ok:
                continue

            # Flip horizontal pour effet miroir naturel
            frame = cv2.flip(frame, 1)
            
            # Conversion BGR -> RGB pour MediaPipe
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
            display_frame = frame.copy()

            # --- DÉTECTION DE LA MAIN ---
            if results.multi_hand_landmarks:
                hand_detected = True

                for lm in results.multi_hand_landmarks:
                    
                    # ⭐ APPLIQUER LE RENDU FUTURISTE
                    if ENABLE_HAND_MASK:
                        display_frame = apply_futuristic_hand_rendering(frame, lm)
                        # Dessiner landmarks avec style custom
                        draw_custom_landmarks(display_frame, lm)
                    else:
                        # Mode classique : juste dessiner les landmarks
                        mp_draw.draw_landmarks(display_frame, lm, mp_hands.HAND_CONNECTIONS)

                    # Récupération des landmarks pour calculs
                    allp = lm.landmark
                    wrist = allp[mp_hands.HandLandmark.WRIST]
                    ref = allp[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                    palm = get_distance(wrist, ref)

                    # ---- CALCUL DE L'ÉTAT DE CHAQUE DOIGT ----
                    for dname, tid in tips_ids.items():
                        tip = allp[tid]
                        ratio = get_distance(wrist, tip) / palm

                        # Seuils dédiés pour le pouce (morphologie différente)
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

                        # Mapping dans le dictionnaire d'états
                        if dname == "pouce":
                            final_states["pouce_articulation"] = mapped
                        elif dname == "index":
                            final_states["index"] = mapped
                        elif dname == "majeur":
                            final_states["majeur"] = mapped
                        elif dname in ("annulaire", "auriculaire"):
                            # Annulaire et auriculaire groupés (servomoteur commun)
                            final_states["annulaire_auriculaire"] = max(
                                final_states["annulaire_auriculaire"], mapped
                            )

                # ---- STABILISATION AU DÉMARRAGE (sécurité) ----
                elapsed = (time.time() - startup_time) * 1000

                if not is_stabilized:
                    # Phase de stabilisation : attendre main ouverte stable
                    if elapsed > STARTUP_DELAY_MS:
                        if all(v < OPEN_THRESHOLD_CHECK for v in final_states.values()):
                            stable_frame_count += 1
                            if stable_frame_count >= STARTUP_STABLE_FRAMES:
                                is_stabilized = True
                                print("[READY] ✓ Main ouverte stabilisée ! Tracking actif.")
                                send_visible_flag(True)
                        else:
                            stable_frame_count = 0

                    remaining = max(0, STARTUP_STABLE_FRAMES - stable_frame_count)
                    cv2.putText(display_frame, f"MAIN OUVERTE REQUISE: {remaining}",
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                COLOR_CYAN, 2, cv2.LINE_AA)

                else:
                    # Tracking actif : envoi des données
                    cv2.putText(display_frame, "TRACKING ACTIF",
                                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 0), 2, cv2.LINE_AA)

                    # Paquet complet vers le Raspberry Pi
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
                # ---- AUCUNE MAIN DÉTECTÉE ----
                stable_frame_count = 0

                # Fond stylisé si masque activé
                if ENABLE_HAND_MASK:
                    h, w = frame.shape[:2]
                    display_frame = create_radial_gradient(h, w, (w//2, h//2), 
                                                          (30, 20, 10), COLOR_BG_DARK)
                    # Ajouter scanlines même sans main
                    if SCANLINE_ENABLED:
                        add_scanlines(display_frame, scanline_offset)

                cv2.putText(display_frame, "EN ATTENTE DE MAIN...",
                            (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            COLOR_CYAN, 2, cv2.LINE_AA)

                # Si on perd la main après stabilisation, informer le RPi
                if is_stabilized:
                    send_visible_flag(False)

            # ---- MISE À JOUR DU STREAM MJPG ----
            with lock:
                frame_to_stream = display_frame

            # Affichage local pour debug
            cv2.imshow("DEBUG LOCAL", display_frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC pour quitter
                break

    except Exception as e:
        print(f"[CRASH] {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Nettoyage à la sortie
        try:
            send_visible_flag(False)
        except Exception as e:
            print(f"[WARN] Impossible d'envoyer le flag de fin : {e}")

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
