from dotenv import load_dotenv
from google.genai import Client as GoogleClient

load_dotenv()

def main():
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

    # Create a client (for Gemini Developer API)
    # Make sure to set GOOGLE_API_KEY environment variable (automatically loaded from .env file)
    google_client = GoogleClient()

    response = google_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents="Hello, who are you?",
    )
    print(response.text)


if __name__ == "__main__":
    main()
