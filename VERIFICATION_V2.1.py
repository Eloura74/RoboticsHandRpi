#!/usr/bin/env python3
"""
Script de vérification de l'intégrité de NEURO-HAND V2.1.
Vérifie que tous les fichiers critiques existent et sont cohérents.

Usage:
    python VERIFICATION_V2.1.py
"""

import sys
from pathlib import Path


class Colors:
    """Codes couleur ANSI pour terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def check_file(path: Path, description: str) -> bool:
    """Vérifie qu'un fichier existe."""
    if path.exists():
        print(f"{Colors.GREEN}✓{Colors.RESET} {description}: {Colors.BLUE}{path}{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.RESET} {description}: {Colors.RED}{path} MANQUANT{Colors.RESET}")
        return False


def check_no_file(path: Path, description: str) -> bool:
    """Vérifie qu'un fichier a bien été supprimé."""
    if not path.exists():
        print(f"{Colors.GREEN}✓{Colors.RESET} {description}: {Colors.GREEN}Correctement supprimé{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.RESET} {description}: {Colors.RED}{path} EXISTE ENCORE{Colors.RESET}")
        return False


def check_import_in_file(file_path: Path, bad_import: str) -> bool:
    """Vérifie qu'un import n'est pas présent dans un fichier."""
    if not file_path.exists():
        return True  # Si le fichier n'existe pas, on ne peut pas vérifier
    
    try:
        content = file_path.read_text(encoding='utf-8')
        if bad_import in content:
            print(f"{Colors.RED}✗{Colors.RESET} {file_path}: Contient encore '{bad_import}'")
            return False
        else:
            print(f"{Colors.GREEN}✓{Colors.RESET} {file_path}: Pas d'import obsolète")
            return True
    except Exception as e:
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {file_path}: Erreur lecture ({e})")
        return False


def main():
    """Point d'entrée principal."""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}VÉRIFICATION NEURO-HAND V2.1{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    base_dir = Path(__file__).parent
    checks_passed = 0
    checks_total = 0
    
    # ========================================
    # 1. Fichiers core/
    # ========================================
    print(f"\n{Colors.BOLD}[1] Vérification core/{Colors.RESET}")
    checks_total += 4
    checks_passed += check_file(base_dir / "core" / "__init__.py", "core/__init__.py")
    checks_passed += check_file(base_dir / "core" / "hand_controller.py", "HandController")
    checks_passed += check_file(base_dir / "core" / "config_loader.py", "ConfigLoader")
    checks_passed += check_file(base_dir / "core" / "logger.py", "Logger")
    
    # ========================================
    # 2. Configuration
    # ========================================
    print(f"\n{Colors.BOLD}[2] Vérification configuration{Colors.RESET}")
    checks_total += 3
    checks_passed += check_file(base_dir / "config.yaml", "config.yaml (unifié)")
    checks_passed += check_file(base_dir / "config" / "servos_v2.json", "servos_v2.json")
    checks_passed += check_no_file(base_dir / "apps" / "dashboard_config.py", "dashboard_config.py (SUPPRIMÉ)")
    
    # ========================================
    # 3. Tests
    # ========================================
    print(f"\n{Colors.BOLD}[3] Vérification tests/{Colors.RESET}")
    checks_total += 4
    checks_passed += check_file(base_dir / "tests" / "__init__.py", "tests/__init__.py")
    checks_passed += check_file(base_dir / "tests" / "conftest.py", "Fixtures pytest")
    checks_passed += check_file(base_dir / "tests" / "test_hand_controller.py", "Tests HandController")
    checks_passed += check_file(base_dir / "tests" / "test_config_loader.py", "Tests ConfigLoader")
    
    # ========================================
    # 4. Tools
    # ========================================
    print(f"\n{Colors.BOLD}[4] Vérification tools/{Colors.RESET}")
    checks_total += 2
    checks_passed += check_file(base_dir / "tools" / "monitor_rpi.py", "Monitoring système")
    checks_passed += check_file(base_dir / "tools" / "calibrate_servos.py", "Calibration servos")
    
    # ========================================
    # 5. Apps
    # ========================================
    print(f"\n{Colors.BOLD}[5] Vérification apps/{Colors.RESET}")
    checks_total += 3
    checks_passed += check_file(base_dir / "apps" / "neuro_dashboardV2_new.py", "Dashboard principal")
    checks_passed += check_file(base_dir / "apps" / "dashboard_network.py", "Threads réseau")
    checks_passed += check_file(base_dir / "apps" / "dashboard_ui.py", "Interface UI")
    
    # ========================================
    # 6. Vérification imports obsolètes
    # ========================================
    print(f"\n{Colors.BOLD}[6] Vérification imports obsolètes{Colors.RESET}")
    bad_import = "from apps.dashboard_config import"
    
    files_to_check = [
        base_dir / "apps" / "neuro_dashboardV2_new.py",
        base_dir / "apps" / "dashboard_network.py",
        base_dir / "apps" / "dashboard_ui.py",
        base_dir / "apps" / "udp_server_v2.py",
    ]
    
    for file_path in files_to_check:
        if file_path.exists():
            checks_total += 1
            checks_passed += check_import_in_file(file_path, bad_import)
    
    # ========================================
    # 7. Documentation
    # ========================================
    print(f"\n{Colors.BOLD}[7] Vérification documentation{Colors.RESET}")
    checks_total += 3
    checks_passed += check_file(base_dir / "README.md", "README principal")
    checks_passed += check_file(base_dir / "README_V2.1.md", "README V2.1 (nouveautés)")
    checks_passed += check_file(base_dir / "CHANGELOG.md", "CHANGELOG")
    
    # ========================================
    # Résumé
    # ========================================
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    success_rate = (checks_passed / checks_total * 100) if checks_total > 0 else 0
    
    if checks_passed == checks_total:
        color = Colors.GREEN
        status = "✅ EXCELLENT"
    elif success_rate >= 80:
        color = Colors.YELLOW
        status = "⚠️  ATTENTION"
    else:
        color = Colors.RED
        status = "❌ PROBLÈMES DÉTECTÉS"
    
    print(f"{color}{Colors.BOLD}{status}{Colors.RESET}")
    print(f"Vérifications réussies : {color}{checks_passed}/{checks_total}{Colors.RESET} ({success_rate:.1f}%)")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    if checks_passed < checks_total:
        print(f"{Colors.YELLOW}⚠️  Certains fichiers manquent ou contiennent des imports obsolètes.{Colors.RESET}")
        print(f"{Colors.YELLOW}   Voir détails ci-dessus.{Colors.RESET}\n")
        return 1
    else:
        print(f"{Colors.GREEN}🎉 V2.1 est prêt pour production !{Colors.RESET}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
