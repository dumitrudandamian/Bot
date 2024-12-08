import signal
import sys

class SignalHandler:
    @staticmethod
    def make_handler(workbook):
        def signal_handler(sig, frame):
            print('You pressed Ctrl+C!')
            print('Performing cleanup...')
            workbook.close()
            sys.exit(0)
        return signal_handler