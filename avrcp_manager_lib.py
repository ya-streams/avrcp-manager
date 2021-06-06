import dbus
import time

# MediaPlayer API: https://github.com/pauloborges/bluez/blob/master/doc/media-api.txt

class TrackMetaInfo:
    def __init__(self):
        self.artist = '[unknown]'
        self.title = '[unknown]'
        self.status = ''
        self.position = 0


class AvrcpManager:
    def __init__(self, bus):
        self.track = TrackMetaInfo()
        self.bus = bus
        self.player = self.get_player()
        self.get_current_track()

        self.print_player()

        self.receivers = []
        self.receivers.append(bus.add_signal_receiver(self.interfaces_added,
                                                      dbus_interface="org.freedesktop.DBus.ObjectManager",
                                                      signal_name="InterfacesAdded"))

        self.receivers.append(bus.add_signal_receiver(self.properties_changed,
                                                      dbus_interface="org.freedesktop.DBus.Properties",
                                                      signal_name="PropertiesChanged",
                                                      arg0="org.bluez.Device1",
                                                      path_keyword="path"))

        self.receivers.append(bus.add_signal_receiver(self.properties_changed,
                                                      dbus_interface="org.freedesktop.DBus.Properties",
                                                      signal_name="PropertiesChanged",
                                                      arg0="org.bluez.MediaPlayer1",
                                                      path_keyword="path"))

    def stop(self):
        for handler in self.receivers:
            self.bus.remove_signal_receiver(handler)

    def print_player(self):
        if self.player:
            print("Player detected at", self.player)
        else:
            print("No player detected")

    def assert_player(self):
        return self.player is not None

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
        if not self.assert_player():
            return

        if interface == "org.bluez.Device1":
            if 'Connected' in changed and not changed['Connected']:
                if self.player.startswith(path):
                    self.player = None
                    self.print_player()

        if interface == "org.bluez.MediaPlayer1":
            self.update_track(changed)

    def update_track(self, changed):
        if "Status" in changed:
            self.track.status = changed["Status"]

        if "Position" in changed:
            self.track.position = changed["Position"]

        if "Track" in changed:
            track_props = changed["Track"]
            if "Title" in track_props:
                self.track.title = track_props['Title']
            if "Artist" in track_props:
                self.track.artist = track_props['Artist']

    def send_media_command(self, command):
        if not self.assert_player():
            return

        proxy = self.bus.get_object('org.bluez', self.player)
        iface = dbus.Interface(proxy, dbus_interface='org.bluez.MediaPlayer1')
        method = getattr(iface, command)
        method()

    def get_current_track(self):
        if not self.assert_player():
            return

        proxy = self.bus.get_object('org.bluez', self.player)
        props_iface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        player_props = props_iface.GetAll('org.bluez.MediaPlayer1')
        self.update_track(player_props)

    def print_status(self):
        print(self.track.artist, '-', self.track.title, self.track.status, self.track.position)

    def status(self):
        self.print_status()

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
