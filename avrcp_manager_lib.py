import dbus
import time

# MediaPlayer API: https://github.com/pauloborges/bluez/blob/master/doc/media-api.txt


class AvrcpManager:
    def __init__(self, bus):
        self.bus = bus
        self.player = self.get_player()

        self.print_player()

        bus.add_signal_receiver(self.interfaces_added,
                                dbus_interface="org.freedesktop.DBus.ObjectManager",
                                signal_name="InterfacesAdded")

        bus.add_signal_receiver(self.properties_changed,
                                dbus_interface="org.freedesktop.DBus.Properties",
                                signal_name="PropertiesChanged",
                                arg0="org.bluez.Device1",
                                path_keyword="path")

    def print_player(self):
        if self.player:
            print("Player detected at", self.player)
        else:
            print("No player detected")

    def assert_player(self):
        if self.player is None:
            print("No player detected")
            return False

        return True

    def get_player(self):
        proxy = self.bus.get_object('org.bluez', '/')
        manager = dbus.Interface(proxy, dbus_interface='org.freedesktop.DBus.ObjectManager')
        objects = manager.GetManagedObjects()
        for path, interfaces in objects.items():
            if 'org.bluez.MediaPlayer1' in interfaces.keys():
                return path

    def interfaces_added(self, path, interfaces):
        if "org.bluez.MediaPlayer1" in interfaces:
            self.player = path
            self.print_player()

    def properties_changed(self, interface, changed, invalidated, path):
        if interface != "org.bluez.Device1":
            return

        if 'Connected' in changed and not changed['Connected']:
            if self.player.startswith(path):
                self.player = None
                self.print_player()

    def send_media_command(self, command):
        if not self.assert_player():
            return

        proxy = self.bus.get_object('org.bluez', self.player)
        iface = dbus.Interface(proxy, dbus_interface='org.bluez.MediaPlayer1')
        method = getattr(iface, command)
        method()

    def get_media_property(self):
        if not self.assert_player():
            return

        proxy = self.bus.get_object('org.bluez', self.player)
        props_iface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        player_props = props_iface.GetAll('org.bluez.MediaPlayer1')

        status = player_props.get("Status", "")
        position = player_props.get("Position", "")
        track = player_props.get('Track', "")
        print(track.get('Title', 'unknown'), '-', track.get('Artist', 'unknown'), status, position)

    def status(self):
        self.get_media_property()

    def pause(self):
        self.send_media_command('Pause')

    def resume(self):
        self.send_media_command('Play')

    def next(self):
        self.send_media_command('Next')

    def prev(self):
        self.send_media_command('Previous')
        time.sleep(0.1)
        self.send_media_command('Previous')
