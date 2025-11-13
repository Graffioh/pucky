import sys
import threading
import time


def print_pucky_header():
    """Print the Pucky ASCII art header."""
    pucky_ascii_header = r"""
            _       _ |     
            |_) |_| (_ |< \/ 
            |             /  
                   -                       
                 :=+-                    
               +:...:=++=====            
            %*-.           ..:+=         
         **=:.                  :==      
       **--:.                     ==     
      #++-:                        -+    
     *===-:.                       .=    
**+  =---::.                  ......-.   
  .+=--::-:.     ..:=++=.   .       .=   
    .:*-:-:.:+=::.                   .=  
       .:--..                          :=
-..    ...::.                    ....:::=
#==:.   .:-.:.         ..-+*++-::...   .=
  %#*+:::::::.   .-=-..              .-= 
      +:--:-:::. .                 .-+   
       *----=-==...              -+-     
        *#*====--:::.          :+        
            #**==--:.            -+      
             *+=---..             :+     
            %+=---:                :+    
            +=-:::..                :*   
           =:-:.:-:.                 -*                 
"""
    print(pucky_ascii_header)
    print("Type 'quit' or 'q' to end the conversation\n")


class Spinner:
    """A simple ASCII spinner for loading indicators."""

    def __init__(self, message="🐤 Pucky is thinking"):
        self.message = message
        self.spinner_chars = "|/-\\"
        self.stop_spinner = False
        self.spinner_thread = None

    def _spin(self):
        """Internal method that runs the spinner animation."""
        i = 0
        while not self.stop_spinner:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f"\r{self.message} {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        """Start the spinner in a separate thread."""
        self.stop_spinner = False
        self.spinner_thread = threading.Thread(target=self._spin, daemon=True)
        self.spinner_thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.2)
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()
