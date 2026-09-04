"""
Lylis Karaoke Studio - License Key Generator CLI Tool
Used by the software author (gegacy) to generate cryptographic, hardware-locked license keys.
"""
import sys
import os
import argparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.license_manager import LicenseManager, MASTER_KEY

def main():
    parser = argparse.ArgumentParser(description="Lylis Karaoke Studio - License Key Generator")
    parser.add_argument("--machine-id", "-m", help="Client Machine ID (e.g. XXXX-XXXX-XXXX-XXXX). If omitted, uses current machine.")
    parser.add_argument("--name", "-n", help="Client Name or Email", default="gegacy Studio User")
    parser.add_argument("--tier", "-t", help="License Tier (PRO or STUDIO)", default="PRO", choices=["PRO", "STUDIO"])
    parser.add_argument("--show-local", "-l", action="store_true", help="Display local machine ID and current status")
    parser.add_argument("--activate-local", "-a", action="store_true", help="Instantly activate current machine with a generated key")

    args = parser.parse_args()

    local_mach = LicenseManager.get_machine_id()

    if args.show_local:
        print("=" * 65)
        print("  Lylis Karaoke Studio - Local Machine Status")
        print("=" * 65)
        print(f"Local Machine ID : {local_mach}")
        print(f"Activation Status: {'ACTIVATED' if LicenseManager.is_activated() else 'NOT ACTIVATED'}")
        info = LicenseManager.get_license_info()
        print(f"Licensee         : {info.get('name')}")
        print(f"License Key      : {info.get('key')}")
        print(f"License Tier     : {info.get('tier')}")
        return

    mach_id = args.machine_id.strip() if args.machine_id else local_mach
    client_name = args.name.strip()
    tier = args.tier.strip().upper()

    key = LicenseManager.generate_license_key(mach_id, client_name, tier)

    print("=" * 65)
    print("  Lylis Karaoke Studio - Official License Key Generated")
    print("=" * 65)
    print(f"Client Name : {client_name}")
    print(f"Machine ID  : {mach_id}")
    print(f"License Tier: {tier}")
    print(f"License Key : {key}")
    print(f"Master Key  : {MASTER_KEY}")
    print("=" * 65)
    print("\nSend this key to your client along with their registered name.")

    if args.activate_local or (not args.machine_id and not args.show_local):
        ok, msg = LicenseManager.activate(key, client_name, tier)
        print(f"\n[Local Activation]: {msg}")

if __name__ == "__main__":
    main()
