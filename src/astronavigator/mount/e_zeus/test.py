
import time

from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2Protocol, EZeus2_RA_DEC, EZeus2_Direction, EZeus2_Speed


port = "/dev/tty.usbserial-A906VB1T"
mount = EZeus2Protocol(port)
mount.connect()

print(f"Version: {mount.get_version()}")
print(f"Status: {mount.get_status()}")
print(f"Position: {mount.get_position()}")


input("Press Enter to start driving...")
mount.drive(EZeus2_RA_DEC.RA, EZeus2_Direction.FORWARD, EZeus2_Speed.FAST, None)

time.sleep(3)

print(f"Position: {mount.get_position()}")

mount.stop(to_siderial=True)

mount.disconnect()