# midi_engine.py
import mido
import queue

class MidiEngine:
    def __init__(self):
        self.port = None
        self.msg_queue = queue.Queue()

    def get_ports(self):
        try:
            return mido.get_input_names()
        except Exception:
            return []

    def connect(self, port_name):
        if not port_name: 
            return False
        if self.port:
            self.port.close()
        
        self.port = mido.open_input(port_name, callback=self._midi_callback)
        return True

    def _midi_callback(self, msg):
        # Background thread callback
        if msg.type == 'note_on' and msg.velocity > 0:
            self.msg_queue.put(msg)

    def get_messages(self):
        """Yields all messages currently in the queue for the main UI thread"""
        msgs = []
        while not self.msg_queue.empty():
            msgs.append(self.msg_queue.get())
        return msgs

    def close(self):
        if self.port:
            self.port.close()