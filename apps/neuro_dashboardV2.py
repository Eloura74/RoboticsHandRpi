import sys

import json

import socket

import time

import threading

import os

import signal

import math

import traceback

from pathlib import Path

from nicegui import ui, app



# --------------------------------------------------------------------

# 1. SETUP & IMPORTS

# --------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:

    sys.path.insert(0, str(BASE_DIR))



# Import réel du contrôleur matériel

try:

    from core.hand_controller import HandController

except ImportError:

    # Stub de secours pour développement sans matériel

    class HandController:

        def open_hand(self, parallel=True): pass

        def close_hand(self, parallel=True): pass

        def open_finger(self, f, parallel=False): pass

        def close_finger(self, f, parallel=False): pass

        def stop_all(self): pass

        def shutdown(self): pass

        def thumb_rotation_step(self, direction: int): pass

        def thumb_rotation_reset(self): pass

        def thumb_from_value(self, value: float): pass  # important pour le pouce



# Styles NiceGUI (CSS + structure 3D)

try:

    from apps.styles.dashboard_stylesV2 import CSS_STYLE, HAND_3D_STRUCTURE, HAND_3D_JS

except ImportError:

    print("[ERROR] Cannot import dashboard styles")

    sys.exit(1)



# --------------------------------------------------------------------

# 2. CONFIGURATION

# --------------------------------------------------------------------

PC_IP = '192.168.1.10'

MJPEG_PORT = 8090

MJPEG_URL = f'http://{PC_IP}:{MJPEG_PORT}/cam.mjpg'



UDP_IP = '0.0.0.0'

UDP_PORT = 5005

LOST_TIMEOUT = 2.0



# Seuils d’ouverture/fermeture (comme avant, juste centralisés)

OPEN_THRESHOLD = 0.3

CLOSE_THRESHOLD = 0.7



# Doigts pilotés en servos continus

FINGERS = ['pouce_articulation', 'index', 'majeur', 'annulaire_auriculaire']



controller = None





def get_local_ip() -> str:

    """Retourne l'IP locale du Raspberry Pi (pour l'affichage des infos UDP)."""

    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "127.0.0.1"





LOCAL_IP = get_local_ip()



# --------------------------------------------------------------------

# 3. GESTION ÉTAT & SÉCURITÉ

# --------------------------------------------------------------------

state_lock = threading.Lock()

state = {

    'values': {f: 0.0 for f in FINGERS},

    'udp_connected': False,

    'fps': 0,

    'packet_count': 0,

    'simu_mode': False,

}





def signal_handler(signum, frame):

    """Arrêt propre quand on tue le process (Ctrl+C / SIGTERM)."""

    print("\n[SYSTEM] Shutdown sequence initiated...")

    try:

        if controller:

            # On passe par la séquence d'arrêt propre du HandController

            controller.shutdown()

    except Exception as e:

        print(f"[SYSTEM] Erreur lors du shutdown contrôleur: {e}")

    app.shutdown()

    sys.exit(0)





# --------------------------------------------------------------------

# 3.1 Thread UDP : réception des valeurs doigts 0..1

# --------------------------------------------------------------------

def receiver_thread():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if hasattr(socket, 'SO_REUSEPORT'):

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        sock.bind((UDP_IP, UDP_PORT))

        sock.setblocking(False)

        print(f"[UDP] Thread UDP démarré - écoute sur {UDP_IP}:{UDP_PORT}")

        print(f"[UDP] IP locale du Raspberry Pi: {LOCAL_IP}")

        print(f"[UDP] Le PC doit envoyer les données UDP à: {LOCAL_IP}:{UDP_PORT}")

    except Exception as e:

        print(f"[ERROR] Impossible de démarrer le thread UDP: {e}")

        return



    packet_cnt = 0

    t0 = time.time()

    last_rx = time.time()

    rx_count = 0



    while True:

        now = time.time()



        # Détection de perte de signal

        if state['udp_connected'] and (now - last_rx > LOST_TIMEOUT):

            print(f"[UDP] TIMEOUT - Pas de données depuis {LOST_TIMEOUT}s. Déconnexion.")

            with state_lock:

                state['udp_connected'] = False



        data = None

        # On vide le buffer UDP pour garder le dernier paquet reçu

        try:

            while True:

                chunk, _ = sock.recvfrom(4096)

                data = chunk

        except Exception:

            pass



        if data:

            last_rx = now

            packet_cnt += 1

            rx_count += 1



            # Calcul "FPS" UDP

            if now - t0 > 1.0:

                with state_lock:

                    state['fps'] = packet_cnt

                print(f"[UDP] {packet_cnt} paquets/sec reçus (total: {rx_count})")

                packet_cnt = 0

                t0 = now



            # Parsing JSON des valeurs de doigts

            try:

                msg = json.loads(data.decode())

                with state_lock:

                    if not state['simu_mode']:

                        if not state['udp_connected']:

                            print("[UDP] CONNEXION ÉTABLIE - Réception de données depuis le PC")

                        state['udp_connected'] = True

                        state['packet_count'] += 1



                        for f in FINGERS:

                            if f in msg:

                                try:

                                    v = float(msg[f])

                                    state['values'][f] = max(0.0, min(1.0, v))

                                except Exception:

                                    pass

            except Exception as e:

                print(f"[UDP] Erreur de parsing: {e}")



        time.sleep(0.001)





# --------------------------------------------------------------------

# 3.2 Thread matériel : commandes des servos

#      -> ICI on ajoute le pilotage FLUIDE de la rotation du pouce

# --------------------------------------------------------------------

def hardware_thread(ctrl: HandController):

    """

    Boucle de contrôle matérielle :

    - convertit les valeurs 0..1 reçues en actions open/close pour les servos continus,

    - pilote la rotation du pouce (MG90S) de manière fluide via thumb_from_value().

    """

    logical = {f: 'open' for f in FINGERS}

    last_thumb_value = 0.0  # pour lisser les mouvements de rotation du pouce



    while True:

        # On récupère l'état courant (snapshot)

        with state_lock:

            targets = state['values'].copy()

            active = state['udp_connected'] or state['simu_mode']



        if active:

            try:

                # -----------------------------

                # 1) Pilotage rotation pouce

                # -----------------------------

                v_thumb = float(targets.get('pouce_articulation', 0.0))



                # On évite de piloter le servo si la variation est minime (anti-flutter)

                if abs(v_thumb - last_thumb_value) > 0.02:

                    # Mapping 0..1 -> angle_min..angle_max dans HandController

                    # (utilise angle_min/angle_max/angle_neutral définis dans servos_v2.json)

                    ctrl.thumb_from_value(v_thumb)

                    last_thumb_value = v_thumb



                # --------------------------------

                # 2) Pilotage des doigts continus

                # --------------------------------

                for f, val in targets.items():

                    curr_state = logical.get(f, 'open')



                    # Fermeture

                    if val > CLOSE_THRESHOLD and curr_state != 'close':

                        ctrl.close_finger(f, parallel=True)

                        logical[f] = 'close'



                    # Ouverture

                    elif val < OPEN_THRESHOLD and curr_state != 'open':

                        ctrl.open_finger(f, parallel=True)

                        logical[f] = 'open'



            except Exception as e:

                print(f"[HARDWARE] Erreur dans hardware_thread: {e}")

                traceback.print_exc()



        time.sleep(0.05)





# --------------------------------------------------------------------

# 4. UI PRINCIPALE

# --------------------------------------------------------------------

def build_ui():
    """Construit l'interface NiceGUI (en-tête, vidéo, panneau servo, main 3D)."""
    ui.add_head_html(CSS_STYLE)

    # ----- HEADER GLOBAL -----
    with ui.row().classes(
        'hud-header w-full h-[8vh] min-h-[60px] '
        'items-center justify-between px-6 sm:px-8'
    ):
        # Bloc titre
        with ui.row().classes('items-center gap-3'):
            ui.icon('hub', color='cyan-400').classes('text-2xl')
            with ui.column().classes('gap-0'):
                ui.label('NEURO-HAND V3.0') \
                    .classes('text-sm sm:text-lg text-cyan-400 font-bold tracking-widest')
                ui.label('NEURO-LINK // SYSTEM ONLINE') \
                    .classes('text-[10px] text-gray-400 tracking-wider')

        # Badge statut réseau
        status_label = ui.label('INIT') \
            .classes(
                'text-xs px-3 py-1 bg-cyan-900/40 text-cyan-300 '
                'border border-cyan-500 rounded font-bold'
            )

    # ----- BODY -----
    with ui.row().classes('w-full h-[92vh] p-4 gap-4 bg-transparent'):
        # =========================================================
        # Colonne gauche : flux vidéo + panneau de commandes
        # =========================================================
        with ui.column().classes('w-[25%] min-w-[260px] h-full gap-4'):
            # ----------------- Flux vidéo (caméra PC) -----------------
            with ui.card().classes(
                'w-full h-[30%] hud-panel p-0 overflow-hidden relative'
            ):
                # Header du panneau vidéo
                with ui.row().classes(
                    'hud-panel-header px-3 pt-2 pb-1 absolute top-0 left-0 right-0 '
                    'bg-black/50 z-20'
                ):
                    with ui.column().classes('gap-0'):
                        ui.label('OPTICAL FEED').classes(
                            'hud-section-title text-[9px]'
                        )
                        ui.label('MEDIAPIPE LIVE OVERLAY').classes(
                            'hud-section-caption'
                        )
                    ui.label('CAM-01').classes('hud-chip')

                # Image MJPEG
                ui.image(MJPEG_URL).classes(
                    'w-full h-full object-cover opacity-80'
                )

                # Cadre HUD vidéo déjà défini dans le CSS
                ui.html('''
                    <div class="video-hud-frame">
                        <div class="video-hud-corner vh-tl"></div>
                        <div class="video-hud-corner vh-tr"></div>
                        <div class="video-hud-corner vh-bl"></div>
                        <div class="video-hud-corner vh-br"></div>
                        <div class="scan-line"></div>
                    </div>
                ''', sanitize=False)

            # ----------------- Panneau de contrôle des servos -----------------
            with ui.card().classes(
                'w-full flex-1 hud-panel p-4 flex flex-col gap-3'
            ):
                # Header du panneau
                with ui.row().classes('hud-panel-header'):
                    with ui.column().classes('gap-0'):
                        ui.label('CONTROL NODES').classes('hud-section-title')
                        ui.label('HAND ACTUATOR BUS').classes(
                            'hud-section-caption'
                        )
                    ui.label('LIVE LINK').classes('hud-chip')

                # Infos rapides UDP + mode
                with ui.row().classes('justify-between items-center text-xs'):
                    with ui.column().classes('gap-0'):
                        ui.label('UDP ROUTE').classes('hud-mini-label')
                        ui.label(f'{LOCAL_IP}:{UDP_PORT}').classes('hud-value-strong')
                    with ui.column().classes('items-end gap-0'):
                        ui.label('MODE').classes('hud-mini-label')
                        sim_label = ui.label('TRACKING').classes('hud-value-strong')

                ui.html('<div class="hud-divider"></div>', sanitize=False)

                # --------- Stack de 3 grands boutons rectangulaires ---------
                with ui.column().classes('w-full gap-2'):
                    ui.button(
                        'OPEN',
                        icon='back_hand',
                        on_click=lambda: controller.open_hand()
                    ).classes('w-full control-btn h-12')

                    ui.button(
                        'CLOSE',
                        icon='pan_tool_alt',
                        on_click=lambda: controller.close_hand()
                    ).classes('w-full control-btn h-12')

                    # Toggle mode simulation
                    def toggle_sim():
                        with state_lock:
                            state['simu_mode'] = not state['simu_mode']
                            mode = 'SIMU MODE' if state['simu_mode'] else 'TRACKING'
                        sim_label.text = mode

                    ui.button(
                        'SIMULATION MODE',
                        icon='settings_backup_restore',
                        on_click=toggle_sim
                    ).classes('w-full sim-btn h-11')

                # --------- Section rotation pouce (sous-bloc) ---------
                ui.html('<div class="hud-divider"></div>', sanitize=False)
                ui.label('THUMB ROTATION (MG90S)').classes(
                    'hud-section-title text-[10px]'
                )
                ui.label('LINKED TO THUMB ARTICULATION CHANNEL').classes(
                    'hud-section-caption mb-1'
                )

                with ui.row().classes('w-full gap-2'):
                    ui.button(
                        '⟲ -1°',
                        on_click=lambda: controller.thumb_rotation_step(-1),
                    ).classes('flex-1 cyber-btn thumb-btn h-8')
                    ui.button(
                        '+1° ⟳',
                        on_click=lambda: controller.thumb_rotation_step(+1),
                    ).classes('flex-1 cyber-btn thumb-btn h-8')

                ui.button(
                    'CENTER THUMB',
                    on_click=lambda: controller.thumb_rotation_reset(),
                ).classes('w-full cyber-btn thumb-btn h-8 mt-1')

                # --------- EMERGENCY STOP circulaire en bas ---------
                ui.html('<div class="hud-divider"></div>', sanitize=False)
                with ui.row().classes('emergency-wrapper'):
                    ui.html('''
                        <div class="emergency-ring"></div>
                    ''', sanitize=False)
                    # On place le bouton par-dessus avec style absolute
                    # via une petite astuce NiceGUI : container + JS
                # Pour rester simple : on met le bouton dans le même wrapper
                with ui.row().classes('emergency-wrapper -mt-[125px]'):
                    ui.button(
                        'EMERGENCY\nSTOP',
                        on_click=lambda: controller.stop_all(),
                    ).classes('emergency-btn')

        # =========================================================
        # Carte centrale : main 3D + télémétrie (inchangé)
        # =========================================================
        with ui.card().classes(
            'flex-1 h-full hud-panel p-0 overflow-hidden relative bg-black'
        ):
            ui.html(HAND_3D_STRUCTURE, sanitize=False).classes('w-full h-full')
            ui.add_body_html(HAND_3D_JS)

    # ------------------------------------------------------------
    # Boucle de mise à jour UI -> envoi des valeurs à la main 3D
    # ------------------------------------------------------------
    loop_count = [0]

    def update_loop():
        try:
            loop_count[0] += 1

            # Simulation éventuelle + snapshot
            with state_lock:
                if state['simu_mode']:
                    t = time.time()
                    for i, f in enumerate(FINGERS):
                        state['values'][f] = (math.sin(t * 2 + i) + 1) / 2

                vals = state['values'].copy()
                connected = state['udp_connected'] or state['simu_mode']
                fps = state['fps']

            # Envoi vers le JS de la main 3D
            json_data = json.dumps(vals)
            ui.run_javascript(
                "try { "
                "if (typeof window.updateHandData === 'function') "
                f"window.updateHandData('{json_data}'); "
                "} catch(e) { console.error('updateHandData error:', e); }"
            )

            # Mise à jour du badge de statut global
            status_label.text = f"ONLINE ({fps} TPS)" if connected else "OFFLINE"
            if connected:
                status_label.classes(
                    replace='text-xs px-3 py-1 bg-green-900/40 text-green-300 '
                            'border border-green-500 rounded font-bold'
                )
            else:
                status_label.classes(
                    replace='text-xs px-3 py-1 bg-red-900/40 text-red-500 '
                            'border border-red-500 rounded font-bold'
                )
        except Exception as e:
            print(f"[ERROR] update_loop: {e}")
            traceback.print_exc()

    ui.timer(0.05, update_loop)


# --------------------------------------------------------------------

# 6. RUN

# --------------------------------------------------------------------

if __name__ in {"__main__", "__mp_main__"}:

    signal.signal(signal.SIGINT, signal_handler)



    try:

        controller = HandController()

    except Exception as e:

        print(f"[ERROR] Impossible d'initialiser HandController: {e}")

        sys.exit(1)



    print("[INIT] Démarrage des threads de communication...")

    threading.Thread(target=receiver_thread, daemon=True).start()

    threading.Thread(target=hardware_thread, args=(controller,), daemon=True).start()

    time.sleep(0.5)



    # Exposer le dossier /assets pour le chargement 3D

    ASSETS_DIR = BASE_DIR / 'assets'

    if not ASSETS_DIR.exists():

        print("[WARNING] Le dossier '/assets' n'existe pas. "

              "Créez-le et placez-y main_modele.obj.")

        ASSETS_DIR.mkdir(exist_ok=True)



    app.add_static_files('/assets', ASSETS_DIR)

    print("[ASSET] Dossier '/assets' exposé pour le chargement 3D.")



    @ui.page('/')

    def index():

        build_ui()



    ui.run(

        host='0.0.0.0',

        port=8080,

        dark=True,

        reload=False,

        title='NEURO-LINK V2.0'

    )





