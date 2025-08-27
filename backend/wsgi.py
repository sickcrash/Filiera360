from app import app

"""
debug = true -> reload = true
Flask crea due processi all’avvio:
    Uno è il monitor che osserva i file.
    L’altro è il processo reale che esegue la tua app.
    
    Siccome ho usato i threadPool globali, ne avrai 2. 
    Per perforamnce reali, disattivare il reload -> use_reloader=False
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
